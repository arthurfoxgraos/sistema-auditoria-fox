"""
Sistema de Auditoria FOX - Interface Streamlit
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Configurar path
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import get_database_connection
from src.database_service import DatabaseService
from src.audit_engine import AuditEngine
from src.data_models import DataProcessor

# Configuração da página
st.set_page_config(
    page_title="Sistema de Auditoria FOX",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .alert-low {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Carrega dados do banco com cache"""
    try:
        db_config = get_database_connection()
        if not db_config:
            st.error("❌ Erro ao conectar com o banco de dados")
            return None, None, None
        
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)
        
        # Carregar dados
        with st.spinner("Carregando dados..."):
            tickets = db_service.get_tickets(limit=1000)
            orders = db_service.get_orders(limit=1000)
            transactions = db_service.get_ticket_transactions(limit=1000)
        
        return tickets, orders, transactions
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return None, None, None

def main():
    """Função principal da aplicação"""
    
    # Header
    st.markdown('<h1 class="main-header">🚛 Sistema de Auditoria FOX</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("📊 Navegação")
    
    # Menu de navegação
    page = st.sidebar.selectbox(
        "Selecione uma página:",
        [
            "🏠 Dashboard Principal",
            "🎫 Tickets",
            "📋 Pedidos",
            "🔄 Transações",
            "⚙️ Operações",
            "🔍 Auditoria",
            "📈 Relatórios"
        ]
    )
    
    # Carregar dados
    tickets, orders, transactions = load_data()
    
    if tickets is None:
        st.error("❌ Não foi possível carregar os dados. Verifique a conexão com o banco.")
        return
    
    # Roteamento de páginas
    if page == "🏠 Dashboard Principal":
        show_dashboard(tickets, orders, transactions)
    elif page == "🎫 Tickets":
        show_tickets_page(tickets)
    elif page == "📋 Pedidos":
        show_orders_page(orders)
    elif page == "🔄 Transações":
        show_transactions_page(transactions)
    elif page == "⚙️ Operações":
        show_operations_page(tickets, orders)
    elif page == "🔍 Auditoria":
        show_audit_page(tickets, orders, transactions)
    elif page == "📈 Relatórios":
        show_reports_page(tickets, orders, transactions)

def show_dashboard(tickets, orders, transactions):
    """Mostra dashboard principal"""
    st.header("📊 Dashboard Principal")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total de Tickets",
            value=len(tickets),
            delta=f"{len([t for t in tickets if t.status == 'Finalizado'])} finalizados"
        )
    
    with col2:
        st.metric(
            label="📋 Total de Pedidos",
            value=len(orders),
            delta=f"{len([o for o in orders if o.status_flags['isDone']])} concluídos"
        )
    
    with col3:
        st.metric(
            label="🔄 Total de Transações",
            value=len(transactions),
            delta=f"{len([t for t in transactions if t.status == 'Provisionado'])} provisionadas"
        )
    
    with col4:
        total_frete = sum(t.freightValue for t in tickets if t.freightValue)
        st.metric(
            label="💰 Valor Total Frete",
            value=f"R$ {total_frete:,.2f}",
            delta="Últimos dados"
        )
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Status dos Tickets")
        
        # Contar status
        status_counts = {}
        for ticket in tickets:
            status = ticket.status or "Sem status"
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="Distribuição por Status"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Pedidos por Status")
        
        # Contar status dos pedidos
        done_count = len([o for o in orders if o.status_flags['isDone']])
        canceled_count = len([o for o in orders if o.status_flags['isCanceled']])
        in_progress_count = len([o for o in orders if o.status_flags['isInProgress']])
        pending_count = len(orders) - done_count - canceled_count - in_progress_count
        
        fig = go.Figure(data=[
            go.Bar(name='Concluídos', x=['Pedidos'], y=[done_count]),
            go.Bar(name='Cancelados', x=['Pedidos'], y=[canceled_count]),
            go.Bar(name='Em Progresso', x=['Pedidos'], y=[in_progress_count]),
            go.Bar(name='Pendentes', x=['Pedidos'], y=[pending_count])
        ])
        fig.update_layout(barmode='stack', title="Status dos Pedidos")
        st.plotly_chart(fig, use_container_width=True)
    
    # Alertas rápidos
    st.subheader("🚨 Alertas Rápidos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tickets_sem_amount = len([t for t in tickets if t.amount is None])
        if tickets_sem_amount > 0:
            st.markdown(f"""
            <div class="alert-medium">
                <strong>⚠️ Tickets sem quantidade</strong><br>
                {tickets_sem_amount} tickets não possuem quantidade definida
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        tickets_sem_loading_date = len([t for t in tickets if t.loadingDate is None])
        if tickets_sem_loading_date > 0:
            st.markdown(f"""
            <div class="alert-medium">
                <strong>📅 Tickets sem data de carregamento</strong><br>
                {tickets_sem_loading_date} tickets não possuem data de carregamento
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        # Pedidos vencidos
        today = datetime.now()
        orders_vencidos = 0
        for o in orders:
            if (o.deliveryDeadline and 
                not o.status_flags['isDone'] and 
                not o.status_flags['isCanceled']):
                try:
                    if isinstance(o.deliveryDeadline, str):
                        deadline = datetime.fromisoformat(o.deliveryDeadline.replace('Z', '+00:00'))
                    else:
                        deadline = o.deliveryDeadline
                    
                    if deadline < today:
                        orders_vencidos += 1
                except:
                    continue
        
        if orders_vencidos > 0:
            st.markdown(f"""
            <div class="alert-high">
                <strong>🔴 Pedidos vencidos</strong><br>
                {orders_vencidos} pedidos passaram do prazo de entrega
            </div>
            """, unsafe_allow_html=True)

def show_tickets_page(tickets):
    """Mostra página de tickets"""
    st.header("🎫 Gestão de Tickets")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filtrar por Status:",
            ["Todos"] + list(set(t.status for t in tickets if t.status))
        )
    
    with col2:
        # Filtro por data
        date_filter = st.date_input(
            "Data de carregamento (a partir de):",
            value=datetime.now() - timedelta(days=30)
        )
    
    with col3:
        # Busca por número
        search_ticket = st.text_input("Buscar por número do ticket:")
    
    # Aplicar filtros
    filtered_tickets = tickets
    
    if status_filter != "Todos":
        filtered_tickets = [t for t in filtered_tickets if t.status == status_filter]
    
    if search_ticket:
        try:
            ticket_number = int(search_ticket)
            filtered_tickets = [t for t in filtered_tickets if t.ticket == ticket_number]
        except ValueError:
            st.warning("Digite um número válido para o ticket")
    
    if date_filter:
        filtered_tickets = [
            t for t in filtered_tickets 
            if t.loadingDate and t.loadingDate.date() >= date_filter
        ]
    
    # Mostrar resultados
    st.subheader(f"📊 Resultados: {len(filtered_tickets)} tickets")
    
    if filtered_tickets:
        # Converter para DataFrame
        df = DataProcessor.tickets_to_dataframe(filtered_tickets)
        
        # Mostrar tabela
        st.dataframe(
            df[['ticket_number', 'status', 'loadingDate', 'amount', 'freightValue', 'valueGrain']],
            use_container_width=True
        )
        
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_frete = sum(t.freightValue for t in filtered_tickets if t.freightValue)
            st.metric("💰 Valor Total Frete", f"R$ {total_frete:,.2f}")
        
        with col2:
            total_grao = sum(t.valueGrain for t in filtered_tickets if t.valueGrain)
            st.metric("🌾 Valor Total Grão", f"R$ {total_grao:,.2f}")
        
        with col3:
            total_amount = sum(t.amount for t in filtered_tickets if t.amount)
            st.metric("📦 Total Sacas", f"{total_amount:,.0f}")
    
    else:
        st.info("Nenhum ticket encontrado com os filtros aplicados.")

def show_orders_page(orders):
    """Mostra página de pedidos"""
    st.header("📋 Gestão de Pedidos")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Filtrar por Status:",
            ["Todos", "Concluídos", "Cancelados", "Em Progresso", "Pendentes"]
        )
    
    with col2:
        date_filter = st.date_input(
            "Data de criação (a partir de):",
            value=datetime.now() - timedelta(days=30)
        )
    
    # Aplicar filtros
    filtered_orders = orders
    
    if status_filter == "Concluídos":
        filtered_orders = [o for o in filtered_orders if o.status_flags['isDone']]
    elif status_filter == "Cancelados":
        filtered_orders = [o for o in filtered_orders if o.status_flags['isCanceled']]
    elif status_filter == "Em Progresso":
        filtered_orders = [o for o in filtered_orders if o.status_flags['isInProgress']]
    elif status_filter == "Pendentes":
        filtered_orders = [
            o for o in filtered_orders 
            if not o.status_flags['isDone'] and not o.status_flags['isCanceled'] and not o.status_flags['isInProgress']
        ]
    
    if date_filter:
        filtered_orders = [
            o for o in filtered_orders 
            if o.createdAt and o.createdAt.date() >= date_filter
        ]
    
    # Mostrar resultados
    st.subheader(f"📊 Resultados: {len(filtered_orders)} pedidos")
    
    if filtered_orders:
        # Converter para DataFrame
        df = DataProcessor.orders_to_dataframe(filtered_orders)
        
        # Mostrar tabela
        st.dataframe(
            df[['buyer_name', 'seller_name', 'amount', 'bagPrice', 'deliveryDeadline', 'isDone', 'isCanceled']],
            use_container_width=True
        )
        
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_amount = sum(o.amount for o in filtered_orders if o.amount)
            st.metric("📦 Total Quantidade", f"{total_amount:,.0f}")
        
        with col2:
            avg_price = sum(o.bagPrice for o in filtered_orders if o.bagPrice) / len([o for o in filtered_orders if o.bagPrice])
            st.metric("💰 Preço Médio/Saca", f"R$ {avg_price:.2f}" if avg_price else "N/A")
        
        with col3:
            done_count = len([o for o in filtered_orders if o.status_flags['isDone']])
            completion_rate = done_count / len(filtered_orders) * 100 if filtered_orders else 0
            st.metric("✅ Taxa Conclusão", f"{completion_rate:.1f}%")

