import os
import json
import datetime
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Incident Notification Center")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NOTIFICATIONS = []

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def forward_to_telegram(text: str):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print("Failed to forward alert to Telegram:", e)

@app.post("/alerts")
async def receive_alerts(request: Request):
    payload = await request.json()
    received_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    alerts = payload.get("alerts", [])
    status = payload.get("status", "firing")

    for a in alerts:
        alert_name = a.get("labels", {}).get("alertname", "UnknownAlert")
        severity = a.get("labels", {}).get("severity", "info")
        description = a.get("annotations", {}).get("description", "No description provided")
        summary = a.get("annotations", {}).get("summary", alert_name)
        instance = a.get("labels", {}).get("instance", "n/a")
        alert_status = a.get("status", status)

        entry = {
            "id": len(NOTIFICATIONS) + 1,
            "time": received_at,
            "status": alert_status,
            "alertname": alert_name,
            "severity": severity,
            "summary": summary,
            "description": description,
            "instance": instance,
            "raw": a
        }
        NOTIFICATIONS.insert(0, entry)

        tg_text = (
            f"*CRITICAL: {alert_name}*\n"
            f"*Target:* {instance}\n"
            f"*Status:* {alert_status.upper()}\n"
            f"*Severity:* {severity.upper()}\n"
            f"*Description:* {description}\n"
            f"*Timestamp:* {received_at}"
        )
        forward_to_telegram(tg_text)

    if len(NOTIFICATIONS) > 100:
        del NOTIFICATIONS[100:]

    return JSONResponse(content={"status": "received", "count": len(alerts)})

@app.get("/api/notifications")
def get_notifications():
    return JSONResponse(content={"notifications": NOTIFICATIONS})

@app.delete("/api/notifications")
def clear_notifications():
    NOTIFICATIONS.clear()
    return {"message": "Notifications cleared"}

