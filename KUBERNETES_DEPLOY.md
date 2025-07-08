# 🚀 Guia de Deploy - Sistema de Auditoria FOX no Kubernetes

Este guia fornece instruções passo a passo para fazer deploy do Sistema de Auditoria FOX em um cluster Kubernetes.

## 📋 Pré-requisitos

### 1. Ferramentas Necessárias
- **Docker** (versão 20.10+)
- **kubectl** (versão 1.25+)
- **Acesso a um cluster Kubernetes**
- **Registry Docker** (Docker Hub, AWS ECR, etc.)

### 2. Verificar Cluster Kubernetes
```bash
# Verificar conexão com o cluster
kubectl cluster-info

# Verificar nodes disponíveis
kubectl get nodes
```

### 3. Configurar Registry Docker
```bash
# Login no Docker Hub (ou seu registry)
docker login

# Para AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

## 🔧 Passo 1: Preparar a Imagem Docker

### 1.1 Build da Imagem
```bash
# Navegar para o diretório do projeto
cd /caminho/para/sistema-auditoria-fox

# Build da imagem Docker
docker build -t fox-auditoria:latest .

# Verificar se a imagem foi criada
docker images | grep fox-auditoria
```

### 1.2 Testar Localmente (Opcional)
```bash
# Executar container localmente para teste
docker run -p 8501:8501 \
  -e MONGODB_URI="mongodb+srv://doadmin:5vk9a08N2tX3e64U@foxdigital-e8bf0024.mongo.ondigitalocean.com/admin?authSource=admin&replicaSet=foxdigital" \
  fox-auditoria:latest

# Acessar http://localhost:8501 para verificar
```

### 1.3 Tag e Push para Registry
```bash
# Tag da imagem para o registry
docker tag fox-auditoria:latest seu-usuario/fox-auditoria:v1.0.0
docker tag fox-auditoria:latest seu-usuario/fox-auditoria:latest

# Push para o registry
docker push seu-usuario/fox-auditoria:v1.0.0
docker push seu-usuario/fox-auditoria:latest
```

## 🎯 Passo 2: Configurar Secrets

### 2.1 Atualizar String de Conexão MongoDB
```bash
# Codificar a string de conexão em base64
echo -n "mongodb+srv://doadmin:5vk9a08N2tX3e64U@foxdigital-e8bf0024.mongo.ondigitalocean.com/admin?authSource=admin&replicaSet=foxdigital" | base64

# Copiar o resultado e atualizar k8s/secret.yaml
```

### 2.2 Editar Secret
```bash
# Editar o arquivo de secret
nano k8s/secret.yaml

# Substituir o valor de mongodb-uri pelo resultado do base64
```

## 🚀 Passo 3: Deploy no Kubernetes

### 3.1 Atualizar Imagem no Deployment
```bash
# Editar deployment.yaml
nano k8s/deployment.yaml

# Alterar a linha:
# image: fox-auditoria:latest
# Para:
# image: seu-usuario/fox-auditoria:latest
```

### 3.2 Atualizar Domínio no Ingress
```bash
# Editar ingress.yaml
nano k8s/ingress.yaml

# Substituir "fox-auditoria.seu-dominio.com" pelo seu domínio real
```

### 3.3 Aplicar Manifests
```bash
# Aplicar todos os manifests na ordem correta
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

## 📊 Passo 4: Verificar Deploy

### 4.1 Verificar Pods
```bash
# Verificar status dos pods
kubectl get pods -n fox-auditoria

# Ver logs dos pods
kubectl logs -f deployment/fox-auditoria-app -n fox-auditoria

# Descrever pod para debug
kubectl describe pod <nome-do-pod> -n fox-auditoria
```

### 4.2 Verificar Services
```bash
# Verificar services
kubectl get svc -n fox-auditoria

# Verificar endpoints
kubectl get endpoints -n fox-auditoria
```

### 4.3 Verificar Ingress
```bash
# Verificar ingress
kubectl get ingress -n fox-auditoria

# Descrever ingress
kubectl describe ingress fox-auditoria-ingress -n fox-auditoria
```

### 4.4 Teste de Conectividade
```bash
# Port-forward para teste local
kubectl port-forward svc/fox-auditoria-service 8080:80 -n fox-auditoria

# Acessar http://localhost:8080
```

