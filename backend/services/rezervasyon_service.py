"""Rezervasyon iş mantığı."""
from datetime import date

from repositories.misafir_repository import MisafirRepository
from repositories.oda_repository import OdaRepository
from repositories.rezervasyon_repository import RezervasyonRepository
from utils.dogrulama import pozitif_tamsayi, tarih_coz
from utils.hatalar import BulunamadiHatasi, UygulamaHatasi, YasakHatasi


GECERLI_DURUMLAR = ("beklemede", "onayli", "iptal", "tamamlandi")


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

    def misafir_rezervasyonlari(self, kullanici, durum=None):
        """Giriş yapmış misafirin kendi rezervasyonları."""
        if durum is not None and durum not in GECERLI_DURUMLAR:
            raise UygulamaHatasi("'durum' şunlardan biri olmalıdır: " + ", ".join(GECERLI_DURUMLAR) + ".")
        liste = self._rezervasyonlar.misafire_ait(kullanici["misafir_id"], durum)
        return {"rezervasyon_sayisi": len(liste), "rezervasyonlar": [r.sozluk() for r in liste]}

    def iptal_et(self, kullanici, rezervasyon_id):
        rezervasyon = self._rezervasyonlar.bul_id(rezervasyon_id)
        if rezervasyon is None:
            raise BulunamadiHatasi("Rezervasyon bulunamadı.")

        # Sıra önemli: önce yetki (başkasının rezervasyonu hakkında bilgi sızmasın),
        # sonra rezervasyonun durumu, en sonda misafire özel tarih kuralı.
        if kullanici["rol"] == "misafir" and rezervasyon.misafir_id != kullanici["misafir_id"]:
            raise YasakHatasi("Bu rezervasyon size ait değil.")

        if rezervasyon.durum == "iptal":
            raise UygulamaHatasi("Rezervasyon zaten iptal edilmiş.")
        if rezervasyon.durum == "tamamlandi":
            raise UygulamaHatasi("Tamamlanmış rezervasyon iptal edilemez.")
        if self._rezervasyonlar.konaklama_var_mi(rezervasyon_id):
            raise UygulamaHatasi("Check-in yapılmış rezervasyon iptal edilemez.")

        if kullanici["rol"] == "misafir" and rezervasyon.giris_tarihi <= date.today():
            raise UygulamaHatasi(
                "Giriş günü gelen rezervasyonu iptal edemezsiniz, lütfen resepsiyonla görüşün.")

        if not self._rezervasyonlar.iptal_et(rezervasyon_id):
            raise UygulamaHatasi("Rezervasyon iptal edilemedi, durumu değişmiş olabilir.", 409)
        return self._rezervasyonlar.bul_id(rezervasyon_id).sozluk()

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
