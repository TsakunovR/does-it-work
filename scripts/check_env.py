#!/usr/bin/env python3
"""Префлайт проверка стенда перед генерацией или прогоном тестов.

Без зависимостей (stdlib): можно запускать до установки venv.

Скрипт лежит в директории скилла, а cwd при работе — проект пользователя,
поэтому вызывайте его по полному пути к директории скилла:
    python <директория-скилла>/scripts/check_env.py https://stage.example.com/api
    python <директория-скилла>/scripts/check_env.py https://stage.example.com/api --path /health --token <JWT>

Проверяет: доступность base_url, латентность, код ответа health-пути,
и (с --token) что авторизованный запрос не отдаёт 401.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def probe(url: str, token: str | None = None, timeout: float = 10.0) -> tuple[int | None, float, str]:
    """GET url → (status | None при сетевой ошибке, латентность сек, фрагмент тела/ошибки)."""
    request = urllib.request.Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(500).decode("utf-8", "replace")
            return response.status, time.monotonic() - started, body
    except urllib.error.HTTPError as error:
        return error.code, time.monotonic() - started, error.read(500).decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return None, time.monotonic() - started, str(error)


def main() -> int:
    parser = argparse.ArgumentParser(description="Префлайт проверка API-стенда")
    parser.add_argument("base_url", help="Базовый URL API (без завершающего /)")
    parser.add_argument("--path", default="/health",
                        help="Служебный путь (default: /health; для WEB-стенда укажите /)")
    parser.add_argument("--auth-path", default=None, help="Путь для проверки токена (например /users/me)")
    parser.add_argument("--token", default=None, help="Bearer-токен для авторизованной пробы")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    failures = 0

    status, latency, body = probe(base + args.path)
    if status is None:
        print(f"FAIL  {base}{args.path} — стенд недоступен: {body}")
        failures += 1
    else:
        verdict = "OK  " if status == 200 else "WARN"
        print(f"{verdict}  GET {args.path} → {status} за {latency * 1000:.0f} мс: {body.strip()[:120]}")
        if status != 200:
            failures += 1

    if args.token:
        auth_path = args.auth_path or args.path
        status, latency, body = probe(base + auth_path, token=args.token)
        if status in (None, 401, 403):
            print(f"FAIL  токен не работает: GET {auth_path} → {status}: {str(body).strip()[:120]}")
            failures += 1
        else:
            print(f"OK    токен принят: GET {auth_path} → {status} за {latency * 1000:.0f} мс")

    if failures:
        print(f"\nИтог: {failures} проблем(ы) — разберитесь до генерации тестов.")
        return 1
    print("\nИтог: стенд готов к прогону.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
