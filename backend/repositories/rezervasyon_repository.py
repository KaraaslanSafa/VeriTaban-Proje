"""Rezervasyon tablosuna erişim.

Çakışma kontrolü burada yapılmaz: Rezervasyon tablosundaki BEFORE INSERT trigger'ı
(trg_rez_cakisma_ins) çakışan tarihleri ve kapasite aşımını veritabanı seviyesinde engeller.
"""
from models.rezervasyon import Rezervasyon
from repositories.base_repository import BaseRepository


class RezervasyonRepository(BaseRepository):
    def ekle(self, misafir_id, oda_id, giris_tarihi, cikis_tarihi, kisi_sayisi, durum):
        """Yeni rezervasyon ekler, oluşan rezervasyon_id'yi döndürür."""
        yeni_id, _ = self._calistir(
            "INSERT INTO Rezervasyon (misafir_id, oda_id, giris_tarihi, cikis_tarihi, kisi_sayisi, durum) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (misafir_id, oda_id, giris_tarihi, cikis_tarihi, kisi_sayisi, durum))
        return yeni_id

    def bul_id(self, rezervasyon_id):
        satir = self._bir(
            "SELECT r.*, o.oda_no FROM Rezervasyon r JOIN Oda o ON o.oda_id = r.oda_id "
            "WHERE r.rezervasyon_id = %s", (rezervasyon_id,))
        return Rezervasyon.satirdan(satir) if satir else None
