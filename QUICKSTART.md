# ⚡ Quick Start Guide - Get Running in 2 Minutes

## Option 1: Simple Mode (No Redis/Celery Required) ✅ EASIEST

This mode runs immediately without any external dependencies.

### Step 1: Start the server
```bash
./start-simple.sh
```

That's it! The API is now running at http://localhost:8501

### Step 2: Test it
```bash
# Open API docs
open http://localhost:8501/docs

# Or test with curl
curl http://localhost:8501/health
```

**Note:** This mode disables caching and rate limiting but handles thousands of requests.

---

## Option 2: Full Production Mode (With Redis) 🚀 RECOMMENDED

For 10K+ users with caching and rate limiting.

### Prerequisites
```bash
# macOS - Install Redis
brew install redis
brew services start redis

# Ubuntu/Linux - Install Redis
sudo apt-get install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

### Step 1: Install dependencies
```bash
uv sync
```

### Step 2: Configure
```bash
cp .env.example .env
# Edit .env if needed (optional)
```

### Step 3: Start all services
```bash
./start-production.sh start
```

### Step 4: Verify
```bash
# Check status
./start-production.sh status

# Check health
curl http://localhost:8501/health

# Check metrics
curl http://localhost:8501/metrics

# Open Flower dashboard (Celery monitoring)
open http://localhost:5555
```

---

## Test Document Generation

### Test with sample data
```bash
# Generate a resume (sync mode)
curl -X POST http://localhost:8501/generate \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "resume",
    "template": "classic",
    "format": "pdf",
    "data": {
      "personalInfo": {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1 555-1234",
        "location": "New York, NY"
      },
      "professionalSummary": "Experienced software engineer with 5+ years of expertise.",
      "experience": [],
      "education": [],
      "skills": []
    }
  }' \
  --output resume.pdf

# Check the generated PDF
open resume.pdf
```

### Test async mode (recommended for production)
```bash
# Submit job
curl -X POST http://localhost:8501/generate/async \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "resume",
    "template": "classic",
    "data": {...}
  }'

# Response: {"job_id": "abc-123", ...}

# Check status
curl http://localhost:8501/jobs/abc-123

# Download when ready
curl http://localhost:8501/jobs/abc-123/download --output resume.pdf
```

---

## Troubleshooting

### Issue: "Redis not available"
**Solution:**
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Or use simple mode (no Redis needed)
./start-simple.sh
```

### Issue: "Port 8501 already in use"
**Solution:**
```bash
# Find what's using the port
lsof -i :8501

# Kill it
kill -9 <PID>

# Or use a different port
./start-simple.sh 8502
```

### Issue: "uv: command not found"
**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell
source ~/.bashrc  # or ~/.zshrc
```

### Issue: Import errors
**Solution:**
```bash
# Reinstall dependencies
uv sync --reinstall
```

---

## Stop Services

### Simple mode
Just press `Ctrl+C`

### Production mode
```bash
./start-production.sh stop
```

---

## What's Next?

1. **Read the API docs:** http://localhost:8501/docs
2. **See full deployment guide:** See `SCALING_GUIDE.md`
3. **Load testing:** See `PERFORMANCE.md`
4. **Configuration:** Edit `.env` file

---

## Quick Reference

| Mode | Command | Requirements | Capacity |
|------|---------|--------------|----------|
| **Simple** | `./start-simple.sh` | None | 1K-5K users |
| **Production** | `./start-production.sh start` | Redis | 10K+ users |

---

## Common Commands

```bash
# Simple mode
./start-simple.sh              # Start on port 8501
./start-simple.sh 8502         # Start on custom port

# Production mode
./start-production.sh start    # Start all services
./start-production.sh stop     # Stop all services
./start-production.sh restart  # Restart all services
./start-production.sh status   # Check status

# Testing
curl http://localhost:8501/health    # Health check
curl http://localhost:8501/metrics   # Performance metrics
open http://localhost:8501/docs      # API documentation
open http://localhost:5555           # Celery dashboard (production mode)
```

---

## Need Help?

- **Can't start:** Make sure port 8501 is free
- **Redis issues:** Use `./start-simple.sh` instead
- **Import errors:** Run `uv sync`
- **Other issues:** Check logs or create a GitHub issue

**You're ready to go! 🎉**
