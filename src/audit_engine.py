"""
Motor de auditoria para cruzamento de dados e detecção de inconsistências
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass

from .data_models import Ticket, TicketTransaction, Order, Operation, DataProcessor

# Alias para compatibilidade
Operacao = Operation

@dataclass
class AuditResult:
    """Resultado de uma auditoria"""
    type: str  # tipo de auditoria
    severity: str  # "low", "medium", "high", "critical"
    message: str  # descrição do problema
    affected_items: List[str]  # IDs dos itens afetados
    details: Dict[str, Any]  # detalhes adicionais
    timestamp: datetime

class AuditEngine:
    """Motor de auditoria para cruzamento e validação de dados"""
    
    def __init__(self):
        self.audit_results: List[AuditResult] = []
    
    def clear_results(self):
        """Limpa resultados anteriores"""
        self.audit_results = []
    
    def audit_tickets_orders_consistency(self, tickets: List[Ticket], orders: List[Order]) -> List[AuditResult]:
        """Audita consistência entre tickets e pedidos"""
        results = []
        
        # Criar mapeamento de pedidos por ID
        orders_map = {order._id: order for order in orders}
        
        # Verificar tickets com pedidos inexistentes
        for ticket in tickets:
            # Verificar destinationOrder
            if ticket.destinationOrder and ticket.destinationOrder not in orders_map:
                results.append(AuditResult(
                    type="ticket_destination_order_missing",
                    severity="high",
                    message=f"Ticket {ticket.ticket} referencia destinationOrder inexistente",
                    affected_items=[ticket._id],
                    details={
                        "ticket_id": ticket._id,
                        "ticket_number": ticket.ticket,
                        "missing_destination_order": ticket.destinationOrder
                    },
                    timestamp=datetime.now()
                ))
            
            # Verificar originOrder
            if ticket.originOrder and ticket.originOrder not in orders_map:
                results.append(AuditResult(
                    type="ticket_origin_order_missing",
                    severity="high",
                    message=f"Ticket {ticket.ticket} referencia originOrder inexistente",
                    affected_items=[ticket._id],
                    details={
                        "ticket_id": ticket._id,
                        "ticket_number": ticket.ticket,
                        "missing_origin_order": ticket.originOrder
                    },
                    timestamp=datetime.now()
                ))
        
        return results
    
    def audit_tickets_transactions_consistency(self, tickets: List[Ticket], transactions: List[TicketTransaction]) -> List[AuditResult]:
        """Audita consistência entre tickets e transações"""
        results = []
        
        # Criar mapeamento de tickets por ID
        tickets_map = {ticket._id: ticket for ticket in tickets}
        
        # Verificar transações com tickets inexistentes
        for transaction in transactions:
            if transaction.ticket and transaction.ticket not in tickets_map:
                results.append(AuditResult(
                    type="transaction_ticket_missing",
                    severity="medium",
                    message=f"Transação referencia ticket inexistente",
                    affected_items=[transaction._id],
                    details={
                        "transaction_id": transaction._id,
                        "missing_ticket": transaction.ticket,
                        "transaction_amount": transaction.amount
                    },
                    timestamp=datetime.now()
                ))
        
        # Verificar tickets sem transações correspondentes
        transaction_tickets = {t.ticket for t in transactions if t.ticket}
        for ticket in tickets:
            if ticket._id not in transaction_tickets:
                results.append(AuditResult(
                    type="ticket_without_transaction",
                    severity="low",
                    message=f"Ticket {ticket.ticket} não possui transação correspondente",
                    affected_items=[ticket._id],
                    details={
                        "ticket_id": ticket._id,
                        "ticket_number": ticket.ticket,
                        "ticket_status": ticket.status
                    },
                    timestamp=datetime.now()
                ))
        
        return results
    
    def audit_data_quality(self, tickets: List[Ticket], orders: List[Order]) -> List[AuditResult]:
        """Audita qualidade dos dados"""
        results = []
        
        # Verificar tickets sem quantidade (amount)
        tickets_sem_amount = [t for t in tickets if t.amount is None]
        if tickets_sem_amount:
            results.append(AuditResult(
                type="tickets_missing_amount",
                severity="medium",
                message=f"{len(tickets_sem_amount)} tickets sem quantidade definida",
                affected_items=[t._id for t in tickets_sem_amount],
                details={
                    "count": len(tickets_sem_amount),
                    "percentage": len(tickets_sem_amount) / len(tickets) * 100 if tickets else 0
                },
                timestamp=datetime.now()
            ))
        
        # Verificar tickets sem data de carregamento
        tickets_sem_loading_date = [t for t in tickets if t.loadingDate is None]
        if tickets_sem_loading_date:
            results.append(AuditResult(
                type="tickets_missing_loading_date",
                severity="medium",
                message=f"{len(tickets_sem_loading_date)} tickets sem data de carregamento",
                affected_items=[t._id for t in tickets_sem_loading_date],
                details={
                    "count": len(tickets_sem_loading_date),
                    "percentage": len(tickets_sem_loading_date) / len(tickets) * 100 if tickets else 0
                },
                timestamp=datetime.now()
            ))
        
        # Verificar pedidos vencidos não finalizados
        today = datetime.now()
        orders_vencidos = []
        
        for o in orders:
            if o.deliveryDeadline and not o.status_flags['isDone'] and not o.status_flags['isCanceled']:
                # Converter deliveryDeadline para datetime se necessário
                deadline = o.deliveryDeadline
                if isinstance(deadline, str):
                    try:
                        deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    except:
                        continue  # Pular se não conseguir converter
                elif hasattr(deadline, 'date'):
                    # Se for um objeto date, converter para datetime
                    deadline = datetime.combine(deadline, datetime.min.time())
                
                if deadline < today:
                    orders_vencidos.append(o)
        
        if orders_vencidos:
            results.append(AuditResult(
                type="orders_overdue",
                severity="high",
                message=f"{len(orders_vencidos)} pedidos vencidos não finalizados",
                affected_items=[o._id for o in orders_vencidos],
                details={
                    "count": len(orders_vencidos),
                    "oldest_overdue": min(o.deliveryDeadline for o in orders_vencidos) if orders_vencidos else None
                },
                timestamp=datetime.now()
            ))
        
        # Verificar tickets com valores inconsistentes
        tickets_valor_inconsistente = []
        for ticket in tickets:
            if ticket.freightValue and ticket.freightValue < 0:
                tickets_valor_inconsistente.append(ticket)
            if ticket.valueGrain and ticket.valueGrain < 0:
                tickets_valor_inconsistente.append(ticket)
        
        if tickets_valor_inconsistente:
            results.append(AuditResult(
                type="tickets_negative_values",
                severity="high",
                message=f"{len(tickets_valor_inconsistente)} tickets com valores negativos",
                affected_items=[t._id for t in tickets_valor_inconsistente],
                details={
                    "count": len(tickets_valor_inconsistente)
                },
                timestamp=datetime.now()
            ))
        
        return results
    
    def audit_business_rules(self, tickets: List[Ticket], orders: List[Order], transactions: List[TicketTransaction]) -> List[AuditResult]:
        """Audita regras de negócio"""
        results = []
        
        # Verificar tickets finalizados sem valor de frete
        tickets_finalizados_sem_frete = [
            t for t in tickets 
            if t.status == "Finalizado" and (t.freightValue is None or t.freightValue == 0)
        ]
        
        if tickets_finalizados_sem_frete:
            results.append(AuditResult(
                type="finalized_tickets_no_freight",
                severity="high",
                message=f"{len(tickets_finalizados_sem_frete)} tickets finalizados sem valor de frete",
                affected_items=[t._id for t in tickets_finalizados_sem_frete],
                details={
                    "count": len(tickets_finalizados_sem_frete)
                },
                timestamp=datetime.now()
            ))
        
        # Verificar discrepâncias entre ticket e transação
        tickets_map = {t._id: t for t in tickets}
        for transaction in transactions:
            if transaction.ticket and transaction.ticket in tickets_map:
                ticket = tickets_map[transaction.ticket]
                
                # Verificar se status são compatíveis
                if ticket.status == "Finalizado" and transaction.status != "Finalizado":
                    results.append(AuditResult(
                        type="status_mismatch_ticket_transaction",
                        severity="medium",
                        message=f"Status incompatível entre ticket e transação",
                        affected_items=[ticket._id, transaction._id],
                        details={
                            "ticket_id": ticket._id,
                            "ticket_status": ticket.status,
                            "transaction_id": transaction._id,
                            "transaction_status": transaction.status
                        },
                        timestamp=datetime.now()
                    ))
        
        # Verificar pedidos com quantidade muito alta (possível erro)
        threshold_amount = 100000  # 100k sacas
        orders_quantidade_alta = [
            o for o in orders 
            if o.amount and o.amount > threshold_amount
        ]
        
        if orders_quantidade_alta:
            results.append(AuditResult(
                type="orders_high_amount",
                severity="medium",
                message=f"{len(orders_quantidade_alta)} pedidos com quantidade muito alta (>{threshold_amount:,} sacas)",
                affected_items=[o._id for o in orders_quantidade_alta],
                details={
                    "count": len(orders_quantidade_alta),
                    "threshold": threshold_amount,
                    "max_amount": max(o.amount for o in orders_quantidade_alta) if orders_quantidade_alta else 0
                },
                timestamp=datetime.now()
            ))
        
        return results
    
    def create_operations_from_tickets(self, tickets: List[Ticket], orders: List[Order]) -> List[Operacao]:
        """Cria operações agrupando tickets por critérios específicos"""
        operations = []
        
        # Agrupar tickets por operação (se campo operation existir)
        tickets_by_operation = {}
        tickets_sem_operation = []
        
        for ticket in tickets:
            if ticket.operation:
                if ticket.operation not in tickets_by_operation:
                    tickets_by_operation[ticket.operation] = []
                tickets_by_operation[ticket.operation].append(ticket)
            else:
                tickets_sem_operation.append(ticket)
        
        # Criar operações para tickets com campo operation
        orders_map = {order._id: order for order in orders}
        
        for operation_id, operation_tickets in tickets_by_operation.items():
            # Encontrar pedidos relacionados
            related_orders = []
            for ticket in operation_tickets:
                if ticket.destinationOrder and ticket.destinationOrder in orders_map:
                    related_orders.append(orders_map[ticket.destinationOrder])
                if ticket.originOrder and ticket.originOrder in orders_map:
                    related_orders.append(orders_map[ticket.originOrder])
            
            # Remover duplicatas
            related_orders = list({order._id: order for order in related_orders}.values())
            
            try:
                operacao = Operacao.from_tickets_and_orders(operation_tickets, related_orders)
                operacao._id = f"op_{operation_id}"
                operations.append(operacao)
            except Exception as e:
                print(f"Erro ao criar operação {operation_id}: {e}")
        
        return operations
    
    def run_full_audit(self, tickets: List[Ticket], orders: List[Order], transactions: List[TicketTransaction]) -> Dict[str, Any]:
        """Executa auditoria completa"""
        self.clear_results()
        
        print("🔍 Executando auditoria completa...")
        
        # Executar diferentes tipos de auditoria
        consistency_results = self.audit_tickets_orders_consistency(tickets, orders)
        transaction_results = self.audit_tickets_transactions_consistency(tickets, transactions)
        quality_results = self.audit_data_quality(tickets, orders)
        business_results = self.audit_business_rules(tickets, orders, transactions)
        
        # Combinar todos os resultados
        all_results = consistency_results + transaction_results + quality_results + business_results
        self.audit_results = all_results
        
        # Criar operações
        operations = self.create_operations_from_tickets(tickets, orders)
        
        # Calcular estatísticas
        severity_counts = {}
        type_counts = {}
        
        for result in all_results:
            severity_counts[result.severity] = severity_counts.get(result.severity, 0) + 1
            type_counts[result.type] = type_counts.get(result.type, 0) + 1
        
        # Calcular métricas gerais
        metricas = DataProcessor.calcular_metricas_gerais(tickets, orders)
        
        return {
            "audit_results": all_results,
            "operations": operations,
            "summary": {
                "total_issues": len(all_results),
                "severity_breakdown": severity_counts,
                "type_breakdown": type_counts,
                "total_tickets": len(tickets),
                "total_orders": len(orders),
                "total_transactions": len(transactions),
                "total_operations": len(operations)
            },
            "metrics": metricas,
            "timestamp": datetime.now()
        }
    
    def get_audit_summary_dataframe(self) -> pd.DataFrame:
        """Retorna resumo da auditoria em DataFrame"""
        if not self.audit_results:
            return pd.DataFrame()
        
        data = []
        for result in self.audit_results:
            data.append({
                "tipo": result.type,
                "severidade": result.severity,
                "mensagem": result.message,
                "itens_afetados": len(result.affected_items),
                "timestamp": result.timestamp
            })
        
        return pd.DataFrame(data)
    
    def get_critical_issues(self) -> List[AuditResult]:
        """Retorna apenas issues críticos"""
        return [r for r in self.audit_results if r.severity == "critical"]
    
    def get_high_priority_issues(self) -> List[AuditResult]:
        """Retorna issues de alta prioridade"""
        return [r for r in self.audit_results if r.severity in ["critical", "high"]]