## 🔄 Passo 5: Atualizações e Manutenção

### 5.1 Atualizar Aplicação
```bash
# Build nova versão
docker build -t seu-usuario/fox-auditoria:v1.0.1 .
docker push seu-usuario/fox-auditoria:v1.0.1

# Atualizar deployment
kubectl set image deployment/fox-auditoria-app fox-auditoria=seu-usuario/fox-auditoria:v1.0.1 -n fox-auditoria

# Verificar rollout
kubectl rollout status deployment/fox-auditoria-app -n fox-auditoria
```

### 5.2 Rollback (se necessário)
```bash
# Ver histórico de rollouts
kubectl rollout history deployment/fox-auditoria-app -n fox-auditoria

# Fazer rollback
kubectl rollout undo deployment/fox-auditoria-app -n fox-auditoria
```

### 5.3 Escalar Aplicação
```bash
# Escalar manualmente
kubectl scale deployment fox-auditoria-app --replicas=5 -n fox-auditoria

# Verificar HPA
kubectl get hpa -n fox-auditoria
```

## 🛠️ Troubleshooting

### Problemas Comuns

#### 1. Pod não inicia
```bash
# Verificar eventos
kubectl get events -n fox-auditoria --sort-by='.lastTimestamp'

# Verificar logs
kubectl logs <nome-do-pod> -n fox-auditoria

# Verificar recursos
kubectl top pods -n fox-auditoria
```

#### 2. Erro de conexão MongoDB
```bash
# Verificar secret
kubectl get secret mongodb-secret -n fox-auditoria -o yaml

# Testar conexão dentro do pod
kubectl exec -it <nome-do-pod> -n fox-auditoria -- /bin/bash
# Dentro do pod: echo $MONGODB_URI
```

#### 3. Ingress não funciona
```bash
# Verificar se nginx-ingress está instalado
kubectl get pods -n ingress-nginx

# Verificar certificado TLS
kubectl get certificate -n fox-auditoria

# Verificar DNS
nslookup fox-auditoria.seu-dominio.com
```

### Comandos Úteis

```bash
# Ver todos os recursos
kubectl get all -n fox-auditoria

# Deletar tudo
kubectl delete namespace fox-auditoria

# Logs em tempo real
kubectl logs -f deployment/fox-auditoria-app -n fox-auditoria

# Entrar no pod
kubectl exec -it <nome-do-pod> -n fox-auditoria -- /bin/bash

# Ver uso de recursos
kubectl top pods -n fox-auditoria
kubectl top nodes
```

## 🔒 Segurança

### Recomendações de Segurança

1. **Secrets**: Nunca commitar secrets no Git
2. **RBAC**: Configurar Role-Based Access Control
3. **Network Policies**: Implementar políticas de rede
4. **Pod Security**: Usar Pod Security Standards
5. **TLS**: Sempre usar HTTPS em produção

### Exemplo de Network Policy
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fox-auditoria-netpol
  namespace: fox-auditoria
spec:
  podSelector:
    matchLabels:
      app: fox-auditoria
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8501
  egress:
  - {} # Permitir todo tráfego de saída
```

## 📈 Monitoramento

### Configurar Monitoramento (Opcional)

1. **Prometheus + Grafana**
2. **Logs centralizados (ELK Stack)**
3. **Alertas (AlertManager)**

### Métricas Importantes
- CPU e Memória dos pods
- Latência das requisições
- Taxa de erro
- Conexões MongoDB
- Uptime da aplicação

## 🎉 Conclusão

Após seguir todos os passos, sua aplicação estará rodando no Kubernetes com:

- ✅ **Alta disponibilidade** (múltiplas réplicas)
- ✅ **Auto-scaling** (HPA configurado)
- ✅ **SSL/TLS** (certificados automáticos)
- ✅ **Monitoramento** (health checks)
- ✅ **Segurança** (usuário não-root, secrets)

Para suporte adicional, consulte a documentação oficial do Kubernetes ou entre em contato com a equipe de DevOps.

---

**Versão:** 1.0  
**Data:** $(date +%Y-%m-%d)  
**Autor:** Sistema de Auditoria FOX

