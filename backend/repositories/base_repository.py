"""Tüm repository sınıflarının ortak tabanı. SQL çalıştırma ayrıntıları burada toplanır.

Sorgular her zaman parametreli (%s) çalıştırılır, böylece SQL injection oluşmaz.
"""
from database import baglanti_al


class BaseRepository:
    def _tum(self, sql, parametreler=None):
        """Tüm satırları sözlük listesi olarak döndürür."""
        baglanti = baglanti_al()
        try:
            imlec = baglanti.cursor(dictionary=True)
            imlec.execute(sql, parametreler or ())
            return imlec.fetchall()
        finally:
            baglanti.close()

    def _bir(self, sql, parametreler=None):
        """İlk satırı sözlük olarak döndürür, yoksa None."""
        satirlar = self._tum(sql, parametreler)
        return satirlar[0] if satirlar else None

    def _calistir(self, sql, parametreler=None):
        """INSERT/UPDATE/DELETE çalıştırır. (eklenen_id, etkilenen_satir) döndürür."""
        baglanti = baglanti_al()
        try:
            imlec = baglanti.cursor()
            imlec.execute(sql, parametreler or ())
            return imlec.lastrowid, imlec.rowcount
        finally:
            baglanti.close()

    def _prosedur(self, ad, parametreler=()):
        """Stored procedure çağırır.

        Döndürür: (cikis_parametreleri, sonuc_kumeleri)
          cikis_parametreleri: OUT parametrelerin son değerleri (tuple)
          sonuc_kumeleri: procedure içindeki her SELECT için sözlük listesi
        """
        baglanti = baglanti_al()
        try:
            imlec = baglanti.cursor()
            cikis = imlec.callproc(ad, list(parametreler))
            kumeler = []
            for sonuc in imlec.stored_results():
                sutunlar = sonuc.column_names
                kumeler.append([dict(zip(sutunlar, satir)) for satir in sonuc.fetchall()])
            return cikis, kumeler
        finally:
            baglanti.close()
