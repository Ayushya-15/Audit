# 🛡️ RiskShield — GRC Compliance Tool

**ISO 31000-aligned Governance, Risk & Compliance tool with ML-powered risk detection.**

RiskShield identifies and eliminates risks in end-user systems within a network using machine learning for behavioral anomaly detection, probabilistic risk scoring, and automated treatment workflows — all aligned with ISO 31000 risk management principles.

## Key Features

| Feature | Description |
|---------|-------------|
| **ML Anomaly Detection** | Isolation Forest for outlier detection in network traffic and system resource metrics |
| **Risk Prediction** | Random Forest classifier scoring risks as Low/Medium/High/Critical per ISO 31000 (likelihood × impact) |
| **Behavior Profiling** | Time-series deviation detection for user logon patterns and data exfiltration indicators |
| **Network Discovery** | Auto-discover end-user devices with telemetry collection (CPU, memory, network flows, processes) |
| **Risk Treatment** | One-click actions: quarantine device, apply firewall rules, patch, accept, or escalate |
| **PDF Reports** | ISO 31000-compliant reports with executive summary, heatmaps, treatment plans, and audit trail |
| **Real-time Dashboard** | Risk heatmap, network topology visualization (Cytoscape.js), alerts, and treatment workflows |

## Tech Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy, scikit-learn, ReportLab
- **Frontend:** React 19, Vite, Tailwind CSS, Chart.js, Cytoscape.js
- **Database:** SQLite (default) / PostgreSQL
- **Deployment:** Docker Compose ready

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (optional — only needed for the frontend UI)

### One-command setup

```bash
python run.py
```

This will:
1. Create a Python virtual environment (`venv/`)
2. Install all backend dependencies
3. Install frontend dependencies (if `npm` is available)
4. Start the **backend** on http://localhost:8000
5. Start the **frontend** dev server on http://localhost:5173 (if Node.js is installed)

Press `Ctrl+C` to stop both services.

### Manual setup

```bash
# 1. Backend
cd backend
python -m venv ../venv
source ../venv/bin/activate   # Windows: ..\venv\Scripts\activate
pip install -r requirements.txt

# 2. Generate demo data (discovers 5 devices, trains ML models)
cd .. && python demo/generate_data.py

# 3. Start backend server
cd backend && uvicorn app.main:app --reload --port 8000

# 4. Frontend (new terminal — optional, requires Node.js 18+)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser (or http://localhost:8000/docs for the API).

### Docker (alternative)

```bash
docker-compose up --build
```

Open **http://localhost:3000** in your browser.

## 2-Minute Demo

1. Start the backend server (see Quick Start above)
2. Run the demo script:

```bash
chmod +x demo/demo_script.sh
./demo/demo_script.sh
```

Or use the web UI:
1. Click **"Run Full Scan"** on the Dashboard
2. View detected risks in the **Treatment** tab
3. Apply treatment actions (quarantine, firewall rule, etc.)
4. Download a **PDF Report** from the Reports tab

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/devices/` | List all devices |
| `POST` | `/api/devices/discover` | Auto-discover network devices |
| `GET` | `/api/risks/dashboard` | Dashboard statistics |
| `GET` | `/api/risks/heatmap` | Risk heatmap data |
| `POST` | `/api/risks/scan` | Run full scan (telemetry + risk assessment) |
| `GET` | `/api/risks/alerts` | List alerts |
| `GET` | `/api/ml/status` | ML model status |
| `POST` | `/api/ml/train` | Retrain ML models |
| `POST` | `/api/treatment/execute` | Execute risk treatment |
| `GET` | `/api/treatment/audit-log` | ISO 31000 audit trail |
| `GET` | `/api/reports/pdf` | Download PDF report |

## ISO 31000 Alignment

RiskShield follows the ISO 31000 risk management framework:

1. **Context Establishment** — Network discovery, device profiling
2. **Risk Identification** — ML-based anomaly and behavior detection
3. **Risk Analysis** — Probabilistic scoring (likelihood × impact)
4. **Risk Evaluation** — Severity classification and prioritization
5. **Risk Treatment** — Automated remediation actions with pre/post re-scoring
6. **Monitoring & Review** — Continuous telemetry collection and model retraining

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Application settings
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/              # DB models and Pydantic schemas
│   │   ├── ml/                  # ML models (anomaly, risk, behavior)
│   │   ├── network/             # Device discovery and telemetry
│   │   ├── risk/                # Risk assessment and treatment
│   │   ├── reports/             # PDF report generation
│   │   └── routers/             # API route handlers
│   ├── tests/                   # Pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # React UI components
│   │   ├── api/                 # API client
│   │   └── App.jsx              # Main application
│   ├── package.json
│   └── Dockerfile
├── demo/
│   ├── generate_data.py         # Synthetic data generator
│   └── demo_script.sh           # CLI demo script
├── docker-compose.yml
└── README.md
```

## Security Notes

- No real exploits — focuses on detection and remediation
- API key authentication (configure `API_KEY` env var in production)
- CORS configured for frontend origins only
- All treatment actions are simulated (no actual network changes)