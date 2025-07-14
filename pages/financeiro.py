import streamlit as st
import pandas as pd
from config.database import get_database_connection
from src.database_service import DatabaseService
from bson import ObjectId

def format_currency(value):
    """Formatar valor como moeda brasileira"""
    if pd.isna(value) or value == 0:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def clean_objectids(data):
    """Converter ObjectIds para strings para evitar erro Arrow"""
    if isinstance(data, list):
        cleaned_data = []
        for item in data:
            if isinstance(item, dict):
                cleaned_item = {}
                for key, value in item.items():
                    if isinstance(value, ObjectId):
                        cleaned_item[key] = str(value)
                    elif isinstance(value, list):
                        cleaned_item[key] = clean_objectids(value)
                    elif isinstance(value, dict):
                        cleaned_item[key] = clean_objectids(value)
                    else:
                        cleaned_item[key] = value
                cleaned_data.append(cleaned_item)
            else:
                cleaned_data.append(item)
        return cleaned_data
    elif isinstance(data, dict):
        cleaned_dict = {}
        for key, value in data.items():
            if isinstance(value, ObjectId):
                cleaned_dict[key] = str(value)
            elif isinstance(value, list):
                cleaned_dict[key] = clean_objectids(value)
            elif isinstance(value, dict):
                cleaned_dict[key] = clean_objectids(value)
            else:
                cleaned_dict[key] = value
        return cleaned_dict
    else:
        return data

@st.cache_data(ttl=60)
def load_finances_data():
    """Carrega dados financeiros do MongoDB"""
    try:
        db_config = get_database_connection()
        if not db_config:
            st.error("Não foi possível conectar ao banco de dados")
            return None
        
        collections = db_config.get_collections()
        if not collections:
            st.error("Não foi possível obter as coleções do banco")
            return None
            
        db_service = DatabaseService(collections)
        data = db_service.get_finances_with_lookups()
        
        if data:
            # Limpar ObjectIds antes de converter para DataFrame
            cleaned_data = clean_objectids(data)
            
            # Converter lista de dicionários para DataFrame
            df = pd.DataFrame(cleaned_data)
            return df
        else:
            return pd.DataFrame()  # DataFrame vazio se não há dados
            
    except Exception as e:
        st.error(f"Erro ao carregar dados financeiros: {e}")
        print(f"Erro detalhado: {e}")
        return None

