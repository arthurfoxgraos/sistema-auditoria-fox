"""
Teste completo do sistema de auditoria FOX
"""
import sys
import os
import time
from datetime import datetime

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import DatabaseConfig
from src.database_service import DatabaseService
from src.audit_engine import AuditEngine
from src.data_models import DataProcessor

def test_database_connection():
    """Testa conexão com banco de dados"""
    print("🔄 Testando conexão com banco de dados...")
    
    try:
        db_config = DatabaseConfig()
        if not db_config.connect():
            print("❌ Falha na conexão com MongoDB")
            return False
        
        # Testar coleções
        collections = db_config.get_collections()
        results = db_config.test_collections()
        
        print("✅ Conexão com MongoDB estabelecida")
        for name, count in results.items():
            print(f"  📊 {name}: {count:,} documentos")
        
        db_config.close_connection()
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def test_data_loading():
    """Testa carregamento de dados"""
    print("\n🔄 Testando carregamento de dados...")
    
    try:
        db_config = DatabaseConfig()
        if not db_config.connect():
            return False
        
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)
        
        # Carregar dados
        start_time = time.time()
        
        tickets = db_service.get_tickets(limit=500)
        orders = db_service.get_orders(limit=500)
        transactions = db_service.get_ticket_transactions(limit=500)
        
        load_time = time.time() - start_time
        
        print(f"✅ Dados carregados em {load_time:.2f}s:")
        print(f"  🎫 Tickets: {len(tickets)}")
        print(f"  📋 Pedidos: {len(orders)}")
        print(f"  🔄 Transações: {len(transactions)}")
        
        # Testar conversão para DataFrame
        df_tickets = DataProcessor.tickets_to_dataframe(tickets)
        df_orders = DataProcessor.orders_to_dataframe(orders)
        df_transactions = DataProcessor.ticket_transactions_to_dataframe(transactions)
        
        print(f"✅ DataFrames criados:")
        print(f"  📊 Tickets: {df_tickets.shape}")
        print(f"  📊 Pedidos: {df_orders.shape}")
        print(f"  📊 Transações: {df_transactions.shape}")
        
        db_config.close_connection()
        return True
        
    except Exception as e:
        print(f"❌ Erro no carregamento: {e}")
        return False

def test_audit_engine():
    """Testa motor de auditoria"""
    print("\n🔄 Testando motor de auditoria...")
    
    try:
        db_config = DatabaseConfig()
        if not db_config.connect():
            return False
        
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)
        
        # Carregar dados para auditoria
        tickets = db_service.get_tickets(limit=300)
        orders = db_service.get_orders(limit=300)
        transactions = db_service.get_ticket_transactions(limit=300)
        
        # Executar auditoria
        start_time = time.time()
        
        audit_engine = AuditEngine()
        audit_result = audit_engine.run_full_audit(tickets, orders, transactions)
        
        audit_time = time.time() - start_time
        
        print(f"✅ Auditoria executada em {audit_time:.2f}s:")
        
        summary = audit_result["summary"]
        print(f"  🔍 Total issues: {summary['total_issues']}")
        print(f"  ⚙️ Operações criadas: {summary['total_operations']}")
        
        # Breakdown por severidade
        severity_breakdown = summary["severity_breakdown"]
        for severity, count in severity_breakdown.items():
            print(f"  📊 {severity}: {count}")
        
        # Testar alertas específicos
        alerts = db_service.get_audit_alerts()
        print(f"✅ Alertas específicos:")
        for alert_type, alert_list in alerts.items():
            print(f"  ⚠️ {alert_type}: {len(alert_list)}")
        
        db_config.close_connection()
        return True
        
    except Exception as e:
        print(f"❌ Erro na auditoria: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance():
    """Testa performance do sistema"""
    print("\n🔄 Testando performance...")
    
    try:
        db_config = DatabaseConfig()
        if not db_config.connect():
            return False
        
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)
        
        # Teste de carga progressiva
        limits = [100, 500, 1000]
        
        for limit in limits:
            start_time = time.time()
            
            tickets = db_service.get_tickets(limit=limit)
            orders = db_service.get_orders(limit=limit)
            transactions = db_service.get_ticket_transactions(limit=limit)
            
            load_time = time.time() - start_time
            
            # Executar auditoria
            audit_start = time.time()
            audit_engine = AuditEngine()
            audit_result = audit_engine.run_full_audit(tickets, orders, transactions)
            audit_time = time.time() - audit_start
            
            total_time = time.time() - start_time
            
            print(f"✅ Teste com {limit} registros:")
            print(f"  📥 Carregamento: {load_time:.2f}s")
            print(f"  🔍 Auditoria: {audit_time:.2f}s")
            print(f"  ⏱️ Total: {total_time:.2f}s")
            print(f"  📊 Issues encontrados: {audit_result['summary']['total_issues']}")
        
        db_config.close_connection()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de performance: {e}")
        return False

