from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from typing import Optional
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.database.repository import NotificationRepository

router = APIRouter()

@router.get("/logs")
async def get_logs_api(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_id: Optional[str] = None,
    user_id: Optional[str] = None,
    channel: Optional[str] = None,
    status: Optional[str] = None,
):
    async with AsyncSessionLocal() as session:
        repo = NotificationRepository(session)
        logs = await repo.get_logs(
            limit=limit,
            offset=offset,
            event_id=event_id,
            user_id=user_id,
            channel=channel,
            status=status,
        )
        result = [
            {
                "id": str(log.id),
                "event_id": log.event_id,
                "user_id": log.user_id,
                "channel": log.channel,
                "status": log.status,
                "message": log.message,
                "error_detail": log.error_detail,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None,
                "severity": log.severity,
            }
            for log in logs
        ]
        return {
            "data": result,
            "total": len(result),
            "limit": limit,
            "offset": offset,
        }

@router.get("/logs/html", response_class=HTMLResponse)
async def logs_html():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Notification Logs</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .filters { margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
            .filters input, .filters select { padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
            .filters button { padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .filters button:hover { background: #0056b3; }
            table { border-collapse: collapse; width: 100%; font-size: 14px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .status-success { color: green; font-weight: bold; }
            .status-failed { color: red; font-weight: bold; }
            .pagination { margin-top: 20px; display: flex; gap: 10px; align-items: center; }
            .pagination button { padding: 6px 12px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .pagination button:hover { background: #1e7e34; }
            .pagination button:disabled { opacity: 0.5; cursor: not-allowed; }
            .loading { color: #666; }
            .nav-link { display: inline-block; margin-bottom: 20px; color: #007bff; text-decoration: none; }
            .nav-link:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <a href="/" class="nav-link">← Back to Dashboard</a>
        <h1>📋 Notification Logs</h1>
        <div class="filters">
            <input type="text" id="eventFilter" placeholder="Event ID">
            <input type="text" id="userFilter" placeholder="User ID">
            <select id="channelFilter">
                <option value="">All Channels</option>
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="telegram">Telegram</option>
                <option value="display">Display</option>
                <option value="log">Log (LOW severity)</option>
            </select>
            <select id="statusFilter">
                <option value="">All Status</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
            </select>
            <button onclick="loadLogs(0)">Apply Filters</button>
            <button onclick="resetFilters()">Reset</button>
        </div>
        <div id="logsContainer">
            <p class="loading">Loading...</p>
        </div>
        <div class="pagination" id="pagination">
            <button id="prevBtn" onclick="loadLogs(currentOffset - limit)" disabled>Previous</button>
            <span id="pageInfo">Page 1</span>
            <button id="nextBtn" onclick="loadLogs(currentOffset + limit)">Next</button>
        </div>
        <script>
            let currentOffset = 0;
            let limit = 50;

            async function loadLogs(offset) {
                const eventId = document.getElementById('eventFilter').value.trim();
                const userId = document.getElementById('userFilter').value.trim();
                const channel = document.getElementById('channelFilter').value;
                const status = document.getElementById('statusFilter').value;
                
                let url = `/logs?limit=${limit}&offset=${offset}`;
                if (eventId) url += '&event_id=' + encodeURIComponent(eventId);
                if (userId) url += '&user_id=' + encodeURIComponent(userId);
                if (channel) url += '&channel=' + encodeURIComponent(channel);
                if (status) url += '&status=' + encodeURIComponent(status);
                
                try {
                    const resp = await fetch(url);
                    const data = await resp.json();
                    const container = document.getElementById('logsContainer');
                    currentOffset = offset;
                    
                    if (data.data.length === 0) {
                        container.innerHTML = '<p>No logs found.</p>';
                    } else {
                        let html = '<table><thead><tr><th>Time</th><th>Event ID</th><th>User</th><th>Channel</th><th>Status</th><th>Message</th><th>Error</th></tr></thead><tbody>';
                        for (const log of data.data) {
                            const statusClass = log.status === 'success' ? 'status-success' : 'status-failed';
                            const time = log.created_at ? new Date(log.created_at).toLocaleString('vi-VN') : '-';
                            html += `<tr>
                                <td>${time}</td>
                                <td><code>${log.event_id}</code></td>
                                <td>${log.user_id}</td>
                                <td>${log.channel}</td>
                                <td class="${statusClass}">${log.status}</td>
                                <td>${log.message || '-'}</td>
                                <td>${log.error_detail || '-'}</td>
                            </tr>`;
                        }
                        html += '</tbody></table>';
                        container.innerHTML = html;
                    }
                    
                    const page = Math.floor(offset / limit) + 1;
                    document.getElementById('pageInfo').textContent = `Page ${page}`;
                    document.getElementById('prevBtn').disabled = offset === 0;
                    document.getElementById('nextBtn').disabled = data.data.length < limit;
                } catch (e) {
                    document.getElementById('logsContainer').innerHTML = '<p style="color:red;">Error loading logs. Please try again.</p>';
                }
            }

            function resetFilters() {
                document.getElementById('eventFilter').value = '';
                document.getElementById('userFilter').value = '';
                document.getElementById('channelFilter').value = '';
                document.getElementById('statusFilter').value = '';
                loadLogs(0);
            }

            window.onload = () => loadLogs(0);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)