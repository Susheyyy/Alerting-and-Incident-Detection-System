# Alerting and Incident Detection System

A complete real-time monitoring, telemetry analysis, and incident response architecture built with **FastAPI**, **Prometheus**, **Alertmanager**, **Grafana**, and an **Incident Alert Notification Center**. 

### ⚝ Tech Stack
- **Monitored Application**: FastAPI, Python 3.11, Uvicorn, Prometheus Python Client
- **Monitoring & Metrics Collection**: Prometheus v2.51.0, Node Exporter v1.7.0
- **Alert Routing Engine**: Alertmanager v0.27.0
- **Visualization & Dashboards**: Grafana v10.4.1 (Auto-provisioned Dashboards & Datasources)
- **Incident Dispatch Console**: FastAPI, Modern Vanilla CSS, JetBrains Mono & Inter typography
- **Containerization & Orchestration**: Docker, Docker Compose

### ⚝ System Architecture <br>
The incident detection and alerting system is structured around an automated observability and response loop:
- **FastAPI Application**: Exposes core business logic endpoints alongside `/metrics` for Prometheus scraping and `/chaos` endpoints for failure simulation.
- **Traffic Generator**: Produces continuous simulated user traffic across endpoints to create live metrics telemetry and realistic operational load.
- **Node Exporter & Prometheus**: Node Exporter gathers host metrics (CPU, Memory, Disk). Prometheus evaluates configured alerting rules periodically and fires alerts when thresholds are breached.
- **Alertmanager**: Deduplicates, groups, and routes active alerts according to severity and service tags, inhibiting notification storms.
- **Live Dispatch Console & Telegram Relay**: Receives Alertmanager webhooks, maintaining an operational incident stream and dispatching push alerts to mobile devices.
- **Grafana**: Visualizes Golden Signals, SLO compliance, latency percentiles, and infrastructure load with automatic provisioning.

```
                      +-----------------------------+
                      |   Traffic Generator         |
                      | (Continuous user traffic)   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |       FastAPI App           | :8000
                      |   /metrics (Prometheus)     |
                      |   /chaos (Failure Testing)  |
                      +--------------+--------------+
                                     |
                      +--------------+--------------+
                      | Node Exporter (Host Metrics)| :9100
                      +--------------+--------------+
                                     | Scraped every 5s
                                     v
                      +-----------------------------+
                      |     Prometheus Server       | :9090
                      |  - Evaluates Alert Rules    |
                      |  - InstanceDown, HighLatency|
                      |  - HighCPU, HighMemory      |
                      +--------------+--------------+
                                     |
                                     | Dispatches Firing Alerts
                                     v
                      +-----------------------------+
                      |        Alertmanager         | :9093
                      |  - Grouping, Routing, Inhibit|
                      |  - Silencing UI             |
                      +--------------+--------------+
                                     |
            +------------------------+------------------------+
            |                                                 |
            v                                                 v
+-------------------------------+             +-------------------------------+
|  Live Alert Notifier Web UI   | :5001       |     Telegram Bot Channel      |
|  - Instant event feed         |             |  - Direct push notifications  |
|  - Auto-refreshing cards      |             |    to ops team phone / chat   |
+-------------------------------+             +-------------------------------+
                                     ^
                                     |
+------------------------------------+------------------------+
|                      Grafana Dashboard                      | :3000
|  - Stat Panels (App Status, Request Rate, Error Rate %)     |
|  - Gauge Panels (CPU %, Memory %, SLO Compliance %)         |
|  - Time Series Panels (p50/p90/p95 Latency, Endpoint Rates) |
|  - Variable Dropdown for server/component selection         |
+-------------------------------------------------------------+
```

### ⚝ Installation & Setup
1. **Clone the Repository**
   ```bash
   git clone https://github.com/Susheyyy/Alerting-and-Incident-Detection-System.git
   cd Alerting-and-Incident-Detection-System
   ```
2. **Configure Environment Variables (Optional for Telegram Push)**
   Create a `.env` file in the root directory:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_telegram_chat_id_here
   ```
3. **Start the Entire Monitoring Stack**
   ```bash
   docker compose up -d
   ```
4. **Verify Container Health**
   ```bash
   docker compose ps
   ```

### ⚝ How to Use
- **Access Dashboards**:
  - **Monitored Application**: [http://localhost:8000](http://localhost:8000) (Swagger docs at `/docs`)
  - **Grafana Metrics Dashboard**: [http://localhost:3000](http://localhost:3000) (`admin` / `admin`)
  - **Incident Live Dispatch Console**: [http://localhost:5001](http://localhost:5001)
  - **Prometheus Console & Alerts**: [http://localhost:9090](http://localhost:9090)
  - **Alertmanager UI**: [http://localhost:9093](http://localhost:9093)
- **Simulate High Latency**:
  ```powershell
  curl.exe -X POST "http://localhost:8000/chaos/latency?delay=0.8"
  ```
- **Simulate 500 Error Spikes**:
  ```powershell
  curl.exe -X POST "http://localhost:8000/chaos/errors?enable=true"
  ```
- **Simulate Application Outage**:
  ```powershell
  docker stop incident_app
  ```
- **Reset Fault Injections & Restore Service**:
  ```powershell
  curl.exe -X POST "http://localhost:8000/chaos/reset"
  docker start incident_app
  ```

---

*Built for DevOps Practical Exam*
