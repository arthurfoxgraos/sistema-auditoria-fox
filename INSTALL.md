# 📦 Guia de Instalação - Sistema FOX

## 🔧 Dependências Locais

### 1. Instalar dependências Python:
```bash
pip install -r requirements.txt
```

### 2. Para funcionalidade PostgreSQL:
```bash
pip install psycopg2-binary
```

### 3. Executar localmente:
```bash
streamlit run app.py
```

## 🐘 PostgreSQL

O sistema agora suporta PostgreSQL como fonte de dados para cargas:

- **Host:** 24.199.75.66
- **Porta:** 5432
- **Usuário:** myuser
- **Senha:** mypassword
- **Database:** mydb

## 🔄 Sincronização

1. **MongoDB → PostgreSQL:** Use o botão "Sincronizar Agora" na página de Cargas
2. **Automático:** O sistema detecta quando sincronização é necessária
3. **Status:** Visualize contadores e última sincronização na sidebar

## ☸️ Kubernetes

Para deploy no Kubernetes, todas as dependências estão incluídas no container.

## ⚠️ Troubleshooting

### Erro: "No module named 'psycopg2'"
```bash
pip install psycopg2-binary
```

### Erro de conexão PostgreSQL
- Verificar credenciais
- Verificar conectividade de rede
- Verificar se PostgreSQL está rodando

### MongoDB não conecta
- Verificar variável MONGODB_URI
- Verificar conectividade com DigitalOcean

