"""
Página de Cargas - Sistema de Auditoria FOX
Agora usando PostgreSQL como fonte principal
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from src.postgres_service import PostgreSQLService
from src.sync_service import SyncService

@st.cache_data(ttl=60)
def load_cargas_data():
    """Carrega dados de cargas do PostgreSQL"""
    try:
        postgres_service = PostgreSQLService()
        df = postgres_service.get_cargas_data()
        postgres_service.close()
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar cargas: {e}")
        return pd.DataFrame()

def show_sync_panel():
    """Mostra painel de sincronização"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 Sincronização")
    
    # Inicializar serviço de sync
    sync_service = SyncService()
    
    # Status da sincronização
    status = sync_service.get_sync_status()
    
    st.sidebar.metric("📊 MongoDB", f"{status['mongodb_count']:,} cargas")
    st.sidebar.metric("🐘 PostgreSQL", f"{status['postgres_count']:,} cargas")
    
    if status['last_sync']:
        last_sync_str = status['last_sync'].strftime('%d/%m/%Y %H:%M')
        st.sidebar.info(f"🕒 Última sync: {last_sync_str}")
    else:
        st.sidebar.warning("⚠️ Nunca sincronizado")
    
    # Botão de sincronização
    if status['sync_needed']:
        st.sidebar.warning("🔄 Sincronização necessária")
    else:
        st.sidebar.success("✅ Dados sincronizados")
    
    if st.sidebar.button("🔄 Sincronizar Agora", type="primary"):
        with st.spinner("🔄 Sincronizando dados..."):
            success, message = sync_service.sync_data()
            
            if success:
                st.sidebar.success(message)
                st.cache_data.clear()  # Limpar cache para recarregar dados
                st.rerun()
            else:
                st.sidebar.error(message)
    
    sync_service.close_connections()

