# Project Structure

This document describes the current folder and file layout for the repository.

## High-level overview

- Root app entry and deployment config:
  - `api/index.py`
  - `Procfile`
  - `vercel.json`
  - `requirements.txt`
  - `runtime.txt`
- Main application package:
  - `LegalAI/` (Flask-style app code, templates, static assets, tests)
- Metadata and automation:
  - `.github/` (present, currently no files detected)
- Local/generated artifacts:
  - `legal_chat.db`
  - `LegalAI/legal_chat.db`
  - `LegalAI/__pycache__/`
  - `LegalAI/.env` (local environment file)

## Directory tree (current snapshot)

```text
oryzed-shared-With-akash/
|-- .github/
|   |-- appmod/
|   |   `-- appcat/
|   `-- workflows/
|-- .gitignore
|-- Procfile
|-- README.md
|-- requirements.txt
|-- runtime.txt
|-- vercel.json
|-- legal_chat.db
|-- api/
|   `-- index.py
|-- LegalAI/
|   |-- .env
|   |-- __init__.py
|   |-- _verify.py
|   |-- app.py
|   |-- LICENSE
|   |-- PRD.md
|   |-- Procfile
|   |-- README.md
|   |-- REDESIGN_IMPLEMENTATION_GUIDE.md
|   |-- requirements.txt
|   |-- setup.py
|   |-- test_app.py
|   |-- legal_chat.db
|   |-- justice_lady_landingpage.mp4
|   |-- Live_Oryzed.mp4
|   |-- Oryzed_Logo.png
|   |-- Techy_Lady_Justice_Video_Creation.mp4
|   |-- src/
|   |   `-- styles/
|   |-- tests/
|   |-- templates/
|   |   |-- 17.png
|   |   |-- legal_chat.html
|   |   |-- legal_chat_v2.html
|   |   |-- legal_chat_v3.html
|   |   |-- login.html
|   |   |-- profile.html
|   |   |-- signup.html
|   |   `-- terms.html
|   |-- static/
|   |   |-- 17.png
|   |   |-- auth.css
|   |   |-- auth.js
|   |   |-- gavel_loader.json
|   |   |-- legal_app.js
|   |   |-- legal_app_v2.js
|   |   |-- legal_style_final.css
|   |   |-- legal_style_final_v2.css
|   |   |-- terms.css
|   |   |-- terms.js
|   |   |-- justice_lady_landingpage.mp4
|   |   |-- Live_Oryzed.mp4
|   |   |-- lj_video.mp4
|   |   |-- Oryzed_Logo.png
|   |   |-- css/
|   |   |   `-- legal_animations.css
|   |   |-- js/
|   |   |   `-- legal_animations.js
|   |   `-- vendor/
|   |       |-- marked.min.js
|   |       |-- purify.min.js
|   |       `-- fontawesome/
|   |           |-- all.min.css
|   |           `-- webfonts/
|   |               |-- fa-brands-400.ttf
|   |               |-- fa-brands-400.woff2
|   |               |-- fa-regular-400.ttf
|   |               |-- fa-regular-400.woff2
|   |               |-- fa-solid-900.ttf
|   |               |-- fa-solid-900.woff2
|   |               |-- fa-v4compatibility.ttf
|   |               `-- fa-v4compatibility.woff2
|   `-- __pycache__/
|       |-- app.cpython-312.pyc
|       |-- app.cpython-313.pyc
|       |-- store_index.cpython-310.pyc
|       `-- store_medical_reports.cpython-310.pyc
`-- PROJECT_STRUCTURE.md
```

## Notes

- `LegalAI/.env`, `*.db`, and `__pycache__/` are environment/runtime artifacts and typically should not be committed unless intentionally required.
- `LegalAI/src/styles/` and `LegalAI/tests/` currently appear as directories with no files.
