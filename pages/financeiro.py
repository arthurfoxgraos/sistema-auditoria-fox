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
        
        # Análise Mensal - ENTRADAS, SAÍDAS e SALDO DE CAIXA
        st.subheader("📅 Detalhamento Mensal")
        
        if date_column_found and not df_filtered.empty:
            # Criar coluna de mês/ano
            df_filtered['month_year'] = df_filtered['date'].dt.to_period('M')
            
            # Agrupar por mês e separar entradas/saídas
            monthly_summary = df_filtered.groupby('month_year').agg({
                'value': lambda x: [x[x > 0].sum(), x[x < 0].sum(), x.sum()]
            }).reset_index()
            
            # Expandir os valores em colunas separadas
            monthly_summary[['ENTRADAS', 'SAÍDAS', 'SALDO DE CAIXA']] = pd.DataFrame(
                monthly_summary['value'].tolist(), 
                index=monthly_summary.index
            )
            
            # Remover coluna temporária
            monthly_summary = monthly_summary.drop('value', axis=1)
            
            # Ordenar por data
            monthly_summary = monthly_summary.sort_values('month_year')
            
            # Formatar mês/ano para exibição
            monthly_summary['Mês/Ano'] = monthly_summary['month_year'].astype(str)
            
            # Criar DataFrame final para exibição
            display_df = monthly_summary[['Mês/Ano', 'ENTRADAS', 'SAÍDAS', 'SALDO DE CAIXA']].copy()
            
            # Formatar valores monetários
            for col in ['ENTRADAS', 'SAÍDAS', 'SALDO DE CAIXA']:
                display_df[col] = display_df[col].apply(format_currency)
            
            # Exibir tabela
            st.dataframe(
                display_df, 
                use_container_width=True, 
                height=400,
                hide_index=True
            )
            
            # Totais gerais
            st.subheader("📊 Totais Gerais")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_entradas = monthly_summary['ENTRADAS'].sum()
                st.metric("💰 Total ENTRADAS", format_currency(total_entradas))
            
            with col2:
                total_saidas = monthly_summary['SAÍDAS'].sum()
                st.metric("💸 Total SAÍDAS", format_currency(total_saidas))
            
            with col3:
                saldo_total = monthly_summary['SALDO DE CAIXA'].sum()
                st.metric("📈 SALDO TOTAL", format_currency(saldo_total))
        
        else:
            if not date_column_found:
                st.warning("Campo 'date' não encontrado ou inválido. Não é possível realizar análise mensal.")
            else:
                st.info("Nenhum dado após aplicar filtros.")
            
    else:
        st.info("Nenhum dado financeiro encontrado.")


if __name__ == "__main__":
    show_financeiro_page()

