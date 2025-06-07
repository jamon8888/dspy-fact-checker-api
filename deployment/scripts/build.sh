#!/bin/bash

# DSPy-Enhanced Fact-Checker API Platform Docker Build Script
# This script builds and optionally pushes Docker images

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-fact-checker}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-}"
DOCKERFILE="${DOCKERFILE:-Dockerfile}"
BUILD_TARGET="${BUILD_TARGET:-production}"
PUSH_IMAGE="${PUSH_IMAGE:-false}"
NO_CACHE="${NO_CACHE:-false}"

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
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    # Check if Dockerfile exists
    if [ ! -f "$DOCKERFILE" ]; then
        log_error "Dockerfile not found: $DOCKERFILE"
        exit 1
    fi
    
    log_success "Prerequisites check completed"
}

build_image() {
    log_info "Building Docker image..."
    
    # Construct full image name
    FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="$REGISTRY/$FULL_IMAGE_NAME"
    fi
    
    # Build arguments
    BUILD_ARGS=""
    if [ "$NO_CACHE" = "true" ]; then
        BUILD_ARGS="$BUILD_ARGS --no-cache"
    fi
    
    # Add build target
    BUILD_ARGS="$BUILD_ARGS --target $BUILD_TARGET"
    
    # Add build context and labels
    BUILD_ARGS="$BUILD_ARGS --label version=$IMAGE_TAG"
    BUILD_ARGS="$BUILD_ARGS --label build-date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    BUILD_ARGS="$BUILD_ARGS --label git-commit=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    
    log_info "Building image: $FULL_IMAGE_NAME"
    log_info "Build target: $BUILD_TARGET"
    log_info "Build args: $BUILD_ARGS"
    
    # Build the image
    docker build $BUILD_ARGS -t "$FULL_IMAGE_NAME" -f "$DOCKERFILE" .
    
    log_success "Image built successfully: $FULL_IMAGE_NAME"
    
    # Show image size
    IMAGE_SIZE=$(docker images "$FULL_IMAGE_NAME" --format "table {{.Size}}" | tail -n 1)
    log_info "Image size: $IMAGE_SIZE"
}

test_image() {
    log_info "Testing Docker image..."
    
    FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="$REGISTRY/$FULL_IMAGE_NAME"
    fi
    
    # Test if image can start
    log_info "Testing if image can start..."
    CONTAINER_ID=$(docker run -d --rm -p 8001:8000 "$FULL_IMAGE_NAME")
    
    # Wait a bit for the container to start
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost:8001/health &> /dev/null; then
        log_success "Image test passed - health endpoint responding"
    else
        log_error "Image test failed - health endpoint not responding"
        docker logs "$CONTAINER_ID"
        docker stop "$CONTAINER_ID"
        exit 1
    fi
    
    # Stop test container
    docker stop "$CONTAINER_ID"
    
    log_success "Image testing completed"
}

push_image() {
    if [ "$PUSH_IMAGE" = "true" ]; then
        log_info "Pushing Docker image..."
        
        FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"
        if [ -n "$REGISTRY" ]; then
            FULL_IMAGE_NAME="$REGISTRY/$FULL_IMAGE_NAME"
        fi
        
        # Check if we're logged into the registry
        if [ -n "$REGISTRY" ]; then
            log_info "Checking registry authentication..."
            if ! docker info | grep -q "Registry:"; then
                log_warning "You may need to login to the registry: docker login $REGISTRY"
            fi
        fi
        
        docker push "$FULL_IMAGE_NAME"
        
        log_success "Image pushed successfully: $FULL_IMAGE_NAME"
    else
        log_info "Skipping image push (PUSH_IMAGE=false)"
    fi
}

