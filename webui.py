import os
from datetime import datetime
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash, current_app

from transpose_chords import transpose_text
from utils import (
    outputs_dir,
    make_pdf,
    slugify,
    resolve_output_stem,
    describe_output_group,
    parse_output_stem,
    is_supported_output_file,
)

DEFAULT_FLASK_SECRET = "capotokeys-local"


def _env_int(name: str, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        value = default
    else:
        try:
            value = int(raw)
        except ValueError:
            value = default

    if minimum is not None and value < minimum:
        value = minimum
    if maximum is not None and value > maximum:
        value = maximum
    return value


def _is_production_runtime() -> bool:
    app_env = os.getenv("APP_ENV", "").strip().lower()
    flask_env = os.getenv("FLASK_ENV", "").strip().lower()
    return app_env == "production" or flask_env == "production"


def _validate_runtime_config() -> None:
    if _is_production_runtime():
        secret = os.getenv("FLASK_SECRET", "").strip()
        if not secret or secret == DEFAULT_FLASK_SECRET:
            raise RuntimeError("FLASK_SECRET must be set to a strong value in production.")


def _safe_output_target(filename: str):
    outdir = outputs_dir()
    target = outdir / filename

    if not target.exists():
        return outdir, target, "File not found."

    try:
        target.resolve().relative_to(outdir.resolve())
    except ValueError:
        return outdir, target, "Invalid file path."

    return outdir, target, None


def _collect_output_groups(outdir, list_limit: int):
    files = sorted(outdir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[:list_limit]
    groups_by_key = {}

    for p in files:
        if not is_supported_output_file(p):
            continue

        stat = p.stat()
        stem = p.stem
        ext = p.suffix.lower().lstrip(".")
        group_key, label = describe_output_group(stem)

        if group_key not in groups_by_key:
            groups_by_key[group_key] = {
                "key": group_key,
                "label": label,
                "mtime_epoch": stat.st_mtime,
                "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "files": [],
            }

        g = groups_by_key[group_key]
        if stat.st_mtime > g["mtime_epoch"]:
            g["mtime_epoch"] = stat.st_mtime
            g["mtime"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

        g["files"].append(
            {
                "name": p.name,
                "ext": ext,
                "size_kb": f"{stat.st_size / 1024:.1f}",
                "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    groups = sorted(groups_by_key.values(), key=lambda x: x["mtime_epoch"], reverse=True)

    ext_order = {"pdf": 0, "txt": 1}
    for g in groups:
        g["files"] = sorted(g["files"], key=lambda x: (ext_order.get(x["ext"], 99), x["name"]))

    return groups


def _register_routes(app: Flask) -> None:
    @app.errorhandler(413)
    def too_large_payload(_):
        flash("Request body is too large. Reduce input size and try again.")
        return redirect(url_for("home"))

    @app.get("/")
    def home():
        return render_template("index.html", capo=0, title="", text="", result=None, txt_name=None, pdf_name=None)

    @app.post("/generate")
    def generate():
        text = request.form.get("text", "")
        title = request.form.get("title", "") or "Chord Sheet"
        capo = request.form.get("capo", "0")

        try:
            capo_i = int(capo)
            if capo_i < 0 or capo_i > 11:
                raise ValueError()
        except Exception:
            flash("Capo must be a number from 0 to 11.")
            return redirect(url_for("home"))

        if not text.strip():
            flash("Paste some chord sheet text first.")
            return redirect(url_for("home"))

        max_text_length = current_app.config["MAX_TEXT_LENGTH"]
        if len(text) > max_text_length:
            flash(f"Input is too large. Maximum allowed text length is {max_text_length} characters.")
            return redirect(url_for("home"))

        result = transpose_text(text, capo_i)

        outdir = outputs_dir()
        conflict_mode = os.getenv("OUTPUT_CONFLICT_MODE", "suffix")
        base_stem = f"{slugify(title)}-capo{capo_i}"
        final_stem = resolve_output_stem(outdir, base_stem, ["txt", "pdf"], mode=conflict_mode)

        txt_name = f"{final_stem}.txt"
        pdf_name = f"{final_stem}.pdf"

        (outdir / txt_name).write_text(result, encoding="utf-8")
        make_pdf(result, outdir / pdf_name, title=title)

        if final_stem != base_stem and conflict_mode.strip().lower() != "overwrite":
            flash(f"Existing file detected. Saved as {final_stem}.*")

        return render_template(
            "index.html",
            capo=capo_i,
            title=title,
            text=text,
            result=result,
            txt_name=txt_name,
            pdf_name=pdf_name,
        )

    @app.get("/outputs")
    def list_outputs():
        outdir = outputs_dir()
        list_limit = current_app.config["OUTPUT_LIST_LIMIT"]
        groups = _collect_output_groups(outdir, list_limit)

        selected_key = request.args.get("group")
        if not selected_key and groups:
            selected_key = groups[0]["key"]

        selected_group = None
        if selected_key:
            selected_group = next((g for g in groups if g["key"] == selected_key), None)

        return render_template("list.html", groups=groups, selected_group=selected_group, selected_key=selected_key)

    @app.post("/delete-group")
    def delete_group():
        group_key = (request.form.get("group_key") or "").strip()
        if not group_key:
            flash("Invalid group key.")
            return redirect(url_for("list_outputs"))

        outdir = outputs_dir()
        deleted = 0

        for p in outdir.glob("*"):
            if not is_supported_output_file(p):
                continue
            parsed = parse_output_stem(p.stem)
            if parsed["group_key"] != group_key:
                continue
            p.unlink(missing_ok=True)
            deleted += 1

        if deleted == 0:
            flash("No files found for that group.")
        else:
            flash(f"Deleted {deleted} files from group.")

        return redirect(url_for("list_outputs"))

    @app.get("/view/<path:filename>")
    def view_file(filename):
        outdir, _, err = _safe_output_target(filename)
        if err:
            flash(err)
            return redirect(url_for("list_outputs"))

        return send_from_directory(outdir, filename, as_attachment=False)

    @app.get("/download/<path:filename>")
    def download(filename):
        outdir, _, err = _safe_output_target(filename)
        if err:
            flash(err)
            return redirect(url_for("list_outputs"))

        return send_from_directory(outdir, filename, as_attachment=True)

    @app.post("/delete/<path:filename>")
    def delete_file(filename):
        outdir, target, err = _safe_output_target(filename)
        if err:
            flash(err)
            return redirect(url_for("list_outputs"))

        target.unlink()
        flash(f"Deleted {filename}")
        return redirect(url_for("list_outputs"))


def create_app(config: dict | None = None) -> Flask:
    _validate_runtime_config()

    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET", DEFAULT_FLASK_SECRET)

    app.config["MAX_CONTENT_LENGTH"] = _env_int("MAX_REQUEST_BYTES", 1_048_576, minimum=1_024, maximum=20_000_000)
    app.config["MAX_TEXT_LENGTH"] = _env_int("MAX_TEXT_LENGTH", 200_000, minimum=1_000, maximum=1_000_000)
    app.config["OUTPUT_LIST_LIMIT"] = _env_int("OUTPUT_LIST_LIMIT", 300, minimum=1, maximum=5_000)

    if config:
        app.config.update(config)

    _register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "4506"))
    app.run(host=host, port=port)
