"""
Script para testar os modelos com dados reais do MongoDB
"""
import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import DatabaseConfig
from src.database_service import DatabaseService
from src.data_models import DataProcessor

def test_models():
    """Testa os modelos com dados reais"""
    print("🔄 Testando modelos com dados reais...")
    
    # Conectar ao banco
    db_config = DatabaseConfig()
    if not db_config.connect():
        print("❌ Falha na conexão")
        return False
    
    # Obter coleções
    collections = db_config.get_collections()
    
    # Criar serviço de banco
    db_service = DatabaseService(collections)
    
    print("\n📊 Testando busca de tickets...")
    try:
        # Buscar alguns tickets
        tickets = db_service.get_tickets(limit=5)
        print(f"✅ Encontrados {len(tickets)} tickets")
        
        if tickets:
            print("\n📄 Exemplo de ticket:")
            ticket = tickets[0]
            print(f"  ID: {ticket._id}")
            print(f"  Número: {ticket.ticket}")
            print(f"  Status: {ticket.status}")
            print(f"  Data carregamento: {ticket.loadingDate}")
            print(f"  Quantidade: {ticket.amount}")
            print(f"  Valor frete: {ticket.freightValue}")
            print(f"  Destination Order: {ticket.destinationOrder}")
            print(f"  Origin Order: {ticket.originOrder}")
            
            # Converter para DataFrame
            df_tickets = DataProcessor.tickets_to_dataframe(tickets)
            print(f"\n📊 DataFrame de tickets: {df_tickets.shape}")
            print(f"Colunas: {list(df_tickets.columns)}")
            
    except Exception as e:
        print(f"❌ Erro ao testar tickets: {e}")
    
    print("\n📊 Testando busca de transações...")
    try:
        # Buscar transações
        transactions = db_service.get_ticket_transactions(limit=5)
        print(f"✅ Encontradas {len(transactions)} transações")
        
        if transactions:
            print("\n📄 Exemplo de transação:")
            trans = transactions[0]
            print(f"  ID: {trans._id}")
            print(f"  Quantidade: {trans.amount}")
            print(f"  Status: {trans.status}")
            print(f"  Destination Order: {trans.destinationOrder}")
            print(f"  Origin Order: {trans.originOrder}")
            print(f"  Ticket: {trans.ticket}")
            print(f"  Distância: {trans.distanceInKm}")
            
            # Converter para DataFrame
            df_trans = DataProcessor.ticket_transactions_to_dataframe(transactions)
            print(f"\n📊 DataFrame de transações: {df_trans.shape}")
            print(f"Colunas: {list(df_trans.columns)}")
            
    except Exception as e:
        print(f"❌ Erro ao testar transações: {e}")
    
    print("\n📊 Testando busca de pedidos...")
    try:
        # Buscar pedidos
        orders = db_service.get_orders(limit=5)
        print(f"✅ Encontrados {len(orders)} pedidos")
        
        if orders:
            print("\n📄 Exemplo de pedido:")
            order = orders[0]
            print(f"  ID: {order._id}")
            print(f"  Quantidade: {order.amount}")
            print(f"  Preço por saca: {order.bagPrice}")
            print(f"  Prazo entrega: {order.deliveryDeadline}")
            print(f"  Status flags: {order.status_flags}")
            print(f"  Buyer: {order.buyer.get('name', 'N/A') if order.buyer else 'N/A'}")
            print(f"  Seller: {order.seller.get('name', 'N/A') if order.seller else 'N/A'}")
            
            # Converter para DataFrame
            df_orders = DataProcessor.orders_to_dataframe(orders)
            print(f"\n📊 DataFrame de pedidos: {df_orders.shape}")
            print(f"Colunas: {list(df_orders.columns)}")
            
    except Exception as e:
        print(f"❌ Erro ao testar pedidos: {e}")
    
    print("\n📊 Testando métricas gerais...")
    try:
        # Buscar dados para métricas
        tickets = db_service.get_tickets(limit=100)
        orders = db_service.get_orders(limit=100)
        
        # Calcular métricas
        metricas = DataProcessor.calcular_metricas_gerais(tickets, orders)
        
        print("✅ Métricas calculadas:")
        for key, value in metricas.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"❌ Erro ao calcular métricas: {e}")
    
    print("\n📊 Testando resumo de pedidos...")
    try:
        summary = db_service.get_orders_summary()
        print("✅ Resumo de pedidos:")
        for key, value in summary.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"❌ Erro ao obter resumo: {e}")
    
    print("\n📊 Testando alertas de auditoria...")
    try:
        alerts = db_service.get_audit_alerts()
        print("✅ Alertas de auditoria:")
        for alert_type, alert_list in alerts.items():
            print(f"  {alert_type}: {len(alert_list)} itens")
            if alert_list:
                print(f"    Exemplo: {alert_list[0]}")
                
    except Exception as e:
        print(f"❌ Erro ao obter alertas: {e}")
    
    # Fechar conexão
    db_config.close_connection()
    
    print("\n✅ Teste dos modelos concluído!")
    return True

if __name__ == "__main__":
    test_models()

