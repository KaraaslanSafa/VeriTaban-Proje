"""Rezervasyon uç noktaları."""
from flask import Blueprint, jsonify, request

from services.rezervasyon_service import RezervasyonService
from utils.yetki import mevcut_kullanici, rol_gerekli

rezervasyon_bp = Blueprint("rezervasyonlar", __name__, url_prefix="/api/rezervasyonlar")
_servis = RezervasyonService()


@rezervasyon_bp.post("")
@rol_gerekli()  # misafir, resepsiyon, yönetici
def rezervasyon_olustur():
    """Gövde (JSON):
        {"oda_id": 14, "giris_tarihi": "2027-05-10", "cikis_tarihi": "2027-05-13",
         "kisi_sayisi": 2, "misafir_id": 1}
    misafir_id yalnızca resepsiyon/yönetici için zorunludur; misafir kendi adına yapar."""
    veri = request.get_json(silent=True)
    if not isinstance(veri, dict):
        veri = {}
    sonuc = _servis.olustur(mevcut_kullanici(), veri)
    return jsonify(sonuc), 201
