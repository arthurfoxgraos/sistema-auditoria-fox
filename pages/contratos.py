import streamlit as st
import pandas as pd
from src.database_service import DatabaseService
from config.database import DatabaseConfig

@st.cache_data(ttl=60)
def load_contratos_data():
    """Carrega dados de contratos do MongoDB"""
    try:
        db_config = DatabaseConfig()
        if not db_config.connect():
            return pd.DataFrame()
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)

        pipeline = [
            {"$lookup": {"from": "ticketv2", "let": {"contractId": "$_id"},
             "pipeline": [
                 {"$unwind": "$transactions"},
                 {"$match": {"$expr": {"$eq": ["$transactions.destinationOrder", "$$contractId"]}}},
                 {"$group": {"_id": "$_id", "loadingDate": {"$max": "$loadingDate"},
                            "deliveryDate": {"$max": "$deliveredIn"}, "transactions": {"$push": "$transactions"}}}
             ], "as": "tickets"}},
            {"$lookup": {"from": "users", "localField": "buyer", "foreignField": "_id", "as": "buyer_info"}},
            {"$lookup": {"from": "users", "localField": "seller", "foreignField": "_id", "as": "seller_info"}},
            {"$lookup": {"from": "grains", "localField": "grain", "foreignField": "_id", "as": "grain_info"}},
            {"$addFields": {
                "buyer_name": {"$ifNull": [{"$arrayElemAt": ["$buyer_info.name", 0]}, {"$arrayElemAt": ["$buyer_info.companyName", 0]}]},
                "seller_name": {"$ifNull": [{"$arrayElemAt": ["$seller_info.name", 0]}, {"$arrayElemAt": ["$seller_info.companyName", 0]}]},
                "grain_name": {"$arrayElemAt": ["$grain_info.name", 0]},
                "contract_type": {"$switch": {"branches": [
                    {"case": {"$eq": ["$isGrain", True]}, "then": "🌾 Grão"},
                    {"case": {"$eq": ["$isFreight", True]}, "then": "🚛 Frete"},
                    {"case": {"$eq": ["$isService", True]}, "then": "⭐ Clube FX"}],
                "default": "❓ Indefinido"}},
                "direction_type": {"$cond": {"if": {"$eq": ["$isBuying", True]}, "then": "Originação", "else": "Supply"}},
                "status_display": {"$switch": {"branches": [
                    {"case": {"$eq": ["$isDone", True]}, "then": "✅ Concluído"},
                    {"case": {"$eq": ["$isCanceled", True]}, "then": "❌ Cancelado"},
                    {"case": {"$eq": ["$isInProgress", True]}, "then": "🔄 Em Progresso"}],
                "default": "⏳ Pendente"}},
                "loadingDate": {"$arrayElemAt": ["$tickets.loadingDate", 0]},
                "deliveryDate": {"$arrayElemAt": ["$tickets.deliveryDate", 0]},
                "amountOrderedSafe": {"$ifNull": ["$amountOrdered", 0]},
                "paymentDaysSafe": {"$ifNull": ["$paymentDaysAfterDelivery", 0]},
                "destOrderList": {"$map": {"input": {"$arrayElemAt": ["$tickets.transactions", 0]}, "as": "tr", "in": "$$tr.destinationOrder"}},
                "origOrderList": {"$map": {"input": {"$arrayElemAt": ["$tickets.transactions", 0]}, "as": "tr", "in": "$$tr.originOrder"}},
                "Ordem": {"$cond": [
                    {"$eq": ["$direction_type", "Supply"]},
                    {"$arrayElemAt": ["$destOrderList", -1]},
                    {"$arrayElemAt": ["$origOrderList", -1]}
                ]},
                "pis_status": {"$cond": {"if": {"$eq": ["$hasPIS", True]}, "then": "✅ Com PIS", "else": "❌ Sem PIS"}},
                "pis_cofins_value": {"$cond": {
                    "if": {"$eq": ["$hasPIS", True]}, 
                    "then": {"$multiply": [{"$multiply": ["$amount", "$bagPrice"]}, 0.0925]}, 
                    "else": 0
                }}
            }},
            {"$match": {"$expr": {"$ne": ["$isCanceled", True]}}},
            {"$sort": {"createdAt": -1}},
            {"$limit": 1000}
        ]
        results = list(db_service.orderv2.aggregate(pipeline))
        df = pd.DataFrame(results)
        for col in ['createdAt', 'loadingDate', 'deliveryDate']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados de contratos: {e}")
        return pd.DataFrame()


