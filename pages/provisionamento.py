"""
Página de Provisionamento - Sistema de Auditoria FOX
"""
import streamlit as st
import pandas as pd
from config.database import get_database_connection
from src.database_service_provisioning import ProvisioningService

def show_provisionamento_page():
    """Mostra página de provisionamento"""
    st.header("📦 Gestão de Provisionamento")
    
    # Obter dados de provisionamento
    db_config = get_database_connection()
    if not db_config:
        st.error("❌ Erro ao conectar com o banco de dados")
        return
    
    collections = db_config.get_collections()
    prov_service = ProvisioningService(collections)
    
    # Carregar dados com a consulta específica
    with st.spinner("Carregando dados de provisionamento..."):
        df_provisionings = prov_service.get_simple_provisionings_table()
    
    if not df_provisionings.empty:
        st.subheader(f"📋 Provisionamentos: {len(df_provisionings)} registros")
        
        # Tabela simples conforme consulta
        st.dataframe(
            df_provisionings,
            use_container_width=True,
            column_config={
                'comprador': 'Comprador',
                'vendedor': 'Vendedor',
                'destinationOrder': 'Destination Order',
                'originOrder': 'Origin Order', 
                'amount': st.column_config.NumberColumn('Amount Remaining', format="%.0f"),
                'grain': 'Grain'
            }
        )
        
        # Estatísticas básicas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_amount = df_provisionings['amount'].sum()
            st.metric("📦 Total Amount Remaining", f"{total_amount:,.0f}")
        
        with col2:
            unique_buyers = df_provisionings['comprador'].nunique()
            st.metric("👥 Compradores Únicos", unique_buyers)
        
        with col3:
            unique_sellers = df_provisionings['vendedor'].nunique()
            st.metric("🏪 Vendedores Únicos", unique_sellers)
    
    else:
        st.warning("Nenhum dado de provisionamento encontrado.")
    
    db_config.close_connection()

if __name__ == "__main__":
    show_provisionamento_page()

