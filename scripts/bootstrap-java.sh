#!/usr/bin/env bash
# Проверка Java-окружения и компиляция тестового проекта.
# Запускать из корня сгенерированного проекта (там, где pom.xml).
set -euo pipefail

if [ ! -f pom.xml ]; then
    echo "Ошибка: запустите из корня тестового проекта (нет pom.xml)" >&2
    exit 1
fi

echo "--- Java: $(java -version 2>&1 | head -1)"
echo "--- Maven: $(mvn -version 2>&1 | head -1)"

echo "--- Компиляция тестов:"
mvn -q test-compile

echo ""
echo "Готово. Запуск:"
echo "  mvn test                  # весь сьют (flaky в карантине)"
echo "  mvn test -Dgroups=smoke   # быстрый смоук"
echo "  allure serve target/allure-results   # отчёт после прогона"
