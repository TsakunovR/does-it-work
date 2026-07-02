#!/usr/bin/env bash
# Развёртывание окружения тестового проекта: venv + зависимости + проверка коллекции.
# Запускать из корня сгенерированного проекта (там, где pytest.ini).
set -euo pipefail

if [ ! -f pytest.ini ] || [ ! -f requirements.txt ]; then
    echo "Ошибка: запустите из корня тестового проекта (нет pytest.ini/requirements.txt)" >&2
    exit 1
fi

uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt

echo "--- Проверка коллекции тестов:"
PYTHONPATH=. .venv/bin/pytest --collect-only -q | tail -2

echo ""
echo "Готово. Запуск:"
echo "  PYTHONPATH=. .venv/bin/pytest                # весь сьют"
echo "  PYTHONPATH=. .venv/bin/pytest -m smoke       # быстрый смоук"
echo "  allure serve allure-results                  # отчёт после прогона"
