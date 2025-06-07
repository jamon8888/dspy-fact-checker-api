# DSPy-Enhanced Fact-Checker API Platform - Deployment Guide

This directory contains all the necessary files and configurations for deploying the DSPy-Enhanced Fact-Checker API Platform using Docker and Kubernetes.

## 📁 Directory Structure

```
deployment/
├── k8s/                    # Kubernetes manifests
│   ├── namespace.yaml      # Namespace and RBAC
│   ├── configmap.yaml      # Configuration and secrets
│   ├── pvc.yaml           # Persistent volume claims
│   ├── app-deployment.yaml # Main application deployment
│   ├── postgres-deployment.yaml # Database deployments
│   ├── celery-deployment.yaml   # Worker deployments
│   └── ingress.yaml       # Ingress and load balancer
├── scripts/               # Deployment scripts
│   ├── build.sh          # Docker build script
│   └── deploy.sh         # Kubernetes deployment script
├── nginx/                # Nginx configurations
├── postgres/             # PostgreSQL configurations
├── redis/                # Redis configurations
└── qdrant/               # Qdrant configurations
```

## 🐳 Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 20GB+ disk space

### Quick Start with Docker Compose

1. **Development Environment:**
   ```bash
   # Start all services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f app
   
   # Stop services
   docker-compose down
   ```

2. **Production Environment:**
   ```bash
   # Start production services
   docker-compose -f docker-compose.prod.yml up -d
   
   # Scale workers
   docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=3
   ```

3. **Test Build:**
   ```bash
   # Test the Docker build
   docker-compose -f docker-compose.test.yml up --build
   ```

### Building Custom Images

```bash
# Build development image
./deployment/scripts/build.sh

# Build production image
BUILD_TARGET=production ./deployment/scripts/build.sh

# Build and push to registry
REGISTRY=your-registry.com PUSH_IMAGE=true ./deployment/scripts/build.sh

# Build multi-architecture image
./deployment/scripts/build.sh multi-arch
```

### Environment Variables

Create a `.env` file with the following variables:

```env
# Application
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-here
DEBUG=false

# Database
DATABASE_USER=postgres
DATABASE_PASSWORD=your-secure-password
DATABASE_NAME=fact_checker_prod

# API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key

# Security
JWT_SECRET_KEY=your-jwt-secret-key
```

## ☸️ Kubernetes Deployment

### Prerequisites

- Kubernetes 1.24+
- kubectl configured
- 16GB+ RAM cluster
- 100GB+ storage
- Ingress controller (nginx recommended)

### Quick Start with Kubernetes

1. **Deploy Everything:**
   ```bash
   # Deploy the entire application
   ./deployment/scripts/deploy.sh
   
   # Check deployment status
   ./deployment/scripts/deploy.sh check
   
   # View logs
   ./deployment/scripts/deploy.sh logs
   ```

2. **Manual Deployment:**
   ```bash
   # Create namespace and RBAC
   kubectl apply -f deployment/k8s/namespace.yaml
   
   # Create secrets and config
   kubectl apply -f deployment/k8s/configmap.yaml
   
   # Create storage
   kubectl apply -f deployment/k8s/pvc.yaml
   
   # Deploy databases
   kubectl apply -f deployment/k8s/postgres-deployment.yaml
   
   # Deploy application
   kubectl apply -f deployment/k8s/app-deployment.yaml
   
   # Deploy workers
   kubectl apply -f deployment/k8s/celery-deployment.yaml
   
   # Deploy ingress
   kubectl apply -f deployment/k8s/ingress.yaml
   ```

### Configuration

1. **Update Secrets:**
   ```bash
   # Edit secrets (base64 encoded)
   kubectl edit secret fact-checker-secrets -n fact-checker
   ```

2. **Update Configuration:**
   ```bash
   # Edit configuration
   kubectl edit configmap fact-checker-config -n fact-checker
   ```

3. **Scale Services:**
   ```bash
   # Scale application
   kubectl scale deployment fact-checker-app --replicas=5 -n fact-checker
   
   # Scale workers
   kubectl scale deployment celery-worker --replicas=10 -n fact-checker
   ```

### Monitoring and Maintenance

1. **Check Status:**
   ```bash
   # View all resources
   kubectl get all -n fact-checker
   
   # Check pod logs
   kubectl logs -f deployment/fact-checker-app -n fact-checker
   
   # Check events
   kubectl get events -n fact-checker --sort-by='.lastTimestamp'
   ```