def show_contratos_page():
    st.title("📋 Contratos")
    df = load_contratos_data()
    if df.empty:
        st.warning("Nenhum contrato encontrado.")
        return

    # Filtros de data baseados em createdAt
    min_created_date = df['createdAt'].min().date() if not df['createdAt'].isna().all() else pd.Timestamp.now().date()
    max_created_date = df['createdAt'].max().date() if not df['createdAt'].isna().all() else pd.Timestamp.now().date()
    
    # Filtros de entrega baseados em deliveryDate
    min_deliv_date = df['deliveryDate'].min().date() if not df['deliveryDate'].isna().all() else pd.Timestamp.now().date()
    max_deliv_date = df['deliveryDate'].max().date() if not df['deliveryDate'].isna().all() else pd.Timestamp.now().date()

    grains = sorted(df['grain_name'].dropna().unique())
    types = sorted(df['contract_type'].dropna().unique())
    directions = sorted(df['direction_type'].dropna().unique())
    statuses = sorted(df['status_display'].dropna().unique())
    pis_options = sorted(df['pis_status'].dropna().unique()) if 'pis_status' in df.columns else []

    # Extrair anos e meses da deliveryDate para filtros
    if 'deliveryDate' in df.columns:
        df['delivery_year'] = pd.to_datetime(df['deliveryDate'], errors='coerce').dt.year
        df['delivery_month'] = pd.to_datetime(df['deliveryDate'], errors='coerce').dt.month
        
        # Listas para filtros
        delivery_years = sorted([year for year in df['delivery_year'].dropna().unique() if not pd.isna(year)], reverse=True)
        delivery_months = sorted([month for month in df['delivery_month'].dropna().unique() if not pd.isna(month)])
        
        # Nomes dos meses
        month_names = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        year_options = ['Todos'] + [str(int(year)) for year in delivery_years]
        month_options = ['Todos'] + [month_names[month] for month in delivery_months]
    else:
        year_options = ['Todos']
        month_options = ['Todos']

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1: grain_opt = st.selectbox("Grão", ["Todos"] + grains)
    with c2: type_opt = st.selectbox("Tipo de contrato", ["Todos"] + types)
    with c3: 
        # Definir valor padrão como Originação se existir, senão o primeiro da lista
        default_direction = "Originação" if "Originação" in directions else (directions[0] if directions else "Todos")
        direction_options = ["Todos"] + directions
        default_index = direction_options.index(default_direction) if default_direction in direction_options else 0
        dir_opt = st.selectbox("Fluxo", direction_options, index=default_index)
    with c4: pis_opt = st.selectbox("PIS", ["Todos"] + pis_options)
    with c5: year_opt = st.selectbox("Ano Entrega", year_options)
    with c6: month_opt = st.selectbox("Mês Entrega", month_options)
    with c7: cli_search = st.text_input("Pesquisar cliente")
    
    # Definir cliente baseado no tipo de contrato e direção
    def define_cliente(row):
        # Para contratos de frete, sempre usar seller_name
        if row.get('contract_type') == '🚛 Frete':
            return row.get('seller_name', 'N/A')
        # Para outros tipos, usar regra original
        elif row.get('direction_type') != 'Originação':
            return row.get('buyer_name', 'N/A')
        else:
            return row.get('seller_name', 'N/A')
    
    df['cliente'] = df.apply(define_cliente, axis=1)
    
    c8, c9 = st.columns(2)
    with c8: status_opt = st.multiselect("Status", statuses, default=statuses)
    with c9: created_date_range = st.date_input("Intervalo de Criação (createdAt)", [min_created_date, max_created_date])
    
    c10, c11 = st.columns(2)
    with c10: deliv_range = st.date_input("Intervalo Última Entrega", [min_deliv_date, max_deliv_date])

    df_f = df.copy()
    if grain_opt != "Todos": df_f = df_f[df_f['grain_name']==grain_opt]
    if type_opt != "Todos": df_f = df_f[df_f['contract_type']==type_opt]
    if dir_opt != "Todos": df_f = df_f[df_f['direction_type']==dir_opt]
    if pis_opt != "Todos": df_f = df_f[df_f['pis_status']==pis_opt]
    
    # Filtros de ano e mês de entrega
    if year_opt != "Todos" and 'delivery_year' in df_f.columns:
        df_f = df_f[df_f['delivery_year'] == int(year_opt)]
    
    if month_opt != "Todos" and 'delivery_month' in df_f.columns:
        # Converter nome do mês para número
        month_names_reverse = {v: k for k, v in month_names.items()}
        selected_month = month_names_reverse.get(month_opt)
        if selected_month:
            df_f = df_f[df_f['delivery_month'] == selected_month]
    if cli_search: df_f = df_f[df_f['cliente'].str.contains(cli_search, case=False, na=False)]
    if status_opt: df_f = df_f[df_f['status_display'].isin(status_opt)]
    
    # Filtro por data de criação (createdAt)
    if isinstance(created_date_range, list) and len(created_date_range) == 2:
        start_date, end_date = created_date_range
        df_f = df_f[(df_f['createdAt'].dt.date >= start_date) & (df_f['createdAt'].dt.date <= end_date)]
    
    # Filtro por data de entrega
    if isinstance(deliv_range, list) and len(deliv_range) == 2:
        deliv_start, deliv_end = deliv_range
        df_f = df_f[(df_f['deliveryDate'].dt.date >= deliv_start) & (df_f['deliveryDate'].dt.date <= deliv_end)]

    df_f['Entregue'] = df_f['amountOrderedSafe']
    df_f['% Entregue'] = (df_f['Entregue']/df_f['amount']*100).round(2).fillna(0)
    df_f.loc[(df_f['Entregue']>0)&(df_f['status_display']!='✅ Concluído'),'status_display']='🔄 Em Progresso'

    df_f['Prazo Pagamento (dias)'] = pd.to_numeric(df_f['paymentDaysSafe'], errors='coerce').fillna(0).astype(int)
    df_f['Data Pagamento'] = df_f['deliveryDate'] + pd.to_timedelta(df_f['Prazo Pagamento (dias)'], unit='d')

    df_f['total'] = df_f['amount'] * df_f['bagPrice']
    
    # Cards de métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total de Sacas", f"{int(df_f['amount'].sum()):,}".replace(',', '.'))
    
    with col2:
        st.metric("Valor Total (R$)", f"R$ {df_f['total'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))
    
    with col3:
        # Número de clientes únicos
        unique_clients = df_f['cliente'].nunique()
        st.metric("Número de Clientes", f"{unique_clients}")
    
    with col4:
        # Volume médio por cliente
        avg_volume_per_client = df_f['amount'].sum() / unique_clients if unique_clients > 0 else 0
        st.metric("Volume Médio/Cliente", f"{int(avg_volume_per_client):,}".replace(',', '.'))
    
    with col5:
        # Total PIS/COFINS
        total_pis_cofins = df_f['pis_cofins_value'].sum()
        st.metric("Total PIS/COFINS", f"R$ {total_pis_cofins:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))
    
    # Análise de volumes por cliente
    st.subheader("📊 Volumes Comercializados por Cliente")
    
    # Calcular volumes por cliente
    client_volumes = df_f.groupby('cliente').agg({
        'amount': 'sum',
        'total': 'sum',
        '_id': 'count'  # número de contratos
    }).round(2)
    client_volumes.columns = ['Volume (Sacas)', 'Valor Total (R$)', 'Nº Contratos']
    client_volumes = client_volumes.sort_values('Volume (Sacas)', ascending=False)
    
    # Top 10 clientes
    top_clients = client_volumes.head(10).copy()
    
    # Formatar valores para exibição
    top_clients['Volume (Sacas)'] = top_clients['Volume (Sacas)'].astype(int).apply(lambda x: f"{x:,}".replace(',', '.'))
    top_clients['Valor Total (R$)'] = top_clients['Valor Total (R$)'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    # Exibir tabela dos top clientes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Top 10 Clientes por Volume:**")
        st.dataframe(top_clients, use_container_width=True)
    
    with col2:
        # Gráfico de pizza dos top 5 clientes
        import plotly.express as px
        
        top5_data = client_volumes.head(5)
        if not top5_data.empty:
            fig = px.pie(
                values=top5_data['Volume (Sacas)'].astype(float),
                names=top5_data.index,
                title="Top 5 Clientes - Distribuição de Volume"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()

    display_map = {
        'Status':'status_display','Última Carga':'loadingDate','Data Pagamento':'Data Pagamento',
        '% Entregue':'% Entregue','Cliente':'cliente','Grão':'grain_name',
        'Quantidade':'amount','Total':'total','Preço/Saca':'bagPrice'
    }

    sort_label = st.selectbox("Ordenar por", list(display_map.keys()), index=list(display_map.keys()).index('Última Carga'))
    ascending = st.checkbox("Ascendente", value=False)
    df_f = df_f.sort_values(by=display_map[sort_label], ascending=ascending)

    st.subheader(f"📊 {len(df_f)} contratos")
    labels = list(display_map.keys())
    cols = [display_map[label] for label in labels]
    df_disp = df_f[cols].copy()
    df_disp.columns = labels

    date_cols = ['Última Carga','Data Pagamento']
    for dc in date_cols:
        if dc in df_disp:
            df_disp[dc] = pd.to_datetime(df_disp[dc], errors='coerce').dt.strftime('%d/%m/%Y')
    if 'Preço/Saca' in df_disp:
        df_disp['Preço/Saca'] = df_disp['Preço/Saca'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))
    if 'Quantidade' in df_disp:
        df_disp['Quantidade'] = df_disp['Quantidade'].astype(int).apply(lambda x: f"{x:,}".replace(',', '.'))
    if '% Entregue' in df_disp:
        df_disp['% Entregue'] = df_disp['% Entregue'].apply(lambda x: f"{x:.2f}%")
    if 'Total' in df_disp:
        df_disp['Total'] = df_disp['Total'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))

    st.dataframe(df_disp, use_container_width=True, height=600)


if __name__ == "__main__":
    show_contratos_page()