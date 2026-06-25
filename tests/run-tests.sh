#!/bin/bash
# run-tests.sh - Chạy test cho B7, báo cáo ra thư mục reports (JSON + HTML)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

COLLECTION="$SCRIPT_DIR/collection/notification_collection.json"
ENV_FILE="$SCRIPT_DIR/environment/notification_environment.json"
PUBLISH_SCRIPT="$SCRIPT_DIR/scripts/publish_events.py"
REPORTS_DIR="$PROJECT_ROOT/reports"
REPORT_JSON="$REPORTS_DIR/newman-report.json"
REPORT_HTML="$REPORTS_DIR/newman-report.html"

mkdir -p "$REPORTS_DIR"

echo "🚀 B7 Notification Service Test Suite (Ubuntu)"
echo "=============================================="
echo "📁 Project root: $PROJECT_ROOT"
echo "📄 JSON report: $REPORT_JSON"
echo "📄 HTML report: $REPORT_HTML"

if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ B7 service is not running at http://localhost:8000"
    echo "   Please start it with: docker-compose up -d"
    exit 1
fi

echo "📤 Sending test events to RabbitMQ..."
EVENT_ID=$(python3 "$PUBLISH_SCRIPT" --host localhost --port 5672 | tail -n 1)
if [ -z "$EVENT_ID" ]; then
    echo "❌ Failed to get event ID. Please check RabbitMQ and script."
    exit 1
fi
echo "   Event ID for created: $EVENT_ID"

echo "⏳ Waiting for events to be processed..."
sleep 5

# Cập nhật testEventId vào environment file bằng Python (chính xác và an toàn)
python3 -c "
import json
with open('$ENV_FILE', 'r+') as f:
    data = json.load(f)
    for val in data.get('values', []):
        if val.get('key') == 'testEventId':
            val['value'] = '$EVENT_ID'
            break
    f.seek(0)
    json.dump(data, f, indent=2)
    f.truncate()
"

echo ""
echo "🧪 Running Newman tests..."
echo "==========================="

cd "$SCRIPT_DIR"
if [ ! -d "node_modules/newman-reporter-htmlextra" ]; then
    echo "📦 Installing newman-reporter-htmlextra locally..."
    npm install newman-reporter-htmlextra
fi

npx newman run "$COLLECTION" \
    --environment "$ENV_FILE" \
    --reporters cli,json,htmlextra \
    --reporter-json-export "$REPORT_JSON" \
    --reporter-htmlextra-export "$REPORT_HTML"

echo ""
echo "✅ Tests completed."
echo "📊 JSON report: $REPORT_JSON"
echo "📄 HTML report: $REPORT_HTML"

if command -v jq &> /dev/null; then
    total=$(jq '.run.stats.assertions.total' "$REPORT_JSON")
    failed=$(jq '.run.stats.assertions.failed' "$REPORT_JSON")
    passed=$((total - failed))
    echo "   Assertions: $passed passed, $failed failed (total $total)"
else
    echo "   (Install 'jq' for a detailed summary)"
fi