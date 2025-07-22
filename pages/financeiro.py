import streamlit as st
import pandas as pd
from typing import Optional
from config.database import get_database_connection
from src.database_service import DatabaseService
from bson import ObjectId


def format_currency(value: float) -> str:
    """
    Formata um número float como moeda brasileira.
    """
    if pd.isna(value) or value == 0:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def clean_objectids(data):
    """
    Converte ObjectIds para strings recursivamente em listas ou dicionários.
    """
    if isinstance(data, list):
        return [clean_objectids(item) for item in data]
    if isinstance(data, dict):
        return {k: clean_objectids(v) for k, v in data.items()}
    if isinstance(data, ObjectId):
        return str(data)
    return data

@st.cache_data(ttl=60)
def load_finances_data(
    year_filter: Optional[str] = None,
    limit: Optional[int] = None
) -> pd.DataFrame:
    """
    Carrega dados financeiros do MongoDB com filtro opcional de ano.
    Retorna DataFrame vazio em caso de erro ou ausência de dados.
    """
    try:
        db = get_database_connection()
        if not db:
            st.error("Não foi possível conectar ao banco de dados.")
            return pd.DataFrame()
        cols = db.get_collections()
        if not cols:
            st.error("Coleções do banco não disponíveis.")
            return pd.DataFrame()
        service = DatabaseService(cols)
        raw = service.get_finances_with_lookups(year_filter=year_filter, limit=limit)
        if not raw:
            return pd.DataFrame()
        cleaned = clean_objectids(raw)
        df = pd.DataFrame(cleaned)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()


