# CapoToKeys

Convert guitar capo chord charts into piano-ready keys while preserving lyrics and chord structure.

CapoToKeys provides a Docker-first Flask WebUI, a CLI mode for scripts, and an optional desktop app build from the same codebase.

## Features

- Transpose by capo value (`0-11` semitones)
- Keep lyrics and chord formatting intact
- Generate both `.txt` and `.pdf` outputs
- Conflict-safe output naming (`suffix` or `overwrite`)
- Archive view grouped by song set
- Docker deployment + GHCR image publishing

## Screenshots

> Replace the placeholders below with your own captures.

### Generator View

![Generator View](docs/assets/screenshot-generator.png)

### Archive View

![Archive View](docs/assets/screenshot-archive.png)

### Desktop App (Optional)

![Desktop View](docs/assets/screenshot-desktop.png)

## Quick Start (Docker)

```bash
docker build -t capo-to-keys:latest -f dockerfile .

docker run -d \
  --name capotokeys \
  -p 4506:4506 \
  -v "./data:/data" \
  capo-to-keys:latest
```

Open: `http://localhost:4506`

`capo-to-keys:dev` in this section is a local image tag built on your machine.

Outputs are written to `/data/outputs` (mapped to your local volume path).

## Pull From GHCR (No Local Build)

Pinned release (recommended for reproducible testing):

```bash
docker pull ghcr.io/reprodev/capotokeys:v1.0
docker run --rm -it \
  --name capotokeys \
  -p 4506:4506 \
  -v "$(pwd)/appdata/config/capotokeys:/data" \
  ghcr.io/reprodev/capotokeys:v1.0
```

Latest default-branch image:

```bash
docker pull ghcr.io/reprodev/capotokeys:latest
```
## Quick Start (GHCR + Compose)

Use the included compose example:

```bash
docker compose up -d
```

Default image reference in that file:

- `ghcr.io/reprodev/capotokeys:latest`

If the package is private, authenticate first:

```bash
docker login ghcr.io -u <github-username>
```

## Image Tags

Published GHCR image format:

- `ghcr.io/<owner>/<repo>:<tag>`

Common tags:

- `v1.0` (current release tag)
- `latest` (default branch, moving tag)
- `dev` (dev branch)
- `vX.Y.Z` (future release tags)
- `sha-<commit>`

## Configuration

| Variable | Default | Description |
|---|---:|---|
| `DATA_DIR` | `/data` | Base data path (uses `/data/outputs`) |
| `WEB_HOST` | `0.0.0.0` | Flask bind host |
| `WEB_PORT` | `4506` | Flask port |
| `OUTPUT_CONFLICT_MODE` | `suffix` | `suffix` or `overwrite` when file exists |
| `MAX_REQUEST_BYTES` | `1048576` | Maximum HTTP request size |
| `MAX_TEXT_LENGTH` | `200000` | Maximum submitted chord text length |
| `OUTPUT_LIST_LIMIT` | `300` | Max files considered in archive view |
| `PDF_LEFT_MARGIN` | `54` | PDF left margin |
| `PDF_TOP_MARGIN` | `62` | PDF top margin |
| `PDF_BOTTOM_MARGIN` | `54` | PDF bottom margin |
| `PDF_TITLE_SIZE` | `14` | PDF title font size |
| `PDF_BODY_SIZE` | `10` | PDF body font size |
| `PDF_LINE_HEIGHT` | `12` | PDF line height |
| `PDF_MAX_WIDTH_CHARS` | `110` | PDF wrap width |

Production note:

- Set `APP_ENV=production` (or `FLASK_ENV=production`)
- Set `FLASK_SECRET` to a strong non-default value

## CLI Usage

List outputs:

```bash
python entrypoint.py --list
```

Transpose from stdin and save TXT + PDF:

```bash
cat song.txt | python entrypoint.py --capo 1 --title "Song Title" --pdf
```

Overwrite behavior:

```bash
cat song.txt | python entrypoint.py --capo 1 --title "Song Title" --pdf --conflict overwrite
```

## Desktop App (Optional)

Install desktop dependencies:

```bash
pip install -r requirements-desktop.txt
```

Run desktop app:

```bash
python desktop_app.py
```

Build executable:

```bash
pyinstaller --noconfirm --onefile --windowed --name CapoToKeys desktop_app.py
```

## Development

Run tests:

```bash
python -m unittest discover -s tests -v
```

## GitHub Actions

Workflows included:

- `CI`: test matrix and compile checks
- `Docker GHCR`: build and publish container image
- `Desktop Release`: build and attach Windows desktop artifact

GHCR setup details: `docs/GHCR_SETUP.md`

## Project Docs

- `CONTRIBUTING.md`
- `SECURITY.md`
- `docs/PUBLIC_RELEASE_CHECKLIST.md`
- `docs/GHCR_SETUP.md`

## License

MIT — see `LICENSE`.





