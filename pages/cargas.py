"""
Página de Cargas - Sistema de Auditoria FOX
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from config.database import get_database_connection
from src.database_service import DatabaseService

@st.cache_data(ttl=60)
def load_cargas_data():
    """Carrega dados de cargas do MongoDB"""
    try:
        db_config = get_database_connection()
        if not db_config:
            return None, None
        
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)
        
        # Buscar tickets com lookup de users
        tickets = db_service.get_tickets_with_users(limit=1000)
        
        # Buscar transações
        transactions = db_service.get_ticket_transactions(limit=1000)
        
        db_config.close_connection()
        return tickets, transactions
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar cargas: {e}")
        return None, None

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
    
    # Filtros
    st.subheader("🔍 Filtros")
    
    # Primeira linha de filtros (4 colunas)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'status' in df_tickets.columns:
            status_options = ['Todos'] + list(df_tickets['status'].dropna().unique())
            status_filter = st.selectbox("Status:", status_options)
        else:
            status_filter = "Todos"
    
    with col2:
        # Filtro por conformidade de provisioning
        conformity_options = ["Todos", "✅ Conforme", "❌ Não Conforme"]
        conformity_filter = st.selectbox(
            "Conformidade:",
            options=conformity_options,
            key="conformity_filter"
        )
    
    with col3:
        # Filtro por status de pagamento
        payment_options = ["Todos", "✅ Pago", "⏰ Não Pago"]
        payment_filter = st.selectbox(
            "Status Pagamento:",
            options=payment_options,
            key="payment_filter"
        )
    
    with col4:
        # Filtro por grão
        grain_options = ["Todos"]
        if 'grain_name' in df_tickets.columns:
            unique_grains = df_tickets['grain_name'].dropna().unique()
            grain_options.extend(sorted(unique_grains))
        
        grain_filter = st.selectbox(
            "Grão:",
            options=grain_options,
            key="grain_filter"
        )
    
    # Segunda linha de filtros (3 colunas)
    col5, col6, col7 = st.columns(3)
    
    with col5:
        # Filtro por intervalo de datas
        if 'loadingDate' in df_tickets.columns:
            df_tickets['loadingDate'] = pd.to_datetime(df_tickets['loadingDate'], errors='coerce')
            
            # Definir padrão de 30 dias
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=30)
            
            date_range = st.date_input(
                "Intervalo de datas:",
                value=(start_date, end_date),
                key="date_range_filter"
            )
        else:
            date_range = None
    
    with col6:
        # Filtro por tipo de contrato
        contract_types = ["Todos"]
        if 'contract_type' in df_tickets.columns:
            unique_types = df_tickets['contract_type'].dropna().unique()
            contract_types.extend(unique_types)
        
        contract_filter = st.selectbox(
            "Tipo de Contrato:",
            options=contract_types,
            key="contract_filter"
        )
    
    with col7:
        # Filtro por produtor (seller quando é originação)
        producer_options = ["Todos"]
        if 'seller_name' in df_tickets.columns:
            unique_producers = df_tickets['seller_name'].dropna().unique()
            producer_options.extend(sorted(unique_producers))
        
        producer_filter = st.selectbox(
            "Produtor:",
            options=producer_options,
            key="producer_filter"
        )
    
    # Terceira linha de filtros (1 coluna)
    col8, col9, col10 = st.columns(3)
    
    with col8:
        # Filtro por comprador (movido para terceira linha)
        buyer_options = ["Todos"]
        if 'buyer_name' in df_tickets.columns:
            unique_buyers = df_tickets['buyer_name'].dropna().unique()
            buyer_options.extend(sorted(unique_buyers))
        
        buyer_filter = st.selectbox(
            "Comprador:",
            options=buyer_options,
            key="buyer_filter"
        )
    
    # Aplicar filtros
    df_filtered = df_tickets.copy()
    
    # Filtro por status
    if status_filter != "Todos" and 'status' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status'] == status_filter]
    
    # Filtro por conformidade de provisioning
    if conformity_filter != "Todos" and 'provisioning_status' in df_filtered.columns:
        if conformity_filter == "✅ Conforme":
            df_filtered = df_filtered[df_filtered['provisioning_status'] == "✅ Conforme"]
        elif conformity_filter == "❌ Não Conforme":
            df_filtered = df_filtered[df_filtered['provisioning_status'] == "❌ Não Conforme"]
    
    # Filtro por status de pagamento
    if payment_filter != "Todos" and 'paid_status' in df_filtered.columns:
        if payment_filter == "✅ Pago":
            df_filtered = df_filtered[df_filtered['paid_status'] == "✅"]
        elif payment_filter == "⏰ Não Pago":
            df_filtered = df_filtered[df_filtered['paid_status'] == "⏰"]
    
    # Filtro por grão
    if grain_filter != "Todos" and 'grain_name' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['grain_name'] == grain_filter]
    
    # Filtro por intervalo de datas
    if date_range and len(date_range) == 2 and 'loadingDate' in df_filtered.columns:
        start_date, end_date = date_range
        df_filtered['loadingDate'] = pd.to_datetime(df_filtered['loadingDate'], errors='coerce')
        df_filtered = df_filtered[
            (df_filtered['loadingDate'].dt.date >= start_date) & 
            (df_filtered['loadingDate'].dt.date <= end_date)
        ]
    
    # Filtro por tipo de contrato
    if contract_filter != "Todos" and 'contract_type' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['contract_type'] == contract_filter]
    
    # Filtro por comprador
    if buyer_filter != "Todos" and 'buyer_name' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['buyer_name'] == buyer_filter]
    
    # Filtro por produtor
    if producer_filter != "Todos" and 'seller_name' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['seller_name'] == producer_filter]
    
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
            'provisioning_status': 'Conformidade',
            'paid_status': 'Pago',
            'ticket': 'Nro Ticket',
            'loadingDate': 'Data de Carregamento', 
            'buyer_name': 'Comprador',
            'seller_name': 'Vendedor',
            'driver_name': 'Caminhoneiro',
            'grain_name': 'Grão',
            'contract_type': 'Tipo Contrato',
            'status': 'Status',
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
            
            # Formatar valores monetários no padrão brasileiro
            monetary_columns = ['Receita', 'Custo', 'Frete', 'Lucro Bruto']
            
            for col in monetary_columns:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(
                        lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notnull(x) and x != 0 else "R$ 0,00"
                    )
            
            # Formatar sacas como número inteiro
            if 'Sacas' in df_display.columns:
                df_display['Sacas'] = df_display['Sacas'].apply(
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

if __name__ == "__main__":
    show_cargas_page()