def show_financeiro_page():
    """
    Renderiza a página Financeiro no Streamlit.
    """
    st.title("💰 Financeiro")

    # 1. Seleção de ano
    df_all = load_finances_data()
    if 'date' in df_all.columns:
        df_all['date'] = pd.to_datetime(
            df_all['date'].astype(str),
            format='%Y%m%d',
            errors='coerce'
        )
        years = sorted(df_all['date'].dt.year.dropna().unique(), reverse=True)
    else:
        years = []
    year_options = ['Todos'] + [str(int(y)) for y in years]
    year_filter = st.selectbox("Ano:", year_options)

    # 2. Carregar e filtrar dados
    yf = None if year_filter == 'Todos' else year_filter
    df = load_finances_data(year_filter=yf)
    if df.empty:
        st.info("Nenhum dado encontrado para o filtro selecionado.")
        return
    df['date'] = pd.to_datetime(
        df['date'].astype(str),
        format='%Y%m%d',
        errors='coerce'
    )
    if year_filter != 'Todos':
        df = df[df['date'].dt.year == int(year_filter)]
        if df.empty:
            st.info(f"Nenhum dado para o ano {year_filter}.")
            return

    # 3. Utilitário para exibir pivôs
    def display_pivot(df_pivot: pd.DataFrame):
        if df_pivot.empty:
            st.write("Sem registros.")
            return
        df_sum = df_pivot.copy()
        df_sum['TOTAL'] = df_sum.sum(axis=1)
        df_fmt = df_sum.astype(float)
        for col in df_fmt.columns:
            df_fmt[col] = df_fmt[col].apply(format_currency)
        st.dataframe(df_fmt)

    # 4. Dados Operacional
    oper_mask = df['category_name'].str.upper().str.contains('OPERACIONAL', na=False)
    df_oper = df[oper_mask].copy()
    df_oper['month_year'] = df_oper['date'].dt.to_period('M')
    df_oper['tipo_oper'] = df_oper['value'].apply(
        lambda v: 'RECEITA OPERACIONAL' if v > 0 else 'CUSTO OPERACIONAL'
    )
    grouped_oper = (
        df_oper
        .groupby(['tipo_oper', 'category_item', 'month_year'])['value']
        .sum()
        .reset_index()
    )

    # Caixa Total: soma de todos os lançamentos por mês
    caixa_total = (
        df
        .groupby(df['date'].dt.to_period('M'))['value']
        .sum()
        .to_frame()
    )

    # 5. Dados Financiamento e Impostos
    def prepare_category(cat_name: str) -> pd.DataFrame:
        mask = df['category_name'].str.upper().str.contains(cat_name, na=False)
        df_cat = df[mask].copy()
        if df_cat.empty:
            return pd.DataFrame()
        df_cat['month_year'] = df_cat['date'].dt.to_period('M')
        return df_cat.pivot_table(
            index='category_item',
            columns='month_year',
            values='value',
            aggfunc='sum',
            fill_value=0
        )
    pivot_fin = prepare_category('FINANCIAMENTO')
    pivot_imp = prepare_category('IMPOSTOS')

    # 6. Seções colapsáveis
    st.subheader("📅 Fluxos Mensais por Categoria")
    sections = [
        ('RECEITA OPERACIONAL', grouped_oper[grouped_oper['tipo_oper']=='RECEITA OPERACIONAL']),
        ('CUSTO OPERACIONAL', grouped_oper[grouped_oper['tipo_oper']=='CUSTO OPERACIONAL']),
        ('FINANCIAMENTO', pivot_fin),
        ('IMPOSTOS', pivot_imp),
        ('CAIXA TOTAL', caixa_total.T)
    ]
    for title, data in sections:
        with st.expander(f"▶️ {title}"):
            if title == 'CAIXA TOTAL':
                display_pivot(data)
            elif isinstance(data, pd.DataFrame) and 'value' in data.columns:
                pivot_long = data.pivot_table(
                    index='category_item',
                    columns='month_year',
                    values='value',
                    aggfunc='sum',
                    fill_value=0
                )
                display_pivot(pivot_long)
            elif isinstance(data, pd.DataFrame):
                display_pivot(data)
            else:
                st.write("Sem registros.")

        # 7. DRE Simplificado com Percentual
    st.subheader("📊 DRE Simplificado")
    dre_order = [
        'RECEITA OPERACIONAL',
        'CUSTO OPERACIONAL',
        'DESPESAS ADMINISTRATIVAS',
        'DESPESAS NAO OPERACIONAL',
        'NAO OPERACIONAL',
        'IMPOSTOS',
        'FINANCIAMENTO',
        'INVESTIMENTOS',
        'OUTROS',
        'CAIXA TOTAL'
    ]
    # Calcula totais numéricos
    dre_values = {}
    for line in dre_order:
        if line in ['RECEITA OPERACIONAL', 'CUSTO OPERACIONAL']:
            mask = df_oper[df_oper['tipo_oper']==line]['value']
        elif line == 'CAIXA TOTAL':
            mask = caixa_total['value'] if 'value' in caixa_total.columns else caixa_total.iloc[:,0]
        else:
            mask = df[df['category_name'].str.upper().str.contains(line, na=False)]['value']
        dre_values[line] = mask.sum() if not mask.empty else 0
    # Converte para DataFrame
    dre_df = pd.DataFrame.from_dict(dre_values, orient='index', columns=['VALOR'])
    total_geral = dre_df['VALOR'].sum()
    # Calcula percentual
    dre_df['%'] = (dre_df['VALOR'] / total_geral * 100).round(2).astype(str) + '%'
    # Formata moeda
    dre_df['VALOR'] = dre_df['VALOR'].apply(format_currency)
    # Exibe tabela com valor e percentual
    st.table(dre_df)

    # 8. EBITDA
    # EBITIDA = Receita Operacional - Custo Operacional - Despesas Administrativas - Despesas Nao Operacional
    ebitda_value = (
        dre_values.get('RECEITA OPERACIONAL', 0)
        - dre_values.get('CUSTO OPERACIONAL', 0)
        - dre_values.get('DESPESAS ADMINISTRATIVAS', 0)
        - dre_values.get('DESPESAS NAO OPERACIONAL', 0)
    )
    st.subheader("📈 EBITDA")
    st.metric("EBITDA", format_currency(ebitda_value))



if __name__ == "__main__":
    show_financeiro_page()