def show_cargas_page():
    """Mostra página de cargas"""
    st.header("🚚 Gestão de Cargas")
    st.caption("📊 Dados carregados do PostgreSQL")
    
    # Painel de sincronização na sidebar
    show_sync_panel()
    
    # Carregar dados do PostgreSQL
    with st.spinner("🔄 Carregando dados do PostgreSQL..."):
        df = load_cargas_data()
    
    if df.empty:
        st.warning("⚠️ Nenhuma carga encontrada no PostgreSQL")
        st.info("💡 Use o botão 'Sincronizar Agora' na barra lateral para importar dados do MongoDB")
        return
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_cargas = len(df)
        finalizadas = len(df[df['status'].isin(['Finalizado', 'Concluído'])])
        st.metric("📊 Total de Cargas", f"{total_cargas:,}", f"↗ {finalizadas} finalizadas")
    
    with col2:
        total_quantidade = df['quantidade'].sum()
        st.metric("📦 Quantidade Total", f"{total_quantidade:,.0f} sacas")
    
    with col3:
        valor_total_frete = df['frete'].sum()
        st.metric("💰 Valor Total Frete", f"R$ {valor_total_frete:,.2f}")
    
    with col4:
        cargas_por_quantidade = total_cargas / total_quantidade if total_quantidade > 0 else 0
        percentual_finalizadas = (finalizadas / total_cargas * 100) if total_cargas > 0 else 0
        st.metric("📈 Cargas/Quantidade", f"{cargas_por_quantidade:.0f}", f"↗ {percentual_finalizadas:.1f}%")
    
    # Filtros
    st.subheader("🔍 Filtros")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        status_unicos = ['Todos'] + sorted(df['status'].unique().tolist())
        filtro_status = st.selectbox("Status", status_unicos)
    
    with col2:
        pagamento_opcoes = ['Todos', '✅ Pago', '⏰ Não Pago']
        filtro_pagamento = st.selectbox("Status Pagamento", pagamento_opcoes)
    
    with col3:
        data_min = datetime.now() - timedelta(days=30)
        data_max = datetime.now()
        filtro_data = st.date_input(
            "Intervalo de datas",
            value=(data_min.date(), data_max.date()),
            format="DD/MM/YYYY"
        )
    
    with col4:
        tipos_contrato = ['Todos'] + sorted(df['tipo_contrato'].unique().tolist())
        filtro_tipo = st.selectbox("Tipo de Contrato", tipos_contrato)
    
    with col5:
        compradores_unicos = ['Todos'] + sorted(df['comprador'].unique().tolist())
        filtro_comprador = st.selectbox("Comprador", compradores_unicos)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if filtro_status != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['status'] == filtro_status]
    
    if filtro_pagamento == '✅ Pago':
        df_filtrado = df_filtrado[df_filtrado['paid_status'] == '✅']
    elif filtro_pagamento == '⏰ Não Pago':
        df_filtrado = df_filtrado[df_filtrado['paid_status'] == '⏰']
    
    if filtro_tipo != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['tipo_contrato'] == filtro_tipo]
    
    if filtro_comprador != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['comprador'] == filtro_comprador]
    
    # Totalizadores dos resultados filtrados
    st.subheader(f"📊 Resultados: {len(df_filtrado)} cargas (PostgreSQL)")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        receita_total = df_filtrado['receita'].sum()
        st.metric("💰 Receita Total", f"R$ {receita_total:,.2f}")
    
    with col2:
        custo_total = df_filtrado['custo'].sum()
        st.metric("💸 Custo Total", f"R$ {custo_total:,.2f}")
    
    with col3:
        frete_total = df_filtrado['frete'].sum()
        st.metric("🚛 Frete Total", f"R$ {frete_total:,.2f}")
    
    with col4:
        lucro_bruto_total = df_filtrado['lucro_bruto'].sum()
        margem = (lucro_bruto_total / receita_total * 100) if receita_total > 0 else 0
        st.metric("📈 Lucro Bruto Total", f"R$ {lucro_bruto_total:,.2f}", f"↗ {margem:.2f}%")
    
    with col5:
        total_sacas = df_filtrado['quantidade'].sum()
        st.metric("📦 Total Sacas", f"{total_sacas:,.0f}")
    
    # Tabela
    st.subheader("📋 Tabela de Cargas")
    
    # Formatação da tabela
    df_display = df_filtrado.copy()
    df_display['quantidade'] = df_display['quantidade'].apply(lambda x: f"{x:,.0f}")
    df_display['receita'] = df_display['receita'].apply(lambda x: f"R$ {x:,.2f}")
    df_display['custo'] = df_display['custo'].apply(lambda x: f"R$ {x:,.2f}")
    df_display['frete'] = df_display['frete'].apply(lambda x: f"R$ {x:,.2f}")
    df_display['lucro_bruto'] = df_display['lucro_bruto'].apply(lambda x: f"R$ {x:,.2f}")
    
    # Selecionar e renomear colunas
    colunas_exibir = [
        'paid_status', 'ticket_id', 'data_carregamento', 'comprador', 'vendedor', 
        'caminhoneiro', 'grao', 'tipo_contrato', 'status', 'quantidade', 
        'receita', 'custo', 'frete', 'lucro_bruto'
    ]
    
    df_display = df_display[colunas_exibir].rename(columns={
        'paid_status': 'Pago',
        'ticket_id': 'Nro Ticket',
        'data_carregamento': 'Data de Carregamento',
        'comprador': 'Comprador',
        'vendedor': 'Vendedor',
        'caminhoneiro': 'Caminhoneiro',
        'grao': 'Grão',
        'tipo_contrato': 'Tipo Contrato',
        'status': 'Status',
        'quantidade': 'Sacas',
        'receita': 'Receita',
        'custo': 'Custo',
        'frete': 'Frete',
        'lucro_bruto': 'Lucro Bruto'
    })
    
    st.dataframe(df_display, use_container_width=True, height=600)
    
    # Gráficos
    if not df_filtrado.empty:
        st.subheader("📊 Análises")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico por status
            df_status = df_filtrado.groupby('status').size().reset_index(name='count')
            fig = px.bar(df_status, x='status', y='count', 
                        title="📊 Distribuição por Status")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gráfico por pagamento
            df_pagamento = df_filtrado.groupby('paid_status').size().reset_index(name='count')
            fig = px.pie(df_pagamento, values='count', names='paid_status', 
                        title="💰 Status de Pagamento")
            st.plotly_chart(fig, use_container_width=True)
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
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if 'status' in df_tickets.columns:
            status_options = ['Todos'] + list(df_tickets['status'].dropna().unique())
            status_filter = st.selectbox("Status:", status_options)
        else:
            status_filter = "Todos"
    
    with col2:
        # Filtro por status de pagamento
        payment_options = ["Todos", "✅ Pago", "⏰ Não Pago"]
        payment_filter = st.selectbox(
            "Status Pagamento:",
            options=payment_options,
            key="payment_filter"
        )
    
    with col3:
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
    
    with col4:
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
    
    with col5:
        # Filtro por comprador
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
    
    # Filtro por status de pagamento
    if payment_filter != "Todos" and 'paid_status' in df_filtered.columns:
        if payment_filter == "✅ Pago":
            df_filtered = df_filtered[df_filtered['paid_status'] == "✅"]
        elif payment_filter == "⏰ Não Pago":
            df_filtered = df_filtered[df_filtered['paid_status'] == "⏰"]
    
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

