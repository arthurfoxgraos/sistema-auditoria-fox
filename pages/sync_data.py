import pandas as pd
import psycopg2
from config.database import get_database_connection
from src.database_service import DatabaseService


def get_db_service():
    """Retorna o serviço de banco de dados MongoDB"""
    cfg = get_database_connection()
    return DatabaseService(cfg.get_collections()) if cfg else None


def get_pg_conn():
    """Retorna conexão com PostgreSQL"""
    return psycopg2.connect(
        host="24.199.75.66",
        port=5432,
        user="myuser",
        password="mypassword",
        database="mydb"
    )


def load_raw_data():
    """Carrega dados brutos de MongoDB: tickets, transactions e distances"""
    db = get_db_service()
    if not db:
        return [], [], []
    tickets = [t.__dict__ if hasattr(t, '__dict__') else dict(t) for t in db.get_tickets_with_users(limit=1000)]
    trans   = [t.__dict__ if hasattr(t, '__dict__') else dict(t) for t in db.get_ticket_transactions(limit=1000)]
    dists   = [d.__dict__ if hasattr(d, '__dict__') else dict(d) for d in db.get_distances(limit=1000)]
    return tickets, trans, dists


def sync_data():
    """Sincroniza dados do MongoDB para a tabela cargas no PostgreSQL"""
    tickets, trans, dists = load_raw_data()
    df = pd.DataFrame(tickets)
    df_trans = pd.DataFrame(trans)
    df_dist = pd.DataFrame(dists)

    # Calcular distância por par origin→destination
    df['orig_str'] = df['originOrder'].astype(str)
    df['dest_str'] = df['destinationOrder'].astype(str)
    df_dist['from_str'] = df_dist['from'].astype(str)
    df_dist['to_str'] = df_dist['to'].astype(str)
    df = df.merge(
        df_dist[['from_str','to_str','inKm']],
        how='left',
        left_on=['orig_str','dest_str'],
        right_on=['from_str','to_str']
    )
    df['distanceInKm'] = df['inKm']

    # Preparar registros para inserção
    records = []
    for r in df.to_dict('records'):
        records.append((
            r.get('ticket'), r.get('loadingDate'), r.get('buyer_name'), r.get('seller_name'),
            r.get('driver_name'), r.get('grain_name'), r.get('contract_type'), r.get('status'),
            r.get('paid_status'), r.get('amount'), r.get('revenue_value'), r.get('cost_value'),
            r.get('total_freight_value'), r.get('gross_profit'), r.get('distanceInKm')
        ))

    conn = get_pg_conn()
    cur = conn.cursor()
    # Criar tabela se não existir
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cargas (
            ticket TEXT PRIMARY KEY,
            loading_date TIMESTAMP,
            buyer_name TEXT,
            seller_name TEXT,
            driver_name TEXT,
            grain_name TEXT,
            contract_type TEXT,
            status TEXT,
            paid_status TEXT,
            amount NUMERIC,
            revenue_value NUMERIC,
            cost_value NUMERIC,
            total_freight_value NUMERIC,
            gross_profit NUMERIC,
            distance_in_km NUMERIC
        )""")
    # Limpar dados antigos
    cur.execute("TRUNCATE cargas;")
    # Inserir novos
    cur.executemany(
        "INSERT INTO cargas VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        records
    )
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    sync_data()
    print("Sincronização concluída com sucesso!")