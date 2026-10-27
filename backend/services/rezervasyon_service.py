"""Rezervasyon iş mantığı."""
from datetime import date

from repositories.misafir_repository import MisafirRepository
from repositories.oda_repository import OdaRepository
from repositories.rezervasyon_repository import RezervasyonRepository
from utils.dogrulama import opsiyonel_tarih, pozitif_tamsayi, sinirli_tamsayi, tarih_coz
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

    def listele(self, filtreler):
        """Personel için tüm rezervasyonlar. filtreler: istek parametreleri (request.args)."""
        durum = filtreler.get("durum")
        if durum is not None and durum not in GECERLI_DURUMLAR:
            raise UygulamaHatasi("'durum' şunlardan biri olmalıdır: " + ", ".join(GECERLI_DURUMLAR) + ".")
        misafir_id = pozitif_tamsayi(filtreler.get("misafir_id"), "misafir_id")
        oda_id = pozitif_tamsayi(filtreler.get("oda_id"), "oda_id")
        baslangic = opsiyonel_tarih(filtreler.get("giris_baslangic"), "giris_baslangic")
        bitis = opsiyonel_tarih(filtreler.get("giris_bitis"), "giris_bitis")
        if baslangic and bitis and bitis < baslangic:
            raise UygulamaHatasi("'giris_bitis', 'giris_baslangic' tarihinden önce olamaz.")
        limit = sinirli_tamsayi(filtreler.get("limit"), "limit", 50, 1, 200)
        offset = sinirli_tamsayi(filtreler.get("offset"), "offset", 0, 0, 1_000_000)

        toplam, liste = self._rezervasyonlar.ara(
            durum, misafir_id, oda_id, baslangic, bitis, limit, offset)
        return {"toplam": toplam, "limit": limit, "offset": offset,
                "rezervasyonlar": [r.sozluk() for r in liste]}

    def getir(self, kullanici, rezervasyon_id):
        rezervasyon = self._rezervasyonlar.bul_id(rezervasyon_id)
        if rezervasyon is None:
            raise BulunamadiHatasi("Rezervasyon bulunamadı.")
        if kullanici["rol"] == "misafir" and rezervasyon.misafir_id != kullanici["misafir_id"]:
            raise YasakHatasi("Bu rezervasyon size ait değil.")
        return rezervasyon.sozluk()

    def onayla(self, rezervasyon_id):
        """Misafirin açtığı 'beklemede' rezervasyonu personel onaylar."""
        rezervasyon = self._rezervasyonlar.bul_id(rezervasyon_id)
        if rezervasyon is None:
            raise BulunamadiHatasi("Rezervasyon bulunamadı.")
        if rezervasyon.durum != "beklemede":
            raise UygulamaHatasi(
                "Yalnızca beklemedeki rezervasyon onaylanabilir. Şu anki durum: " + rezervasyon.durum + ".")
        if rezervasyon.giris_tarihi < date.today():
            raise UygulamaHatasi("Giriş tarihi geçmiş rezervasyon onaylanamaz.")
        if not self._rezervasyonlar.onayla(rezervasyon_id):
            raise UygulamaHatasi("Rezervasyon onaylanamadı, durumu değişmiş olabilir.", 409)
        return self._rezervasyonlar.bul_id(rezervasyon_id).sozluk()

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
