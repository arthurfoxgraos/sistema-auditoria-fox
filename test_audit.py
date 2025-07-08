"""
Script para testar o motor de auditoria
"""
import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.database import DatabaseConfig
from src.database_service import DatabaseService
from src.audit_engine import AuditEngine

def test_audit_engine():
    """Testa o motor de auditoria"""
    print("🔍 Testando motor de auditoria...")
    
    # Conectar ao banco
    db_config = DatabaseConfig()
    if not db_config.connect():
        print("❌ Falha na conexão")
        return False
    
    # Obter coleções
    collections = db_config.get_collections()
    
    # Criar serviço de banco
    db_service = DatabaseService(collections)
    
    print("\n📊 Carregando dados para auditoria...")
    try:
        # Carregar dados
        tickets = db_service.get_tickets(limit=200)
        orders = db_service.get_orders(limit=200)
        transactions = db_service.get_ticket_transactions(limit=200)
        
        print(f"✅ Carregados: {len(tickets)} tickets, {len(orders)} pedidos, {len(transactions)} transações")
        
        # Criar motor de auditoria
        audit_engine = AuditEngine()
        
        print("\n🔍 Executando auditoria completa...")
        audit_result = audit_engine.run_full_audit(tickets, orders, transactions)
        
        print("\n📊 Resultados da auditoria:")
        summary = audit_result["summary"]
        
        print(f"  Total de issues: {summary['total_issues']}")
        print(f"  Total de operações criadas: {summary['total_operations']}")
        
        print("\n📈 Breakdown por severidade:")
        for severity, count in summary["severity_breakdown"].items():
            print(f"  {severity}: {count}")
        
        print("\n📋 Breakdown por tipo:")
        for issue_type, count in summary["type_breakdown"].items():
            print(f"  {issue_type}: {count}")
        
        # Mostrar alguns exemplos de issues
        print("\n🚨 Exemplos de issues encontrados:")
        for i, result in enumerate(audit_result["audit_results"][:5]):
            print(f"  {i+1}. [{result.severity.upper()}] {result.message}")
            print(f"     Tipo: {result.type}")
            print(f"     Itens afetados: {len(result.affected_items)}")
        
        # Mostrar operações criadas
        operations = audit_result["operations"]
        if operations:
            print(f"\n🔄 Exemplos de operações criadas:")
            for i, op in enumerate(operations[:3]):
                print(f"  {i+1}. Operação {op._id}")
                print(f"     Tickets: {op.num_tickets}")
                print(f"     Status: {op.status}")
                print(f"     Valor total frete: R$ {op.valor_total_frete:.2f}")
                print(f"     Quantidade total sacas: {op.quantidade_total_sacas}")
        
        # Testar DataFrame de resumo
        print("\n📊 Testando DataFrame de resumo...")
        df_summary = audit_engine.get_audit_summary_dataframe()
        if not df_summary.empty:
            print(f"✅ DataFrame criado: {df_summary.shape}")
            print(f"Colunas: {list(df_summary.columns)}")
            
            # Mostrar contagem por severidade
            severity_counts = df_summary['severidade'].value_counts()
            print("Contagem por severidade:")
            for severity, count in severity_counts.items():
                print(f"  {severity}: {count}")
        
        # Testar issues críticos
        critical_issues = audit_engine.get_critical_issues()
        high_priority_issues = audit_engine.get_high_priority_issues()
        
        print(f"\n⚠️  Issues críticos: {len(critical_issues)}")
        print(f"🔴 Issues alta prioridade: {len(high_priority_issues)}")
        
        # Mostrar métricas gerais
        print("\n📈 Métricas gerais:")
        metrics = audit_result["metrics"]
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Erro durante auditoria: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Fechar conexão
    db_config.close_connection()
    
    print("\n✅ Teste do motor de auditoria concluído!")
    return True

if __name__ == "__main__":
    test_audit_engine()

