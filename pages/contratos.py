"""
Página de Contratos - Sistema de Auditoria FOX
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from src.database_service import DatabaseService
from config.database import DatabaseConfig

@st.cache_data(ttl=60)
def load_contratos_data():
    """Carrega dados de contratos do MongoDB"""
    try:
        db_config = DatabaseConfig()
        if db_config.connect():
            collections = db_config.get_collections()
            db_service = DatabaseService(collections)
            
            # Buscar contratos da orderv2
            pipeline = [
                # Lookup com users para buyer
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "buyer",
                        "foreignField": "_id",
                        "as": "buyer_info"
                    }
                },
                # Lookup com users para seller
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "seller",
                        "foreignField": "_id",
                        "as": "seller_info"
                    }
                },
                # Lookup com grains
                {
                    "$lookup": {
                        "from": "grains",
                        "localField": "grain",
                        "foreignField": "_id",
                        "as": "grain_info"
                    }
                },
                # Adicionar campos calculados
                {
                    "$addFields": {
                        "buyer_name": {
                            "$ifNull": [
                                {"$arrayElemAt": ["$buyer_info.name", 0]},
                                {"$arrayElemAt": ["$buyer_info.companyName", 0]}
                            ]
                        },
                        "seller_name": {
                            "$ifNull": [
                                {"$arrayElemAt": ["$seller_info.name", 0]},
                                {"$arrayElemAt": ["$seller_info.companyName", 0]}
                            ]
                        },
                        "grain_name": {"$arrayElemAt": ["$grain_info.name", 0]},
                        "contract_type": {
                            "$cond": {
                                "if": {"$eq": ["$isGrain", True]},
                                "then": "🌾 Grão",
                                "else": {
                                    "$cond": {
                                        "if": {"$eq": ["$isFreight", True]},
                                        "then": "🚛 Frete",
                                        "else": "❓ Indefinido"
                                    }
                                }
                            }
                        },
                        "status_display": {
                            "$cond": {
                                "if": {"$eq": ["$isDone", True]},
                                "then": "✅ Concluído",
                                "else": {
                                    "$cond": {
                                        "if": {"$eq": ["$isCanceled", True]},
                                        "then": "❌ Cancelado",
                                        "else": {
                                            "$cond": {
                                                "if": {"$eq": ["$isInProgress", True]},
                                                "then": "🔄 Em Progresso",
                                                "else": "⏳ Pendente"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                {"$sort": {"createdAt": -1}},
                {"$limit": 1000}
            ]
            
            results = list(db_service.orderv2.aggregate(pipeline))
            
            if results:
                df = pd.DataFrame(results)
                return df
            else:
                return pd.DataFrame()
                
    except Exception as e:
        st.error(f"Erro ao carregar dados de contratos: {e}")
        return pd.DataFrame()

def show_contratos_page():
    """Exibe a página de contratos"""
    st.title("📋 Contratos")
    
    # Carregar dados
    with st.spinner("Carregando dados de contratos..."):
        df_contratos = load_contratos_data()
    
    if df_contratos.empty:
        st.warning("Nenhum contrato encontrado.")
        return
    
    # Mostrar resultados
    st.subheader(f"📊 Resultados: {len(df_contratos)} contratos")
    
    # Preparar dados para exibição
    display_columns = []
    column_mapping = {
        '_id': 'ID',
        'createdAt': 'Data Criação',
        'buyer_name': 'Comprador',
        'seller_name': 'Vendedor',
        'grain_name': 'Grão',
        'contract_type': 'Tipo',
        'amount': 'Quantidade',
        'bagPrice': 'Preço/Saca',
        'deliveryDeadline': 'Prazo Entrega',
        'status_display': 'Status'
    }
    
    # Verificar quais colunas existem
    for col, display_name in column_mapping.items():
        if col in df_contratos.columns:
            display_columns.append(col)
    
    if display_columns:
        # Criar DataFrame para exibição
        df_display = df_contratos[display_columns].copy()
        df_display.columns = [column_mapping.get(col, col) for col in display_columns]
        
        # Formatar data se existir
        if 'Data Criação' in df_display.columns:
            df_display['Data Criação'] = pd.to_datetime(
                df_display['Data Criação'], errors='coerce'
            ).dt.strftime('%d/%m/%Y')
        
        # Formatar prazo de entrega se existir
        if 'Prazo Entrega' in df_display.columns:
            df_display['Prazo Entrega'] = pd.to_datetime(
                df_display['Prazo Entrega'], errors='coerce'
            ).dt.strftime('%d/%m/%Y')
        
        # Formatar preço por saca
        if 'Preço/Saca' in df_display.columns:
            df_display['Preço/Saca'] = df_display['Preço/Saca'].apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if pd.notnull(x) else "R$ 0,00"
            )
        
        # Formatar quantidade
        if 'Quantidade' in df_display.columns:
            df_display['Quantidade'] = df_display['Quantidade'].apply(
                lambda x: f"{int(x):,}".replace(',', '.') if pd.notnull(x) and x != 0 else "0"
            )
        
        # Exibir tabela
        st.dataframe(
            df_display,
            use_container_width=True,
            height=600
        )
    else:
        st.warning("Colunas solicitadas não encontradas nos dados.")
        st.dataframe(df_contratos, use_container_width=True)

if __name__ == "__main__":
    show_contratos_page()

