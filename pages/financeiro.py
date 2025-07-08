"""
Página de Financeiro - Sistema de Auditoria FOX
"""
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

def show_financeiro_page():
    """Exibe a página de financeiro"""
    st.title("💰 Financeiro")
    
    # Carregar dados
    with st.spinner("Carregando dados financeiros..."):
        df_finances = load_finances_data()
    
    if df_finances.empty:
        st.warning("Nenhum dado financeiro encontrado.")
        return
    
    # Métricas principais
    st.subheader("📊 Resumo Financeiro")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_registros = len(df_finances)
        st.metric(
            label="📋 Total de Registros",
            value=f"{total_registros:,}"
        )
    
    with col2:
        total_valor = df_finances['value'].sum() if 'value' in df_finances.columns else 0
        st.metric(
            label="💰 Valor Total",
            value=f"R$ {total_valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )
    
    with col3:
        if 'status' in df_finances.columns:
            conciliados = len(df_finances[df_finances['status'] == 'conciliado'])
            percentual = (conciliados / total_registros * 100) if total_registros > 0 else 0
            st.metric(
                label="✅ Conciliados",
                value=f"{conciliados}",
                delta=f"{percentual:.1f}%"
            )
    
    with col4:
        if 'category_type' in df_finances.columns:
            variaveis = len(df_finances[df_finances['category_type'] == 'variavel'])
            st.metric(
                label="📈 Variáveis",
                value=f"{variaveis}"
            )
    
    # Filtros
    st.subheader("🔍 Filtros")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Filtro por status
        if 'status' in df_finances.columns:
            status_options = ['Todos'] + list(df_finances['status'].dropna().unique())
            status_filter = st.selectbox("Status:", status_options)
        else:
            status_filter = "Todos"
    
    with col2:
        # Filtro por categoria
        if 'category_name' in df_finances.columns:
            category_options = ['Todos'] + list(df_finances['category_name'].dropna().unique())
            category_filter = st.selectbox("Categoria:", category_options)
        else:
            category_filter = "Todos"
    
    with col3:
        # Filtro por tipo
        if 'category_type' in df_finances.columns:
            type_options = ['Todos'] + list(df_finances['category_type'].dropna().unique())
            type_filter = st.selectbox("Tipo:", type_options)
        else:
            type_filter = "Todos"
    
    with col4:
        # Filtro por usuário
        if 'user_name' in df_finances.columns:
            user_options = ['Todos'] + list(df_finances['user_name'].dropna().unique())
            user_filter = st.selectbox("Usuário:", user_options)
        else:
            user_filter = "Todos"
    
    # Aplicar filtros
    df_filtered = df_finances.copy()
    
    if status_filter != "Todos" and 'status' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['status'] == status_filter]
    
    if category_filter != "Todos" and 'category_name' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['category_name'] == category_filter]
    
    if type_filter != "Todos" and 'category_type' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['category_type'] == type_filter]
    
    if user_filter != "Todos" and 'user_name' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['user_name'] == user_filter]
    
    # Mostrar resultados
    st.subheader(f"📊 Resultados: {len(df_filtered)} registros financeiros")
    
    if not df_filtered.empty:
        # Preparar dados para exibição
        display_columns = []
        column_mapping = {
            'date': 'Data',
            'name': 'Nome',
            'value': 'Valor',
            'status': 'Status',
            'category_name': 'Categoria',
            'category_item': 'Item',
            'category_type': 'Tipo',
            'user_name': 'Usuário',
            'bank': 'Banco',
            'account': 'Conta',
            'saldo': 'Saldo'
        }
        
        # Verificar quais colunas existem
        for col, display_name in column_mapping.items():
            if col in df_filtered.columns:
                display_columns.append(col)
        
        if display_columns:
            # Criar DataFrame para exibição
            df_display = df_filtered[display_columns].copy()
            df_display.columns = [column_mapping.get(col, col) for col in display_columns]
            
            # Formatar data se existir
            if 'Data' in df_display.columns:
                df_display['Data'] = pd.to_datetime(
                    df_display['Data'], errors='coerce'
                ).dt.strftime('%d/%m/%Y %H:%M')
            
            # Formatar valores monetários
            monetary_columns = ['Valor', 'Saldo']
            for col in monetary_columns:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(
                        lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notnull(x) else "R$ 0,00"
                    )
            
            # Exibir tabela
            st.dataframe(
                df_display,
                use_container_width=True,
                height=600
            )
        else:
            st.warning("Colunas solicitadas não encontradas nos dados.")
            st.dataframe(df_filtered, use_container_width=True)
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            if 'category_name' in df_filtered.columns:
                st.subheader("📈 Distribuição por Categoria")
                category_counts = df_filtered['category_name'].value_counts()
                
                if not category_counts.empty:
                    fig = px.pie(
                        values=category_counts.values,
                        names=category_counts.index,
                        title="Distribuição por Categoria"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'status' in df_filtered.columns:
                st.subheader("📊 Distribuição por Status")
                status_counts = df_filtered['status'].value_counts()
                
                if not status_counts.empty:
                    fig = px.bar(
                        x=status_counts.index,
                        y=status_counts.values,
                        title="Distribuição por Status"
                    )
                    fig.update_layout(
                        xaxis_title="Status",
                        yaxis_title="Quantidade"
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("Nenhum registro encontrado com os filtros aplicados.")

if __name__ == "__main__":
    show_financeiro_page()

