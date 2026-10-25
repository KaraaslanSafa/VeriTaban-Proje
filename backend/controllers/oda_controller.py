"""Oda uç noktaları."""
from flask import Blueprint, jsonify, request

from services.oda_service import OdaService
from utils.yetki import rol_gerekli

oda_bp = Blueprint("odalar", __name__, url_prefix="/api/odalar")
_servis = OdaService()


@oda_bp.get("/bos")
@rol_gerekli()  # giriş yapmış herkes (misafir, resepsiyon, yönetici) arayabilir
def bos_odalar():
    """Örnek: GET /api/odalar/bos?giris=2026-11-23&cikis=2026-11-26&tip_id=2&kisi=2
    tip_id ve kisi isteğe bağlıdır."""
    sonuc = _servis.bos_odalari_ara(
        request.args.get("giris"),
        request.args.get("cikis"),
        request.args.get("tip_id"),
        request.args.get("kisi"),
    )
    return jsonify(sonuc)
