# Codespace Setup: Python, psql & Grafana

This codespace includes:
- **Latest Python 3.x** — ready for development
- **PostgreSQL client (psql)** — connect to external PostgreSQL databases
- **Grafana** — auto-starting on port 3000

## Getting Started

### GitHub Codespaces
1. Push these files to your GitHub repository
2. Click **Code** → **Codespaces** → **Create codespace on main**
3. Wait for the container to build (first time takes ~2 min)
4. Services auto-start automatically

### Local Development (VS Code)
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Open the project in VS Code
3. Click the **><** icon (bottom left) → **Dev Containers: Reopen in Container**
4. Wait for setup to complete

## Accessing Services

### Grafana
- **URL:** `http://localhost:3000`
- **Username:** `admin`
- **Password:** `admin`
- Change the default password after first login

### PostgreSQL (psql)
Connect to an external PostgreSQL database:
```bash
psql -h <hostname> -U <username> -d <database_name>
```

Example:
```bash
psql -h db.example.com -U myuser -d mydatabase
```

### Python
Start developing with Python:
```bash
python --version
python -m pip install <package>
python script.py
```

## File Structure
```
.devcontainer/
├── devcontainer.json    # Codespace configuration
├── Dockerfile           # Dev container image setup
├── docker-compose.yml   # Services (Grafana)
└── README.md           # This file
```

## Adding Python Dependencies

Create a `requirements.txt` in the root:
```
numpy==1.24.0
pandas==2.0.0
requests==2.31.0
```

Then install:
```bash
pip install -r requirements.txt
```

## Grafana Setup

Grafana persists data in a Docker volume, so your dashboards and configurations survive container restarts.

### Add a Data Source
1. Go to **http://localhost:3000**
2. Navigate to **Connections** → **Data sources**
3. Click **Add data source**
4. Select your database type (PostgreSQL, etc.)

### Example: PostgreSQL Data Source
- **Host:** `host.docker.internal:5432` (for local database on your machine)
- Or use an external database hostname
- **Database:** Your database name
- **User:** Your database user

## Troubleshooting

**Grafana not starting?**
- Check logs: `docker logs grafana`
- Ensure port 3000 isn't already in use

**psql command not found?**
- Restart the container (Cmd/Ctrl + Shift + P → "Dev Containers: Rebuild")

**Python packages won't install?**
- Try: `pip install --upgrade pip setuptools wheel`
- Then: `pip install <package>`

## More Info
- [Grafana Documentation](https://grafana.com/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Python Official](https://python.org)
