import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from src.database_service import DatabaseService
from config.database import DatabaseConfig

@st.cache_data(ttl=60)
def load_finances_data():
    """Carrega dados financeiros do MongoDB"""
    try:
        db_config = DatabaseConfig()
        if db_config.connect():
            collections = db_config.get_collections()
            db_service = DatabaseService(collections)

            finances = db_service.get_finances_with_lookups(limit=1000)

            if finances:
                df = pd.DataFrame(finances)
                return df
            else:
                return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados financeiros: {e}")
        return pd.DataFrame()


def format_currency(x):
    """Formata número em string de moeda brasileira"""
    try:
        return f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return "R$ 0,00"


def show_financeiro_page():
    """Exibe a página de financeiro"""
    st.title("💰 Financeiro")

    # Carregar dados
    with st.spinner("Carregando dados financeiros..."):
        df_finances = load_finances_data()

    if df_finances.empty:
        st.warning("Nenhum dado financeiro encontrado.")
        return

    # Ajustar coluna de data a partir da tag e converter para datetime
    if 'date' in df_finances.columns:
        # Extrai os 14 dígitos iniciais (YYYYMMDDHHMMSS)
        df_finances['date'] = (
            df_finances['date']
            .astype(str)
            .str.extract(r"(\d{14})")[0]
        )
        df_finances['date'] = pd.to_datetime(
            df_finances['date'], format='%Y%m%d%H%M%S', errors='coerce'
        )

    # Filtros
    st.subheader("🔍 Filtros")
    col1, col2 = st.columns(2)

    with col1:
        # Filtro por usuário
        if 'user_name' in df_finances.columns:
            user_options = ['Todos'] + sorted(df_finances['user_name'].dropna().unique().tolist())
            user_filter = st.selectbox("Usuário:", user_options)
        else:
            user_filter = "Todos"

    with col2:
        # Filtro por item
        if 'category_item' in df_finances.columns:
            item_options = ['Todos'] + sorted(df_finances['category_item'].dropna().unique().tolist())
            item_filter = st.selectbox("Item:", item_options)
        else:
            item_filter = "Todos"

    # Aplicar filtros
    df_filtered = df_finances.copy()
    if user_filter != "Todos" and 'user_name' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['user_name'] == user_filter]
    if item_filter != "Todos" and 'category_item' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['category_item'] == item_filter]

    # Mostrar resultados
    st.subheader(f"📊 Resultados: {len(df_filtered)} registros financeiros")

    if not df_filtered.empty:
        # Totalizador
        total_valor = df_filtered['value'].sum()
        total_formatado = format_currency(total_valor)
        st.markdown(f"**🎯 Total Geral: {total_formatado}**")

        # Preparar dados para exibição - apenas 4 colunas
        display_columns = []
        column_mapping = {
            'date': 'Data',
            'name': 'Usuário (Descrição)',
            'value': 'Valor',
            'category_item': 'Item'
        }
        for col, display_name in column_mapping.items():
            if col in df_filtered.columns:
                display_columns.append(col)

        if display_columns:
            df_display = df_filtered[display_columns].copy()
            df_display.columns = [column_mapping.get(col, col) for col in display_columns]

            # Formatar data
            if 'Data' in df_display.columns:
                df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')

            # Formatar valor monetário
            if 'Valor' in df_display.columns:
                df_display['Valor'] = df_display['Valor'].apply(lambda x: format_currency(x) if pd.notnull(x) else format_currency(0))

            st.dataframe(
                df_display,
                use_container_width=True,
                height=600
            )
        else:
            st.warning("Colunas solicitadas não encontradas nos dados.")
            st.dataframe(df_filtered, use_container_width=True)
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados.")


if __name__ == "__main__":
    show_financeiro_page()
