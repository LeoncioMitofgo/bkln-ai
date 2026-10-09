#!/usr/bin/env python3
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

BASE_DIR = Path(__file__).resolve().parent
BACKEND_ENV = BASE_DIR.parent / "backend" / ".env"


def admin_token() -> str:
    """El backend exige X-Admin-Token: BKLN_AI_ADMIN_TOKEN o, si no, ADMIN_TOKEN de backend/.env."""
    token = os.environ.get("BKLN_AI_ADMIN_TOKEN", "").strip()
    if token or not BACKEND_ENV.exists():
        return token
    for line in BACKEND_ENV.read_text(encoding="utf-8").splitlines():
        if line.startswith("ADMIN_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""
KNOWLEDGE_PATH = BASE_DIR / "knowledge.json"
STATE_PATH = BASE_DIR / "ingest_state.json"
ERRORS_PATH = BASE_DIR / "ingest_errors.json"
API_URL = "https://ai.bklnsoftware.tech/sources/text"
REQUEST_DELAY_SECONDS = 0.5


def load_json_file(path: Path, default: Any):
    if not path.exists():
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        return default

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if data is not None else default
    except json.JSONDecodeError:
        return default


def save_json_file(path: Path, data: Any):
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def load_known_titles() -> set[str]:
    state = load_json_file(STATE_PATH, [])
    if isinstance(state, list):
        return {str(item) for item in state}
    if isinstance(state, dict):
        return {str(k) for k in state.keys()}
    return set()


def append_error(title: str, reason: str):
    errors = load_json_file(ERRORS_PATH, [])
    if not isinstance(errors, list):
        errors = []

    errors.append({
        "title": title,
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    save_json_file(ERRORS_PATH, errors)


def main() -> None:
    started = time.time()

    try:
        with KNOWLEDGE_PATH.open("r", encoding="utf-8") as fh:
            knowledge = json.load(fh)
    except Exception as exc:
        print(f"No se pudo leer knowledge.json: {exc}")
        return

    if not isinstance(knowledge, list):
        print("knowledge.json no tiene el formato esperado: debe ser un array de objetos.")
        return

    token = admin_token()
    if not token:
        print("Falta el token de administración: define BKLN_AI_ADMIN_TOKEN o ADMIN_TOKEN en backend/.env.")
        return
    headers = {"X-Admin-Token": token}

    known_titles = load_known_titles()
    sent_successfully = 0
    skipped = 0
    failed = 0

    for item in knowledge:
        title = str(item.get("title", "")).strip()
        if not title:
            continue

        if title in known_titles:
            skipped += 1
            continue

        payload = {
            "title": title,
            "content": item.get("content", ""),
            "source_url": item.get("source_url", ""),
        }

        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                known_titles.add(title)
                save_json_file(STATE_PATH, sorted(known_titles))
                sent_successfully += 1
            else:
                failed += 1
                append_error(title, f"HTTP {response.status_code}: {response.text[:500]}")
        except Exception as exc:
            failed += 1
            append_error(title, str(exc))

        time.sleep(REQUEST_DELAY_SECONDS)

    total_duration = time.time() - started
    print(f"Fragmentos ya indexados (skipped): {skipped}")
    print(f"Fragmentos enviados con éxito: {sent_successfully}")
    print(f"Fragmentos fallidos: {failed}")
    print(f"Duración total: {total_duration:.2f}s")


if __name__ == "__main__":
    main()
