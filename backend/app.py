"""Flask uygulamasının giriş noktası.

Çalıştırma (proje kök klasöründen):
    python backend/app.py
"""
import re

import mysql.connector
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from controllers.auth_controller import auth_bp
from controllers.oda_controller import oda_bp
from controllers.oda_tipi_controller import oda_tipi_bp
from controllers.rezervasyon_controller import rezervasyon_bp
from utils.hatalar import UygulamaHatasi
from utils.json_saglayici import OtelJSONSaglayici


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.json = OtelJSONSaglayici(app)
    CORS(app)

    jwt = JWTManager(app)
    _jwt_mesajlarini_ayarla(jwt)

    app.register_blueprint(auth_bp)
    app.register_blueprint(oda_bp)
    app.register_blueprint(oda_tipi_bp)
    app.register_blueprint(rezervasyon_bp)
    # Yeni controller'lar buraya eklenecek.

    @app.get("/api/saglik")
    def saglik():
        return jsonify({"durum": "calisiyor"})

    _hata_yoneticilerini_kaydet(app)
    return app


def _jwt_mesajlarini_ayarla(jwt):
    @jwt.unauthorized_loader
    def token_yok(neden):
        return jsonify({"hata": "Giriş yapmanız gerekiyor (Authorization: Bearer <token>)."}), 401

    @jwt.invalid_token_loader
    def token_gecersiz(neden):
        return jsonify({"hata": "Geçersiz token."}), 401

    @jwt.expired_token_loader
    def token_suresi_doldu(baslik, veri):
        return jsonify({"hata": "Oturum süresi doldu, tekrar giriş yapın."}), 401


def _hata_yoneticilerini_kaydet(app):
    @app.errorhandler(UygulamaHatasi)
    def uygulama_hatasi(hata):
        return jsonify({"hata": hata.mesaj}), hata.durum_kodu

    @app.errorhandler(mysql.connector.Error)
    def veritabani_hatasi(hata):
        # SIGNAL SQLSTATE '45000' ile trigger/procedure'lerin attığı iş kuralı hataları
        # (örn. "Bu oda seçilen tarihlerde zaten rezerve edilmiş.") kullanıcıya iletilir.
        if getattr(hata, "errno", None) == 1644:
            mesaj = re.sub(r"^\d+ \(\w+\): ", "", str(hata))
            return jsonify({"hata": mesaj}), 409
        app.logger.exception("Veritabanı hatası")
        return jsonify({"hata": "Veritabanı hatası oluştu."}), 500

    @app.errorhandler(404)
    def bulunamadi(hata):
        return jsonify({"hata": "Böyle bir adres yok."}), 404

    @app.errorhandler(405)
    def metot_yok(hata):
        return jsonify({"hata": "Bu adres bu HTTP metodunu desteklemiyor."}), 405


app = create_app()

if __name__ == "__main__":
    if not Config.JWT_ANAHTAR_TANIMLI:
        print("UYARI: .env dosyasında JWT_SECRET_KEY yok. Geçici anahtar kullanılıyor, "
              "sunucu yeniden başlayınca girişler geçersiz olur.")
    app.run(debug=True, port=5000)
