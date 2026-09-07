#!/usr/bin/env bash
# Охота на флаки и доказательство стабильности повторными прогонами.
#
# Режим «Стабилизация» из reference/stabilize-and-review.md требует двух вещей,
# которые руками делать долго и легко подделать самому себе: воспроизвести флак
# повторами и доказать починку N зелёными прогонами подряд. Скрипт делает и то,
# и другое, и сводит результат в таблицу «тест → упал X из N».
#
#   scripts/flake_hunt.sh -n 10 -- pytest -m "not flaky"
#   scripts/flake_hunt.sh -n 5 --prove -- pytest tests/users/test_lifecycle.py
#   scripts/flake_hunt.sh -n 10 -- mvn -B test
#
# Флаги:
#   -n N       число прогонов (default: 5)
#   --prove    доказательство стабильности: останавливаемся на первом красном
#              (после починки нужны N зелёных ПОДРЯД, а не N попыток)
#   --log DIR  куда складывать логи прогонов (default: .flake-hunt)
#
# Код возврата: 0 — все прогоны зелёные, 1 — были падения.
#
# Прогон должен печатать имена упавших тестов: pytest делает это в короткой
# сводке (`-q` достаточно, при своём addopts добавьте `-rf`), maven — строками
# `[ERROR]   Класс.метод`. Если сводки нет, скрипт всё равно покажет,
# сколько прогонов упало, но не разложит по тестам.
set -uo pipefail

times=5
prove=false
log_dir=.flake-hunt

while [[ $# -gt 0 ]]; do
    case "$1" in
        -n) times="$2"; shift 2 ;;
        --prove) prove=true; shift ;;
        --log) log_dir="$2"; shift 2 ;;
        --) shift; break ;;
        -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
        *) echo "Неизвестный флаг: $1 (команду прогона передавайте после --)" >&2; exit 2 ;;
    esac
done

if [[ $# -eq 0 ]]; then
    echo "Не передана команда прогона. Пример: $0 -n 10 -- pytest -m \"not flaky\"" >&2
    exit 2
fi

mkdir -p "$log_dir"
rm -f "$log_dir"/run-*.log "$log_dir"/failures.txt
touch "$log_dir/failures.txt"

failed_runs=0
green_streak=0

echo "Прогонов: $times; команда: $*"
echo "Логи: $log_dir/run-N.log"
echo

for run in $(seq 1 "$times"); do
    started=$(date +%s)
    "$@" > "$log_dir/run-$run.log" 2>&1
    status=$?
    elapsed=$(( $(date +%s) - started ))

    if [[ $status -eq 0 ]]; then
        green_streak=$((green_streak + 1))
        printf 'Прогон %2d/%d: зелёный  (%dс)\n' "$run" "$times" "$elapsed"
    else
        failed_runs=$((failed_runs + 1))
        streak_before_red=$green_streak
        green_streak=0
        # Имена упавших тестов: короткая сводка pytest и строки ошибок surefire.
        grep -hoE '^FAILED [^ ]+|^ERROR [^ ]+' "$log_dir/run-$run.log" \
            | awk '{print $2}' >> "$log_dir/failures.txt"
        grep -hoE '^\[ERROR\]   [A-Za-z0-9_.]+' "$log_dir/run-$run.log" \
            | sed 's/^\[ERROR\]   //' >> "$log_dir/failures.txt"
        printf 'Прогон %2d/%d: КРАСНЫЙ (%dс, код %d) → %s\n' \
            "$run" "$times" "$elapsed" "$status" "$log_dir/run-$run.log"

        if [[ "$prove" == true ]]; then
            echo
            echo "Режим --prove: остановились на первом красном прогоне."
            echo "Стабильность НЕ доказана: до падения прошло $streak_before_red зелёных из $times."
            exit 1
        fi
    fi
done

echo
if [[ $failed_runs -eq 0 ]]; then
    if [[ "$prove" == true ]]; then
        echo "Стабильность доказана: зелёных прогонов подряд — $times."
    else
        echo "Флак не воспроизвёлся: зелёных $times из $times."
        echo "Это не значит, что его нет — расширьте набор до полного сьюта"
        echo "(причина может быть в соседях, а не в самом тесте) или увеличьте -n."
    fi
    exit 0
fi

echo "Красных прогонов: $failed_runs из $times."
if [[ -s "$log_dir/failures.txt" ]]; then
    echo
    echo "Частота падений по тестам:"
    sort "$log_dir/failures.txt" | uniq -c | sort -rn \
        | awk -v total="$times" '{printf "  %s из %s  %s\n", $1, total, $2}'
    echo
    echo "Дальше — не перезапуск, а диагноз: таблица причин в"
    echo "reference/stabilize-and-review.md (раздел «Классифицируй причину»)."
else
    echo "Имена упавших тестов из логов не извлеклись — смотрите $log_dir/run-*.log."
fi
exit 1
