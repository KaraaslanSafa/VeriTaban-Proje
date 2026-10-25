"""Oda iş mantığı."""
from datetime import date

from repositories.oda_repository import OdaRepository
from utils.dogrulama import pozitif_tamsayi, tarih_coz
from utils.hatalar import BulunamadiHatasi, UygulamaHatasi

GECERLI_DURUMLAR = ("bos", "dolu", "temizlikte", "bakimda")


class OdaService:
    def __init__(self, oda_repo=None):
        self._odalar = oda_repo or OdaRepository()

    def bos_odalari_ara(self, giris, cikis, tip_id=None, kisi=None):
        giris_tarihi = tarih_coz(giris, "giris")
        cikis_tarihi = tarih_coz(cikis, "cikis")
        tip_id = pozitif_tamsayi(tip_id, "tip_id")
        kisi = pozitif_tamsayi(kisi, "kisi")

        if giris_tarihi < date.today():
            raise UygulamaHatasi("Giriş tarihi geçmişte olamaz.")
        if cikis_tarihi <= giris_tarihi:
            raise UygulamaHatasi("Çıkış tarihi giriş tarihinden sonra olmalıdır.")

        odalar = self._odalar.bos_odalar(giris_tarihi, cikis_tarihi, tip_id, kisi)
        return {
            "giris": giris_tarihi.isoformat(),
            "cikis": cikis_tarihi.isoformat(),
            "gece_sayisi": (cikis_tarihi - giris_tarihi).days,
            "oda_sayisi": len(odalar),
            "odalar": [oda.sozluk() for oda in odalar],
        }

    def listele(self, tip_id=None, durum=None):
        tip_id = pozitif_tamsayi(tip_id, "tip_id")
        if durum is not None and durum not in GECERLI_DURUMLAR:
            raise UygulamaHatasi(
                "'durum' şunlardan biri olmalıdır: " + ", ".join(GECERLI_DURUMLAR) + ".")
        odalar = self._odalar.tum(tip_id, durum)
        return {"oda_sayisi": len(odalar), "odalar": [oda.sozluk() for oda in odalar]}

    def getir(self, oda_id):
        oda = self._odalar.bul_id(oda_id)
        if oda is None:
            raise BulunamadiHatasi("Oda bulunamadı.")
        return oda.sozluk()
