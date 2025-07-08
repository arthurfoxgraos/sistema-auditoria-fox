"""
Utilitário para carregamento de dados com cache
"""
import streamlit as st
import sys
import os

# Configurar path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from config.database import get_database_connection
from src.database_service import DatabaseService
from src.database_service_provisioning import ProvisioningService

@st.cache_data
def load_data():
    """Carrega dados do banco com cache"""
    try:
        db_config = get_database_connection()
        if not db_config:
            st.error("❌ Erro ao conectar com o banco de dados")
            return None, None, None
        
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)
        
        # Carregar dados
        with st.spinner("Carregando dados..."):
            tickets = db_service.get_tickets(limit=1000)
            orders = db_service.get_orders(limit=1000)
            transactions = db_service.get_ticket_transactions(limit=1000)
        
        return tickets, orders, transactions
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return None, None, None

def get_database_services():
    """Retorna serviços de banco de dados"""
    try:
        db_config = get_database_connection()
        if not db_config:
            return None, None
        
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)
        prov_service = ProvisioningService(collections)
        
        return db_service, prov_service
    
    except Exception as e:
        st.error(f"❌ Erro ao conectar com banco: {e}")
        return None, None