def test_data_quality():
    """Testa qualidade dos dados"""
    print("\n🔄 Testando qualidade dos dados...")
    
    try:
        db_config = DatabaseConfig()
        if not db_config.connect():
            return False
        
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)
        
        # Carregar dados
        tickets = db_service.get_tickets(limit=1000)
        orders = db_service.get_orders(limit=1000)
        
        # Calcular métricas de qualidade
        metricas = DataProcessor.calcular_metricas_gerais(tickets, orders)
        
        print("✅ Métricas de qualidade:")
        print(f"  📊 Taxa finalização tickets: {metricas['taxa_finalizacao']:.1%}")
        print(f"  📊 Taxa amount preenchido: {metricas['taxa_amount_preenchido']:.1%}")
        print(f"  📊 Taxa orders concluídos: {metricas['taxa_orders_done']:.1%}")
        
        # Verificar dados específicos
        tickets_sem_amount = len([t for t in tickets if t.amount is None])
        tickets_sem_loading_date = len([t for t in tickets if t.loadingDate is None])
        
        print(f"  ⚠️ Tickets sem amount: {tickets_sem_amount} ({tickets_sem_amount/len(tickets)*100:.1f}%)")
        print(f"  ⚠️ Tickets sem loading date: {tickets_sem_loading_date} ({tickets_sem_loading_date/len(tickets)*100:.1f}%)")
        
        # Verificar consistência de IDs
        destination_orders = set(t.destinationOrder for t in tickets if t.destinationOrder)
        origin_orders = set(t.originOrder for t in tickets if t.originOrder)
        order_ids = set(o._id for o in orders)
        
        missing_destination = destination_orders - order_ids
        missing_origin = origin_orders - order_ids
        
        print(f"  🔗 Destination orders inexistentes: {len(missing_destination)}")
        print(f"  🔗 Origin orders inexistentes: {len(missing_origin)}")
        
        db_config.close_connection()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de qualidade: {e}")
        return False

def test_business_logic():
    """Testa lógica de negócio"""
    print("\n🔄 Testando lógica de negócio...")
    
    try:
        db_config = DatabaseConfig()
        if not db_config.connect():
            return False
        
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)
        
        # Testar estatísticas por operação
        operation_stats = db_service.get_operation_statistics()
        print(f"✅ Estatísticas por operação: {operation_stats.shape[0]} operações")
        
        if not operation_stats.empty:
            print(f"  📊 Operação com mais tickets: {operation_stats['total_tickets'].max()}")
            print(f"  💰 Maior valor de frete: R$ {operation_stats['total_freight_value'].max():,.2f}")
            print(f"  📦 Maior quantidade: {operation_stats['total_amount'].max():,.0f}")
        
        # Testar estatísticas diárias
        daily_stats = db_service.get_daily_statistics(days=7)
        print(f"✅ Estatísticas diárias: {daily_stats.shape[0]} dias")
        
        if not daily_stats.empty:
            print(f"  📈 Dia com mais tickets: {daily_stats['total_tickets'].max()}")
            print(f"  💰 Maior valor diário: R$ {daily_stats['total_freight_value'].max():,.2f}")
        
        # Testar resumo de pedidos
        orders_summary = db_service.get_orders_summary()
        print(f"✅ Resumo de pedidos:")
        print(f"  📋 Total: {orders_summary['total_orders']:,}")
        print(f"  ✅ Concluídos: {orders_summary['done_count']:,} ({orders_summary['done_rate']:.1%})")
        print(f"  ❌ Cancelados: {orders_summary['canceled_count']:,}")
        print(f"  💰 Preço médio/saca: R$ {orders_summary['media_bag_price']:.2f}")
        
        db_config.close_connection()
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de lógica: {e}")
        return False

def run_full_system_test():
    """Executa teste completo do sistema"""
    print("🚀 INICIANDO TESTE COMPLETO DO SISTEMA DE AUDITORIA FOX")
    print("=" * 60)
    
    start_time = time.time()
    
    # Lista de testes
    tests = [
        ("Conexão com Banco", test_database_connection),
        ("Carregamento de Dados", test_data_loading),
        ("Motor de Auditoria", test_audit_engine),
        ("Performance", test_performance),
        ("Qualidade dos Dados", test_data_quality),
        ("Lógica de Negócio", test_business_logic)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSOU")
            else:
                print(f"❌ {test_name}: FALHOU")
        except Exception as e:
            print(f"❌ {test_name}: ERRO - {e}")
            results.append((test_name, False))
    
    # Resumo final
    total_time = time.time() - start_time
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:.<30} {status}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram")
    print(f"⏱️ TEMPO TOTAL: {total_time:.2f}s")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema pronto para produção.")
    else:
        print("⚠️ Alguns testes falharam. Revisar antes de deploy.")
    
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    run_full_system_test()

