#!/bin/bash

# Script de Atualização - Sistema de Auditoria FOX
# Versão: 1.0

set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
NAMESPACE="fox-auditoria"
APP_NAME="fox-auditoria"
REGISTRY_USER=${REGISTRY_USER:-"seu-usuario"}
NEW_VERSION=${NEW_VERSION:-$(date +%Y%m%d-%H%M%S)}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Atualizar aplicação
update_app() {
    log_info "Atualizando aplicação para versão ${NEW_VERSION}..."
    
    # Build nova imagem
    docker build -t ${REGISTRY_USER}/${APP_NAME}:${NEW_VERSION} .
    docker push ${REGISTRY_USER}/${APP_NAME}:${NEW_VERSION}
    
    # Atualizar deployment
    kubectl set image deployment/${APP_NAME}-app ${APP_NAME}=${REGISTRY_USER}/${APP_NAME}:${NEW_VERSION} -n ${NAMESPACE}
    
    # Aguardar rollout
    kubectl rollout status deployment/${APP_NAME}-app -n ${NAMESPACE}
    
    log_success "Aplicação atualizada com sucesso!"
}

# Rollback
rollback_app() {
    log_info "Fazendo rollback da aplicação..."
    
    kubectl rollout undo deployment/${APP_NAME}-app -n ${NAMESPACE}
    kubectl rollout status deployment/${APP_NAME}-app -n ${NAMESPACE}
    
    log_success "Rollback realizado com sucesso!"
}

# Função principal
case "$1" in
    "update")
        update_app
        ;;
    "rollback")
        rollback_app
        ;;
    *)
        echo "Uso: $0 {update|rollback}"
        echo ""
        echo "  update    - Atualizar aplicação"
        echo "  rollback  - Fazer rollback da aplicação"
        echo ""
        echo "Variáveis de ambiente:"
        echo "  REGISTRY_USER  - Usuário do registry"
        echo "  NEW_VERSION    - Nova versão (padrão: timestamp)"
        exit 1
        ;;
esac

