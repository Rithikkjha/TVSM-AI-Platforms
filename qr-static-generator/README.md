# QR Static Generator

A tiny, standalone QR code generator. Enter a URL, click **Create QR**, get a
styled QR code. Frontend and backend are the same Spring Boot app — **no
database, no auth, no cloud storage, nothing else**.

The QR image is rendered server-side with ZXing (the same renderer as the
parent project), so the output looks identical.

## Run it (one command)

Requires only **Docker** (no Java/Gradle needed — the build happens inside
Docker). Copy this folder to the machine, then:

```bash
./run.sh
```

Then open **http://localhost:8090**, type a URL, and click **Create QR**.

Equivalent manual commands:

```bash
docker compose up --build      # build + run
docker compose up -d           # run in background
docker compose down            # stop
```

## What's editable

Only the **URL**. Everything else is locked server-side and cannot be changed
from the UI:

| Setting          | Value          |
|------------------|----------------|
| Logo             | Default TVS logo |
| Logo scale       | 0.15           |
| Foreground color | `#000000`      |
| Background color  | `#ffffff`      |
| Corner color     | `#000000`      |
| QR style         | Squared        |
| Size             | 600 px         |

To change any of these, edit the constants at the top of
`src/main/java/com/tvsmotor/qrstatic/QrController.java` and rebuild.

## API

A single endpoint (used by the page, but callable directly):

```bash
curl -X POST http://localhost:8090/api/generate \
     -d "url=https://example.com" \
     -o qr.svg
```

Returns an SVG (`image/svg+xml`). The raw URL is encoded directly into the QR
(static — no redirect/short-code indirection).

## Sizes

- Source you ship to the VM: **~200 KB** (`build/` and `.gradle/` are excluded)
- Docker image: **~164 MB** (reported) / **~62 MB** compressed
- Port: **8090** (change the mapping in `docker-compose.yml` if needed)

## How the image is kept small

- Multi-stage Docker build (build → jlink trimmed JRE → Alpine runtime)
- Custom JRE via `jlink` with only the modules the app needs (including
  `java.desktop` for the AWT/ImageIO rendering)
- `alpine:3.20` runtime base
- Provenance/SBOM attestations disabled

## Security note

`/api/generate` has **no authentication** (by design — static, local/internal
use). Add access control before exposing it publicly.

## Local development (optional, needs JDK 21)

```bash
./gradlew bootRun
```

Runs on http://localhost:8090 without Docker.
