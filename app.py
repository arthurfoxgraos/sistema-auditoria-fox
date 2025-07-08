"""
Sistema de Auditoria FOX - Versão Enxuta
Apenas menus de Cargas e Provisionamento
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

# Configuração da página
st.set_page_config(
    page_title="Sistema FOX - Cargas e Provisionamento",
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

@st.cache_data(ttl=60)  # Cache por apenas 1 minuto para debug
def load_cargas_data():
    """Carrega dados de cargas com cache"""
    try:
        db_config = get_database_connection()
        if not db_config:
            return None, None
        
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)
        
        with st.spinner("Carregando cargas..."):
            tickets = db_service.get_tickets_with_users(limit=1000)
            transactions = db_service.get_ticket_transactions(limit=1000)
        
        db_config.close_connection()
        return tickets, transactions
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar cargas: {e}")
        return None, None

def main():
    """Função principal da aplicação"""
    
    # Header
    st.markdown('<h1 class="main-header">🚛 Sistema FOX - Cargas e Provisionamento</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("📊 Navegação")
    
    # Menu de navegação simplificado
    page = st.sidebar.selectbox(
        "Selecione uma página:",
        [
            "🚚 Cargas",
            "📦 Provisionamento"
        ]
    )
    
    # Roteamento de páginas
    if page == "🚚 Cargas":
        show_cargas_page()
    elif page == "📦 Provisionamento":
        show_provisionamento_page()

def show_cargas_page():
    """Mostra página de cargas"""
    st.header("🚚 Gestão de Cargas")
    
    # Carregar dados
    tickets_data, transactions_data = load_cargas_data()
    
    if tickets_data is None:
        st.error("❌ Não foi possível carregar os dados de cargas.")
        return
    
    # Converter para DataFrame
    df_tickets = pd.DataFrame(tickets_data)
    
    if df_tickets.empty:
        st.warning("Nenhuma carga encontrada.")
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_cargas = len(df_tickets)
        cargas_finalizadas = len(df_tickets[df_tickets.get('status', '') == 'Finalizado'])
        st.metric(
            label="🚚 Total de Cargas",
            value=total_cargas,
            delta=f"{cargas_finalizadas} finalizadas"
        )
    
    with col2:
        total_quantidade = df_tickets['amount'].sum() if 'amount' in df_tickets.columns else 0
        st.metric(
            label="📦 Quantidade Total",
            value=f"{total_quantidade:,.0f} sacas"
        )
    
    with col3:
        total_frete = df_tickets['freightValue'].sum() if 'freightValue' in df_tickets.columns else 0
        st.metric(
            label="💰 Valor Total Frete",
            value=f"R$ {total_frete:,.2f}"
        )
    
    with col4:
        cargas_com_quantidade = len(df_tickets[df_tickets['amount'].notna()]) if 'amount' in df_tickets.columns else 0
        percentual = (cargas_com_quantidade / total_cargas * 100) if total_cargas > 0 else 0
        st.metric(
            label="📊 Cargas c/ Quantidade",
            value=f"{cargas_com_quantidade}",
            delta=f"{percentual:.1f}%"
        )
    
    # Filtros
    st.subheader("🔍 Filtros")
    col1, col2 = st.columns(2)
    
    with col1:
        if 'status' in df_tickets.columns:
            status_options = ['Todos'] + list(df_tickets['status'].dropna().unique())
            status_filter = st.selectbox("Status:", status_options)
        else:
            status_filter = "Todos"
    
    with col2:
        if 'seller_name' in df_tickets.columns or 'buyer_name' in df_tickets.columns:
            user_filter = st.text_input("Filtrar por vendedor/comprador:")
        else:
            user_filter = ""
    
    # Aplicar filtros
    df_filtered = df_tickets.copy()
    
    if status_filter != "Todos" and 'status' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status'] == status_filter]
    
    if user_filter:
        if 'seller_name' in df_filtered.columns:
            mask1 = df_filtered['seller_name'].str.contains(user_filter, case=False, na=False)
        else:
            mask1 = pd.Series([False] * len(df_filtered))
        
        if 'buyer_name' in df_filtered.columns:
            mask2 = df_filtered['buyer_name'].str.contains(user_filter, case=False, na=False)
        else:
            mask2 = pd.Series([False] * len(df_filtered))
        
        df_filtered = df_filtered[mask1 | mask2]
    
    # Mostrar resultados
    st.subheader(f"📊 Resultados: {len(df_filtered)} cargas (apenas 2025+)")
    
    if not df_filtered.empty:
        # Calcular totalizadores
        total_revenue = df_filtered['revenue_value'].sum() if 'revenue_value' in df_filtered.columns else 0
        total_cost = df_filtered['cost_value'].sum() if 'cost_value' in df_filtered.columns else 0
        total_freight = df_filtered['total_freight_value'].sum() if 'total_freight_value' in df_filtered.columns else 0
        total_gross_profit = df_filtered['gross_profit'].sum() if 'gross_profit' in df_filtered.columns else 0
        total_bags = df_filtered['amount'].sum() if 'amount' in df_filtered.columns else 0
        
        # Exibir totalizadores em métricas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="💰 Receita Total",
                value=f"R$ {total_revenue:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )
        
        with col2:
            st.metric(
                label="💸 Custo Total", 
                value=f"R$ {total_cost:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )
        
        with col3:
            st.metric(
                label="🚛 Frete Total",
                value=f"R$ {total_freight:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )
        
        with col4:
            st.metric(
                label="📈 Lucro Bruto Total",
                value=f"R$ {total_gross_profit:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                delta=f"{((total_gross_profit / total_revenue * 100) if total_revenue > 0 else 0):.1f}%" if total_revenue > 0 else None
            )
        
        with col5:
            st.metric(
                label="📦 Total Sacas",
                value=f"{total_bags:,.0f}".replace(',', '.')
            )
        
        st.divider()
        # Selecionar colunas específicas solicitadas
        display_columns = []
        column_mapping = {
            'ticket': 'Nro Ticket',
            'loadingDate': 'Data de Carregamento', 
            'buyer_name': 'Comprador',
            'seller_name': 'Vendedor',
            'driver_name': 'Caminhoneiro',
            'grain_name': 'Grão',
            'contract_type': 'Tipo Contrato',
            'amount': 'Sacas',
            'revenue_value': 'Receita',
            'cost_value': 'Custo',
            'total_freight_value': 'Frete',
            'gross_profit': 'Lucro Bruto'
        }
        
        # Verificar quais colunas existem e adicionar
        for col, display_name in column_mapping.items():
            if col in df_filtered.columns:
                display_columns.append(col)
        
        # Adicionar coluna de conformidade se existir
        if 'compliance_status' in df_filtered.columns:
            display_columns.append('compliance_status')
            column_mapping['compliance_status'] = 'Status'
        
        # Se temos transaction_amount mas não amount, usar transaction_amount como Sacas
        if 'amount' not in df_filtered.columns and 'transaction_amount' in df_filtered.columns:
            df_filtered['amount'] = df_filtered['transaction_amount']
            if 'amount' not in display_columns:
                display_columns.append('amount')
        
        if display_columns:
            # Renomear colunas para exibição
            df_display = df_filtered[display_columns].copy()
            df_display.columns = [column_mapping.get(col, col) for col in display_columns]
            
            # Formatar data se existir
            if 'Data de Carregamento' in df_display.columns:
                # Garantir que é datetime antes de formatar
                df_display['Data de Carregamento'] = pd.to_datetime(
                    df_display['Data de Carregamento'], errors='coerce'
                ).dt.strftime('%d/%m/%Y')
            
            # Formatar valores monetários
            monetary_columns = ['revenue_value', 'cost_value', 'total_freight_value', 'gross_profit']
            
            for col in monetary_columns:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(
                        lambda x: f"R$ {x:.2f}" if pd.notnull(x) and x != 0 else "R$ 0,00"
                    )
            
            # Formatar sacas como número inteiro
            if 'amount' in df_display.columns:
                df_display['amount'] = df_display['amount'].apply(
                    lambda x: f"{int(x)}" if pd.notnull(x) and x != 0 else "0"
                )
            
            st.dataframe(
                df_display,
                use_container_width=True
            )
        else:
            st.warning("Colunas solicitadas não encontradas nos dados.")
            st.dataframe(df_filtered, use_container_width=True)
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            if 'status' in df_filtered.columns:
                st.subheader("📈 Distribuição por Status")
                status_counts = df_filtered['status'].value_counts()
                
                if not status_counts.empty:
                    fig = px.pie(
                        values=status_counts.values,
                        names=status_counts.index,
                        title="Distribuição de Cargas por Status"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'loadingDate' in df_filtered.columns:
                st.subheader("📅 Cargas por Data")
                df_filtered['loadingDate'] = pd.to_datetime(df_filtered['loadingDate'])
                df_filtered['data'] = df_filtered['loadingDate'].dt.date
                
                date_counts = df_filtered['data'].value_counts().sort_index()
                
                if not date_counts.empty:
                    fig = px.line(
                        x=date_counts.index,
                        y=date_counts.values,
                        title="Número de Cargas por Data"
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("Nenhuma carga encontrada com os filtros aplicados.")

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

if __name__ == "__main__":
    main()

