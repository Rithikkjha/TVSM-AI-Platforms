#!/usr/bin/env bash
# One command to build + run the standalone static QR generator in Docker.
# Frontend + backend are the same Spring Boot app (no DB, nothing else).
# The build happens entirely inside Docker, so this machine only needs Docker
# (no Java or Gradle required on the host).
set -e

cd "$(dirname "$0")"

# Build a lean image (no provenance/SBOM attestation manifests).
docker buildx build --provenance=false --sbom=false --load -t qr-static-generator-qr .

# Start it (frontend + backend in one container) on http://localhost:8090
docker compose up
