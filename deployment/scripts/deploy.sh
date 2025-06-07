#!/bin/bash

# DSPy-Enhanced Fact-Checker API Platform Deployment Script
# This script deploys the application to Kubernetes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="fact-checker"
APP_NAME="dspy-fact-checker"
IMAGE_TAG="${IMAGE_TAG:-latest}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    # Check if Docker is installed (for building images)
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not installed. You may need it for building images."
    fi
    
    log_success "Prerequisites check completed"
}

create_namespace() {
    log_info "Creating namespace and RBAC..."
    
    kubectl apply -f deployment/k8s/namespace.yaml
    
    log_success "Namespace created"
}

create_secrets() {
    log_info "Creating secrets and configmaps..."
    
    # Check if secrets file exists
    if [ ! -f "deployment/k8s/configmap.yaml" ]; then
        log_error "ConfigMap file not found. Please ensure deployment/k8s/configmap.yaml exists."
        exit 1
    fi
    
    kubectl apply -f deployment/k8s/configmap.yaml
    
    log_success "Secrets and configmaps created"
}

create_storage() {
    log_info "Creating persistent volumes..."
    
    kubectl apply -f deployment/k8s/pvc.yaml
    
    log_success "Persistent volumes created"
}

deploy_databases() {
    log_info "Deploying databases..."
    
    kubectl apply -f deployment/k8s/postgres-deployment.yaml
    
    # Wait for databases to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready pod -l app=dspy-fact-checker,component=postgres -n $NAMESPACE --timeout=300s
    
    log_info "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=dspy-fact-checker,component=redis -n $NAMESPACE --timeout=300s
    
    log_info "Waiting for Qdrant to be ready..."
    kubectl wait --for=condition=ready pod -l app=dspy-fact-checker,component=qdrant -n $NAMESPACE --timeout=300s
    
    log_success "Databases deployed and ready"
}

run_migrations() {
    log_info "Running database migrations..."
    
    # Create a temporary job to run migrations
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration-$(date +%s)
  namespace: $NAMESPACE
  labels:
    app: $APP_NAME
    component: migration
spec:
  template:
    spec:
      serviceAccountName: fact-checker-service-account
      containers:
      - name: migration
        image: fact-checker:$IMAGE_TAG
        command: ["python", "-m", "alembic", "upgrade", "head"]
        env:
        - name: ENVIRONMENT
          value: "$ENVIRONMENT"
        - name: DATABASE_HOST
          valueFrom:
            configMapKeyRef:
              name: fact-checker-config
              key: DATABASE_HOST
        - name: DATABASE_PORT
          valueFrom:
            configMapKeyRef:
              name: fact-checker-config
              key: DATABASE_PORT
        - name: DATABASE_NAME
          valueFrom:
            configMapKeyRef:
              name: fact-checker-config
              key: DATABASE_NAME
        - name: DATABASE_USER
          valueFrom:
            secretKeyRef:
              name: fact-checker-secrets
              key: DATABASE_USER
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: fact-checker-secrets
              key: DATABASE_PASSWORD
      restartPolicy: Never
  backoffLimit: 3
EOF
    
    log_success "Database migration job created"
}

deploy_application() {
    log_info "Deploying application..."
    
    kubectl apply -f deployment/k8s/app-deployment.yaml
    
    log_info "Waiting for application to be ready..."
    kubectl wait --for=condition=ready pod -l app=dspy-fact-checker,component=app -n $NAMESPACE --timeout=300s
    
    log_success "Application deployed and ready"
}

deploy_workers() {
    log_info "Deploying Celery workers..."
    
    kubectl apply -f deployment/k8s/celery-deployment.yaml
    
    log_info "Waiting for workers to be ready..."
    kubectl wait --for=condition=ready pod -l app=dspy-fact-checker,component=celery-worker -n $NAMESPACE --timeout=300s
    
    log_success "Workers deployed and ready"
}

deploy_ingress() {
    log_info "Deploying ingress and load balancer..."
    
    kubectl apply -f deployment/k8s/ingress.yaml
    
    log_success "Ingress deployed"
}

check_deployment() {
    log_info "Checking deployment status..."
    
    echo ""
    log_info "Pods status:"
    kubectl get pods -n $NAMESPACE
    
    echo ""
    log_info "Services status:"
    kubectl get services -n $NAMESPACE
    
    echo ""
    log_info "Ingress status:"
    kubectl get ingress -n $NAMESPACE
    
    echo ""
    log_info "PVC status:"
    kubectl get pvc -n $NAMESPACE
    
    # Check if application is responding
    log_info "Checking application health..."
    APP_SERVICE_IP=$(kubectl get service app-service -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
    if kubectl run --rm -i --tty --restart=Never test-pod --image=curlimages/curl -- curl -f http://$APP_SERVICE_IP:8000/health; then
        log_success "Application is responding to health checks"
    else
        log_warning "Application health check failed"
    fi
}

show_access_info() {
    log_info "Deployment completed!"
    echo ""
    log_info "Access information:"
    
    # Get LoadBalancer IP
    EXTERNAL_IP=$(kubectl get service nginx-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$EXTERNAL_IP" ]; then
        EXTERNAL_IP=$(kubectl get service nginx-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
    
    if [ -n "$EXTERNAL_IP" ]; then
        echo "  External IP/Hostname: $EXTERNAL_IP"
        echo "  API Documentation: http://$EXTERNAL_IP/docs"
        echo "  Health Check: http://$EXTERNAL_IP/health"
    else
        log_warning "External IP not yet assigned. Check 'kubectl get service nginx-service -n $NAMESPACE' later."
    fi
    
    echo ""
    log_info "Useful commands:"
    echo "  View logs: kubectl logs -f deployment/fact-checker-app -n $NAMESPACE"
    echo "  Scale app: kubectl scale deployment fact-checker-app --replicas=5 -n $NAMESPACE"
    echo "  Port forward: kubectl port-forward service/app-service 8000:8000 -n $NAMESPACE"
    echo "  Delete deployment: kubectl delete namespace $NAMESPACE"
}

# Main deployment flow
main() {
    log_info "Starting deployment of $APP_NAME to $ENVIRONMENT environment..."
    
    check_prerequisites
    create_namespace
    create_secrets
    create_storage
    deploy_databases
    run_migrations
    deploy_application
    deploy_workers
    deploy_ingress
    
    sleep 10  # Wait a bit for everything to settle
    
    check_deployment
    show_access_info
    
    log_success "Deployment completed successfully!"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "check")
        check_deployment
        ;;
    "clean")
        log_warning "This will delete the entire $NAMESPACE namespace. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            kubectl delete namespace $NAMESPACE
            log_success "Namespace $NAMESPACE deleted"
        else
            log_info "Cleanup cancelled"
        fi
        ;;
    "logs")
        kubectl logs -f deployment/fact-checker-app -n $NAMESPACE
        ;;
    *)
        echo "Usage: $0 {deploy|check|clean|logs}"
        echo "  deploy: Deploy the entire application"
        echo "  check:  Check deployment status"
        echo "  clean:  Delete the entire deployment"
        echo "  logs:   Follow application logs"
        exit 1
        ;;
esac
