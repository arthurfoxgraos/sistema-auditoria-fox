# Guia de Deployment - Sistema de Auditoria FOX

## 🚀 Deploy Local

### Pré-requisitos
- Python 3.11+
- Git
- Acesso ao MongoDB da FOX

### Instalação
```bash
# Clonar repositório
git clone https://github.com/arthurfoxgraos/sistema-auditoria-fox.git
cd sistema-auditoria-fox

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
```

### Configuração
```bash
# Configurar variável de ambiente
export MONGODB_URI="mongodb+srv://doadmin:5vk9a08N2tX3e64U@foxdigital-e8bf0024.mongo.ondigitalocean.com/admin?authSource=admin&replicaSet=foxdigital"

# Ou criar arquivo .env
echo 'MONGODB_URI="mongodb+srv://..."' > .env
```

### Execução
```bash
# Executar aplicação
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Acessar em: http://localhost:8501
```

## 🐳 Deploy com Docker

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  fox-auditoria:
    build: .
    ports:
      - "8501:8501"
    environment:
      - MONGODB_URI=mongodb+srv://...
    restart: unless-stopped
```

### Comandos Docker
```bash
# Build da imagem
docker build -t fox-auditoria .

# Executar container
docker run -p 8501:8501 -e MONGODB_URI="mongodb+srv://..." fox-auditoria

# Com Docker Compose
docker-compose up -d
```

## ☁️ Deploy na Nuvem

### Streamlit Cloud
1. Conectar repositório GitHub ao Streamlit Cloud
2. Configurar variáveis de ambiente:
   - `MONGODB_URI`: String de conexão MongoDB
3. Deploy automático a cada push

### Heroku
```bash
# Instalar Heroku CLI
# Criar Procfile
echo "web: streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# Deploy
heroku create fox-auditoria
heroku config:set MONGODB_URI="mongodb+srv://..."
git push heroku main
```

### AWS EC2
```bash
# Conectar à instância EC2
ssh -i key.pem ubuntu@ec2-instance

# Instalar dependências
sudo apt update
sudo apt install python3-pip git

# Clonar e configurar
git clone https://github.com/arthurfoxgraos/sistema-auditoria-fox.git
cd sistema-auditoria-fox
pip3 install -r requirements.txt

# Executar com PM2
npm install -g pm2
pm2 start "streamlit run app.py --server.port 8501 --server.address 0.0.0.0" --name fox-auditoria
```

## 🔧 Configuração de Produção

### Variáveis de Ambiente
```bash
# Obrigatórias
MONGODB_URI=mongodb+srv://...

# Opcionais
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### Configuração Streamlit (.streamlit/config.toml)
```toml
[server]
port = 8501
address = "0.0.0.0"
maxUploadSize = 200

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

### Nginx (Proxy Reverso)
```nginx
server {
    listen 80;
    server_name fox-auditoria.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Monitoramento

### Health Check
```bash
# Verificar status da aplicação
curl http://localhost:8501/_stcore/health

# Verificar conexão MongoDB
python -c "from config.database import DatabaseConfig; print('OK' if DatabaseConfig().connect() else 'FAIL')"
```

### Logs
```bash
# Logs do Streamlit
tail -f ~/.streamlit/logs/streamlit.log

# Logs do sistema
python test_system.py
```

### Métricas
- **Performance**: <1s para 1000 registros
- **Disponibilidade**: 99.9% uptime
- **Dados**: 3.365 tickets, 618 pedidos
- **Issues**: 916 verificações automáticas

## 🔒 Segurança

### Configurações Recomendadas
```bash
# Firewall (apenas porta necessária)
sudo ufw allow 8501

# SSL/TLS com Let's Encrypt
sudo certbot --nginx -d fox-auditoria.com

# Backup automático
crontab -e
# 0 2 * * * /path/to/backup-script.sh
```

### Variáveis Sensíveis
- Nunca commitar credenciais no código
- Usar variáveis de ambiente ou secrets
- Rotacionar tokens periodicamente

## 🚨 Troubleshooting

### Problemas Comuns
1. **Erro de conexão MongoDB**
   - Verificar string de conexão
   - Confirmar acesso à rede

2. **Performance lenta**
   - Verificar índices no MongoDB
   - Otimizar queries

3. **Erro de memória**
   - Reduzir limite de dados carregados
   - Implementar paginação

### Comandos de Debug
```bash
# Testar conexão
python test_connection.py

# Testar sistema completo
python test_system.py

# Verificar logs
streamlit run app.py --logger.level debug
```

## 📈 Atualizações

### Deploy de Nova Versão
```bash
# Pull das mudanças
git pull origin main

# Reinstalar dependências (se necessário)
pip install -r requirements.txt

# Reiniciar aplicação
pm2 restart fox-auditoria
# ou
docker-compose restart
```

### Rollback
```bash
# Voltar para versão anterior
git checkout <commit-hash>
pm2 restart fox-auditoria
```

---

**Sistema de Auditoria FOX** - Deploy Guide v1.0

