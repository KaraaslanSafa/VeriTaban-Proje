"""JSON çıktısı için dönüştürücü: Decimal sayı, tarih ve saat değerleri düzgün çıksın."""
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask.json.provider import DefaultJSONProvider


class OtelJSONSaglayici(DefaultJSONProvider):
    ensure_ascii = False  # Türkçe karakterler bozulmasın
    sort_keys = False

    @staticmethod
    def default(nesne):
        if isinstance(nesne, Decimal):
            return float(nesne)
        if isinstance(nesne, datetime):
            return nesne.isoformat(sep=" ")
        if isinstance(nesne, date):
            return nesne.isoformat()
        if isinstance(nesne, timedelta):
            return str(nesne)
        return DefaultJSONProvider.default(nesne)
