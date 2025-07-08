#!/bin/bash

# Script de Deploy Automatizado - Sistema de Auditoria FOX
# Versão: 1.0
# Autor: Sistema de Auditoria FOX

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
NAMESPACE="fox-auditoria"
APP_NAME="fox-auditoria"
IMAGE_NAME="fox-auditoria"
REGISTRY_USER=${REGISTRY_USER:-"seu-usuario"}
VERSION=${VERSION:-"latest"}

# Funções auxiliares
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

# Verificar pré-requisitos
check_prerequisites() {
    log_info "Verificando pré-requisitos..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker não encontrado. Instale o Docker primeiro."
        exit 1
    fi
    
    # Verificar kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl não encontrado. Instale o kubectl primeiro."
        exit 1
    fi
    
    # Verificar conexão com cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Não foi possível conectar ao cluster Kubernetes."
        exit 1
    fi
    
    log_success "Pré-requisitos verificados com sucesso!"
}

# Build da imagem Docker
build_image() {
    log_info "Fazendo build da imagem Docker..."
    
    # Build da imagem
    docker build -t ${IMAGE_NAME}:${VERSION} .
    
    # Tag para registry
    docker tag ${IMAGE_NAME}:${VERSION} ${REGISTRY_USER}/${IMAGE_NAME}:${VERSION}
    docker tag ${IMAGE_NAME}:${VERSION} ${REGISTRY_USER}/${IMAGE_NAME}:latest
    
    log_success "Imagem Docker criada com sucesso!"
}

# Push da imagem para registry
push_image() {
    log_info "Fazendo push da imagem para registry..."
    
    # Push das imagens
    docker push ${REGISTRY_USER}/${IMAGE_NAME}:${VERSION}
    docker push ${REGISTRY_USER}/${IMAGE_NAME}:latest
    
    log_success "Imagem enviada para registry com sucesso!"
}

# Atualizar manifests com configurações
update_manifests() {
    log_info "Atualizando manifests Kubernetes..."
    
    # Criar diretório temporário para manifests
    mkdir -p temp_k8s
    cp -r k8s/* temp_k8s/
    
    # Atualizar imagem no deployment
    sed -i "s|image: fox-auditoria:latest|image: ${REGISTRY_USER}/${IMAGE_NAME}:${VERSION}|g" temp_k8s/deployment.yaml
    
    log_success "Manifests atualizados!"
}

# Deploy no Kubernetes
deploy_kubernetes() {
    log_info "Fazendo deploy no Kubernetes..."
    
    # Aplicar manifests na ordem correta
    kubectl apply -f temp_k8s/namespace.yaml
    kubectl apply -f temp_k8s/secret.yaml
    kubectl apply -f temp_k8s/configmap.yaml
    kubectl apply -f temp_k8s/deployment.yaml
    kubectl apply -f temp_k8s/service.yaml
    kubectl apply -f temp_k8s/ingress.yaml
    kubectl apply -f temp_k8s/hpa.yaml
    
    log_success "Deploy realizado com sucesso!"
}

# Verificar status do deploy
check_deployment() {
    log_info "Verificando status do deployment..."
    
    # Aguardar rollout
    kubectl rollout status deployment/${APP_NAME}-app -n ${NAMESPACE} --timeout=300s
    
    # Verificar pods
    kubectl get pods -n ${NAMESPACE}
    
    # Verificar services
    kubectl get svc -n ${NAMESPACE}
    
    # Verificar ingress
    kubectl get ingress -n ${NAMESPACE}
    
    log_success "Deployment verificado com sucesso!"
}

# Limpeza
cleanup() {
    log_info "Limpando arquivos temporários..."
    rm -rf temp_k8s
    log_success "Limpeza concluída!"
}

# Função principal
main() {
    log_info "Iniciando deploy do Sistema de Auditoria FOX..."
    
    # Verificar argumentos
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        echo "Uso: $0 [opções]"
        echo ""
        echo "Opções:"
        echo "  --skip-build    Pular build da imagem Docker"
        echo "  --skip-push     Pular push para registry"
        echo "  --only-k8s      Apenas aplicar manifests Kubernetes"
        echo "  --help, -h      Mostrar esta ajuda"
        echo ""
        echo "Variáveis de ambiente:"
        echo "  REGISTRY_USER   Usuário do registry Docker (padrão: seu-usuario)"
        echo "  VERSION         Versão da imagem (padrão: latest)"
        echo ""
        echo "Exemplo:"
        echo "  REGISTRY_USER=meuusuario VERSION=v1.0.0 $0"
        exit 0
    fi
    
    # Executar etapas baseadas nos argumentos
    if [ "$1" != "--only-k8s" ]; then
        check_prerequisites
        
        if [ "$1" != "--skip-build" ]; then
            build_image
        fi
        
        if [ "$1" != "--skip-push" ] && [ "$1" != "--skip-build" ]; then
            push_image
        fi
    fi
    
    update_manifests
    deploy_kubernetes
    check_deployment
    cleanup
    
    log_success "Deploy do Sistema de Auditoria FOX concluído com sucesso!"
    log_info "Acesse a aplicação através do Ingress configurado."
}

# Executar função principal
main "$@"

