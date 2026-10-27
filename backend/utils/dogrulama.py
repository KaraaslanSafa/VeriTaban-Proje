"""İstekten gelen değerleri (genelde metin) doğrulayıp doğru türe çeviren yardımcılar."""
from datetime import datetime

from utils.hatalar import UygulamaHatasi


def tarih_coz(deger, alan_adi):
    """'2026-11-23' biçimindeki metni date nesnesine çevirir."""
    if deger is None or str(deger).strip() == "":
        raise UygulamaHatasi(f"'{alan_adi}' tarihi zorunludur (biçim: YYYY-AA-GG).")
    try:
        return datetime.strptime(str(deger).strip(), "%Y-%m-%d").date()
    except ValueError:
        raise UygulamaHatasi(
            f"'{alan_adi}' tarihi geçersiz. Biçim: YYYY-AA-GG (örnek: 2026-11-23).")


def pozitif_tamsayi(deger, alan_adi, zorunlu=False):
    """1 ve üzeri tam sayı bekler. Boşsa ve zorunlu değilse None döndürür."""
    if deger is None or str(deger).strip() == "":
        if zorunlu:
            raise UygulamaHatasi(f"'{alan_adi}' zorunludur.")
        return None
    try:
        sayi = int(str(deger).strip())
    except ValueError:
        raise UygulamaHatasi(f"'{alan_adi}' bir tam sayı olmalıdır.")
    if sayi < 1:
        raise UygulamaHatasi(f"'{alan_adi}' 1 veya daha büyük olmalıdır.")
    return sayi


def opsiyonel_tarih(deger, alan_adi):
    """Boşsa None, doluysa date döndürür (süzme parametreleri için)."""
    if deger is None or str(deger).strip() == "":
        return None
    return tarih_coz(deger, alan_adi)


def sinirli_tamsayi(deger, alan_adi, varsayilan, en_az, en_cok):
    """Belirli bir aralıkta tam sayı bekler (sayfalama için). Boşsa varsayılanı döndürür."""
    if deger is None or str(deger).strip() == "":
        return varsayilan
    try:
        sayi = int(str(deger).strip())
    except ValueError:
        raise UygulamaHatasi(f"'{alan_adi}' bir tam sayı olmalıdır.")
    if not en_az <= sayi <= en_cok:
        raise UygulamaHatasi(f"'{alan_adi}' {en_az} ile {en_cok} arasında olmalıdır.")
    return sayi
