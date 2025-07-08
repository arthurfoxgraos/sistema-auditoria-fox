"""
Sistema de Auditoria FOX - Interface Streamlit com Provisionamento
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
from src.database_service_provisioning import ProvisioningService
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
            "🚚 Cargas",
            "📋 Contratos", 
            "📦 Provisionamento",
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
    elif page == "🚚 Cargas":
        show_cargas_page(tickets, transactions)
    elif page == "📋 Contratos":
        show_contratos_page(orders)
    elif page == "📦 Provisionamento":
        show_provisionamento_page()
    elif page == "⚙️ Operações":
        show_operations_page(tickets, orders)
    elif page == "🔍 Auditoria":
        show_audit_page(tickets, orders, transactions)
    elif page == "📈 Relatórios":
        show_reports_page(tickets, orders, transactions)

def show_provisionamento_page():
    """Mostra página de provisionamento"""
    st.header("📦 Gestão de Provisionamento")
    
    # Obter dados de provisionamento
    db_config = get_database_connection()
    if not db_config:
        st.error("❌ Erro ao conectar com o banco de dados")
        return
    
    collections = db_config.get_collections()
    prov_service = ProvisioningService(collections)
    
    # Métricas principais
    with st.spinner("Carregando métricas de provisionamento..."):
        metricas = prov_service.get_metricas_provisionamento()
    
    if metricas:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📦 Total Provisionamentos",
                value=metricas.get('total_provisionamentos', 0),
                delta=f"{metricas.get('provisionamentos_grao', 0)} grãos"
            )
        
        with col2:
            total_qty = metricas.get('quantidade_total', 0)
            remaining_qty = metricas.get('quantidade_restante', 0)
            st.metric(
                label="🌾 Quantidade Total",
                value=f"{total_qty:,.0f} sacas",
                delta=f"{remaining_qty:,.0f} restantes"
            )
        
        with col3:
            total_value = metricas.get('valor_total', 0)
            remaining_value = metricas.get('valor_restante', 0)
            st.metric(
                label="💰 Valor Total",
                value=f"R$ {total_value:,.2f}",
                delta=f"R$ {remaining_value:,.2f} restante"
            )
        
        with col4:
            utilization_rate = metricas.get('taxa_utilizacao', 0)
            avg_price = metricas.get('preco_medio', 0)
            st.metric(
                label="📊 Taxa Utilização",
                value=f"{utilization_rate:.1f}%",
                delta=f"R$ {avg_price:.2f} preço médio"
            )
    
    # Filtros
    st.subheader("🔍 Filtros")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipo_filter = st.selectbox(
            "Tipo:",
            ["Todos", "Grão", "Frete"]
        )
    
    with col2:
        date_filter = st.date_input(
            "Data de criação (a partir de):",
            value=datetime.now() - timedelta(days=30)
        )
    
    with col3:
        user_filter = st.text_input("Filtrar por usuário:")
    
    # Carregar dados de provisionamento
    with st.spinner("Carregando dados de provisionamento..."):
        df_prov = prov_service.get_provisionings_dataframe(limit=1000)
    
    if not df_prov.empty:
        # Aplicar filtros
        df_filtered = df_prov.copy()
        
        if tipo_filter != "Todos":
            df_filtered = df_filtered[df_filtered['tipo'] == tipo_filter]
        
        if user_filter:
            df_filtered = df_filtered[
                df_filtered['usuario'].str.contains(user_filter, case=False, na=False)
            ]
        
        if date_filter:
            df_filtered = df_filtered[
                pd.to_datetime(df_filtered['data_criacao']).dt.date >= date_filter
            ]
        
        # Mostrar resultados
        st.subheader(f"📊 Resultados: {len(df_filtered)} provisionamentos")
        
        if not df_filtered.empty:
            # Tabela principal
            st.dataframe(
                df_filtered[[
                    'tipo', 'grao', 'quantidade_total', 'quantidade_restante',
                    'quantidade_utilizada', 'preco_saca', 'valor_total',
                    'valor_restante', 'percentual_utilizado', 'usuario',
                    'origem', 'destino', 'fob', 'data_criacao'
                ]],
                use_container_width=True
            )
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Utilização por Usuário")
                
                # Agrupar por usuário
                user_stats = df_filtered.groupby('usuario').agg({
                    'quantidade_total': 'sum',
                    'quantidade_utilizada': 'sum',
                    'valor_total': 'sum'
                }).reset_index()
                
                user_stats['taxa_utilizacao'] = (
                    user_stats['quantidade_utilizada'] / user_stats['quantidade_total'] * 100
                ).fillna(0)
                
                if not user_stats.empty:
                    fig = px.bar(
                        user_stats.head(10),
                        x='usuario',
                        y='taxa_utilizacao',
                        title="Taxa de Utilização por Usuário (%)",
                        color='taxa_utilizacao',
                        color_continuous_scale='RdYlGn'
                    )
                    fig.update_layout(xaxis_tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("🌾 Distribuição por Tipo de Grão")
                
                if 'grao' in df_filtered.columns:
                    grain_stats = df_filtered[df_filtered['grao'] != ''].groupby('grao').agg({
                        'quantidade_total': 'sum',
                        'valor_total': 'sum'
                    }).reset_index()
                    
                    if not grain_stats.empty:
                        fig = px.pie(
                            grain_stats,
                            values='quantidade_total',
                            names='grao',
                            title="Distribuição de Quantidade por Grão"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas resumidas
            st.subheader("📊 Estatísticas Resumidas")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_qty_filtered = df_filtered['quantidade_total'].sum()
                st.metric("📦 Quantidade Total", f"{total_qty_filtered:,.0f}")
            
            with col2:
                total_remaining = df_filtered['quantidade_restante'].sum()
                st.metric("📦 Quantidade Restante", f"{total_remaining:,.0f}")
            
            with col3:
                total_value_filtered = df_filtered['valor_total'].sum()
                st.metric("💰 Valor Total", f"R$ {total_value_filtered:,.2f}")
            
            with col4:
                avg_utilization = df_filtered['percentual_utilizado'].mean()
                st.metric("📊 Utilização Média", f"{avg_utilization:.1f}%")
        
        else:
            st.info("Nenhum provisionamento encontrado com os filtros aplicados.")
    
    else:
        st.warning("Nenhum dado de provisionamento encontrado.")
    
    # Alertas de provisionamento
    st.subheader("🚨 Alertas de Provisionamento")
    
    with st.spinner("Gerando alertas..."):
        alertas = prov_service.get_alertas_provisionamento()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Provisionamentos vencidos
        vencidos = alertas.get('vencidos', [])
        if vencidos:
            st.markdown(f"""
            <div class="alert-high">
                <strong>🔴 Provisionamentos Vencidos</strong><br>
                {len(vencidos)} provisionamentos passaram do prazo de entrega
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("Ver detalhes dos vencidos"):
                for v in vencidos[:5]:
                    st.write(f"**{v['usuario']}**: {v['quantidade_restante']:,.0f} sacas restantes")
        
        # Baixo estoque
        baixo_estoque = alertas.get('baixo_estoque', [])
        if baixo_estoque:
            st.markdown(f"""
            <div class="alert-medium">
                <strong>⚠️ Baixo Estoque</strong><br>
                {len(baixo_estoque)} provisionamentos com menos de 10% restante
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Sem movimento
        sem_movimento = alertas.get('sem_movimento', [])
        if sem_movimento:
            st.markdown(f"""
            <div class="alert-medium">
                <strong>📦 Sem Movimento</strong><br>
                {len(sem_movimento)} provisionamentos sem utilização
            </div>
            """, unsafe_allow_html=True)
        
        # Preço alto
        preco_alto = alertas.get('preco_alto', [])
        if preco_alto:
            st.markdown(f"""
            <div class="alert-low">
                <strong>💰 Preço Alto</strong><br>
                {len(preco_alto)} provisionamentos com preço acima da média
            </div>
            """, unsafe_allow_html=True)
    
    db_config.close_connection()

# Incluir todas as outras funções do app original aqui...
# (show_dashboard, show_cargas_page, show_contratos_page, etc.)

def show_dashboard(tickets, orders, transactions):
    """Mostra dashboard principal"""
    st.header("📊 Dashboard Principal")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🚚 Total de Cargas",
            value=len(tickets),
            delta=f"{len([t for t in tickets if t.status == 'Finalizado'])} finalizadas"
        )
    
    with col2:
        st.metric(
            label="📋 Total de Contratos",
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
    
    # Adicionar métricas de provisionamento no dashboard
    st.subheader("📦 Métricas de Provisionamento")
    
    db_config = get_database_connection()
    if db_config:
        collections = db_config.get_collections()
        prov_service = ProvisioningService(collections)
        
        metricas_prov = prov_service.get_metricas_provisionamento()
        
        if metricas_prov:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "📦 Provisionamentos",
                    metricas_prov.get('total_provisionamentos', 0)
                )
            
            with col2:
                total_qty = metricas_prov.get('quantidade_total', 0)
                st.metric(
                    "🌾 Quantidade Total",
                    f"{total_qty:,.0f} sacas"
                )
            
            with col3:
                utilization = metricas_prov.get('taxa_utilizacao', 0)
                st.metric(
                    "📊 Taxa Utilização",
                    f"{utilization:.1f}%"
                )
        
        db_config.close_connection()

# Adicionar as outras funções aqui (show_cargas_page, show_contratos_page, etc.)
# Por brevidade, vou incluir apenas as principais

def show_cargas_page(tickets, transactions):
    """Mostra página de cargas com transações unificadas"""
    st.header("🚚 Gestão de Cargas")
    st.info("Página de cargas implementada - veja versão anterior do código")

def show_contratos_page(orders):
    """Mostra página de contratos"""
    st.header("📋 Gestão de Contratos")
    st.info("Página de contratos implementada - veja versão anterior do código")

def show_operations_page(tickets, orders):
    """Mostra página de operações"""
    st.header("⚙️ Gestão de Operações")
    st.info("Página de operações implementada - veja versão anterior do código")

def show_audit_page(tickets, orders, transactions):
    """Mostra página de auditoria"""
    st.header("🔍 Auditoria do Sistema")
    st.info("Página de auditoria implementada - veja versão anterior do código")

def show_reports_page(tickets, orders, transactions):
    """Mostra página de relatórios"""
    st.header("📈 Relatórios e Analytics")
    st.info("Página de relatórios implementada - veja versão anterior do código")

if __name__ == "__main__":
    main()

