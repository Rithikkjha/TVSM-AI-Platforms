---
service_id: qrcode-frontend
doc_type: overview
last_reviewed: 2026-10-11
aliases: ["qrcode frontend", "qrcode"]
---

# qrcode-frontend — Overview

## Purpose
Summary: React/Vite frontend for QR code creation, library management and analytics, calling tvsmbe-qrcode APIs.
Also known as: qrcode frontend, qrcode
qrcode-frontend is a `frontend-web` repository (`qrcode-frontend`; service.yaml `type: frontend-web`). Business purpose: README (`README.md`) describes it as: React + TypeScript + Vite.

## Users and Consumers
qrcode-frontend is called over HTTP by: Unknown (no resolved inbound callers in registry). Event consumers of its published messages: none resolved.

## Key Capabilities
qrcode-frontend capabilities derived from code:
- UI making 15 backend API calls

## Tech Stack
qrcode-frontend tech stack (service.yaml `tech_stack`, `meta.json` stacks):

| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | Unknown |
| Framework | react | Unknown |
| Data | None extracted | Unknown |
| Messaging | None extracted | Unknown |
| Hosting | docker (build: node,react) | Unknown |

Key libraries: `@hookform/resolvers`, `@vitejs/plugin-react`, `lucide-react`, `react`, `react-dom`, `react-hook-form`, `typescript`, `vite`, `zod`

## Dependencies at a Glance
Upstream (calls qrcode-frontend): Unknown
Downstream (qrcode-frontend calls): `tvsmbe-qrcode` (hard); plus 1 outbound call(s) with unresolved target
Brokers: none. Data stores: none
Full detail: service.yaml `inbound` / `outbound`.

## Environments
qrcode-frontend environments evidenced by config/infra files (URLs not determinable from code):

| Env | URL | Notes |
|---|---|---|
| default | Unknown | from config/infra file names |

## Environment Variables
qrcode-frontend configuration keys by NAME only (values never recorded; source: service.yaml `config`).

| Name | Purpose | Required | Secret | Provided by |
|---|---|---|---|---|
| `VITE_API_BASE` | points to tvsmbe-qrcode | Unknown | False | Unknown |
| `VITE_ENV` | Unknown | Unknown | False | Unknown |
| `VITE_SHORT_DOMAIN` | Unknown | Unknown | False | Unknown |

## Ownership
qrcode-frontend ownership: Unknown — no CODEOWNERS in repo.

| Role | Person / Team | Contact |
|---|---|---|
| Team | Unknown | Unknown |
| Tech Lead | Unknown | Unknown |
| Product Owner | Unknown | Unknown |
| Vendor | Unknown | Unknown |

## Local Setup
qrcode-frontend local setup evidence:
- README: `README.md`
- Dockerfile(s): `Dockerfile`, `dockerfile`
- Build commands: see HLC.md `Build and Test`

## Known Limitations
qrcode-frontend limitations evidenced by extraction:
- 1 outbound HTTP call(s) have no resolved target service (base URL from config/env).
