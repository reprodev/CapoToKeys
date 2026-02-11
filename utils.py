import os
import re
from pathlib import Path
from typing import Iterable

SUPPORTED_OUTPUT_EXTENSIONS = {"txt", "pdf"}

# Accept both legacy and new naming: [timestamp-]title-capoN[-revision]
LEGACY_PREFIX_RE = re.compile(r"^(?P<stamp>\d{8}-\d{6})-(?P<rest>.+)$")
OUTPUT_STEM_RE = re.compile(r"^(?P<title>[a-z0-9]+(?:-[a-z0-9]+)*)-capo(?P<capo>\d{1,2})(?:-(?P<rev>\d+))?$")


def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "chord-sheet"


def outputs_dir() -> Path:
    data_dir = Path(os.getenv("DATA_DIR", "/data"))
    out = data_dir / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _normalize_extension(ext: str) -> str:
    return ext[1:] if ext.startswith(".") else ext


def is_supported_output_file(path: Path) -> bool:
    if not path.is_file():
        return False
    ext = path.suffix.lower().lstrip(".")
    return ext in SUPPORTED_OUTPUT_EXTENSIONS


def resolve_output_stem(outdir: Path, base_stem: str, extensions: Iterable[str], mode: str = "suffix") -> str:
    """
    Resolve a shared stem for one or more related outputs (for example txt + pdf).

    mode:
      - overwrite: always use base stem
      - suffix: append -2, -3, ... when any output with that stem already exists
    """
    mode = (mode or "suffix").strip().lower()
    exts = [_normalize_extension(ext) for ext in extensions]

    if mode == "overwrite":
        return base_stem

    def exists_for_stem(stem: str) -> bool:
        for ext in exts:
            if (outdir / f"{stem}.{ext}").exists():
                return True
        return False

    if not exists_for_stem(base_stem):
        return base_stem

    i = 2
    while True:
        candidate = f"{base_stem}-{i}"
        if not exists_for_stem(candidate):
            return candidate
        i += 1


def parse_output_stem(stem: str) -> dict:
    """
    Parse output stem into normalized metadata for archive grouping.
    """
    legacy = LEGACY_PREFIX_RE.match(stem)
    core = legacy.group("rest") if legacy else stem

    m = OUTPUT_STEM_RE.match(core)
    if not m:
        return {
            "group_key": core,
            "label": core,
            "title_slug": None,
            "capo": None,
            "revision": None,
            "is_legacy": bool(legacy),
            "valid_schema": False,
        }

    title_slug = m.group("title")
    capo = int(m.group("capo"))
    revision_raw = m.group("rev")
    revision = int(revision_raw) if revision_raw else None

    if capo < 0 or capo > 11:
        return {
            "group_key": core,
            "label": core,
            "title_slug": title_slug,
            "capo": capo,
            "revision": revision,
            "is_legacy": bool(legacy),
            "valid_schema": False,
        }

    title_display = " ".join(part.capitalize() for part in title_slug.split("-") if part) or "Chord Sheet"
    if revision:
        label = f"{title_display} (Capo {capo}, Version {revision})"
    else:
        label = f"{title_display} (Capo {capo})"

    return {
        "group_key": core,
        "label": label,
        "title_slug": title_slug,
        "capo": capo,
        "revision": revision,
        "is_legacy": bool(legacy),
        "valid_schema": True,
    }


def describe_output_group(stem: str) -> tuple[str, str]:
    parsed = parse_output_stem(stem)
    return (parsed["group_key"], parsed["label"])


def _pdf_int_setting(name: str, default: int, minimum: int, maximum: int, overrides: dict | None = None) -> int:
    if overrides and name in overrides:
        raw = overrides[name]
    else:
        raw = os.getenv(name)

    if raw is None:
        value = default
    else:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = default

    if value < minimum:
        value = minimum
    if value > maximum:
        value = maximum
    return value


def get_pdf_layout_options(overrides: dict | None = None) -> dict:
    """
    Return validated PDF layout options from env/overrides.
    """
    return {
        "left_margin": _pdf_int_setting("PDF_LEFT_MARGIN", 54, 20, 200, overrides),
        "top_margin": _pdf_int_setting("PDF_TOP_MARGIN", 62, 20, 200, overrides),
        "bottom_margin": _pdf_int_setting("PDF_BOTTOM_MARGIN", 54, 20, 200, overrides),
        "title_size": _pdf_int_setting("PDF_TITLE_SIZE", 14, 8, 48, overrides),
        "body_size": _pdf_int_setting("PDF_BODY_SIZE", 10, 6, 24, overrides),
        "line_height": _pdf_int_setting("PDF_LINE_HEIGHT", 12, 8, 40, overrides),
        "max_width_chars": _pdf_int_setting("PDF_MAX_WIDTH_CHARS", 110, 40, 300, overrides),
    }


def make_pdf(text: str, pdf_path: Path, title: str, layout_overrides: dict | None = None):
    """
    Common PDF generation logic used by both Web UI and CLI.
    """
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise RuntimeError("PDF generation requires reportlab. Install dependencies from requirements.txt") from exc

    class NumberedCanvas(canvas.Canvas):
        """
        Canvas that supports 'Page X of Y' by buffering pages
        and writing the final total during save().
        """

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self._draw_page_number(total_pages)
                super().showPage()
            super().save()

        def _draw_page_number(self, total_pages: int):
            page_num = self.getPageNumber()
            page_text = f"Page {page_num} of {total_pages}"
            self.setFont("Helvetica", 9)

            page_width, _ = self._pagesize
            right_margin = 54
            bottom_margin = 54
            self.drawRightString(page_width - right_margin, bottom_margin - 18, page_text)

    layout = get_pdf_layout_options(layout_overrides)

    c = NumberedCanvas(str(pdf_path), pagesize=LETTER)
    width, height = LETTER

    left_margin = layout["left_margin"]
    top_margin = layout["top_margin"]
    bottom_margin = layout["bottom_margin"]
    content_x = left_margin + 10

    title_font = "Helvetica-Bold"
    title_size = layout["title_size"]
    body_font = "Courier"
    body_size = layout["body_size"]
    line_height = layout["line_height"]

    c.setTitle(title)
    title_y = height - top_margin

    page_marker_re = re.compile(r"^\s*Page\s+\d+\s*/\s*\d+\s*$", re.IGNORECASE)

    def draw_header():
        c.setFont(title_font, title_size)
        c.drawCentredString(width / 2, title_y, title)
        c.setFont(body_font, body_size)

    def new_page():
        nonlocal y
        c.showPage()
        draw_header()
        y = title_y - (line_height * 2)

    draw_header()
    y = title_y - (line_height * 2)

    max_width_chars = layout["max_width_chars"]
    wrote_anything = False

    for raw_line in text.splitlines():
        if page_marker_re.match(raw_line):
            new_page()
            continue

        line = raw_line
        while True:
            if y < bottom_margin:
                new_page()

            chunk = line[:max_width_chars]
            remainder = line[max_width_chars:]

            c.drawString(content_x, y, chunk)
            wrote_anything = True
            y -= line_height

            if not remainder:
                break
            line = remainder

    if wrote_anything:
        c.showPage()

    c.save()
