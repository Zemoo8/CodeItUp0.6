# Sandy's Treedome Lab - Deployment Guide

## 📋 Quick Reference

| Task | Command |
|------|---------|
| **Local Dev (Windows)** | `run.bat` |
| **Local Dev (Mac/Linux)** | `./run.sh` |
| **Production** | `run.bat prod` or `./run.sh prod` |
| **Docker Build** | `docker build -t sandy-ai-lab:latest .` |
| **Docker Run** | See Docker section below |

---

## 🧹 What Was Cleaned Up

✅ **Removed:**
- `debug_deepagents.py` - Standalone debug script (replaced by test suite)
- `database/` - Empty, stale directory
- Unpinned versions in `requirements.txt` (now explicit versions)

✅ **Added:**
- `.gitignore` - Excludes .venv, __pycache__, .env, debug files
- `README.md` - Complete project documentation
- `run.bat` - Windows startup script (auto-installs deps, loads .env)
- `run.sh` - Mac/Linux startup script  
- `Dockerfile` - Containerization for cloud deployment
- `.dockerignore` - Exclude unnecessary files from Docker image
- Version pinning for reproducibility

**Note:** `backend/` folder still exists but is unused (had stale venv, can be deleted manually if needed)

---

## 🚀 Local Development

### Windows:
```bash
# One-liner startup (auto-detects .env, installs deps, runs dev server)
run.bat

# To run in production mode (gunicorn)
run.bat prod
```

### Mac/Linux:
```bash
# Make script executable (first time only)
chmod +x run.sh

# Run
./run.sh

# Production mode
./run.sh prod
```

Both scripts will:
1. Create `.venv` if it doesn't exist
2. Load environment variables from `.env`
3. Install/update requirements
4. Start the server (dev mode with auto-reload by default)

**Access:**
- Dashboard: http://localhost:8000/ui
- API Docs: http://localhost:8000/docs

---

## 🐳 Docker Deployment

### Build Image:
```bash
docker build -t sandy-ai-lab:latest .
```

### Run Locally (with Docker):
```bash
docker run -p 8000:8000 \
  -e DATABASE_API_URL=http://192.168.1.118:8000 \
  -e GROQ_API_KEY=your_key_here \
  -e USE_DEEPAGENTS=true \
  -e DEEPAGENTS_MODEL=openai:llama-3.3-70b-versatile \
  sandy-ai-lab:latest
```

### Push to Container Registry (AWS ECR):
```bash
# Create ECR repository
aws ecr create-repository --repository-name sandy-ai-lab

# Tag image
docker tag sandy-ai-lab:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/sandy-ai-lab:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

# Push
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/sandy-ai-lab:latest
```

---

## ☁️ Cloud Deployment Options

### Option 1: AWS ECS (Elastic Container Service)

1. **Push image to ECR** (see Docker section)
2. **Create ECS cluster** (one-click via AWS console)
3. **Create task definition** with:
   - Image: `123456789.dkr.ecr.us-east-1.amazonaws.com/sandy-ai-lab:latest`
   - Memory: 512 MB minimum
   - Port: 8000
   - Environment variables (from .env)
4. **Create service** pointing to task definition
5. **Update Application Load Balancer** (ALB) target group to service

**Cost:** ~$10-20/month for small workload

**Access:** ELB DNS name (e.g., `sandy-alb-123456.us-east-1.elb.amazonaws.com`)

---

### Option 2: Google Cloud Run

1. **Build and push to Artifact Registry:**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/sandy-ai-lab
```

2. **Deploy to Cloud Run:**
```bash
gcloud run deploy sandy-ai-lab \
  --image gcr.io/PROJECT_ID/sandy-ai-lab:latest \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --set-env-vars DATABASE_API_URL=http://...,GROQ_API_KEY=...
```

3. **Access:** `https://sandy-ai-lab-HASH-uc.a.run.app`

**Benefits:** 
- Auto-scaling
- Pay-per-use (free tier available)
- No container management needed

---

### Option 3: Heroku

1. **Install Heroku CLI:**
```bash
# Windows: via installer or choco
choco install heroku-cli

# Mac: via Homebrew
brew tap heroku/brew && brew install heroku
```

2. **Login and create app:**
```bash
heroku login
heroku create sandy-ai-lab
```

3. **Set environment variables:**
```bash
heroku config:set \
  DATABASE_API_URL=http://192.168.1.118:8000 \
  GROQ_API_KEY=your_key \
  USE_DEEPAGENTS=true
```

4. **Deploy:**
```bash
git push heroku main
```

5. **Access:** `https://sandy-ai-lab.herokuapp.com/ui`

**Cost:** Free tier (limited), ~$7-50/month for hobby/production

---

### Option 4: Fly.io (Modern Alternative to Heroku)

1. **Install Fly CLI:**
```bash
# Windows
iwr https://fly.io/install.ps1 -useb | iex

# Mac
curl -L https://fly.io/install.sh | sh
```

2. **Initialize:**
```bash
fly auth login
fly launch  # Create fly.toml
```

