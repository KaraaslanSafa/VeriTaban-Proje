"""Rezervasyon iş mantığı."""
from datetime import date

from repositories.misafir_repository import MisafirRepository
from repositories.oda_repository import OdaRepository
from repositories.rezervasyon_repository import RezervasyonRepository
from utils.dogrulama import pozitif_tamsayi, tarih_coz
from utils.hatalar import BulunamadiHatasi, UygulamaHatasi, YasakHatasi


class RezervasyonService:
    def __init__(self, rezervasyon_repo=None, oda_repo=None, misafir_repo=None):
        self._rezervasyonlar = rezervasyon_repo or RezervasyonRepository()
        self._odalar = oda_repo or OdaRepository()
        self._misafirler = misafir_repo or MisafirRepository()

    def olustur(self, kullanici, veri):
        """kullanici: token'dan gelen bilgiler (rol, misafir_id ...). veri: istek gövdesi."""
        oda_id = pozitif_tamsayi(veri.get("oda_id"), "oda_id", zorunlu=True)
        giris = tarih_coz(veri.get("giris_tarihi"), "giris_tarihi")
        cikis = tarih_coz(veri.get("cikis_tarihi"), "cikis_tarihi")
        kisi = pozitif_tamsayi(veri.get("kisi_sayisi"), "kisi_sayisi") or 1

        if giris < date.today():
            raise UygulamaHatasi("Giriş tarihi geçmişte olamaz.")
        if cikis <= giris:
            raise UygulamaHatasi("Çıkış tarihi giriş tarihinden sonra olmalıdır.")

        misafir_id, durum = self._misafir_ve_durum(kullanici, veri)

        oda = self._odalar.bul_id(oda_id)
        if oda is None:
            raise BulunamadiHatasi("Oda bulunamadı.")
        if oda.durum == "bakimda":
            raise UygulamaHatasi("Bu oda bakımda, rezerve edilemez.")
        if kisi > oda.kapasite:
            raise UygulamaHatasi(f"Bu odanın kapasitesi {oda.kapasite} kişidir.")
        if self._misafirler.bul_id(misafir_id) is None:
            raise BulunamadiHatasi("Misafir bulunamadı.")

        # Tarih çakışması varsa veritabanındaki trigger hata fırlatır, app.py bunu 409'a çevirir.
        yeni_id = self._rezervasyonlar.ekle(misafir_id, oda_id, giris, cikis, kisi, durum)

        sonuc = self._rezervasyonlar.bul_id(yeni_id).sozluk()
        sonuc["gece_sayisi"] = (cikis - giris).days
        sonuc["toplam_tutar"] = self._odalar.oda_tutari(oda.tip_id, giris, cikis)
        return sonuc

    @staticmethod
    def _misafir_ve_durum(kullanici, veri):
        """Rezervasyonun kimin adına ve hangi durumla açılacağını belirler.

        Misafir: yalnızca kendi adına, 'beklemede' (resepsiyon onaylayacak).
        Resepsiyon/yönetici: istediği misafir adına, doğrudan 'onayli'.
        """
        istenen = pozitif_tamsayi(veri.get("misafir_id"), "misafir_id")
        if kullanici["rol"] == "misafir":
            kendi = kullanici["misafir_id"]
            if istenen is not None and istenen != kendi:
                raise YasakHatasi("Başka bir misafir adına rezervasyon yapamazsınız.")
            return kendi, "beklemede"
        if istenen is None:
            raise UygulamaHatasi("'misafir_id' zorunludur.")
        return istenen, "onayli"
