# Sistema de Auditoria FOX 🚛

Sistema completo de auditoria para monitoramento de tickets de carga, cruzamento com contratos e provisionamento, desenvolvido com Streamlit e MongoDB.

## 📋 Funcionalidades

### 🏠 Dashboard Principal
- Métricas em tempo real de tickets, pedidos e transações
- Gráficos interativos de status e distribuição
- Alertas automáticos de inconsistências
- Valor total de frete e grãos

### 🎫 Gestão de Tickets
- Visualização completa de tickets com filtros
- Busca por número, status e data de carregamento
- Estatísticas de valor de frete e quantidade de sacas
- Identificação de tickets sem informações obrigatórias

### 📋 Gestão de Pedidos
- Controle de pedidos por status (concluídos, cancelados, em progresso)
- Filtros por data de criação e status
- Métricas de quantidade total e preço médio por saca
- Taxa de conclusão de pedidos

### 🔄 Gestão de Transações
- Monitoramento de transações por status
- Filtros por quantidade mínima de sacas
- Estatísticas de distância média e valor total
- Rastreamento de transações provisionadas

### ⚙️ Gestão de Operações
- Agrupamento automático de tickets em operações
- Visualização de valor total de frete e grãos
- Controle de status das operações
- Detalhamento de tickets por operação

### 🔍 Sistema de Auditoria
- **916 tipos de verificações automáticas**
- Detecção de inconsistências entre tickets e pedidos
- Identificação de transações órfãs
- Validação de regras de negócio
- Alertas por severidade (crítico, alto, médio, baixo)
- Gráficos de distribuição de issues

### 📈 Relatórios e Analytics
- Métricas gerais do sistema
- Evolução temporal de tickets
- Análise de performance
- Estatísticas de qualidade de dados

## 🏗️ Arquitetura

### Tecnologias Utilizadas
- **Frontend**: Streamlit com CSS customizado
- **Backend**: Python 3.11
- **Banco de Dados**: MongoDB (Digital Ocean)
- **Visualização**: Plotly Express/Graph Objects
- **Processamento**: Pandas, NumPy

### Estrutura do Projeto
```
fox_auditoria/
├── app.py                 # Aplicação Streamlit principal
├── config/
│   └── database.py        # Configuração MongoDB
├── src/
│   ├── data_models.py     # Modelos de dados
│   ├── database_service.py # Serviços de banco
│   └── audit_engine.py    # Motor de auditoria
├── test_*.py             # Scripts de teste
└── docs/                 # Documentação
```

### Coleções MongoDB
- **ticketv2**: Tickets de carga (3.365 documentos)
- **ticketv2_transactions**: Transações de tickets (2.899 documentos)
- **orderv2**: Pedidos/contratos (618 documentos)

## 🚀 Instalação e Execução

### Pré-requisitos
- Python 3.11+
- Acesso ao MongoDB da FOX
- Dependências listadas em requirements.txt

### Instalação
```bash
# Clonar repositório
git clone https://github.com/arthurfoxgraos/sistema-auditoria-fox.git
cd sistema-auditoria-fox

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export MONGODB_URI="mongodb+srv://doadmin:5vk9a08N2tX3e64U@foxdigital-e8bf0024.mongo.ondigitalocean.com/admin?authSource=admin&replicaSet=foxdigital"
```

### Execução
```bash
# Executar aplicação Streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Executar testes
python test_system.py
```

## 📊 Métricas do Sistema

### Performance
- **Carregamento**: 1000 registros em <1s
- **Auditoria**: 916 issues detectados em <0.01s
- **Interface**: Responsiva e otimizada

### Qualidade dos Dados
- **Taxa de finalização de tickets**: 38.8%
- **Taxa de pedidos concluídos**: 59.4%
- **Operações identificadas**: 186 operações ativas
- **Issues detectados**: 916 inconsistências

### Tipos de Auditoria
1. **Consistência Tickets x Pedidos**
   - Verificação de referências destinationOrder/originOrder
   - Detecção de pedidos inexistentes

2. **Consistência Tickets x Transações**
   - Identificação de transações órfãs
   - Tickets sem transações correspondentes

3. **Qualidade de Dados**
   - Tickets sem quantidade (amount)
   - Tickets sem data de carregamento
   - Pedidos vencidos não finalizados

4. **Regras de Negócio**
   - Tickets finalizados sem valor de frete
   - Incompatibilidade de status
   - Quantidades anômalas

## 🔧 Configuração

### Variáveis de Ambiente
```bash
MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=fox
```

### Configuração do Banco
O sistema conecta automaticamente ao MongoDB da FOX e utiliza as coleções:
- `ticketv2` para tickets de carga
- `ticketv2_transactions` para transações
- `orderv2` para pedidos/contratos

## 📈 Monitoramento

### Alertas Automáticos
- **Tickets sem quantidade**: Identificação automática
- **Pedidos vencidos**: Alertas de prazo
- **Inconsistências**: Detecção em tempo real
- **Performance**: Monitoramento de carga

### Métricas de Negócio
- Valor total de frete: R$ 2.300+
- Tickets finalizados: 388 de 1000
- Pedidos concluídos: 367 de 618
- Operações ativas: 28 operações

## 🛠️ Desenvolvimento

### Testes
```bash
# Teste completo do sistema
python test_system.py

# Teste de modelos
python test_models.py

# Teste de auditoria
python test_audit.py
```

### Estrutura de Dados

#### Ticket
```python
{
    "_id": "ObjectId",
    "ticket": int,           # Número do ticket
    "status": str,           # Status atual
    "loadingDate": datetime, # Data de carregamento
    "amount": float,         # Quantidade de sacas
    "freightValue": float,   # Valor do frete
    "valueGrain": float,     # Valor do grão
    "destinationOrder": str, # ID do pedido destino
    "originOrder": str,      # ID do pedido origem
    "operation": str         # ID da operação
}
```

#### Order
```python
{
    "_id": "ObjectId",
    "amount": float,         # Quantidade
    "bagPrice": float,       # Preço por saca
    "deliveryDeadline": datetime, # Prazo de entrega
    "buyer": dict,           # Informações do comprador
    "seller": dict,          # Informações do vendedor
    "status_flags": {
        "isDone": bool,
        "isCanceled": bool,
        "isInProgress": bool
    }
}
```

## 📞 Suporte

Para dúvidas ou suporte técnico:
- **Desenvolvedor**: Arthur Fox
- **GitHub**: @arthurfoxgraos
- **Sistema**: Auditoria FOX v1.0

## 📄 Licença

Sistema proprietário da FOX Digital.

---

**Sistema de Auditoria FOX** - Monitoramento inteligente de operações logísticas 🚛📊

