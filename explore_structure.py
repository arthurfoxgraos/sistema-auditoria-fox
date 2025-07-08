"""
Script para explorar a estrutura das coleções ticketv2 e orderv2
"""
import sys
import os
from pprint import pprint

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

from config.database import DatabaseConfig

def explore_collections():
    """Explora a estrutura das coleções"""
    print("🔍 Explorando estrutura das coleções...")
    
    # Criar instância de configuração
    db_config = DatabaseConfig()
    
    # Tentar conectar
    if not db_config.connect():
        print("❌ Falha na conexão")
        return False
    
    fox_db = db_config.client['fox']
    
    # Explorar ticketv2
    print("\n📊 Explorando ticketv2...")
    ticketv2 = fox_db['ticketv2']
    
    # Pegar alguns documentos de exemplo
    samples = list(ticketv2.find().limit(3))
    
    for i, sample in enumerate(samples):
        print(f"\n📄 Documento {i+1} de ticketv2:")
        print("Campos principais:")
        for key, value in sample.items():
            if key == '_id':
                print(f"  {key}: {value}")
            elif isinstance(value, dict):
                print(f"  {key}: (objeto com {len(value)} campos)")
                # Mostrar subcampos se for pequeno
                if len(value) <= 5:
                    for subkey in value.keys():
                        print(f"    - {subkey}")
            elif isinstance(value, list):
                print(f"  {key}: (lista com {len(value)} itens)")
            else:
                print(f"  {key}: {value}")
    
    # Verificar se existe campo transactions
    print("\n🔍 Verificando campo 'transactions' em ticketv2...")
    sample_with_transactions = ticketv2.find_one({"transactions": {"$exists": True}})
    
    if sample_with_transactions:
        print("✅ Encontrado documento com campo 'transactions'")
        transactions = sample_with_transactions.get('transactions', {})
        print(f"Estrutura de transactions: {list(transactions.keys()) if isinstance(transactions, dict) else type(transactions)}")
        
        # Verificar se existem destinationOrder e originOrder
        if isinstance(transactions, dict):
            if 'destinationOrder' in transactions:
                print("✅ Encontrado destinationOrder")
                dest_order = transactions['destinationOrder']
                print(f"Tipo: {type(dest_order)}")
                if isinstance(dest_order, dict):
                    print(f"Campos: {list(dest_order.keys())}")
                elif isinstance(dest_order, list):
                    print(f"Lista com {len(dest_order)} itens")
                    if dest_order:
                        print(f"Primeiro item: {list(dest_order[0].keys()) if isinstance(dest_order[0], dict) else type(dest_order[0])}")
            
            if 'originOrder' in transactions:
                print("✅ Encontrado originOrder")
                origin_order = transactions['originOrder']
                print(f"Tipo: {type(origin_order)}")
                if isinstance(origin_order, dict):
                    print(f"Campos: {list(origin_order.keys())}")
                elif isinstance(origin_order, list):
                    print(f"Lista com {len(origin_order)} itens")
                    if origin_order:
                        print(f"Primeiro item: {list(origin_order[0].keys()) if isinstance(origin_order[0], dict) else type(origin_order[0])}")
    else:
        print("❌ Não encontrado campo 'transactions' em ticketv2")
    
    # Explorar ticketv2_transactions
    print("\n📊 Explorando ticketv2_transactions...")
    ticketv2_trans = fox_db['ticketv2_transactions']
    
    trans_sample = ticketv2_trans.find_one()
    if trans_sample:
        print("📄 Exemplo de documento em ticketv2_transactions:")
        for key, value in trans_sample.items():
            if key == '_id':
                print(f"  {key}: {value}")
            elif isinstance(value, dict):
                print(f"  {key}: (objeto com {len(value)} campos)")
                if len(value) <= 5:
                    for subkey in value.keys():
                        print(f"    - {subkey}")
            elif isinstance(value, list):
                print(f"  {key}: (lista com {len(value)} itens)")
            else:
                print(f"  {key}: {value}")
    
    # Explorar orderv2
    print("\n📊 Explorando orderv2...")
    orderv2 = fox_db['orderv2']
    
    order_sample = orderv2.find_one()
    if order_sample:
        print("📄 Exemplo de documento em orderv2:")
        for key, value in order_sample.items():
            if key == '_id':
                print(f"  {key}: {value}")
            elif key in ['buyer', 'seller']:
                print(f"  {key}: (objeto)")
                if isinstance(value, dict):
                    for subkey in list(value.keys())[:5]:  # Primeiros 5 campos
                        print(f"    - {subkey}: {value[subkey]}")
            elif isinstance(value, dict):
                print(f"  {key}: (objeto com {len(value)} campos)")
            elif isinstance(value, list):
                print(f"  {key}: (lista com {len(value)} itens)")
            else:
                print(f"  {key}: {value}")
    
    # Verificar campos específicos mencionados
    print("\n🔍 Verificando campos específicos...")
    
    # Verificar amount em ticketv2
    amount_sample = ticketv2.find_one({"amount": {"$exists": True}})
    if amount_sample:
        print(f"✅ Campo 'amount' encontrado: {amount_sample.get('amount')}")
    else:
        print("❌ Campo 'amount' não encontrado em ticketv2")
    
    # Verificar loadingDate em ticketv2
    loading_date_sample = ticketv2.find_one({"loadingDate": {"$exists": True}})
    if loading_date_sample:
        print(f"✅ Campo 'loadingDate' encontrado: {loading_date_sample.get('loadingDate')}")
    else:
        print("❌ Campo 'loadingDate' não encontrado em ticketv2")
    
    # Fechar conexão
    db_config.close_connection()
    
    print("\n✅ Exploração concluída!")
    return True

if __name__ == "__main__":
    explore_collections()

