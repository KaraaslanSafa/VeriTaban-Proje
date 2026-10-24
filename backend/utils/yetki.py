"""Rol bazlı yetkilendirme. Controller fonksiyonlarının üstüne dekoratör olarak konur.

Kullanım:
    @rol_gerekli("resepsiyon", "yonetici")   # yalnızca bu roller girebilir
    @rol_gerekli()                           # giriş yapmış herkes girebilir
"""
from functools import wraps

from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from utils.hatalar import YasakHatasi


def rol_gerekli(*izinli_roller):
    def dekorator(fonksiyon):
        @wraps(fonksiyon)
        def sarmal(*args, **kwargs):
            verify_jwt_in_request()
            if izinli_roller and get_jwt().get("rol") not in izinli_roller:
                raise YasakHatasi("Bu işlem için yetkiniz yok.")
            return fonksiyon(*args, **kwargs)
        return sarmal
    return dekorator


def mevcut_kullanici():
    """Token içindeki bilgileri sözlük olarak verir."""
    talepler = get_jwt()
    return {
        "kullanici_id": int(get_jwt_identity()),
        "rol": talepler.get("rol"),
        "misafir_id": talepler.get("misafir_id"),
        "personel_id": talepler.get("personel_id"),
    }