3. **Deploy:**
```bash
fly deploy
```

4. **Set secrets:**
```bash
fly secrets set GROQ_API_KEY=your_key
fly secrets set DATABASE_API_URL=http://...
```

**Cost:** Free tier available, ~$3-10/month for hobby

---

### Option 5: Traditional VPS (DigitalOcean/Linode/AWS EC2)

1. **Create droplet/instance** (2GB RAM minimum):
```bash
# Ubuntu 22.04 LTS recommended
```

2. **SSH in and setup:**
```bash
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3.11 python3-pip postgresql nginx git

# Clone repository
git clone https://github.com/yourname/sandy-ai-lab.git
cd sandy-ai-lab

# Setup app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy .env
cp .env.example .env
# [Edit .env with real values]
nano .env
```

3. **Configure systemd service** (`/etc/systemd/system/sandy-ai-lab.service`):
```ini
[Unit]
Description=Sandy's Treedome Lab API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/root/sandy-ai-lab
Environment="PATH=/root/sandy-ai-lab/.venv/bin"
ExecStart=/root/sandy-ai-lab/.venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Enable and start:**
```bash
systemctl enable sandy-ai-lab
systemctl start sandy-ai-lab
```

5. **Configure Nginx reverse proxy** (`/etc/nginx/sites-available/sandy-ai-lab`):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

6. **Enable HTTPS with Let's Encrypt:**
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

**Cost:** $5-15/month for 2GB VPS

---

## 🔐 Security Checklist

Before deploying to production:

- [ ] **Environment variables:** All sensitive keys in `.env`, never in code
- [ ] **HTTPS/TLS:** Use reverse proxy (Nginx) or cloud provider's SSL/TLS
- [ ] **API authentication:** Consider adding API key/JWT middleware for `/run` endpoint
- [ ] **CORS:** Restrict to specific frontend origins
- [ ] **Database:** Use encrypted connections (PostgreSQL SSL)
- [ ] **Secrets rotation:** Rotate Groq API key every 30 days
- [ ] **Rate limiting:** Add rate limit middleware to prevent abuse
- [ ] **Logging:** Configure structured logging for debugging
- [ ] **Health checks:** Test `/docs` endpoint regularly (set up monitoring)
- [ ] **Backups:** Database daily backups (if using PostgreSQL)

---

## 🧪 Testing Before Deployment

Run full test suite:
```bash
python test_pipeline.py
python test_agents.py
```

Test both execution modes:
```bash
# Deterministic
python -c "from main import app; from fastapi.testclient import TestClient; print(TestClient(app).post('/run').json()['execution_mode'])"

# Deep Agents (if GROQ_API_KEY set)
USE_DEEPAGENTS=true python -c "from main import app; from fastapi.testclient import TestClient; print(TestClient(app).post('/run').json()['execution_mode'])"
```

---

## 📊 Performance Tuning

### For High Traffic:
- Increase Gunicorn workers: `gunicorn -w 8` (2x CPU cores)
- Enable Redis caching for API responses
- Use PostgreSQL connection pooling (pgBouncer)
- Consider Nginx caching for static assets

### For Latency:
- Use `USE_DEEPAGENTS=false` for faster responses
- Or use `openai:llama-3.3-70b-versatile` (fastest Groq model)
- Use API caching to avoid repeated DB queries

### Memory Usage:
- Set `--max-requests` in Gunicorn to restart workers periodically
- Monitor Deep Agents orchestration overhead (~100ms per call)

---

## 🚨 Troubleshooting

### Port 8000 already in use:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -i :8000
kill -9 <PID>
```

### `.venv` creation fails:
```bash
# Delete and recreate
rm -r .venv  # Mac/Linux
rmdir /s .venv  # Windows
python -m venv .venv
```

### Gunicorn not found:
```bash
# Ensure .venv is activated
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate      # Windows

# Reinstall
pip install gunicorn
```

### Docker image too large:
Build is using 2GB+ due to site-packages. Optimize with:
```dockerfile
# In Dockerfile, before final image:
RUN pip install --no-cache-dir -r requirements.txt
```

---

## 🎯 Recommended Production Setup

**For hackathon/small team:**
- Deploy Docker image to Fly.io or Heroku
- Minimal ops overhead
- Costs: $0-10/month
- Time to deploy: 5 minutes

**For scalability:**
- Docker image → AWS ECR
- ECS with Application Load Balancer
- RDS PostgreSQL for database
- CloudFront for static assets
- Costs: $50-200/month
- Time to setup: 30 minutes

**For simplicity:**
- DigitalOcean App Platform or Google Cloud Run
- Automatic HTTPS, auto-scaling, monitoring
- Costs: $5-20/month
- Time to deploy: 10 minutes

---

## 📞 Support

For questions:
1. Check `/docs` endpoint for API spec
2. Review logs: `cat /var/log/syslog | grep sandy-ai-lab`
3. Test connectivity: `curl -v http://localhost:8000/ui`
4. Enable debug logging: `DEEPAGENTS_DEBUG=true`

