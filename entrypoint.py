import os
import sys
import argparse
from datetime import datetime

from transpose_chords import transpose_text
from utils import outputs_dir, make_pdf, slugify, resolve_output_stem, is_supported_output_file


def _validate_semitones(value: int, arg_name: str) -> int:
    if value < 0 or value > 11:
        raise SystemExit(f"{arg_name} must be between 0 and 11.")
    return value


def prompt_capo() -> int:
    sys.stderr.write("Capo number? (0-11): ")
    sys.stderr.flush()
    line = sys.stdin.readline()
    if not line:
        raise SystemExit("No capo provided.")
    capo = int(line.strip())
    return _validate_semitones(capo, "Capo")


def main():
    parser = argparse.ArgumentParser(description="CapoToKeys CLI (no LLM)")
    parser.add_argument("--list", action="store_true", help="List saved outputs")
    parser.add_argument("--capo", type=int, help="Capo number (0-11)")
    parser.add_argument("--semitones", type=int, help="Transpose by semitones (0-11; overrides capo)")
    parser.add_argument("--title", default="Chord Sheet", help="Title for file/PDF")
    parser.add_argument("--pdf", action="store_true", help="Also generate PDF")
    parser.add_argument("--no-save", action="store_true", help="Do not save output")
    parser.add_argument(
        "--conflict",
        choices=["suffix", "overwrite"],
        default=os.getenv("OUTPUT_CONFLICT_MODE", "suffix"),
        help="When filename exists: suffix (default) or overwrite",
    )
    args = parser.parse_args()

    outdir = outputs_dir()

    if args.list:
        files = sorted((p for p in outdir.glob("*") if is_supported_output_file(p)), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            print("No outputs found.")
            return
        for p in files[:200]:
            ts = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            size_kb = p.stat().st_size / 1024
            print(f"{ts}  {size_kb:7.1f} KB  {p.name}")
        return

    interactive = sys.stdin.isatty()

    if args.capo is not None:
        args.capo = _validate_semitones(args.capo, "--capo")
    if args.semitones is not None:
        args.semitones = _validate_semitones(args.semitones, "--semitones")

    if args.semitones is not None:
        semitones = args.semitones
    elif args.capo is not None:
        semitones = args.capo
    else:
        if not interactive:
            raise SystemExit("Provide --capo or --semitones")
        semitones = prompt_capo()

    if interactive:
        sys.stderr.write(
            "Paste chord sheet, then press Ctrl+D (Linux/macOS) "
            "or Ctrl+Z then Enter (Windows)\n\n"
        )
        sys.stderr.flush()

    raw = sys.stdin.read()
    if not raw.strip():
        raise SystemExit("No input received.")

    result = transpose_text(raw, semitones)
    sys.stdout.write(result)

    if args.no_save:
        return

    base_stem = f"{slugify(args.title)}-capo{semitones}"
    output_exts = ["txt"]
    if args.pdf:
        output_exts.append("pdf")

    final_stem = resolve_output_stem(outdir, base_stem, output_exts, mode=args.conflict)

    txt_path = outdir / f"{final_stem}.txt"
    txt_path.write_text(result, encoding="utf-8")

    if args.pdf:
        pdf_path = outdir / f"{final_stem}.pdf"
        make_pdf(result, pdf_path, title=args.title)


if __name__ == "__main__":
    main()