2. **Database Operations:**
   ```bash
   # Connect to PostgreSQL
   kubectl exec -it postgres-0 -n fact-checker -- psql -U postgres -d fact_checker_prod
   
   # Run migrations
   kubectl create job --from=cronjob/db-migration manual-migration -n fact-checker
   ```

3. **Backup and Restore:**
   ```bash
   # Backup database
   kubectl exec postgres-0 -n fact-checker -- pg_dump -U postgres fact_checker_prod > backup.sql
   
   # Restore database
   kubectl exec -i postgres-0 -n fact-checker -- psql -U postgres fact_checker_prod < backup.sql
   ```

## 🔧 Configuration Options

### Application Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment (development/production) | `production` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | API rate limit | `100` |
| `MAX_FILE_SIZE` | Maximum upload size | `50MB` |

### Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_HOST` | PostgreSQL host | `postgres-service` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |
| `DATABASE_NAME` | Database name | `fact_checker_prod` |
| `DATABASE_ECHO` | Enable SQL logging | `false` |

### Resource Requirements

#### Minimum Requirements

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| Application | 500m | 1Gi | - |
| PostgreSQL | 500m | 1Gi | 20Gi |
| Redis | 250m | 512Mi | 5Gi |
| Qdrant | 500m | 1Gi | 10Gi |
| Celery Worker | 500m | 1Gi | - |

#### Production Requirements

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| Application | 2 | 4Gi | - |
| PostgreSQL | 2 | 4Gi | 100Gi |
| Redis | 1 | 2Gi | 20Gi |
| Qdrant | 2 | 4Gi | 50Gi |
| Celery Worker | 2 | 4Gi | - |

## 🚀 Performance Tuning

### Horizontal Pod Autoscaling

The deployment includes HPA configurations that automatically scale based on:
- CPU utilization (70% threshold)
- Memory utilization (80% threshold)

### Database Optimization

1. **PostgreSQL Tuning:**
   - Configured for production workloads
   - Optimized connection pooling
   - Proper indexing strategies

2. **Redis Optimization:**
   - Memory-optimized configuration
   - Persistence enabled
   - Connection pooling

### Application Optimization

1. **Celery Workers:**
   - Auto-scaling based on queue length
   - Task routing optimization
   - Memory leak prevention

2. **API Performance:**
   - Response caching
   - Database query optimization
   - Async processing

## 🔒 Security

### Network Security

- Network policies restrict inter-pod communication
- TLS encryption for external traffic
- Service mesh ready (Istio compatible)

### Container Security

- Non-root user execution
- Read-only root filesystem where possible
- Minimal attack surface
- Security context constraints

### Secrets Management

- Kubernetes secrets for sensitive data
- External secret management integration ready
- Rotation policies supported

## 📊 Monitoring and Observability

### Health Checks

- Liveness probes for all services
- Readiness probes for traffic routing
- Startup probes for slow-starting services

### Metrics

- Prometheus metrics endpoint
- Custom application metrics
- Resource utilization monitoring

### Logging

- Structured JSON logging
- Centralized log aggregation ready
- Log level configuration

## 🆘 Troubleshooting

### Common Issues

1. **Pod Startup Issues:**
   ```bash
   kubectl describe pod <pod-name> -n fact-checker
   kubectl logs <pod-name> -n fact-checker
   ```

2. **Database Connection Issues:**
   ```bash
   kubectl exec -it <app-pod> -n fact-checker -- python -c "from app.db.init_db import check_db_health; import asyncio; print(asyncio.run(check_db_health()))"
   ```

3. **Storage Issues:**
   ```bash
   kubectl get pvc -n fact-checker
   kubectl describe pvc <pvc-name> -n fact-checker
   ```

### Performance Issues

1. **High Memory Usage:**
   - Check for memory leaks in workers
   - Adjust worker concurrency
   - Scale horizontally

2. **Slow Response Times:**
   - Check database performance
   - Review query optimization
   - Scale application pods

### Recovery Procedures

1. **Database Recovery:**
   - Restore from backup
   - Run data consistency checks
   - Verify application connectivity

2. **Application Recovery:**
   - Rolling restart deployment
   - Clear Redis cache if needed
   - Verify external API connectivity

## 📞 Support

For deployment issues:
1. Check the troubleshooting section
2. Review pod logs and events
3. Verify configuration and secrets
4. Check resource availability

For application issues:
1. Check application logs
2. Verify database connectivity
3. Test API endpoints manually
4. Review worker queue status
