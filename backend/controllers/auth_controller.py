"""Giriş uç noktaları. Controller sadece isteği alır, servise iletir, cevabı döndürür."""
from flask import Blueprint, jsonify, request

from services.auth_service import AuthService
from utils.yetki import mevcut_kullanici, rol_gerekli

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
_servis = AuthService()


@auth_bp.post("/login")
def giris():
    veri = request.get_json(silent=True) or {}
    sonuc = _servis.giris(veri.get("kullanici_adi"), veri.get("parola"))
    return jsonify(sonuc)


@auth_bp.get("/me")
@rol_gerekli()
def ben():
    return jsonify(_servis.kimlik(mevcut_kullanici()["kullanici_id"]))
