"""Kullanici tablosuna erişim."""
from models.kullanici import Kullanici
from repositories.base_repository import BaseRepository


class KullaniciRepository(BaseRepository):
    def bul_kullanici_adi(self, kullanici_adi):
        satir = self._bir("SELECT * FROM Kullanici WHERE kullanici_adi = %s", (kullanici_adi,))
        return Kullanici.satirdan(satir) if satir else None

    def bul_id(self, kullanici_id):
        satir = self._bir("SELECT * FROM Kullanici WHERE kullanici_id = %s", (kullanici_id,))
        return Kullanici.satirdan(satir) if satir else None
