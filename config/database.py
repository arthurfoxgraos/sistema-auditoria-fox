"""
Configuração de conexão com MongoDB
"""
import os
from pymongo import MongoClient

class DatabaseConfig:
    """Configuração e conexão com MongoDB"""
    
    def __init__(self):
        self.connection_string = "mongodb+srv://doadmin:5vk9a08N2tX3e64U@foxdigital-e8bf0024.mongo.ondigitalocean.com/admin?authSource=admin&replicaSet=foxdigital"
        self.database_name = "fox"
        self.client = None
        self.db = None
    
    def connect(self):
        """Estabelece conexão com MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            
            # Testar conexão
            self.client.admin.command('ping')
            print("✅ Conexão com MongoDB estabelecida com sucesso!")
            
            # Selecionar banco de dados
            self.db = self.client[self.database_name]
            
            return True
            
        except Exception as e:
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
            'orderv2': self.db['orderv2'],
            'users': self.db['users'],
            'provisionings': self.db['provisionings'],
            'grains': self.db['grains'],
            'finances': self.db['finances'],
            'finances_categories': self.db['finances_categories'],
            'addresses': self.db['addresses'],
            'cities': self.db['cities']
        }
        
        return collections
    
    def test_collections(self):
        """Testa se as coleções existem e têm dados"""
        collections_to_test = ['ticketv2', 'ticketv2_transactions', 'orderv2', 'users', 'provisionings', 'addresses']
        results = {}
        
        for collection_name in collections_to_test:
            try:
                collection = self.db[collection_name]
                count = collection.count_documents({})
                results[collection_name] = count
                print(f"📊 {collection_name}: {count:,} documentos")
            except Exception as e:
                print(f"❌ Erro ao acessar {collection_name}: {e}")
                results[collection_name] = 0
        
        return results
    
    def close_connection(self):
        """Fecha conexão com MongoDB"""
        if self.client:
            self.client.close()
            print("🔌 Conexão com MongoDB fechada")

def get_database_connection():
    """Função helper para obter conexão com banco"""
    db_config = DatabaseConfig()
    if db_config.connect():
        return db_config
    return None

