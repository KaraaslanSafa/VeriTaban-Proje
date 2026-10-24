"""Giriş (kimlik doğrulama) iş mantığı."""
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash

from repositories.kullanici_repository import KullaniciRepository
from utils.hatalar import BulunamadiHatasi, UygulamaHatasi, YetkisizHatasi


class AuthService:
    def __init__(self, kullanici_repo=None):
        self._kullanicilar = kullanici_repo or KullaniciRepository()

    def giris(self, kullanici_adi, parola):
        if not kullanici_adi or not parola:
            raise UygulamaHatasi("Kullanıcı adı ve parola zorunludur.")

        kullanici = self._kullanicilar.bul_kullanici_adi(kullanici_adi.strip())
        # Kullanıcı yok ya da parola yanlışsa aynı mesaj verilir,
        # böylece hangi e-postaların kayıtlı olduğu dışarıdan anlaşılamaz.
        if kullanici is None or not check_password_hash(kullanici.sifre_hash, parola):
            raise YetkisizHatasi("Kullanıcı adı veya parola hatalı.")

        token = create_access_token(
            identity=str(kullanici.kullanici_id),
            additional_claims={
                "rol": kullanici.rol,
                "misafir_id": kullanici.misafir_id,
                "personel_id": kullanici.personel_id,
            },
        )
        return {"access_token": token, "kullanici": kullanici.genel_bilgi()}

    def kimlik(self, kullanici_id):
        kullanici = self._kullanicilar.bul_id(kullanici_id)
        if kullanici is None:
            raise BulunamadiHatasi("Kullanıcı bulunamadı.")
        return kullanici.genel_bilgi()
