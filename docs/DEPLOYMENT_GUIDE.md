# 🚀 **Deployment Guide**

Complete deployment guide for production environments.

## 🎯 **Deployment Options**

### **1. Docker Compose (Recommended)**
- **Best for**: Small to medium deployments
- **Complexity**: Low
- **Scalability**: Moderate
- **Maintenance**: Easy

### **2. Kubernetes**
- **Best for**: Large-scale deployments
- **Complexity**: High
- **Scalability**: Excellent
- **Maintenance**: Complex

### **3. Cloud Platforms**
- **Best for**: Managed deployments
- **Complexity**: Medium
- **Scalability**: Excellent
- **Maintenance**: Managed

## 🐳 **Docker Compose Deployment**

### **Production Setup**
```bash
# 1. Clone repository
git clone https://github.com/your-repo/fact-checker.git
cd fact-checker

# 2. Configure environment
cp .env.production .env
nano .env  # Edit with your values

# 3. Deploy services
docker-compose -f docker-compose.prod.yml up -d

# 4. Initialize database
docker-compose exec app python scripts/init_database.py

# 5. Verify deployment
curl http://localhost:8000/health
```

### **Environment Configuration**
```bash
# Required Environment Variables
MISTRAL_API_KEY=your_mistral_api_key
DATABASE_URL=postgresql://user:pass@postgres:5432/factchecker
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-super-secret-key

# Optional but Recommended
SENTRY_DSN=your_sentry_dsn
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### **SSL/TLS Configuration**
```bash
# Generate SSL certificates
mkdir -p deployment/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deployment/nginx/ssl/nginx.key \
  -out deployment/nginx/ssl/nginx.crt

# Update nginx configuration
nano deployment/nginx/nginx-prod.conf
```

### **Backup Strategy**
```bash
# Database backup
docker-compose exec postgres pg_dump -U factchecker factchecker > backup.sql

# Redis backup
docker-compose exec redis redis-cli --rdb dump.rdb

# File backup
tar -czf uploads_backup.tar.gz uploads/
```

## ☸️ **Kubernetes Deployment**

### **Prerequisites**
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### **Deploy to Kubernetes**
```bash
# 1. Create namespace
kubectl create namespace fact-checker

# 2. Create secrets
kubectl create secret generic fact-checker-secrets \
  --from-literal=mistral-api-key=your_key \
  --from-literal=database-password=your_password \
  --from-literal=redis-password=your_password \
  --from-literal=secret-key=your_secret \
  -n fact-checker

# 3. Deploy services
kubectl apply -f deployment/k8s/ -n fact-checker

# 4. Check deployment
kubectl get pods -n fact-checker
kubectl get services -n fact-checker
```

### **Kubernetes Manifests**

#### **Application Deployment**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fact-checker-app
  namespace: fact-checker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fact-checker-app
  template:
    metadata:
      labels:
        app: fact-checker-app
    spec:
      containers:
      - name: app
        image: fact-checker:latest
        ports:
        - containerPort: 8000
        env:
        - name: MISTRAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: fact-checker-secrets
              key: mistral-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

#### **Service Configuration**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: fact-checker-service
  namespace: fact-checker
spec:
  selector:
    app: fact-checker-app
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### **Horizontal Pod Autoscaler**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fact-checker-hpa
  namespace: fact-checker
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fact-checker-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## ☁️ **Cloud Platform Deployment**

### **AWS Deployment**

#### **ECS with Fargate**
```bash
# 1. Create ECS cluster
aws ecs create-cluster --cluster-name fact-checker-cluster

# 2. Create task definition
aws ecs register-task-definition --cli-input-json file://aws-task-definition.json

# 3. Create service
aws ecs create-service \
  --cluster fact-checker-cluster \
  --service-name fact-checker-service \
  --task-definition fact-checker:1 \
  --desired-count 2 \
  --launch-type FARGATE
```

#### **EKS Deployment**
```bash
# 1. Create EKS cluster
eksctl create cluster --name fact-checker --region us-west-2

# 2. Deploy application
kubectl apply -f deployment/k8s/

# 3. Setup load balancer
kubectl apply -f deployment/aws/alb-ingress.yaml
```

### **Google Cloud Deployment**

#### **Cloud Run**
```bash
# 1. Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/fact-checker

# 2. Deploy to Cloud Run
gcloud run deploy fact-checker \
  --image gcr.io/PROJECT_ID/fact-checker \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### **GKE Deployment**
