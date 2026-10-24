"""Uygulamaya özel hata sınıfları. Her biri bir HTTP durum koduna karşılık gelir."""


class UygulamaHatasi(Exception):
    """İş kuralı veya geçersiz istek hatası (400)."""
    durum_kodu = 400

    def __init__(self, mesaj, durum_kodu=None):
        super().__init__(mesaj)
        self.mesaj = mesaj
        if durum_kodu is not None:
            self.durum_kodu = durum_kodu


class YetkisizHatasi(UygulamaHatasi):
    """Giriş yapılmamış ya da bilgiler yanlış (401)."""
    durum_kodu = 401


class YasakHatasi(UygulamaHatasi):
    """Giriş yapılmış ama bu işlem için rolü uygun değil (403)."""
    durum_kodu = 403


class BulunamadiHatasi(UygulamaHatasi):
    """İstenen kayıt yok (404)."""
    durum_kodu = 404


class CakismaHatasi(UygulamaHatasi):
    """Mevcut durumla çakışan işlem, örneğin dolu oda (409)."""
    durum_kodu = 409
