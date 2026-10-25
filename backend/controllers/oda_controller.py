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


@oda_bp.get("")
@rol_gerekli("resepsiyon", "yonetici")  # oda durumları personele özeldir
def odalar():
    """Örnek: GET /api/odalar?tip_id=2&durum=bos  (ikisi de isteğe bağlı)"""
    return jsonify(_servis.listele(request.args.get("tip_id"), request.args.get("durum")))


@oda_bp.get("/<int:oda_id>")
@rol_gerekli("resepsiyon", "yonetici")
def oda_detay(oda_id):
    return jsonify(_servis.getir(oda_id))
