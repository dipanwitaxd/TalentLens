# Deployment Guide

## Local Development

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Required for full functionality
export GROQ_API_KEY="your_groq_api_key"

# Optional configurations
export LOG_LEVEL="INFO"
export INDEX_DIRECTORY="./custom_indexes"
```

### 3. Run Application
```bash
# Web interface
streamlit run ui/streamlit_app.py

# Command line testing
python main.py
```

## Docker Deployment

### 1. Build Image
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. Run Container
```bash
docker build -t talentlens .
docker run -p 8501:8501 -e GROQ_API_KEY=your_key talentlens
```

## Cloud Deployment

### Streamlit Cloud
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Add secrets: `GROQ_API_KEY = "your_key"`
4. Deploy automatically

### AWS EC2
```bash
# Launch EC2 instance (t3.medium recommended)
# Install dependencies
sudo yum update -y
sudo yum install -y python3 python3-pip git

# Clone and setup
git clone your-repo
cd talentlens-ats
pip3 install -r requirements.txt

# Run with PM2 for process management
npm install -g pm2
pm2 start "streamlit run ui/streamlit_app.py --server.port=8501" --name talentlens
```

### Google Cloud Platform
```bash
# Use Cloud Run for serverless deployment
gcloud run deploy talentlens \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=your_key
```

## Production Considerations

### Performance Optimization
- Use Redis for caching frequent queries
- Implement connection pooling for database
- Add CDN for static assets
- Configure horizontal scaling

### Security
- Implement authentication (OAuth, JWT)
- Use HTTPS in production
- Validate all inputs
- Implement rate limiting

### Monitoring
- Add application monitoring (DataDog, New Relic)
- Set up error tracking (Sentry)
- Configure log aggregation
- Implement health checks

### Backup Strategy
- Regular index backups
- Configuration versioning
- Database snapshots
- Code repository redundancy
