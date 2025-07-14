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
                    st.success(f"✅ {df_finances['date'].notna().sum()} registros com datas válidas encontrados.")
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
            st.warning("Filtro de ano não disponível - campo 'date' não encontrado.")
        
        # Aplicar filtro por ano
        df_filtered = df_finances.copy()
        if year_filter != "Todos" and date_column_found:
            df_filtered = df_filtered[df_filtered['date'].dt.year == int(year_filter)]
        
        # Análise Mensal por Categoria
        st.subheader("📅 Fluxo de Caixa Mensal por Categoria")
        
        if date_column_found and not df_filtered.empty:
            # Criar coluna de mês/ano
            df_filtered['month_year'] = df_filtered['date'].dt.to_period('M')
            
            # Definir categorias baseadas no valor e categoria
            def categorize_financial_flow(row):
                category_name = str(row.get('category_name', '')).upper()
                item = str(row.get('category_item', '')).lower()
                value = row.get('value', 0)
                
                # Separar por Entradas (valores positivos) e Saídas (valores negativos)
                if value > 0:
                    # ENTRADAS
                    if category_name == 'OPERACIONAL':
                        if 'grão' in item or 'soja' in item or 'milho' in item:
                            return 'ENTRADAS - Recebimento de Grãos'
                        else:
                            return 'ENTRADAS - Operacional Outros'
                    elif category_name == 'INVESTIMENTOS':
                        return 'ENTRADAS - Investimentos'
                    elif category_name == 'FINANCIAMENTO':
                        return 'ENTRADAS - Financiamento'
                    else:
                        return 'ENTRADAS - Outras Receitas'
                else:
                    # SAÍDAS
                    if category_name == 'OPERACIONAL':
                        if 'grão' in item or 'soja' in item or 'milho' in item:
                            return 'SAÍDAS - Pagamento de Grãos'
                        elif 'frete' in item:
                            return 'SAÍDAS - Pagamento de Frete'
                        else:
                            return 'SAÍDAS - Operacional Outros'
                    elif category_name == 'DESPESAS ADMINISTRATIVAS':
                        return 'SAÍDAS - Despesas Administrativas'
                    elif category_name == 'IMPOSTOS':
                        return 'SAÍDAS - Impostos'
                    elif category_name == 'FINANCIAMENTO':
                        return 'SAÍDAS - Financiamento'
                    elif category_name == 'INVESTIMENTOS':
                        return 'SAÍDAS - Investimentos'
                    else:
                        return 'SAÍDAS - Outras Despesas'
            
            # Aplicar categorização
            df_filtered['financial_category'] = df_filtered.apply(categorize_financial_flow, axis=1)
            
            # Agrupar por categoria e mês
            monthly_analysis = df_filtered.groupby(['financial_category', 'month_year'])['value'].sum().reset_index()
            
            if not monthly_analysis.empty:
                # Pivot para ter meses como colunas e categorias como linhas
                monthly_pivot = monthly_analysis.pivot(index='financial_category', columns='month_year', values='value').fillna(0)
                
                # Ordenar colunas (meses) cronologicamente
                monthly_pivot = monthly_pivot.sort_index(axis=1)
                
                # Calcular totais por categoria (linha)
                monthly_pivot['TOTAL'] = monthly_pivot.sum(axis=1)
                
                # Separar entradas e saídas para calcular totais
                entradas_mask = monthly_pivot.index.str.startswith('ENTRADAS')
                saidas_mask = monthly_pivot.index.str.startswith('SAÍDAS')
                
                # Calcular totais por mês (coluna)
                total_entradas = monthly_pivot[entradas_mask].sum()
                total_saidas = monthly_pivot[saidas_mask].sum()
                saldo_mensal = total_entradas + total_saidas  # Saídas já são negativas
                
                # Adicionar linhas de totais
                monthly_pivot.loc['TOTAL ENTRADAS'] = total_entradas
                monthly_pivot.loc['TOTAL SAÍDAS'] = total_saidas
                monthly_pivot.loc['SALDO DE CAIXA'] = saldo_mensal
                
                # Formatar colunas de mês para exibição
                monthly_pivot.columns = [str(col) if col != 'TOTAL' else 'TOTAL' for col in monthly_pivot.columns]
                
                # Criar DataFrame para exibição formatado
                display_df = monthly_pivot.copy()
                
                # Formatar valores monetários
                for col in display_df.columns:
                    display_df[col] = display_df[col].apply(format_currency)
                
                # Definir ordem das linhas para melhor visualização
                entradas_categories = [idx for idx in monthly_pivot.index if idx.startswith('ENTRADAS')]
                saidas_categories = [idx for idx in monthly_pivot.index if idx.startswith('SAÍDAS')]
                total_lines = ['TOTAL ENTRADAS', 'TOTAL SAÍDAS', 'SALDO DE CAIXA']
                
                # Reordenar linhas
                ordered_index = entradas_categories + saidas_categories + total_lines
                display_df = display_df.reindex([idx for idx in ordered_index if idx in display_df.index])
                
                # Aplicar estilo para destacar totais
                def highlight_totals(row):
                    if row.name in ['TOTAL ENTRADAS', 'TOTAL SAÍDAS', 'SALDO DE CAIXA']:
                        return ['background-color: #f0f0f0; font-weight: bold'] * len(row)
                    else:
                        return [''] * len(row)
                
                # Exibir tabela com estilo
                st.dataframe(
                    display_df.style.apply(highlight_totals, axis=1),
                    use_container_width=True,
                    height=600
                )
                
                # Resumo final
                st.subheader("📊 Resumo do Período")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_entradas_periodo = monthly_pivot.loc['TOTAL ENTRADAS', 'TOTAL']
                    st.metric("💰 Total ENTRADAS", format_currency(total_entradas_periodo))
                
                with col2:
                    total_saidas_periodo = monthly_pivot.loc['TOTAL SAÍDAS', 'TOTAL']
                    st.metric("💸 Total SAÍDAS", format_currency(total_saidas_periodo))
                
                with col3:
                    saldo_total_periodo = monthly_pivot.loc['SALDO DE CAIXA', 'TOTAL']
                    st.metric("📈 SALDO TOTAL", format_currency(saldo_total_periodo))
                
                # Nova seção: Despesas Administrativas Detalhadas
                st.subheader("🏢 Despesas Administrativas - Detalhamento por Item")
                
                # Filtrar apenas despesas administrativas
                df_desp_admin = df_filtered[
                    (df_filtered['category_name'].str.upper() == 'DESPESAS ADMINISTRATIVAS') |
                    (df_filtered['financial_category'] == 'SAÍDAS - Despesas Administrativas')
                ].copy()
                
                if not df_desp_admin.empty:
                    # Agrupar por item e mês
                    desp_admin_analysis = df_desp_admin.groupby(['category_item', 'month_year'])['value'].sum().reset_index()
                    
                    if not desp_admin_analysis.empty:
                        # Pivot para ter meses como colunas e itens como linhas
                        desp_admin_pivot = desp_admin_analysis.pivot(
                            index='category_item', 
                            columns='month_year', 
                            values='value'
                        ).fillna(0)
                        
                        # Ordenar colunas (meses) cronologicamente
                        desp_admin_pivot = desp_admin_pivot.sort_index(axis=1)
                        
                        # Calcular total por item (linha)
                        desp_admin_pivot['TOTAL'] = desp_admin_pivot.sum(axis=1)
                        
                        # Calcular total por mês (coluna)
                        total_por_mes = desp_admin_pivot.sum()
                        desp_admin_pivot.loc['TOTAL MENSAL'] = total_por_mes
                        
                        # Formatar colunas de mês para exibição
                        desp_admin_pivot.columns = [str(col) if col != 'TOTAL' else 'TOTAL' for col in desp_admin_pivot.columns]
                        
                        # Criar DataFrame para exibição formatado
                        desp_admin_display = desp_admin_pivot.copy()
                        
                        # Formatar valores monetários (valores negativos)
                        for col in desp_admin_display.columns:
                            desp_admin_display[col] = desp_admin_display[col].apply(format_currency)
                        
                        # Aplicar estilo para destacar total
                        def highlight_admin_totals(row):
                            if row.name == 'TOTAL MENSAL':
                                return ['background-color: #ffebee; font-weight: bold'] * len(row)
                            else:
                                return [''] * len(row)
                        
                        # Exibir tabela de despesas administrativas
                        st.dataframe(
                            desp_admin_display.style.apply(highlight_admin_totals, axis=1),
                            use_container_width=True,
                            height=400
                        )
                        
                        # Resumo das despesas administrativas
                        st.write("**📊 Resumo das Despesas Administrativas:**")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            total_desp_admin = desp_admin_pivot.loc['TOTAL MENSAL', 'TOTAL']
                            st.metric("💸 Total Despesas Admin", format_currency(total_desp_admin))
                        
                        with col2:
                            # Número de itens diferentes
                            num_itens = len(desp_admin_pivot.index) - 1  # -1 para excluir linha TOTAL MENSAL
                            st.metric("📋 Itens Diferentes", f"{num_itens}")
                        
                        with col3:
                            # Média mensal (excluindo coluna TOTAL)
                            meses_com_dados = [col for col in desp_admin_pivot.columns if col != 'TOTAL']
                            if meses_com_dados:
                                media_mensal = desp_admin_pivot.loc['TOTAL MENSAL', meses_com_dados].mean()
                                st.metric("📈 Média Mensal", format_currency(media_mensal))
                    
                    else:
                        st.info("Nenhuma despesa administrativa encontrada para análise detalhada.")
                else:
                    st.info("Nenhuma despesa administrativa encontrada no período selecionado.")
            
            else:
                st.info("Nenhum dado encontrado para análise mensal.")
        
        else:
            if not date_column_found:
                st.warning("Campo 'date' não encontrado ou inválido. Não é possível realizar análise mensal.")
            else:
                st.info("Nenhum dado após aplicar filtros.")
            
    else:
        st.info("Nenhum dado financeiro encontrado.")


if __name__ == "__main__":
    show_financeiro_page()