show_image_info() {
    log_info "Image information:"
    
    FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="$REGISTRY/$FULL_IMAGE_NAME"
    fi
    
    echo ""
    docker images "$FULL_IMAGE_NAME"
    echo ""
    
    log_info "Image details:"
    docker inspect "$FULL_IMAGE_NAME" --format='{{json .Config.Labels}}' | jq '.' 2>/dev/null || echo "Labels: $(docker inspect "$FULL_IMAGE_NAME" --format='{{.Config.Labels}}')"
    
    echo ""
    log_info "Usage examples:"
    echo "  Run locally: docker run -p 8000:8000 $FULL_IMAGE_NAME"
    echo "  Run with env: docker run -p 8000:8000 -e ENVIRONMENT=development $FULL_IMAGE_NAME"
    echo "  Interactive: docker run -it --entrypoint /bin/bash $FULL_IMAGE_NAME"
    
    if [ "$PUSH_IMAGE" = "true" ]; then
        echo "  Pull image: docker pull $FULL_IMAGE_NAME"
    fi
}

build_multi_arch() {
    log_info "Building multi-architecture image..."
    
    FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="$REGISTRY/$FULL_IMAGE_NAME"
    fi
    
    # Check if buildx is available
    if ! docker buildx version &> /dev/null; then
        log_error "Docker buildx is not available. Please install Docker buildx for multi-arch builds."
        exit 1
    fi
    
    # Create builder if it doesn't exist
    if ! docker buildx inspect multiarch-builder &> /dev/null; then
        log_info "Creating multi-arch builder..."
        docker buildx create --name multiarch-builder --use
    else
        docker buildx use multiarch-builder
    fi
    
    # Build for multiple architectures
    PLATFORMS="linux/amd64,linux/arm64"
    BUILD_ARGS="--platform $PLATFORMS"
    BUILD_ARGS="$BUILD_ARGS --target $BUILD_TARGET"
    BUILD_ARGS="$BUILD_ARGS --label version=$IMAGE_TAG"
    BUILD_ARGS="$BUILD_ARGS --label build-date=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    BUILD_ARGS="$BUILD_ARGS --label git-commit=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    
    if [ "$PUSH_IMAGE" = "true" ]; then
        BUILD_ARGS="$BUILD_ARGS --push"
    else
        BUILD_ARGS="$BUILD_ARGS --load"
    fi
    
    docker buildx build $BUILD_ARGS -t "$FULL_IMAGE_NAME" -f "$DOCKERFILE" .
    
    log_success "Multi-architecture image built successfully"
}

# Main build flow
main() {
    log_info "Starting Docker build process..."
    log_info "Image: $IMAGE_NAME:$IMAGE_TAG"
    log_info "Target: $BUILD_TARGET"
    log_info "Registry: ${REGISTRY:-'local'}"
    
    check_prerequisites
    build_image
    test_image
    push_image
    show_image_info
    
    log_success "Build process completed successfully!"
}

# Handle command line arguments
case "${1:-build}" in
    "build")
        main
        ;;
    "multi-arch")
        check_prerequisites
        build_multi_arch
        show_image_info
        ;;
    "test")
        test_image
        ;;
    "push")
        PUSH_IMAGE="true"
        push_image
        ;;
    "clean")
        log_info "Cleaning up Docker images..."
        docker image prune -f
        log_success "Docker cleanup completed"
        ;;
    *)
        echo "Usage: $0 {build|multi-arch|test|push|clean}"
        echo ""
        echo "Commands:"
        echo "  build:     Build Docker image (default)"
        echo "  multi-arch: Build multi-architecture image"
        echo "  test:      Test the built image"
        echo "  push:      Push image to registry"
        echo "  clean:     Clean up unused Docker images"
        echo ""
        echo "Environment variables:"
        echo "  IMAGE_NAME:    Image name (default: fact-checker)"
        echo "  IMAGE_TAG:     Image tag (default: latest)"
        echo "  REGISTRY:      Docker registry (default: none)"
        echo "  BUILD_TARGET:  Build target (default: production)"
        echo "  PUSH_IMAGE:    Push after build (default: false)"
        echo "  NO_CACHE:      Build without cache (default: false)"
        echo ""
        echo "Examples:"
        echo "  $0 build"
        echo "  IMAGE_TAG=v1.0.0 PUSH_IMAGE=true $0 build"
        echo "  REGISTRY=gcr.io/my-project BUILD_TARGET=development $0 build"
        exit 1
        ;;
esac
