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
            {"$lookup": {"from": "users", "localField": "buyer", "foreignField": "_id", "as": "buyer_info"}},
            {"$lookup": {"from": "users", "localField": "seller", "foreignField": "_id", "as": "seller_info"}},
            {"$lookup": {"from": "grains", "localField": "grain", "foreignField": "_id", "as": "grain_info"}},
            {
                "$addFields": {
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
                        "default": "⏳ Pendente"}}
                }
            },
            {"$sort": {"createdAt": -1}},
            {"$limit": 1000}
        ]
        results = list(db_service.orderv2.aggregate(pipeline))
        df = pd.DataFrame(results)
        if 'createdAt' in df.columns:
            df['createdAt'] = pd.to_datetime(df['createdAt'], errors='coerce')
        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados de contratos: {e}")
        return pd.DataFrame()


def show_contratos_page():
    """Exibe a página de contratos com filtros e totalizadores"""
    st.title("📋 Contratos")

    with st.spinner("Carregando dados de contratos..."):
        df = load_contratos_data()

    if df.empty:
        st.warning("Nenhum contrato encontrado.")
        return

    # Cliente conforme fluxo
    df['cliente'] = df.apply(
        lambda r: r['buyer_name'] if r['direction_type'] != 'Originação' else r['seller_name'], axis=1
    )

    # Datas para filtro
    min_date = df['createdAt'].min().date()
    max_date = df['createdAt'].max().date()

    # Opções de filtro
    grains = sorted(df['grain_name'].dropna().unique())
    types = sorted(df['contract_type'].dropna().unique())
    directions = sorted(df['direction_type'].dropna().unique())
    statuses = sorted(df['status_display'].dropna().unique())

    # Layout filtros
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        grain_opt = st.selectbox("Grão", ["Todos"] + grains)
    with c2:
        type_opt = st.selectbox("Tipo de contrato", ["Todos"] + types)
    with c3:
        dir_opt = st.selectbox("Fluxo", ["Todos"] + directions)
    with c4:
        cli_search = st.text_input("Pesquisar cliente")
    c5, c6 = st.columns(2)
    with c5:
        status_opt = st.multiselect("Status", statuses, default=statuses)
    with c6:
        date_range = st.date_input("Intervalo de criação", [min_date, max_date])

    # Aplicar filtros
    df_f = df.copy()
    if grain_opt != "Todos": df_f = df_f[df_f['grain_name']==grain_opt]
    if type_opt != "Todos": df_f = df_f[df_f['contract_type']==type_opt]
    if dir_opt != "Todos": df_f = df_f[df_f['direction_type']==dir_opt]
    if cli_search:
        df_f = df_f[df_f['cliente'].str.contains(cli_search, case=False, na=False)]
    if status_opt:
        df_f = df_f[df_f['status_display'].isin(status_opt)]
    if isinstance(date_range, list) and len(date_range)==2:
        start, end = date_range
        df_f = df_f[(df_f['createdAt'].dt.date>=start)&(df_f['createdAt'].dt.date<=end)]

    # Entregue e percentual
    if 'amountOrdered' in df_f.columns:
        df_f['Entregue'] = df_f['amountOrdered'].fillna(0)
        df_f['% Entregue'] = (df_f['Entregue']/df_f['amount']*100).fillna(0).round(2)
    else:
        df_f['Entregue'] = 0
        df_f['% Entregue'] = 0

    # Atualizar status para '🔄 Em Progresso' se houver entrega e não concluído
    df_f.loc[(df_f['Entregue'] > 0) & (df_f['status_display'] != '✅ Concluído'), 'status_display'] = '🔄 Em Progresso'

    # Totalizadores
    df_f['total'] = df_f['amount'] * df_f['bagPrice']
    total_sacas = int(df_f['amount'].sum())
    total_val = df_f['total'].sum()
    st.metric("Total de Sacas", f"{total_sacas:,}".replace(',', '.'))
    st.metric("Valor Total (R$)", f"R$ {total_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))

    # Exibir tabela
    st.subheader(f"📊 {len(df_f)} contratos")
    col_map = {
        '_id':'ID','createdAt':'Data Criação','cliente':'Cliente','grain_name':'Grão',
        'contract_type':'Tipo','direction_type':'Fluxo','amount':'Quantidade',
        'Entregue':'Entregue','% Entregue':'% Entregue','bagPrice':'Preço/Saca',
        'total':'Total','deliveryDeadline':'Prazo Entrega','status_display':'Status'
    }
    disp = [k for k in col_map if k in df_f]
    df_disp = df_f[disp].copy()
    df_disp.columns = [col_map[k] for k in disp]
    # Formata
    if 'Data Criação' in df_disp:
        df_disp['Data Criação'] = df_disp['Data Criação'].dt.strftime('%d/%m/%Y')
    if 'Prazo Entrega' in df_disp:
        df_disp['Prazo Entrega'] = pd.to_datetime(df_disp['Prazo Entrega'], errors='coerce').dt.strftime('%d/%m/%Y')
    if 'Preço/Saca' in df_disp:
        df_disp['Preço/Saca'] = df_disp['Preço/Saca'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))
    if 'Quantidade' in df_disp:
        df_disp['Quantidade'] = df_disp['Quantidade'].apply(lambda x: f"{int(x):,}".replace(',', '.'))
    if 'Entregue' in df_disp:
        df_disp['Entregue'] = df_disp['Entregue'].apply(lambda x: f"{int(x):,}".replace(',', '.'))
    if '% Entregue' in df_disp:
        df_disp['% Entregue'] = df_disp['% Entregue'].apply(lambda x: f"{x:.2f}%")
    if 'Total' in df_disp:
        df_disp['Total'] = df_disp['Total'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))

    st.dataframe(df_disp, use_container_width=True, height=600)

if __name__ == "__main__":
    show_contratos_page()
