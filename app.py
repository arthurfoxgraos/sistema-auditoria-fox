"""
Sistema de Auditoria FOX - Versão Modular
Menus: Cargas, Provisionamento, Financeiro e Contratos
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import datetime
import os
import sys

# Adicionar diretórios ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import get_database_connection
from src.database_service import DatabaseService
from src.database_service_provisioning import ProvisioningService

# Configuração da página
st.set_page_config(
    page_title="Sistema FOX - Auditoria Completa",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    /* Margem full - usar toda largura da tela */
    .main .block-container {
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-top: 1rem;
    }
    
    /* Espaçamento entre elementos */
    .stSelectbox > div > div {
        margin-bottom: 0.5rem;
    }
    
    /* Melhorar espaçamento dos filtros */
    .stColumn {
        padding: 0 0.5rem;
    }
    
    /* Remover padding extra */
    .stApp > header {
        background-color: transparent;
    }
    
    /* Maximizar largura dos dataframes */
    .stDataFrame {
        width: 100%;
    }
    
    /* Melhorar aparência dos selectbox */
    .stSelectbox label {
        font-weight: 600;
        color: #262730;
    }
    
    /* Espaçamento entre seções */
    .stSubheader {
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .alert-low {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Função principal da aplicação"""
    
    # Header
    st.markdown('<h1 class="main-header">🚛 Sistema FOX - Auditoria Completa</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("📊 Navegação")
    
    # Menu de navegação completo
    page = st.sidebar.selectbox(
        "Selecione uma página:",
        [
            "🚚 Cargas",
            "📦 Provisionamento",
            "💰 Financeiro",
            "📋 Contratos"
        ]
    )
    
    # Roteamento de páginas
    if page == "🚚 Cargas":
        from pages.cargas import show_cargas_page
        show_cargas_page()
    elif page == "📦 Provisionamento":
        from pages.provisionamento import show_provisionamento_page
        show_provisionamento_page()
    elif page == "💰 Financeiro":
        from pages.financeiro import show_financeiro_page
        show_financeiro_page()
    elif page == "📋 Contratos":
        from pages.contratos import show_contratos_page
        show_contratos_page()

if __name__ == "__main__":
    main()