def show_financeiro_page():
    st.title("💰 Financeiro")
    
    # Carregar dados
    df_finances = load_finances_data()
    
    if df_finances is not None and not df_finances.empty:
        # Debug: mostrar colunas disponíveis
        st.write("Debug - Colunas disponíveis:", list(df_finances.columns))
        
        # Converter coluna de data - tratamento mais robusto
        date_column_found = False
        if 'date' in df_finances.columns:
            try:
                # Tratar formato específico YYYYMMDDHHMMSS[-3:BRT]
                def parse_date_field(date_value):
                    if pd.isna(date_value) or date_value is None:
                        return None
                    
                    # Converter para string se necessário
                    date_str = str(date_value)
                    
                    # Extrair apenas os 8 primeiros dígitos (YYYYMMDD)
                    if len(date_str) >= 8:
                        date_part = date_str[:8]
                        try:
                            # Converter YYYYMMDD para datetime
                            return pd.to_datetime(date_part, format='%Y%m%d', errors='coerce')
                        except:
                            return None
                    return None
                
                # Aplicar função de parsing
                df_finances['date'] = df_finances['date'].apply(parse_date_field)
                
                # Verificar se conseguimos converter alguma data
                if df_finances['date'].notna().any():
                    date_column_found = True
                    st.success(f"✅ Campo 'date' processado com sucesso! {df_finances['date'].notna().sum()} datas válidas encontradas.")
                else:
                    st.warning("⚠️ Campo 'date' encontrado mas nenhuma data válida após conversão.")
                    
            except Exception as e:
                st.warning(f"Erro ao converter campo date: {e}")
        else:
            st.warning("Campo 'date' não encontrado nos dados.")
        
        # Filtro por ano
        st.subheader("🔍 Filtro")
        if date_column_found:
            years = sorted([int(year) for year in df_finances['date'].dt.year.dropna().unique()], reverse=True)
            year_options = ['Todos'] + [str(year) for year in years]
            year_filter = st.selectbox("Ano:", year_options, index=0)
        else:
            year_filter = "Todos"
            st.warning("Campo 'date' não encontrado ou vazio nos dados. Mostrando todos os dados disponíveis.")
            
            # Mostrar amostra dos dados para debug
            if not df_finances.empty:
                st.write("Amostra dos dados (primeiras 5 linhas):")
                st.write(df_finances.head())
        
        # Aplicar filtro por ano
        df_filtered = df_finances.copy()
        if year_filter != "Todos" and date_column_found:
            df_filtered = df_filtered[df_filtered['date'].dt.year == int(year_filter)]
        
        # Análise Mensal - Fluxo de Caixa
        st.subheader("📅 Análise Mensal - Fluxo de Caixa")
        
        if date_column_found and not df_filtered.empty:
            # Criar coluna de mês/ano
            df_filtered['month_year'] = df_filtered['date'].dt.to_period('M')
            
            # Definir categorias baseadas no category_name e category_item
            def categorize_financial_flow(row):
                category_name = str(row.get('category_name', '')).upper()
                item = str(row.get('category_item', '')).lower()
                value = row.get('value', 0)
                
                # Categorização baseada na estrutura solicitada
                if category_name == 'OPERACIONAL':
                    if 'receb' in item or 'receita' in item or (value > 0 and ('grão' in item or 'soja' in item or 'milho' in item)):
                        return 'Recebimento de Grãos'
                    elif ('pagamento' in item or value < 0) and ('grão' in item or 'soja' in item or 'milho' in item):
                        return 'Pagamento de Grãos'
                    elif 'frete' in item:
                        return 'Pagamento de Frete'
                    else:
                        return 'OPERACIONAL - Outros'
                elif category_name == 'DESPESAS ADMINISTRATIVAS':
                    return 'Despesas Administrativas'
                elif category_name == 'IMPOSTOS':
                    return 'IMPOSTOS'
                elif category_name == 'FINANCIAMENTO':
                    return 'FINANCIAMENTO'
                elif category_name == 'INVESTIMENTOS':
                    return 'INVESTIMENTOS'
                else:
                    # Fallback baseado no valor e item
                    if value > 0 and ('grão' in item or 'soja' in item or 'milho' in item):
                        return 'Recebimento de Grãos'
                    elif value < 0 and ('grão' in item or 'soja' in item or 'milho' in item):
                        return 'Pagamento de Grãos'
                    elif 'frete' in item:
                        return 'Pagamento de Frete'
                    else:
                        return 'Outros'
            
            # Aplicar categorização
            df_filtered['financial_category'] = df_filtered.apply(categorize_financial_flow, axis=1)
            
            # Agrupar por mês e categoria
            monthly_analysis = df_filtered.groupby(['month_year', 'financial_category'])['value'].sum().reset_index()
            
            if not monthly_analysis.empty:
                # Pivot para ter categorias como colunas
                monthly_pivot = monthly_analysis.pivot(index='month_year', columns='financial_category', values='value').fillna(0)
                
                # Definir colunas principais na ordem desejada
                main_columns = [
                    'Recebimento de Grãos',
                    'Pagamento de Grãos', 
                    'Pagamento de Frete',
                    'Despesas Administrativas',
                    'IMPOSTOS',
                    'FINANCIAMENTO',
                    'INVESTIMENTOS',
                    'OPERACIONAL - Outros',
                    'Outros'
                ]
                
                # Garantir que as colunas existam
                for col in main_columns:
                    if col not in monthly_pivot.columns:
                        monthly_pivot[col] = 0
                
                # Calcular totais operacionais
                monthly_pivot['Total OPERACIONAL'] = (
                    monthly_pivot['Recebimento de Grãos'] + 
                    monthly_pivot['Pagamento de Grãos'] + 
                    monthly_pivot['Pagamento de Frete'] + 
                    monthly_pivot.get('OPERACIONAL - Outros', 0)
                )
                
                # Calcular resultado de caixa (todas as entradas - todas as saídas)
                monthly_pivot['Resultado de Caixa'] = monthly_pivot.sum(axis=1)
                
                # Ordenar por data
                monthly_pivot = monthly_pivot.sort_index()
                
                # Formatar índice para exibição
                monthly_pivot.index = monthly_pivot.index.astype(str)
                
                # Criar DataFrame para exibição com estrutura hierárquica
                display_columns = [
                    'Recebimento de Grãos',
                    'Pagamento de Grãos',
                    'Pagamento de Frete', 
                    'Total OPERACIONAL',
                    'Despesas Administrativas',
                    'IMPOSTOS',
                    'FINANCIAMENTO',
                    'INVESTIMENTOS',
                    'Resultado de Caixa'
                ]
                
                # Filtrar apenas colunas que existem
                available_columns = [col for col in display_columns if col in monthly_pivot.columns]
                monthly_display = monthly_pivot[available_columns].copy()
                
                # Formatar valores monetários
                for col in monthly_display.columns:
                    monthly_display[col] = monthly_display[col].apply(lambda x: format_currency(x))
                
                # Exibir tabela
                st.dataframe(monthly_display, use_container_width=True, height=500)
                
                # Gráficos
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de linha - Resultado de Caixa
                    if 'Resultado de Caixa' in monthly_pivot.columns:
                        import plotly.graph_objects as go
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=monthly_pivot.index.astype(str),
                            y=monthly_pivot['Resultado de Caixa'],
                            mode='lines+markers',
                            name='Resultado de Caixa',
                            line=dict(width=4, color='green'),
                            fill='tonexty'
                        ))
                        
                        # Adicionar linha zero
                        fig.add_hline(y=0, line_dash="dash", line_color="red", opacity=0.7)
                        
                        fig.update_layout(
                            title="Resultado de Caixa Mensal",
                            xaxis_title="Mês/Ano",
                            yaxis_title="Valor (R$)",
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Gráfico de barras - Componentes principais
                    import plotly.express as px
                    
                    # Preparar dados para gráfico de barras
                    key_columns = [col for col in ['Total OPERACIONAL', 'Despesas Administrativas', 'IMPOSTOS'] if col in monthly_pivot.columns]
                    if key_columns:
                        monthly_melted = monthly_pivot[key_columns].reset_index().melt(
                            id_vars='month_year', 
                            var_name='Categoria', 
                            value_name='Valor'
                        )
                        monthly_melted['month_year'] = monthly_melted['month_year'].astype(str)
                        
                        fig_bar = px.bar(
                            monthly_melted,
                            x='month_year',
                            y='Valor',
                            color='Categoria',
                            title="Componentes Principais por Mês",
                            labels={'month_year': 'Mês/Ano', 'Valor': 'Valor (R$)'}
                        )
                        fig_bar.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_bar, use_container_width=True)
                
                # Resumo dos totais
                st.subheader("📊 Resumo Geral")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if 'Total OPERACIONAL' in monthly_pivot.columns:
                        total_operacional = monthly_pivot['Total OPERACIONAL'].sum()
                        st.metric("Total OPERACIONAL", format_currency(total_operacional))
                
                with col2:
                    if 'Despesas Administrativas' in monthly_pivot.columns:
                        total_desp_admin = monthly_pivot['Despesas Administrativas'].sum()
                        st.metric("Despesas Administrativas", format_currency(total_desp_admin))
                
                with col3:
                    if 'IMPOSTOS' in monthly_pivot.columns:
                        total_impostos = monthly_pivot['IMPOSTOS'].sum()
                        st.metric("Total IMPOSTOS", format_currency(total_impostos))
                
                with col4:
                    if 'Resultado de Caixa' in monthly_pivot.columns:
                        resultado_total = monthly_pivot['Resultado de Caixa'].sum()
                        st.metric("Resultado Total", format_currency(resultado_total))
                
                # Detalhamento OPERACIONAL
                st.subheader("🔍 Detalhamento OPERACIONAL")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if 'Recebimento de Grãos' in monthly_pivot.columns:
                        recebimento_graos = monthly_pivot['Recebimento de Grãos'].sum()
                        st.metric("Recebimento de Grãos", format_currency(recebimento_graos))
                
                with col2:
                    if 'Pagamento de Grãos' in monthly_pivot.columns:
                        pagamento_graos = monthly_pivot['Pagamento de Grãos'].sum()
                        st.metric("Pagamento de Grãos", format_currency(pagamento_graos))
                
                with col3:
                    if 'Pagamento de Frete' in monthly_pivot.columns:
                        pagamento_frete = monthly_pivot['Pagamento de Frete'].sum()
                        st.metric("Pagamento de Frete", format_currency(pagamento_frete))
            
            else:
                st.info("Nenhum dado encontrado para análise mensal de fluxo de caixa.")
        
        else:
            if not date_column_found:
                st.warning("Campo 'date' não encontrado ou inválido. Não é possível realizar análise mensal.")
                
                # Mostrar análise simples por categoria se possível
                if 'category_name' in df_filtered.columns and 'value' in df_filtered.columns:
                    st.subheader("📊 Análise por Categoria (sem data)")
                    
                    category_summary = df_filtered.groupby('category_name')['value'].sum().sort_values(ascending=False)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Totais por Categoria:**")
                        for category, value in category_summary.items():
                            st.write(f"- {category}: {format_currency(value)}")
                    
                    with col2:
                        if len(category_summary) > 0:
                            import plotly.express as px
                            fig = px.pie(
                                values=category_summary.abs(),
                                names=category_summary.index,
                                title="Distribuição por Categoria"
                            )
                            st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum dado após aplicar filtros.")
            
    else:
        st.info("Nenhum dado financeiro encontrado.")


if __name__ == "__main__":
    show_financeiro_page()

