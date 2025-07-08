"""
Script para testar conexão com MongoDB e validar estrutura das coleções
"""
import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

from config.database import DatabaseConfig

def test_connection():
    """Testa conexão e estrutura das coleções"""
    print("🔄 Testando conexão com MongoDB...")
    
    # Criar instância de configuração
    db_config = DatabaseConfig()
    
    # Tentar conectar
    if not db_config.connect():
        print("❌ Falha na conexão")
        return False
    
    print("✅ Conexão estabelecida com sucesso!")
    
    # Testar coleções
    print("\n📊 Testando coleções...")
    try:
        # Listar bancos de dados disponíveis
        databases = db_config.client.list_database_names()
        print(f"📁 Bancos disponíveis: {databases}")
        
        # Verificar se o banco fox existe
        fox_db = db_config.client['fox']
        print(f"🎯 Banco fox selecionado")
        
        # Listar coleções do banco fox
        collections = fox_db.list_collection_names()
        print(f"📋 Coleções disponíveis no banco fox: {collections}")
        
        # Verificar coleções específicas
        target_collections = ['ticketv2', 'orderv2']
        
        for collection_name in target_collections:
            if collection_name in collections:
                collection = fox_db[collection_name]
                count = collection.count_documents({})
                print(f"✅ {collection_name}: {count} documentos")
                
                # Mostrar exemplo de documento
                sample = collection.find_one()
                if sample:
                    print(f"📄 Exemplo de documento em {collection_name}:")
                    # Mostrar apenas as chaves principais
                    keys = list(sample.keys())[:10]  # Primeiras 10 chaves
                    print(f"   Campos: {keys}")
                else:
                    print(f"⚠️  Nenhum documento encontrado em {collection_name}")
            else:
                print(f"❌ Coleção {collection_name} não encontrada")
        
        # Verificar subcoleções de ticketv2
        if 'ticketv2' in collections:
            print("\n🔍 Verificando subcoleções de ticketv2...")
            ticketv2_collection = fox_db['ticketv2']
            
            # Tentar acessar transactions
            try:
                # No MongoDB, subcoleções são acessadas como coleções separadas
                # Vamos verificar se existem coleções com nomes como ticketv2.transactions.destinationOrder
                all_collections = fox_db.list_collection_names()
                
                transaction_collections = [col for col in all_collections if 'transaction' in col.lower()]
                print(f"📁 Coleções relacionadas a transactions: {transaction_collections}")
                
                # Procurar especificamente pelas coleções mencionadas
                dest_collection_name = None
                origin_collection_name = None
                
                for col in all_collections:
                    if 'destination' in col.lower() and 'order' in col.lower():
                        dest_collection_name = col
                    if 'origin' in col.lower() and 'order' in col.lower():
                        origin_collection_name = col
                
                if dest_collection_name:
                    dest_count = fox_db[dest_collection_name].count_documents({})
                    print(f"📊 {dest_collection_name}: {dest_count} documentos")
                    
                    dest_sample = fox_db[dest_collection_name].find_one()
                    if dest_sample:
                        print(f"📄 Exemplo {dest_collection_name}:")
                        print(f"   Campos: {list(dest_sample.keys())[:10]}")
                
                if origin_collection_name:
                    origin_count = fox_db[origin_collection_name].count_documents({})
                    print(f"📊 {origin_collection_name}: {origin_count} documentos")
                    
                    origin_sample = fox_db[origin_collection_name].find_one()
                    if origin_sample:
                        print(f"📄 Exemplo {origin_collection_name}:")
                        print(f"   Campos: {list(origin_sample.keys())[:10]}")
                
                if not dest_collection_name and not origin_collection_name:
                    print("⚠️  Não foram encontradas coleções de destination/origin orders")
                    print(f"📋 Todas as coleções: {all_collections}")
                    
            except Exception as e:
                print(f"⚠️  Erro ao acessar subcoleções: {e}")
        
    except Exception as e:
        print(f"❌ Erro ao testar coleções: {e}")
        return False
    
    # Fechar conexão
    db_config.close_connection()
    
    print("\n✅ Teste de conexão concluído com sucesso!")
    return True

if __name__ == "__main__":
    test_connection()

