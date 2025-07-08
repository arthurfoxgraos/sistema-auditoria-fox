"""
Configuração de conexão com MongoDB para o sistema de auditoria FOX
"""
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import streamlit as st

class DatabaseConfig:
    def __init__(self):
        # String de conexão MongoDB
        self.connection_string = "mongodb+srv://doadmin:5vk9a08N2tX3e64U@foxdigital-e8bf0024.mongo.ondigitalocean.com/admin?authSource=admin&replicaSet=foxdigital"
        self.client = None
        self.db = None
        
    def connect(self):
        """Estabelece conexão com MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            # Testa a conexão
            self.client.admin.command('ping')
            
            # Conecta ao banco de dados fox (onde estão os dados)
            self.db = self.client['fox']
            
            print("✅ Conexão com MongoDB estabelecida com sucesso!")
            return True
            
        except ConnectionFailure as e:
            print(f"❌ Erro ao conectar com MongoDB: {e}")
            return False
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return False
    
    def get_collections(self):
        """Retorna as coleções necessárias para auditoria"""
        if self.db is None:
            raise Exception("Conexão com banco não estabelecida")
            
        collections = {
            'ticketv2': self.db['ticketv2'],
            'ticketv2_transactions': self.db['ticketv2_transactions'],
            'orderv2': self.db['orderv2']
        }
        
        return collections
    
    def test_collections(self):
        """Testa se as coleções existem e têm dados"""
        try:
            collections = self.get_collections()
            results = {}
            
            for name, collection in collections.items():
                count = collection.count_documents({})
                results[name] = count
                print(f"📊 {name}: {count} documentos")
                
            return results
            
        except Exception as e:
            print(f"❌ Erro ao testar coleções: {e}")
            return {}
    
    def close_connection(self):
        """Fecha a conexão com MongoDB"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB fechada")

# Instância global para uso no Streamlit
@st.cache_resource
def get_database_connection():
    """Retorna conexão cached com MongoDB"""
    db_config = DatabaseConfig()
    if db_config.connect():
        return db_config
    return None

