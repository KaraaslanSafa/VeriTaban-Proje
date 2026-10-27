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


@rezervasyon_bp.get("/benim")
@rol_gerekli("misafir")
def benim_rezervasyonlarim():
    """Giriş yapmış misafirin kendi rezervasyonları. Örnek: GET /api/rezervasyonlar/benim?durum=onayli"""
    return jsonify(_servis.misafir_rezervasyonlari(mevcut_kullanici(), request.args.get("durum")))


@rezervasyon_bp.post("/<int:rezervasyon_id>/iptal")
@rol_gerekli()  # misafir yalnızca kendi rezervasyonunu, resepsiyon/yönetici hepsini iptal edebilir
def rezervasyon_iptal(rezervasyon_id):
    return jsonify(_servis.iptal_et(mevcut_kullanici(), rezervasyon_id))


@rezervasyon_bp.get("")
@rol_gerekli("resepsiyon", "yonetici")
def rezervasyonlar():
    """Tüm rezervasyonlar (personel). İsteğe bağlı süzgeçler:
    ?durum=beklemede&misafir_id=3&oda_id=14&giris_baslangic=2026-11-01&giris_bitis=2026-11-30&limit=50&offset=0"""
    return jsonify(_servis.listele(request.args))


@rezervasyon_bp.get("/<int:rezervasyon_id>")
@rol_gerekli()  # misafir yalnızca kendi rezervasyonunu görebilir
def rezervasyon_detay(rezervasyon_id):
    return jsonify(_servis.getir(mevcut_kullanici(), rezervasyon_id))


@rezervasyon_bp.post("/<int:rezervasyon_id>/onayla")
@rol_gerekli("resepsiyon", "yonetici")
def rezervasyon_onayla(rezervasyon_id):
    return jsonify(_servis.onayla(rezervasyon_id))
