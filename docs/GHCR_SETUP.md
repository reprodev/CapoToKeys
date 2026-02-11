# GHCR Setup For Docker Compose

This project publishes container images to GitHub Container Registry (GHCR).

## 1) Required GitHub Repository Settings

In the repository settings:

1. `Settings` -> `Actions` -> `General`
2. Under Workflow permissions, select `Read and write permissions`
3. Save

This is required because `.github/workflows/docker-ghcr.yml` pushes packages using `GITHUB_TOKEN`.

## 2) Workflow Behavior

The Docker workflow publishes on:

- Push to `main`
- Push to `dev`
- Tag push `v*`
- Manual run (`workflow_dispatch`)

Tags produced include:

- `latest` on default branch
- branch tags (for example `main`, `dev`)
- version tag (`v1.2.3` style)
- semver normalized version tags
- `sha-<commit>`

Image path format:

- `ghcr.io/<owner>/<repo>:<tag>`
- For this repo: `ghcr.io/reprodev/capotokeys:<tag>`

## 3) Make Image Pullable From Compose

If the package remains private, hosts must authenticate first.

```bash
docker login ghcr.io -u <github-username>
# password: GitHub PAT with at least read:packages
```

If you make the package public, no login is needed for pulls.

## 4) Compose Usage

Use `docker-compose.ghcr.yml` from this repo as a template.

Example:

```bash
docker compose -f docker-compose.ghcr.yml up -d
```

For non-release testing from `dev`, use:

- `ghcr.io/reprodev/capotokeys:dev`

For stable release usage, prefer:

- `ghcr.io/reprodev/capotokeys:v1.0`
- or explicit version tags like `ghcr.io/reprodev/capotokeys:v1.1.0`