@app.get("/", response_class=HTMLResponse)
def index_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Incident Alert Live Console</title>
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
      <style>
        :root {
          --bg-main: #0a0e17;
          --bg-panel: #111827;
          --bg-card: #162032;
          --border: #243248;
          --border-subtle: #1e293b;
          --text-primary: #f8fafc;
          --text-secondary: #94a3b8;
          --text-muted: #64748b;
          --status-critical: #ef4444;
          --status-critical-bg: rgba(239, 68, 68, 0.12);
          --status-critical-border: rgba(239, 68, 68, 0.35);
          --status-warning: #f59e0b;
          --status-warning-bg: rgba(245, 158, 11, 0.12);
          --status-warning-border: rgba(245, 158, 11, 0.35);
          --status-resolved: #10b981;
          --status-resolved-bg: rgba(16, 185, 129, 0.12);
          --status-resolved-border: rgba(16, 185, 129, 0.35);
          --status-info: #3b82f6;
          --status-info-bg: rgba(59, 130, 246, 0.12);
          --status-info-border: rgba(59, 130, 246, 0.35);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
          background-color: var(--bg-main);
          color: var(--text-primary);
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          min-height: 100vh;
          padding: 28px 24px;
        }
        .container {
          max-width: 1240px;
          margin: 0 auto;
        }
        header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-bottom: 24px;
          border-bottom: 1px solid var(--border-subtle);
          margin-bottom: 24px;
        }
        .header-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .app-icon {
          width: 42px;
          height: 42px;
          border-radius: 8px;
          background: linear-gradient(135deg, #1e293b, #0f172a);
          border: 1px solid var(--border);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #60a5fa;
        }
        .app-title h1 {
          font-size: 20px;
          font-weight: 700;
          letter-spacing: -0.02em;
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .app-title p {
          color: var(--text-muted);
          font-size: 13px;
          margin-top: 4px;
        }
        .badge-pulse {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 3px 10px;
          border-radius: 9999px;
          font-size: 11px;
          font-weight: 600;
          letter-spacing: 0.05em;
          text-transform: uppercase;
          background: rgba(16, 185, 129, 0.12);
          color: var(--status-resolved);
          border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .pulse-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: var(--status-resolved);
          box-shadow: 0 0 8px var(--status-resolved);
          animation: pulse 2s infinite ease-in-out;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.85); }
        }
        .header-actions {
          display: flex;
          gap: 10px;
        }
        .btn {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: var(--bg-panel);
          border: 1px solid var(--border);
          color: var(--text-secondary);
          padding: 9px 16px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 13px;
          font-weight: 600;
          transition: all 0.15s ease;
        }
        .btn:hover {
          background: #1e293b;
          color: var(--text-primary);
          border-color: #3b82f6;
        }
        .btn-danger:hover {
          background: rgba(239, 68, 68, 0.15);
          color: #f87171;
          border-color: var(--status-critical);
        }

        .metrics-strip {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }
        .metric-card {
          background: var(--bg-panel);
          border: 1px solid var(--border-subtle);
          border-radius: 8px;
          padding: 16px;
        }
        .metric-label {
          color: var(--text-muted);
          font-size: 12px;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 8px;
        }
        .metric-value {
          font-size: 24px;
          font-weight: 700;
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-primary);
        }
        .metric-value.critical { color: var(--status-critical); }
        .metric-value.warning { color: var(--status-warning); }
        .metric-value.resolved { color: var(--status-resolved); }

        .feed-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 14px;
        }
        .feed-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }
        .feed-count {
          font-size: 12px;
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
        }

        .alert-card {
          background: var(--bg-panel);
          border: 1px solid var(--border-subtle);
          border-left: 4px solid var(--border);
          border-radius: 8px;
          padding: 18px 20px;
          margin-bottom: 12px;
          transition: border-color 0.15s ease;
        }
        .alert-card.critical {
          border-left-color: var(--status-critical);
          background: linear-gradient(90deg, rgba(239, 68, 68, 0.05) 0%, var(--bg-panel) 18%);
        }
        .alert-card.warning {
          border-left-color: var(--status-warning);
          background: linear-gradient(90deg, rgba(245, 158, 11, 0.05) 0%, var(--bg-panel) 18%);
        }
        .alert-card.resolved {
          border-left-color: var(--status-resolved);
          opacity: 0.85;
        }

        .alert-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        .alert-headline {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .alert-title-text {
          font-size: 15px;
          font-weight: 600;
          color: var(--text-primary);
        }
        .alert-timestamp {
          font-family: 'JetBrains Mono', monospace;
          font-size: 12px;
          color: var(--text-muted);
        }
        .tag {
          font-size: 11px;
          font-weight: 600;
          padding: 3px 8px;
          border-radius: 4px;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          font-family: 'JetBrains Mono', monospace;
        }
        .tag-critical {
          background: var(--status-critical-bg);
          color: var(--status-critical);
          border: 1px solid var(--status-critical-border);
        }
        .tag-warning {
          background: var(--status-warning-bg);
          color: var(--status-warning);
          border: 1px solid var(--status-warning-border);
        }
        .tag-resolved {
          background: var(--status-resolved-bg);
          color: var(--status-resolved);
          border: 1px solid var(--status-resolved-border);
        }
        .tag-muted {
          background: #1e293b;
          color: var(--text-secondary);
          border: 1px solid var(--border);
        }

        .alert-description {
          font-size: 13px;
          color: #cbd5e1;
          margin-bottom: 12px;
          line-height: 1.55;
        }

        .alert-metadata-grid {
          display: flex;
          flex-wrap: wrap;
          gap: 16px;
          background: var(--bg-main);
          border: 1px solid var(--border-subtle);
          padding: 10px 14px;
          border-radius: 6px;
          font-family: 'JetBrains Mono', monospace;
          font-size: 12px;
        }
        .meta-item {
          display: flex;
          gap: 6px;
        }
        .meta-key {
          color: var(--text-muted);
        }
        .meta-val {
          color: var(--text-secondary);
          font-weight: 500;
        }

        .empty-placeholder {
          text-align: center;
          padding: 64px 24px;
          border: 1px dashed var(--border);
          border-radius: 8px;
          background: rgba(17, 24, 39, 0.4);
        }
        .empty-placeholder-title {
          font-size: 15px;
          font-weight: 600;
          color: var(--text-secondary);
          margin-bottom: 6px;
        }
        .empty-placeholder-desc {
          font-size: 13px;
          color: var(--text-muted);
          max-width: 520px;
          margin: 0 auto;
          line-height: 1.5;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <header>
          <div class="header-left">
            <div class="app-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
              </svg>
            </div>
            <div class="app-title">
              <h1>
                Alertmanager Incident Live Dispatch
                <span class="badge-pulse"><span class="pulse-dot"></span>Active Link</span>
              </h1>
              <p>Real-time webhook dispatcher receiving alerts from Prometheus Alertmanager & Telegram relay</p>
            </div>
          </div>
          <div class="header-actions">
            <button class="btn" onclick="fetchAlerts()">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="23 4 23 10 17 10"></polyline>
                <polyline points="1 20 1 14 7 14"></polyline>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
              </svg>
              Refresh
            </button>
            <button class="btn btn-danger" onclick="clearAlerts()">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
              Clear Feed
            </button>
          </div>
        </header>

        <section class="metrics-strip">
          <div class="metric-card">
            <div class="metric-label">Total Notifications</div>
            <div class="metric-value" id="statTotal">0</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Firing Critical</div>
            <div class="metric-value critical" id="statCritical">0</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Firing Warnings</div>
            <div class="metric-value warning" id="statWarning">0</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Resolved Events</div>
            <div class="metric-value resolved" id="statResolved">0</div>
          </div>
        </section>

        <div class="feed-header">
          <div class="feed-title">Dispatch Stream</div>
          <div class="feed-count" id="feedCount">Showing 0 entries</div>
        </div>

        <div id="alertsContainer">
          <div class="empty-placeholder">
            <div class="empty-placeholder-title">No notifications recorded</div>
            <div class="empty-placeholder-desc">The system is operating within defined thresholds. Firing alerts dispatched by Alertmanager will appear here automatically.</div>
          </div>
        </div>
      </div>

      <script>
        function escapeHtml(str) {
          if (!str) return '';
          return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }

        async function fetchAlerts() {
          try {
            const res = await fetch('/api/notifications');
            const data = await res.json();
            const notifications = data.notifications || [];
            const container = document.getElementById('alertsContainer');

            let criticalCount = 0;
            let warningCount = 0;
            let resolvedCount = 0;

            notifications.forEach(a => {
              if (a.status === 'resolved') {
                resolvedCount++;
              } else if (a.severity === 'critical') {
                criticalCount++;
              } else if (a.severity === 'warning') {
                warningCount++;
              }
            });

            document.getElementById('statTotal').innerText = notifications.length;
            document.getElementById('statCritical').innerText = criticalCount;
            document.getElementById('statWarning').innerText = warningCount;
            document.getElementById('statResolved').innerText = resolvedCount;
            document.getElementById('feedCount').innerText = `Showing ${notifications.length} entries`;

            if (notifications.length === 0) {
              container.innerHTML = `
                <div class="empty-placeholder">
                  <div class="empty-placeholder-title">No notifications recorded</div>
                  <div class="empty-placeholder-desc">The system is operating within defined thresholds. Firing alerts dispatched by Alertmanager will appear here automatically.</div>
                </div>
              `;
              return;
            }

            container.innerHTML = notifications.map(a => {
              const isResolved = a.status === 'resolved';
              const cardClass = isResolved ? 'resolved' : (a.severity === 'critical' ? 'critical' : 'warning');
              const tagStatusClass = isResolved ? 'tag-resolved' : (a.severity === 'critical' ? 'tag-critical' : 'tag-warning');

              return `
                <div class="alert-card ${cardClass}">
                  <div class="alert-top">
                    <div class="alert-headline">
                      <span class="tag ${tagStatusClass}">${escapeHtml((a.status || 'firing').toUpperCase())}</span>
                      <span class="tag tag-muted">${escapeHtml((a.severity || 'info').toUpperCase())}</span>
                      <span class="alert-title-text">${escapeHtml(a.summary || a.alertname)}</span>
                    </div>
                    <span class="alert-timestamp">${escapeHtml(a.time)}</span>
                  </div>
                  <div class="alert-description">${escapeHtml(a.description)}</div>
                  <div class="alert-metadata-grid">
                    <div class="meta-item"><span class="meta-key">Target:</span><span class="meta-val">${escapeHtml(a.instance)}</span></div>
                    <div class="meta-item"><span class="meta-key">Rule:</span><span class="meta-val">${escapeHtml(a.alertname)}</span></div>
                    <div class="meta-item"><span class="meta-key">Severity:</span><span class="meta-val">${escapeHtml(a.severity)}</span></div>
                  </div>
                </div>
              `;
            }).join('');
          } catch (err) {
            console.error('Error fetching alerts:', err);
          }
        }

        async function clearAlerts() {
          await fetch('/api/notifications', { method: 'DELETE' });
          fetchAlerts();
        }

        setInterval(fetchAlerts, 2500);
        fetchAlerts();
      </script>
    </body>
    </html>
    """
