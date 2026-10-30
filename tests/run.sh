#!/usr/bin/env bash
# Тесты расширения: синтаксис всех модулей (OneScript) и ядро ОТ_КлиентAPI.
#   tests/run.sh          — ядро против заглушки tests/mock_server.py
#   tests/run.sh --live   — против настоящего проекта: ONETRACE_URL и ONETRACE_KEY (секретный ключ) в окружении
set -euo pipefail
cd "$(dirname "$0")/.."
image=evilbeaver/onescript:latest

tests/syntax.sh

if [[ "${1:-}" == "--live" ]]; then
    : "${ONETRACE_URL:?ONETRACE_URL}" "${ONETRACE_KEY:?ONETRACE_KEY}"
    url="$ONETRACE_URL"; key="$ONETRACE_KEY"
else
    port=18765; log="$(mktemp)"
    python3 tests/mock_server.py "$port" "$log" & server=$!
    trap 'kill $server 2>/dev/null; rm -f "$log"' EXIT
    sleep 1
    url="http://127.0.0.1:$port"; key=test-secret
fi

docker run --rm --network host -e ONETRACE_URL="$url" -e ONETRACE_KEY="$key" -e ONETRACE_RUN="$(date +%s)" \
    -v "$PWD":/w -w /w "$image" oscript tests/core.os

if [[ "${1:-}" != "--live" ]]; then
    # Что ушло на заглушку: 2 принятых чека (после отклонения пакета с неверным телефоном) и магазин.
    python3 - "$log" <<'PY'
import json, sys
requests = [json.loads(line) for line in open(sys.argv[1], encoding='utf-8')]
batches = [r['body']['batch'] for r in requests if r['path'] == '/api/v1/batch']
assert [len(b) for b in batches] == [3, 2], [len(b) for b in batches]
check = batches[1][0]
assert check['properties']['channel'] == 'offline' and check['properties']['store_id'] == 'msk-1', check
assert check['timestamp'].endswith('Z') and check['messageId'].startswith('1c-run-'), check
stores = [r['body']['items'] for r in requests if r['path'] == '/api/v1/stores']
assert stores == [[{'id': 'msk-1', 'name': 'Тверская', 'city': 'Москва', 'address': 'Тверская, 1'}]], stores
print('Запросы к платформе — как ожидалось')
PY
fi
