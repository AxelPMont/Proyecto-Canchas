import psycopg2
import psycopg2.extras
from config import Config

class Conexion:
    def __init__(self):
        self.dblink = psycopg2.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            dbname=Config.DB_NAME,
            port=Config.DB_PORT,
            #sslmode='require'  # Requerido para conexiones seguras como Supabase
        )
        self.dblink.autocommit = True

    @property
    def open(self):
        return self.dblink

    def cursor(self):
        return self.dblink.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