def show_transactions_page(transactions):
    """Mostra página de transações"""
    st.header("🔄 Gestão de Transações")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Filtrar por Status:",
            ["Todos"] + list(set(t.status for t in transactions if t.status))
        )
    
    with col2:
        min_amount = st.number_input("Quantidade mínima de sacas:", min_value=0, value=0)
    
    # Aplicar filtros
    filtered_transactions = transactions
    
    if status_filter != "Todos":
        filtered_transactions = [t for t in filtered_transactions if t.status == status_filter]
    
    if min_amount > 0:
        filtered_transactions = [t for t in filtered_transactions if t.amount and t.amount >= min_amount]
    
    # Mostrar resultados
    st.subheader(f"📊 Resultados: {len(filtered_transactions)} transações")
    
    if filtered_transactions:
        # Converter para DataFrame
        df = DataProcessor.ticket_transactions_to_dataframe(filtered_transactions)
        
        # Mostrar tabela
        st.dataframe(df, use_container_width=True)
        
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_amount = sum(t.amount for t in filtered_transactions if t.amount)
            st.metric("📦 Total Sacas", f"{total_amount:,.0f}")
        
        with col2:
            avg_distance = sum(t.distanceInKm for t in filtered_transactions if t.distanceInKm) / len([t for t in filtered_transactions if t.distanceInKm])
            st.metric("🛣️ Distância Média", f"{avg_distance:.1f} km" if avg_distance else "N/A")
        
        with col3:
            total_value = sum(t.value for t in filtered_transactions if t.value)
            st.metric("💰 Valor Total", f"R$ {total_value:,.2f}")

