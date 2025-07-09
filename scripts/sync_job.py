#!/usr/bin/env python3
"""
Script de sincronização para CronJob do Kubernetes
Executa a cada 5 minutos para manter dados atualizados
"""

import sys
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Função principal do job de sincronização"""
    try:
        logger.info("🚀 Iniciando job de sincronização FOX Auditoria")
        
        # Adicionar path da aplicação
        sys.path.append('/app')
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Importar módulos necessários
        from config.database import get_database_connection
        from src.database_service import DatabaseService
        
        logger.info("📊 Conectando ao MongoDB...")
        
        # Conectar ao banco
        db_config = get_database_connection()
        if not db_config:
            logger.error("❌ Falha ao conectar ao MongoDB")
            sys.exit(1)
        
        # Obter coleções
        collections = db_config.get_collections()
        db_service = DatabaseService(collections)
        
        logger.info("🔄 Executando sincronização de dados...")
        
        # Buscar tickets atualizados
        tickets = db_service.get_tickets_with_users(limit=1000)
        logger.info(f"📋 Processados {len(tickets)} tickets")
        
        # Buscar dados de provisionamento
        try:
            if hasattr(db_service, 'get_provisioning_data'):
                provisioning = db_service.get_provisioning_data(limit=500)
                logger.info(f"📦 Processados {len(provisioning)} registros de provisionamento")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao processar provisionamento: {str(e)}")
        
        # Buscar dados financeiros
        try:
            if hasattr(db_service, 'get_finances_with_lookups'):
                finances = db_service.get_finances_with_lookups(limit=500)
                logger.info(f"💰 Processados {len(finances)} registros financeiros")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao processar financeiro: {str(e)}")
        
        # Buscar contratos
        try:
            if hasattr(db_service, 'get_contracts_data'):
                contracts = db_service.get_contracts_data(limit=500)
                logger.info(f"📋 Processados {len(contracts)} contratos")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao processar contratos: {str(e)}")
        
        # Fechar conexão
        db_config.close_connection()
        
        logger.info("✅ Sincronização concluída com sucesso!")
        
        # Estatísticas finais
        logger.info(f"📊 Resumo da sincronização:")
        logger.info(f"   - Tickets: {len(tickets)}")
        logger.info(f"   - Timestamp: {datetime.now().isoformat()}")
        
        return 0
        
    except ImportError as e:
        logger.error(f"❌ Erro de importação: {str(e)}")
        logger.error("Verifique se todos os módulos estão disponíveis")
        return 1
        
    except Exception as e:
        logger.error(f"❌ Erro inesperado na sincronização: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

