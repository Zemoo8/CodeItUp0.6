# 🧪 Sandy Lab – Database Setup

This repository provides **two ways** to set up the required PostgreSQL database for the Sandy Lab project.
Choose the method that fits your environment.

---

## 📦 Prerequisites

### Method 1 (Docker)

* Docker
* Docker Compose

### Method 2 (Python Script)

* Python 3.8+
* pip
* PostgreSQL (local or remote)

---

## 🐳 Method 1: Using Docker (Recommended)

This method runs PostgreSQL and pgAdmin in containers.

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <repo-folder>
```

### 2. Start the containers

```bash
docker compose up -d
```

This will:

* Start **PostgreSQL** on host port **5433** → container port **5432**
* Start **pgAdmin** on host port **5050**

### 3. Run the setup script

```bash
python setup_db.py
```

> ⚠️ The script connects to `localhost:5433` when using Docker.

**Credentials:**

* Database: `sandy_lab`
* User: `sandy`
* Password: `sandy123`

---

### 4. (Optional) Access pgAdmin

Open:

```
http://localhost:5050
```

**Login:**

* Email: `sandy@bikini-bottom.com`
* Password: `sandy123`

**Add Server:**

* Host: `sandy-db` (container name)
* Port: `5432`
* Username: `sandy`
* Password: `sandy123`

---

## 🐍 Method 2: Without Docker (Local PostgreSQL)

### 1. Install PostgreSQL (if needed)

**Ubuntu/Debian:**

```bash
sudo apt install postgresql postgresql-contrib
```

**macOS:**

```bash
brew install postgresql
```

**Windows:**
Download from: https://www.postgresql.org/download/windows/

---

### 2. Create database and user

```sql
sudo -u postgres psql

CREATE USER sandy WITH PASSWORD 'sandy123';
CREATE DATABASE sandy_lab OWNER sandy;
GRANT ALL PRIVILEGES ON DATABASE sandy_lab TO sandy;

\q
```

---

### 3. Install dependency

```bash
pip install psycopg2-binary
```

---

### 4. Run setup script

```bash
python setup_db.py
```

> ⚠️ Default connection: `localhost:5432`

---

## 📊 Database Tables & Schema

### projects

| Field       | Type      | Description                   |
| ----------- | --------- | ----------------------------- |
| id          | SERIAL PK | Project ID                    |
| name        | TEXT      | Project name                  |
| description | TEXT      | Optional description          |
| status      | TEXT      | planned / ongoing / completed |
| priority    | INTEGER   | Default = 1                   |
| created_at  | TIMESTAMP | Creation timestamp            |

---

### inventory

| Field        | Type      | Description       |
| ------------ | --------- | ----------------- |
| id           | SERIAL PK | Item ID           |
| name         | TEXT      | Item name         |
| category     | TEXT      | Item category     |
| quantity     | INTEGER   | Default = 0       |
| unit         | TEXT      | Unit type         |
| min_required | INTEGER   | Minimum threshold |
| last_updated | TIMESTAMP | Last update       |

---

### project_requirements

| Field             | Type              | Description     |
| ----------------- | ----------------- | --------------- |
| id                | SERIAL PK         | ID              |
| project_id        | FK → projects.id  | Linked project  |
| inventory_id      | FK → inventory.id | Linked item     |
| required_quantity | INTEGER           | Required amount |

---

### experiments_log

| Field      | Type      | Description        |
| ---------- | --------- | ------------------ |
| id         | SERIAL PK | Log ID             |
| project_id | FK        | Linked project     |
| result     | TEXT      | Result description |
| success    | BOOLEAN   | Success flag       |
| notes      | TEXT      | Additional notes   |
| created_at | TIMESTAMP | Timestamp          |

---

### ai_actions_log

| Field       | Type      | Description    |
| ----------- | --------- | -------------- |
| id          | SERIAL PK | ID             |
| action_type | TEXT      | Type of action |
| description | TEXT      | Description    |
| metadata    | JSONB     | Flexible data  |
| created_at  | TIMESTAMP | Timestamp      |

---

### research_cache

| Field      | Type      | Description      |
| ---------- | --------- | ---------------- |
| id         | SERIAL PK | ID               |
| topic      | TEXT      | Research topic   |
| summary    | TEXT      | Cached summary   |
| source     | TEXT      | Source reference |
| created_at | TIMESTAMP | Timestamp        |

---

### inventory_transactions

| Field         | Type      | Description     |
| ------------- | --------- | --------------- |
| id            | SERIAL PK | ID              |
| inventory_id  | FK        | Linked item     |
| change_amount | INTEGER   | Quantity change |
| reason        | TEXT      | Reason          |
| created_at    | TIMESTAMP | Timestamp       |

---

### agent_tasks

| Field      | Type      | Description                            |
| ---------- | --------- | -------------------------------------- |
| id         | SERIAL PK | ID                                     |
| task       | TEXT      | Task description                       |
| status     | TEXT      | pending / running / completed / failed |
| result     | TEXT      | Task result                            |
| created_at | TIMESTAMP | Timestamp                              |

---

## ⚠️ Important Port Notes

* **Docker method:** uses port `5433`
* **Local PostgreSQL:** uses port `5432`

To change the port, edit:

```python
DB_CONFIG = {
    "dbname": "sandy_lab",
    "user": "sandy",
    "password": "sandy123",
    "host": "localhost",
    "port": "5433"  # change if needed
}
```

---

## ✅ Verification

Check tables:

```bash
# Docker
docker exec -it codeitup-sandy-lab psql -U sandy -d sandy_lab -c "\dt"

# Local
psql -h localhost -p 5433 -U sandy -d sandy_lab -c "\dt"
```

---

## 🛠 Troubleshooting

| Problem                     | Solution                                      |
| --------------------------- | --------------------------------------------- |
| Connection refused          | Ensure DB is running and correct port is used |
| role "sandy" does not exist | Run CREATE USER commands                      |
| psycopg2 error              | `pip install psycopg2-binary`                 |
| Port already in use         | Change port in docker-compose and script      |

---

🚀 Good luck in the competition!
