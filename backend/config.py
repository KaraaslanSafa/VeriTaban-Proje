"""Uygulama ayarları. Değerler proje kökündeki .env dosyasından okunur."""
import os
import secrets
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

KOK_KLASOR = Path(__file__).resolve().parent.parent
load_dotenv(KOK_KLASOR / ".env")


class Config:
    # Veritabanı
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "otel_db")

    # JWT. Anahtar .env içinde JWT_SECRET_KEY olarak tanımlanmalı.
    # Tanımlı değilse her başlatmada rastgele üretilir (eski token'lar geçersiz olur).
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_hex(32)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_ANAHTAR_TANIMLI = bool(os.getenv("JWT_SECRET_KEY"))
