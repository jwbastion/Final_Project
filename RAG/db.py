import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "dbname": "rag_subway",
    "user": "postgres",
    "password": "1234"
}

def connect_db():
    return psycopg2.connect(**DB_CONFIG)