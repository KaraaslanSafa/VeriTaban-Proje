"""MySQL bağlantı havuzu. Her istek havuzdan bir bağlantı alır, işi bitince geri verir."""
from mysql.connector import pooling

from config import Config

_havuz = None


def _havuzu_al():
    global _havuz
    if _havuz is None:
        _havuz = pooling.MySQLConnectionPool(
            pool_name="otel_havuz",
            pool_size=5,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset="utf8mb4",
            autocommit=True,
        )
    return _havuz


def baglanti_al():
    """Havuzdan bağlantı verir. Kullanan kod close() çağırarak geri vermelidir."""
    return _havuzu_al().get_connection()
