import streamlit as st
import pandas as pd
from src.database_service import DatabaseService

def format_currency(value):
    """Formatar valor como moeda brasileira"""
    if pd.isna(value) or value == 0:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_data(ttl=60)
def load_finances_data():
    db_service = DatabaseService()
    return db_service.get_finances_with_lookups()

def show_financeiro_page():
    st.title("💰 Financeiro")
    
    # Carregar dados
    df_finances = load_finances_data()
    
    if df_finances is not None and not df_finances.empty:
        # Converter coluna de data
        if 'date' in df_finances.columns:
            df_finances['date'] = pd.to_datetime(df_finances['date'], format='%Y%m%d%H%M%S', errors='coerce')
        
        # Filtros
        st.subheader("🔍 Filtros")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            users = sorted(df_finances['user_name'].dropna().unique())
            user_filter = st.selectbox("Usuário:", ["Todos"] + users)
        
        with col2:
            items = sorted(df_finances['category_item'].dropna().unique())
            item_filter = st.selectbox("Item:", ["Todos"] + items)
        
        with col3:
            if 'date' in df_finances.columns and not df_finances['date'].isna().all():
                years = sorted([int(year) for year in df_finances['date'].dt.year.dropna().unique()], reverse=True)
                year_options = ['Todos'] + [str(year) for year in years]
                year_filter = st.selectbox("Ano:", year_options)
            else:
                year_filter = "Todos"
        
        with col4:
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
        
        if user_filter != "Todos":
            df_filtered = df_filtered[df_filtered['user_name'] == user_filter]
        
        if item_filter != "Todos":
            df_filtered = df_filtered[df_filtered['category_item'] == item_filter]
        
        # Filtro por ano
        if year_filter != "Todos" and 'date' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['date'].dt.year == int(year_filter)]
        
        # Filtro por mês
        if month_filter != "Todos" and 'date' in df_filtered.columns:
            month_names_reverse = {v: k for k, v in month_names.items()}
            selected_month = month_names_reverse.get(month_filter)
            if selected_month:
                df_filtered = df_filtered[df_filtered['date'].dt.month == selected_month]
        
        # Mostrar total geral
        total_geral = df_filtered['value'].sum()
        st.metric("💰 Total Geral", format_currency(total_geral))
        
        # Separador
        st.divider()
        
        # Consolidado por categoria
        st.subheader("📊 Consolidado por Categoria")
        
        if 'category_name' in df_filtered.columns:
            consolidado = df_filtered.groupby('category_name').agg({
                'value': ['sum', 'count', 'mean']
            }).round(2)
            
            consolidado.columns = ['Total', 'Quantidade', 'Média']
            consolidado = consolidado.sort_values('Total', ascending=False)
            
            # Calcular percentuais
            total_abs = consolidado['Total'].abs().sum()
            if total_abs > 0:
                consolidado['Percentual'] = (consolidado['Total'].abs() / total_abs * 100).round(1)
            else:
                consolidado['Percentual'] = 0
            
            # Formatar para exibição
            consolidado_display = consolidado.copy()
            consolidado_display['Total'] = consolidado_display['Total'].apply(format_currency)
            consolidado_display['Média'] = consolidado_display['Média'].apply(format_currency)
            consolidado_display['Percentual'] = consolidado_display['Percentual'].apply(lambda x: f"{x}%")
            
            st.dataframe(consolidado_display, use_container_width=True, height=400)
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                if len(consolidado) > 0:
                    import plotly.express as px
                    fig = px.pie(
                        values=consolidado['Total'].abs(),
                        names=consolidado.index,
                        title="Distribuição por Categoria"
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
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
        
        # Separador
        st.divider()
        
        # Análise por mês - Estrutura Operacional e Administrativa
        st.subheader("📅 Análise Mensal - Fluxo de Caixa")
        
        if 'date' in df_filtered.columns and not df_filtered['date'].isna().all():
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
                        return 'OPERACIONAL - Recebimento de Grãos'
                    elif ('pagamento' in item or value < 0) and ('grão' in item or 'soja' in item or 'milho' in item):
                        return 'OPERACIONAL - Pagamento de Grãos'
                    elif 'frete' in item:
                        return 'OPERACIONAL - Pagamento de Frete'
                    else:
                        return 'OPERACIONAL - Outros'
                elif category_name == 'DESPESAS ADMINISTRATIVAS':
                    return 'Despesas Administrativas'
                elif category_name in ['IMPOSTOS', 'FINANCIAMENTO', 'INVESTIMENTOS']:
                    return category_name
                else:
                    # Fallback baseado no valor e item
                    if value > 0:
                        return 'OPERACIONAL - Recebimento de Grãos'
                    else:
                        return 'OPERACIONAL - Outros'
            
            # Aplicar categorização
            df_filtered['financial_category'] = df_filtered.apply(categorize_financial_flow, axis=1)
            
            # Agrupar por mês e categoria
            monthly_analysis = df_filtered.groupby(['month_year', 'financial_category'])['value'].sum().reset_index()
            
            if not monthly_analysis.empty:
                # Pivot para ter categorias como colunas
                monthly_pivot = monthly_analysis.pivot(index='month_year', columns='financial_category', values='value').fillna(0)
                
                # Definir colunas principais na ordem desejada
                main_columns = [
                    'OPERACIONAL - Recebimento de Grãos',
                    'OPERACIONAL - Pagamento de Grãos', 
                    'OPERACIONAL - Pagamento de Frete',
                    'OPERACIONAL - Outros',
                    'Despesas Administrativas',
                    'IMPOSTOS',
                    'FINANCIAMENTO',
                    'INVESTIMENTOS'
                ]
                
                # Garantir que as colunas existam
                for col in main_columns:
                    if col not in monthly_pivot.columns:
                        monthly_pivot[col] = 0
                
                # Calcular totais operacionais
                monthly_pivot['Total OPERACIONAL'] = (
                    monthly_pivot['OPERACIONAL - Recebimento de Grãos'] + 
                    monthly_pivot['OPERACIONAL - Pagamento de Grãos'] + 
                    monthly_pivot['OPERACIONAL - Pagamento de Frete'] + 
                    monthly_pivot['OPERACIONAL - Outros']
                )
                
                # Calcular resultado de caixa (todas as entradas - todas as saídas)
                monthly_pivot['Resultado de Caixa'] = monthly_pivot.sum(axis=1)
                
                # Ordenar por data
                monthly_pivot = monthly_pivot.sort_index()
                
                # Formatar índice para exibição
                monthly_pivot.index = monthly_pivot.index.astype(str)
                
                # Criar DataFrame para exibição com estrutura hierárquica
                display_columns = [
                    'OPERACIONAL - Recebimento de Grãos',
                    'OPERACIONAL - Pagamento de Grãos',
                    'OPERACIONAL - Pagamento de Frete', 
                    'Total OPERACIONAL',
                    'Despesas Administrativas',
                    'IMPOSTOS',
                    'FINANCIAMENTO',
                    'INVESTIMENTOS',
                    'Resultado de Caixa'
                ]
                
                monthly_display = monthly_pivot[display_columns].copy()
                
                # Formatar valores monetários
                for col in monthly_display.columns:
                    monthly_display[col] = monthly_display[col].apply(lambda x: format_currency(x))
                
                # Exibir tabela
                st.dataframe(monthly_display, use_container_width=True, height=500)
                
                # Gráficos
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico de linha - Resultado de Caixa
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
                    key_columns = ['Total OPERACIONAL', 'Despesas Administrativas', 'IMPOSTOS']
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
                    total_operacional = monthly_pivot['Total OPERACIONAL'].sum()
                    st.metric("Total OPERACIONAL", format_currency(total_operacional))
                
                with col2:
                    total_desp_admin = monthly_pivot['Despesas Administrativas'].sum()
                    st.metric("Despesas Administrativas", format_currency(total_desp_admin))
                
                with col3:
                    total_impostos = monthly_pivot['IMPOSTOS'].sum()
                    st.metric("Total IMPOSTOS", format_currency(total_impostos))
                
                with col4:
                    resultado_total = monthly_pivot['Resultado de Caixa'].sum()
                    st.metric("Resultado Total", format_currency(resultado_total))
                
                # Detalhamento OPERACIONAL
                st.subheader("🔍 Detalhamento OPERACIONAL")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    recebimento_graos = monthly_pivot['OPERACIONAL - Recebimento de Grãos'].sum()
                    st.metric("Recebimento de Grãos", format_currency(recebimento_graos))
                
                with col2:
                    pagamento_graos = monthly_pivot['OPERACIONAL - Pagamento de Grãos'].sum()
                    st.metric("Pagamento de Grãos", format_currency(pagamento_graos))
                
                with col3:
                    pagamento_frete = monthly_pivot['OPERACIONAL - Pagamento de Frete'].sum()
                    st.metric("Pagamento de Frete", format_currency(pagamento_frete))
            
            else:
                st.info("Nenhum dado encontrado para análise mensal de fluxo de caixa.")
        
        else:
            st.warning("Campo 'date' não encontrado ou vazio para análise mensal.")
            
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados.")


if __name__ == "__main__":
    show_financeiro_page()