def show_operations_page(tickets, orders):
    """Mostra página de operações"""
    st.header("⚙️ Gestão de Operações")
    
    # Criar motor de auditoria para gerar operações
    audit_engine = AuditEngine()
    operations = audit_engine.create_operations_from_tickets(tickets, orders)
    
    st.subheader(f"📊 Total de Operações: {len(operations)}")
    
    if operations:
        # Mostrar operações em cards
        for i, op in enumerate(operations[:10]):  # Mostrar apenas as primeiras 10
            with st.expander(f"Operação {op._id}"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🎫 Tickets", op.num_tickets)
                
                with col2:
                    st.metric("📦 Sacas", f"{op.quantidade_total_sacas:,.0f}")
                
                with col3:
                    st.metric("💰 Frete", f"R$ {op.valor_total_frete:,.2f}")
                
                with col4:
                    st.metric("🌾 Grão", f"R$ {op.valor_total_grao:,.2f}")
                
                # Detalhes
                st.write(f"**Status:** {op.status}")
                st.write(f"**Data Início:** {op.data_inicio}")
                st.write(f"**Data Fim:** {op.data_fim}")
                st.write(f"**Tickets:** {', '.join(op.tickets[:5])}{'...' if len(op.tickets) > 5 else ''}")
    
    else:
        st.info("Nenhuma operação encontrada.")

def show_audit_page(tickets, orders, transactions):
    """Mostra página de auditoria"""
    st.header("🔍 Auditoria do Sistema")
    
    # Executar auditoria
    with st.spinner("Executando auditoria completa..."):
        audit_engine = AuditEngine()
        audit_result = audit_engine.run_full_audit(tickets, orders, transactions)
    
    # Resumo da auditoria
    summary = audit_result["summary"]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔍 Total Issues", summary["total_issues"])
    
    with col2:
        high_priority = len(audit_engine.get_high_priority_issues())
        st.metric("🔴 Alta Prioridade", high_priority)
    
    with col3:
        critical = len(audit_engine.get_critical_issues())
        st.metric("⚠️ Críticos", critical)
    
    with col4:
        st.metric("⚙️ Operações", summary["total_operations"])
    
    # Breakdown por severidade
    st.subheader("📊 Issues por Severidade")
    
    severity_data = summary["severity_breakdown"]
    if severity_data:
        fig = px.bar(
            x=list(severity_data.keys()),
            y=list(severity_data.values()),
            title="Distribuição por Severidade",
            color=list(severity_data.keys()),
            color_discrete_map={
                'critical': '#d32f2f',
                'high': '#f57c00',
                'medium': '#fbc02d',
                'low': '#388e3c'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Lista de issues
    st.subheader("📋 Lista de Issues")
    
    # Filtro por severidade
    severity_filter = st.selectbox(
        "Filtrar por severidade:",
        ["Todos", "critical", "high", "medium", "low"]
    )
    
    # Filtrar issues
    issues = audit_result["audit_results"]
    if severity_filter != "Todos":
        issues = [i for i in issues if i.severity == severity_filter]
    
    # Mostrar issues
    for i, issue in enumerate(issues[:20]):  # Mostrar apenas os primeiros 20
        severity_class = f"alert-{issue.severity}" if issue.severity != "critical" else "alert-high"
        
        st.markdown(f"""
        <div class="{severity_class}">
            <strong>{issue.severity.upper()}: {issue.message}</strong><br>
            <small>Tipo: {issue.type} | Itens afetados: {len(issue.affected_items)}</small>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Espaçamento

def show_reports_page(tickets, orders, transactions):
    """Mostra página de relatórios"""
    st.header("📈 Relatórios e Analytics")
    
    # Métricas gerais
    metricas = DataProcessor.calcular_metricas_gerais(tickets, orders)
    
    st.subheader("📊 Métricas Gerais")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Taxa Finalização Tickets", f"{metricas['taxa_finalizacao']:.1%}")
        st.metric("Taxa Amount Preenchido", f"{metricas['taxa_amount_preenchido']:.1%}")
    
    with col2:
        st.metric("Valor Médio Frete", f"R$ {metricas['valor_medio_frete']:.2f}")
        st.metric("Sacas Média/Ticket", f"{metricas['sacas_media_ticket']:.1f}")
    
    with col3:
        st.metric("Taxa Orders Concluídos", f"{metricas['taxa_orders_done']:.1%}")
        st.metric("Total Sacas", f"{metricas['total_sacas']:,.0f}")
    
    # Gráfico temporal
    st.subheader("📈 Evolução Temporal")
    
    # Agrupar tickets por data
    tickets_por_data = {}
    for ticket in tickets:
        if ticket.loadingDate:
            data = ticket.loadingDate.date()
            if data not in tickets_por_data:
                tickets_por_data[data] = 0
            tickets_por_data[data] += 1
    
    if tickets_por_data:
        df_temporal = pd.DataFrame([
            {"data": data, "tickets": count}
            for data, count in sorted(tickets_por_data.items())
        ])
        
        fig = px.line(
            df_temporal,
            x="data",
            y="tickets",
            title="Tickets por Data de Carregamento"
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()

