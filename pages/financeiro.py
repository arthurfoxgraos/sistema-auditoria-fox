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

            # Buscar dados sem limite, filtrando apenas isIgnored
            finances = db_service.get_finances_with_lookups()

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
    col1, col2, col3, col4 = st.columns(4)

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
    
    with col3:
        # Filtro por ano
        if 'date' in df_finances.columns and not df_finances['date'].isna().all():
            years = sorted(df_finances['date'].dt.year.dropna().unique(), reverse=True)
            year_options = ['Todos'] + [str(int(year)) for year in years]
            year_filter = st.selectbox("Ano:", year_options)
        else:
            year_filter = "Todos"
    
    with col4:
        # Filtro por mês
        if 'date' in df_finances.columns and not df_finances['date'].isna().all():
            month_names = {
                1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
            }
            months = sorted([int(month) for month in df_finances['date'].dt.month.dropna().unique()])
            month_options = ['Todos'] + [month_names[month] for month in months]
            month_filter = st.selectbox("Mês:", month_options)
        else:
            month_filter = "Todos"

    # Aplicar filtros
    df_filtered = df_finances.copy()
    if user_filter != "Todos" and 'user_name' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['user_name'] == user_filter]
    if item_filter != "Todos" and 'category_item' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['category_item'] == item_filter]
    
    # Filtro por ano
    if year_filter != "Todos" and 'date' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['date'].dt.year == int(year_filter)]
    
    # Filtro por mês
    if month_filter != "Todos" and 'date' in df_filtered.columns:
        # Converter nome do mês para número
        month_names_reverse = {
            'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4,
            'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8,
            'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
        }
        month_number = month_names_reverse[month_filter]
        df_filtered = df_filtered[df_filtered['date'].dt.month == month_number]

    # Mostrar resultados
    st.subheader(f"📊 Resultados: {len(df_filtered)} registros financeiros")

    if not df_filtered.empty:
        # Totalizador geral
        total_valor = df_filtered['value'].sum()
        total_formatado = format_currency(total_valor)
        st.markdown(f"**🎯 Total Geral: {total_formatado}**")
        
        st.divider()
        
        # Consolidado por categoria
        st.subheader("📋 Consolidado por Categoria")
        
        if 'category_name' in df_filtered.columns:
            # Agrupar por categoria e calcular totais
            consolidado = df_filtered.groupby('category_name').agg({
                'value': ['sum', 'count', 'mean']
            }).round(2)
            
            # Achatar as colunas multi-nível
            consolidado.columns = ['Total', 'Quantidade', 'Média']
            consolidado = consolidado.sort_values('Total', ascending=False)
            
            # Calcular percentual
            consolidado['Percentual'] = (consolidado['Total'] / total_valor * 100).round(1)
            
            # Formatar valores monetários
            consolidado_display = consolidado.copy()
            consolidado_display['Total'] = consolidado_display['Total'].apply(lambda x: format_currency(x))
            consolidado_display['Média'] = consolidado_display['Média'].apply(lambda x: format_currency(x))
            consolidado_display['Percentual'] = consolidado_display['Percentual'].apply(lambda x: f"{x}%")
            
            # Renomear índice
            consolidado_display.index.name = 'Categoria'
            
            # Exibir tabela consolidada
            st.dataframe(
                consolidado_display,
                use_container_width=True,
                height=400
            )
            
            # Gráfico de pizza das categorias
            col1, col2 = st.columns(2)
            
            with col1:
                # Todas as categorias
                if len(consolidado) > 0:
                    import plotly.express as px
                    fig = px.pie(
                        values=consolidado['Total'],
                        names=consolidado.index,
                        title="Distribuição por Categoria"
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Gráfico de barras
                if len(consolidado) > 0:
                    import plotly.express as px
                    fig_bar = px.bar(
                        x=consolidado['Total'],
                        y=consolidado.index,
                        orientation='h',
                        title="Valores por Categoria",
                        labels={'x': 'Valor Total', 'y': 'Categoria'}
                    )
                    fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_bar, use_container_width=True)
        
        else:
            st.warning("Campo 'category_name' não encontrado nos dados para consolidação.")
            
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados.")


if __name__ == "__main__":
    show_financeiro_page()
