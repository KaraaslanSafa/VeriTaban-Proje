"""Rezervasyon tablosuna erişim.

Çakışma kontrolü burada yapılmaz: Rezervasyon tablosundaki BEFORE INSERT trigger'ı
(trg_rez_cakisma_ins) çakışan tarihleri ve kapasite aşımını veritabanı seviyesinde engeller.
"""
from models.rezervasyon import Rezervasyon
from repositories.base_repository import BaseRepository


class RezervasyonRepository(BaseRepository):
    # Oda numarası ve misafir adıyla zenginleştirilmiş ortak SELECT
    _SECIM = (
        "SELECT r.*, o.oda_no, CONCAT(m.ad, ' ', m.soyad) AS misafir_adi "
        "FROM Rezervasyon r "
        "JOIN Oda o ON o.oda_id = r.oda_id "
        "JOIN Misafir m ON m.misafir_id = r.misafir_id"
    )

    def ekle(self, misafir_id, oda_id, giris_tarihi, cikis_tarihi, kisi_sayisi, durum):
        """Yeni rezervasyon ekler, oluşan rezervasyon_id'yi döndürür."""
        yeni_id, _ = self._calistir(
            "INSERT INTO Rezervasyon (misafir_id, oda_id, giris_tarihi, cikis_tarihi, kisi_sayisi, durum) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (misafir_id, oda_id, giris_tarihi, cikis_tarihi, kisi_sayisi, durum))
        return yeni_id

    def bul_id(self, rezervasyon_id):
        satir = self._bir(self._SECIM + " WHERE r.rezervasyon_id = %s", (rezervasyon_id,))
        return Rezervasyon.satirdan(satir) if satir else None

    def misafire_ait(self, misafir_id, durum=None):
        """Bir misafirin rezervasyonları, en yakın giriş tarihi en üstte. İstenirse duruma göre süzülür."""
        sql = self._SECIM + " WHERE r.misafir_id = %s"
        parametreler = [misafir_id]
        if durum is not None:
            sql += " AND r.durum = %s"
            parametreler.append(durum)
        sql += " ORDER BY r.giris_tarihi DESC, r.rezervasyon_id DESC"
        return [Rezervasyon.satirdan(s) for s in self._tum(sql, parametreler)]

    def ara(self, durum=None, misafir_id=None, oda_id=None,
            giris_baslangic=None, giris_bitis=None, limit=50, offset=0):
        """Personel için süzülebilir, sayfalı rezervasyon listesi.
        (toplam_kayit, rezervasyon_listesi) döndürür. Değerler her zaman parametreli geçer."""
        kosullar, parametreler = [], []
        if durum is not None:
            kosullar.append("r.durum = %s")
            parametreler.append(durum)
        if misafir_id is not None:
            kosullar.append("r.misafir_id = %s")
            parametreler.append(misafir_id)
        if oda_id is not None:
            kosullar.append("r.oda_id = %s")
            parametreler.append(oda_id)
        if giris_baslangic is not None:
            kosullar.append("r.giris_tarihi >= %s")
            parametreler.append(giris_baslangic)
        if giris_bitis is not None:
            kosullar.append("r.giris_tarihi <= %s")
            parametreler.append(giris_bitis)
        nerede = (" WHERE " + " AND ".join(kosullar)) if kosullar else ""

        toplam = self._bir("SELECT COUNT(*) AS n FROM Rezervasyon r" + nerede, parametreler)["n"]
        satirlar = self._tum(
            self._SECIM + nerede + " ORDER BY r.giris_tarihi DESC, r.rezervasyon_id DESC LIMIT %s OFFSET %s",
            parametreler + [limit, offset])
        return toplam, [Rezervasyon.satirdan(s) for s in satirlar]

    def konaklama_var_mi(self, rezervasyon_id):
        """Rezervasyon için check-in yapılmış mı?"""
        satir = self._bir("SELECT 1 AS var FROM Konaklama WHERE rezervasyon_id = %s", (rezervasyon_id,))
        return satir is not None

    def iptal_et(self, rezervasyon_id):
        """Durumu 'iptal' yapar. Yalnızca beklemede/onayli rezervasyonlar iptal edilir.
        Tek sorguda koşullu güncellendiği için iki istek aynı anda gelse bile biri başarısız olur.
        True: iptal edildi, False: durum uygun değildi."""
        _, etkilenen = self._calistir(
            "UPDATE Rezervasyon SET durum = 'iptal' "
            "WHERE rezervasyon_id = %s AND durum IN ('beklemede', 'onayli')", (rezervasyon_id,))
        return etkilenen > 0

    def onayla(self, rezervasyon_id):
        """'beklemede' rezervasyonu 'onayli' yapar. Koşullu güncelleme, iptal_et ile aynı mantık."""
        _, etkilenen = self._calistir(
            "UPDATE Rezervasyon SET durum = 'onayli' "
            "WHERE rezervasyon_id = %s AND durum = 'beklemede'", (rezervasyon_id,))
        return etkilenen > 0
