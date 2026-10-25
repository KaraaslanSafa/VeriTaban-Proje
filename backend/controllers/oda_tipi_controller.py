"""Oda tipi uç noktaları."""
from flask import Blueprint, jsonify

from services.oda_tipi_service import OdaTipiService
from utils.yetki import rol_gerekli

oda_tipi_bp = Blueprint("oda_tipleri", __name__, url_prefix="/api/oda-tipleri")
_servis = OdaTipiService()


@oda_tipi_bp.get("")
@rol_gerekli()  # giriş yapmış herkes görebilir (misafir arama ekranında tip seçecek)
def oda_tipleri():
    return jsonify(_servis.listele())