```bash
# 1. Create GKE cluster
gcloud container clusters create fact-checker-cluster \
  --zone us-central1-a \
  --num-nodes 3

# 2. Deploy application
kubectl apply -f deployment/k8s/
```

### **Azure Deployment**

#### **Container Instances**
```bash
# 1. Create resource group
az group create --name fact-checker-rg --location eastus

# 2. Deploy container
az container create \
  --resource-group fact-checker-rg \
  --name fact-checker \
  --image fact-checker:latest \
  --dns-name-label fact-checker \
  --ports 8000
```

#### **AKS Deployment**
```bash
# 1. Create AKS cluster
az aks create \
  --resource-group fact-checker-rg \
  --name fact-checker-cluster \
  --node-count 3 \
  --enable-addons monitoring

# 2. Get credentials
az aks get-credentials \
  --resource-group fact-checker-rg \
  --name fact-checker-cluster

# 3. Deploy application
kubectl apply -f deployment/k8s/
```

## 🔧 **Configuration Management**

### **Environment-Specific Configs**

#### **Development**
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  app:
    build:
      target: development
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - .:/app
    command: uvicorn app.main:app --reload --host 0.0.0.0
```

#### **Staging**
```yaml
# docker-compose.staging.yml
version: '3.8'
services:
  app:
    build:
      target: production
    environment:
      - ENVIRONMENT=staging
      - LOG_LEVEL=INFO
    replicas: 2
```

#### **Production**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    build:
      target: production
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=WARNING
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

### **Secrets Management**

#### **Docker Secrets**
```bash
# Create secrets
echo "your_mistral_api_key" | docker secret create mistral_api_key -
echo "your_database_password" | docker secret create db_password -

# Use in compose file
services:
  app:
    secrets:
      - mistral_api_key
      - db_password
```

#### **Kubernetes Secrets**
```bash
# Create from file
kubectl create secret generic fact-checker-config \
  --from-file=.env.production \
  -n fact-checker

# Create from literals
kubectl create secret generic api-keys \
  --from-literal=mistral-key=your_key \
  --from-literal=openai-key=your_key \
  -n fact-checker
```

## 📊 **Monitoring & Observability**

### **Prometheus & Grafana**
```yaml
# monitoring/docker-compose.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### **Logging with ELK Stack**
```yaml
# logging/docker-compose.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
  
  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
  
  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    ports:
      - "5601:5601"
```

## 🔒 **Security Hardening**

### **SSL/TLS Configuration**
```nginx
# nginx-prod.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/nginx.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **Network Security**
```yaml
# docker-compose.prod.yml
networks:
  fact-checker-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16
    driver_opts:
      com.docker.network.bridge.enable_icc: "false"
      com.docker.network.bridge.enable_ip_masquerade: "true"
```

### **Container Security**
```dockerfile
# Security-hardened Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set security headers
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Switch to non-root user
USER appuser

# Set secure permissions
COPY --chown=appuser:appuser . /app
RUN chmod -R 755 /app
```

## 🔄 **CI/CD Pipeline**

### **GitHub Actions**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build and push Docker image
      run: |
        docker build -t fact-checker:latest .
        docker tag fact-checker:latest ${{ secrets.REGISTRY_URL }}/fact-checker:latest
        docker push ${{ secrets.REGISTRY_URL }}/fact-checker:latest
    
    - name: Deploy to production
      run: |
        ssh ${{ secrets.PRODUCTION_HOST }} "
          cd /opt/fact-checker &&
          docker-compose -f docker-compose.prod.yml pull &&
          docker-compose -f docker-compose.prod.yml up -d
        "
```

### **GitLab CI/CD**
```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker build -t fact-checker:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/fact-checker-app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
```

## 📈 **Scaling Strategies**

### **Horizontal Scaling**
```bash
# Docker Compose scaling
docker-compose -f docker-compose.prod.yml up -d --scale app=5 --scale celery-worker=10

# Kubernetes scaling
kubectl scale deployment fact-checker-app --replicas=10 -n fact-checker
```

### **Vertical Scaling**
```yaml
# Increase resource limits
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### **Database Scaling**
```yaml
# PostgreSQL read replicas
services:
  postgres-primary:
    image: postgres:13
    environment:
      - POSTGRES_REPLICATION_MODE=master
  
  postgres-replica:
    image: postgres:13
    environment:
      - POSTGRES_REPLICATION_MODE=slave
      - POSTGRES_MASTER_SERVICE=postgres-primary
```

---

**🎯 Production-ready deployment strategies for any environment**
