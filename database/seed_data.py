#!/usr/bin/env python3
"""
Otel veritabani icin ornek veri uretici.

Calistirma (proje kok klasorunden):
    python database/seed_data.py            # veritabani bossa veri uretir
    python database/seed_data.py --reset    # once tum tablolari bosaltir, sonra uretir

Uretilenler:
    3 oda tipi, 24 oda, sezon fiyatlari (2026-2027), 8 personel, 6 ek hizmet,
    50 misafir, 200 rezervasyon (cakismasiz), gecmis/guncel konaklamalar,
    odemeler, temizlik kayitlari ve giris hesaplari.

Giris hesaplari:
    admin@otel.com          / Admin123!        (yonetici)
    resepsiyon@otel.com     / Resepsiyon123!   (resepsiyon)
    resepsiyon2@otel.com    / Resepsiyon123!   (resepsiyon)
    <misafir e-postasi>     / Misafir123!      (misafir)
"""
import hashlib
import os
import random
import secrets
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

KOK = Path(__file__).resolve().parent.parent
load_dotenv(KOK / ".env")

random.seed(42)  # her calistirmada ayni veri uretilsin

REZERVASYON_SAYISI = 200
TARIH_BAS = date(2026, 6, 1)
TARIH_SON = date(2027, 2, 28)
BAKIM_ODASI = "206"

TR_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")

ERKEK_ADLAR = ["Ahmet", "Mehmet", "Mustafa", "Ali", "Hasan", "Hüseyin", "İbrahim", "Yusuf",
               "Emre", "Burak", "Can", "Cem", "Kerem", "Murat", "Oğuz", "Serkan", "Tolga",
               "Volkan", "Barış", "Onur", "Kaan", "Efe", "Arda", "Deniz", "Selim"]
KADIN_ADLAR = ["Ayşe", "Fatma", "Emine", "Hatice", "Zeynep", "Elif", "Merve", "Büşra", "Esra",
               "Selin", "Ece", "Defne", "Gizem", "Pınar", "Seda", "Sibel", "Tuğba", "Burcu",
               "Derya", "Aslı", "Melis", "İrem", "Naz", "Yağmur", "Gamze"]
SOYADLAR = ["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Yıldırım", "Öztürk", "Aydın",
            "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara", "Koç", "Kurt",
            "Özkan", "Şimşek", "Polat", "Korkmaz", "Güneş", "Erdoğan", "Taş", "Acar", "Aksoy",
            "Bulut", "Tekin", "Avcı"]

ODA_TIPLERI = [
    # ad, kapasite, aciklama, temel fiyat
    ("standart", 2, "Çift kişilik yataklı, şehir manzaralı standart oda", 1500),
    ("deluxe", 3, "Geniş, balkonlu deluxe oda", 2500),
    ("suit", 4, "Oturma alanlı, deniz manzaralı suit", 4500),
]

# oda no, kat, tip
ODALAR = (
    [(f"10{i}", 1, "standart") for i in range(1, 7)]
    + [(f"20{i}", 2, "standart") for i in range(1, 7)]
    + [(f"30{i}", 3, "deluxe") for i in range(1, 7)]
    + [(f"40{i}", 4, "suit") for i in range(1, 5)]
    + [(f"40{i}", 4, "deluxe") for i in range(5, 7)]
)

# (baslangic ay-gun, bitis ay-gun, carpan)
SEZONLAR = [
    ((1, 1), (3, 31), 0.8),    # kis
    ((4, 1), (5, 31), 1.0),    # ilkbahar
    ((6, 1), (9, 15), 1.5),    # yaz
    ((9, 16), (11, 30), 1.1),  # sonbahar
    ((12, 1), (12, 31), 1.3),  # yilbasi
]

PERSONEL = [
    ("Ahmet", "Yılmaz", "yonetici", date(2019, 3, 1)),
    ("Elif", "Demir", "resepsiyon", date(2021, 6, 15)),
    ("Mehmet", "Kaya", "resepsiyon", date(2022, 2, 1)),
    ("Zeynep", "Arslan", "resepsiyon", date(2023, 9, 10)),
    ("Fatma", "Çelik", "kat_gorevlisi", date(2020, 5, 20)),
    ("Hasan", "Şahin", "kat_gorevlisi", date(2021, 11, 3)),
    ("Ayşe", "Öztürk", "kat_gorevlisi", date(2022, 7, 18)),
    ("Mustafa", "Aydın", "kat_gorevlisi", date(2024, 4, 5)),
]

EK_HIZMETLER = [
    ("Kahvaltı", 250),
    ("Spa", 800),
    ("Otopark", 150),
    ("Oda Servisi", 350),
    ("Çamaşır", 200),
    ("Havalimanı Transferi", 600),
]

TABLOLAR = ["IslemLog", "TemizlikKaydi", "Odeme", "KonaklamaHizmeti", "Konaklama", "Rezervasyon",
            "Kullanici", "Misafir", "Personel", "EkHizmet", "SezonFiyati", "Oda", "OdaTipi"]


def ascii_yap(metin):
    return metin.translate(TR_ASCII).lower()


def sifre_hash(parola, iterasyon=150_000):
    """Werkzeug (Flask) check_password_hash ile uyumlu PBKDF2 ozeti uretir."""
    tuz = secrets.token_hex(8)
    ozet = hashlib.pbkdf2_hmac("sha256", parola.encode(), tuz.encode(), iterasyon).hex()
    return f"pbkdf2:sha256:{iterasyon}${tuz}${ozet}"


def baglan():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "otel_db"),
        charset="utf8mb4",
    )


def tablolari_bosalt(cur):
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for tablo in TABLOLAR:
        cur.execute(f"TRUNCATE TABLE {tablo}")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")


# ---------------------------------------------------------------- temel veriler

def oda_tiplerini_ekle(cur):
    tipler = {}
    for ad, kapasite, aciklama, fiyat in ODA_TIPLERI:
        cur.execute(
            "INSERT INTO OdaTipi (tip_adi, kapasite, aciklama, temel_fiyat) VALUES (%s,%s,%s,%s)",
            (ad, kapasite, aciklama, fiyat))
        tipler[ad] = {"id": cur.lastrowid, "kapasite": kapasite, "fiyat": fiyat}
    return tipler


def odalari_ekle(cur, tipler):
    odalar = []
    for no, kat, tip in ODALAR:
        cur.execute("INSERT INTO Oda (oda_no, kat, tip_id) VALUES (%s,%s,%s)",
                    (no, kat, tipler[tip]["id"]))
        odalar.append({"id": cur.lastrowid, "no": no, "kapasite": tipler[tip]["kapasite"]})
    return odalar


def sezon_fiyatlarini_ekle(cur, tipler):
    for tip in tipler.values():
        for yil in (2026, 2027):
            for (bay, bgun), (eay, egun), carpan in SEZONLAR:
                fiyat = round(tip["fiyat"] * carpan / 50) * 50
                cur.execute(
                    "INSERT INTO SezonFiyati (tip_id, baslangic_tarihi, bitis_tarihi, gecelik_fiyat) "
                    "VALUES (%s,%s,%s,%s)",
                    (tip["id"], date(yil, bay, bgun), date(yil, eay, egun), fiyat))


def personeli_ekle(cur):
    kayitlar = []
    for ad, soyad, gorev, tarih in PERSONEL:
        cur.execute("INSERT INTO Personel (ad, soyad, gorev, ise_giris_tarihi) VALUES (%s,%s,%s,%s)",
                    (ad, soyad, gorev, tarih))
        kayitlar.append({"id": cur.lastrowid, "gorev": gorev})
    return kayitlar


def hizmetleri_ekle(cur):
    hizmetler = []
    for ad, fiyat in EK_HIZMETLER:
        cur.execute("INSERT INTO EkHizmet (hizmet_adi, birim_fiyat) VALUES (%s,%s)", (ad, fiyat))
        hizmetler.append((cur.lastrowid, fiyat))
    return hizmetler


def misafirleri_ekle(cur, adet=50):
    adlar = ERKEK_ADLAR + KADIN_ADLAR
    random.shuffle(adlar)
    kullanilan_tc = set()
    kayitlar = []
    for i in range(1, adet + 1):
        ad = adlar[(i - 1) % len(adlar)]
        soyad = random.choice(SOYADLAR)
        while True:
            tc = str(random.randint(10**10, 10**11 - 1))
            if tc not in kullanilan_tc:
                kullanilan_tc.add(tc)
                break
        telefon = "05{} {:03d} {:02d} {:02d}".format(
            random.choice([30, 32, 33, 35, 36, 42, 44, 50, 53, 54, 55]),
            random.randint(0, 999), random.randint(0, 99), random.randint(0, 99))
        eposta = f"{ascii_yap(ad)}.{ascii_yap(soyad)}{i}@example.com"
        dogum = date(1960, 1, 1) + timedelta(days=random.randint(0, (date(2004, 12, 31) - date(1960, 1, 1)).days))
        cur.execute(
            "INSERT INTO Misafir (ad, soyad, tc_pasaport_no, telefon, eposta, dogum_tarihi) "
            "VALUES (%s,%s,%s,%s,%s,%s)", (ad, soyad, tc, telefon, eposta, dogum))
        kayitlar.append({"id": cur.lastrowid, "eposta": eposta})
    return kayitlar


def kullanicilari_ekle(cur, personel, misafirler):
    admin_hash = sifre_hash("Admin123!")
    resp_hash = sifre_hash("Resepsiyon123!")
    misafir_hash = sifre_hash("Misafir123!")

    yoneticiler = [p for p in personel if p["gorev"] == "yonetici"]
    resepsiyonlar = [p for p in personel if p["gorev"] == "resepsiyon"]

    cur.execute("INSERT INTO Kullanici (kullanici_adi, sifre_hash, rol, personel_id) VALUES (%s,%s,'yonetici',%s)",
                ("admin@otel.com", admin_hash, yoneticiler[0]["id"]))
    for n, p in enumerate(resepsiyonlar[:2], start=1):
        ad = "resepsiyon@otel.com" if n == 1 else f"resepsiyon{n}@otel.com"
        cur.execute("INSERT INTO Kullanici (kullanici_adi, sifre_hash, rol, personel_id) VALUES (%s,%s,'resepsiyon',%s)",
                    (ad, resp_hash, p["id"]))
    for m in misafirler:
        cur.execute("INSERT INTO Kullanici (kullanici_adi, sifre_hash, rol, misafir_id) VALUES (%s,%s,'misafir',%s)",
                    (m["eposta"], misafir_hash, m["id"]))


# ---------------------------------------------------------- rezervasyon / konaklama

class Baglam:
    """Uretim sirasinda lazim olan ortak veriler."""
    def __init__(self, misafirler, resepsiyon, kat_gorevlileri, hizmetler, bugun):
        self.misafirler = misafirler
        self.resepsiyon = resepsiyon
        self.kat_gorevlileri = kat_gorevlileri
        self.hizmetler = hizmetler
        self.bugun = bugun
        self.araliklar = {}  # oda_id -> [(giris, cikis)] (iptal olmayanlar)

    def musait(self, oda_id, giris, cikis):
        return all(cikis <= g or giris >= c for g, c in self.araliklar.get(oda_id, []))

    def kaydet(self, oda_id, giris, cikis):
        self.araliklar.setdefault(oda_id, []).append((giris, cikis))


def konaklama_ac(cur, ctx, rez_id, oda_id, giris, cikis, kapali):
    """Check-in kaydi acar. kapali=True ise check-out, ek hizmet, odeme ve temizlik de eklenir."""
    gir = datetime.combine(giris, time(14, random.randint(0, 59)))
    cik = datetime.combine(cikis, time(11, random.randint(0, 59))) if kapali else None
    cur.execute(
        "INSERT INTO Konaklama (rezervasyon_id, gercek_giris, gercek_cikis, personel_id, cikis_personel_id) "
        "VALUES (%s,%s,%s,%s,%s)",
        (rez_id, gir, cik, random.choice(ctx.resepsiyon), random.choice(ctx.resepsiyon) if kapali else None))
    kon_id = cur.lastrowid

    son = cik if kapali else datetime.now()
    sure_sn = max(int((son - gir).total_seconds()), 3600)
    for _ in range(random.choice([0, 0, 1, 2, 3])):
        hizmet_id, fiyat = random.choice(ctx.hizmetler)
        cur.execute(
            "INSERT INTO KonaklamaHizmeti (konaklama_id, hizmet_id, adet, birim_fiyat, tarih) "
            "VALUES (%s,%s,%s,%s,%s)",
            (kon_id, hizmet_id, random.randint(1, 3), fiyat, gir + timedelta(seconds=random.randint(0, sure_sn - 1))))

    if kapali:
        cur.execute("SELECT fn_konaklama_oda_tutari(%s) + fn_konaklama_hizmet_tutari(%s)", (kon_id, kon_id))
        tutar = cur.fetchone()[0]
        cur.execute("INSERT INTO Odeme (konaklama_id, tutar, odeme_turu, tarih) VALUES (%s,%s,%s,%s)",
                    (kon_id, tutar, random.choice(["nakit", "kart"]), cik))
        cur.execute("INSERT INTO TemizlikKaydi (oda_id, personel_id, tarih, durum) VALUES (%s,%s,%s,'tamamlandi')",
                    (oda_id, random.choice(ctx.kat_gorevlileri), cikis))


def rezervasyon_ekle(cur, ctx, oda, giris, cikis, durum, kisi=None):
    kisi = kisi or random.randint(1, oda["kapasite"])
    misafir_id = random.choice(ctx.misafirler)
    olusturma = min(
        datetime.combine(giris, time(random.randint(8, 20), random.randint(0, 59)))
        - timedelta(days=random.randint(1, 45)),
        datetime.now() - timedelta(hours=1))
    cur.execute(
        "INSERT INTO Rezervasyon (misafir_id, oda_id, giris_tarihi, cikis_tarihi, kisi_sayisi, durum, olusturma_tarihi) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (misafir_id, oda["id"], giris, cikis, kisi, durum, olusturma))
    rez_id = cur.lastrowid

    if durum != "iptal":
        ctx.kaydet(oda["id"], giris, cikis)
    if durum == "tamamlandi":
        konaklama_ac(cur, ctx, rez_id, oda["id"], giris, cikis, kapali=True)
    elif durum == "onayli" and giris < ctx.bugun < cikis:
        konaklama_ac(cur, ctx, rez_id, oda["id"], giris, cikis, kapali=False)
    return rez_id


def rezervasyonlari_uret(cur, ctx, odalar):
    bugun = ctx.bugun
    havuz = [o for o in odalar if o["no"] != BAKIM_ODASI]
    oda_no = {o["no"]: o for o in odalar}
    sayac = 0

    # Videoda gosterilebilsin diye bugune ait iki sabit kayit:
    #  - 101: 2 gundur kaliyor, bugun cikis yapacak  (vw_bugun_giris_cikis -> CIKIS)
    #  - 301: bugun giris yapacak, henuz check-in yok (vw_bugun_giris_cikis -> GIRIS)
    rez_id = rezervasyon_ekle(cur, ctx, oda_no["101"], bugun - timedelta(days=2), bugun, "onayli", kisi=2)
    # cikis gunu bugun oldugu icin yukaridaki kayit otomatik acilmaz; acik konaklamayi elle ac
    konaklama_ac(cur, ctx, rez_id, oda_no["101"]["id"], bugun - timedelta(days=2), bugun, kapali=False)
    rezervasyon_ekle(cur, ctx, oda_no["301"], bugun, bugun + timedelta(days=3), "onayli", kisi=2)
    sayac += 2

    gun_araligi = (TARIH_SON - TARIH_BAS).days
    while sayac < REZERVASYON_SAYISI:
        oda = random.choice(havuz)
        sure = random.choices(range(1, 11), weights=[3, 5, 6, 6, 5, 4, 3, 2, 1, 1])[0]
        giris = TARIH_BAS + timedelta(days=random.randint(0, gun_araligi))
        cikis = giris + timedelta(days=sure)

        if cikis <= bugun:
            durum = "iptal" if random.random() < 0.08 else "tamamlandi"
        elif giris < bugun:
            durum = "onayli"  # su an konaklayan misafir
        else:
            durum = random.choices(["onayli", "beklemede", "iptal"], weights=[60, 25, 15])[0]

        if durum != "iptal" and not ctx.musait(oda["id"], giris, cikis):
            continue

        rezervasyon_ekle(cur, ctx, oda, giris, cikis, durum)
        sayac += 1


def oda_durumlarini_ayarla(cur, bugun):
    """Gecmis konaklamalar trigger'lari tetikledigi icin oda durumlarini gercege gore yeniden kur."""
    cur.execute("UPDATE Oda SET durum = 'bos'")
    cur.execute(
        "UPDATE Oda SET durum = 'dolu' WHERE oda_id IN ("
        " SELECT r.oda_id FROM Konaklama k"
        " JOIN Rezervasyon r ON r.rezervasyon_id = k.rezervasyon_id"
        " WHERE k.gercek_cikis IS NULL)")
    cur.execute("UPDATE Oda SET durum = 'bakimda' WHERE oda_no = %s", (BAKIM_ODASI,))

    # Temizlik bekleyen bir oda (kat gorevlisi henuz atanmamis)
    cur.execute("SELECT oda_id FROM Oda WHERE durum = 'bos' ORDER BY oda_no = '104' DESC, oda_no LIMIT 1")
    satir = cur.fetchone()
    if satir:
        cur.execute("UPDATE Oda SET durum = 'temizlikte' WHERE oda_id = %s", (satir[0],))
        cur.execute("INSERT INTO TemizlikKaydi (oda_id, personel_id, tarih, durum) VALUES (%s, NULL, %s, 'bekliyor')",
                    (satir[0], bugun))


def ozet_yazdir(cur):
    print("\n--- Özet ---")
    for tablo in ["OdaTipi", "Oda", "SezonFiyati", "Personel", "Kullanici", "Misafir", "Rezervasyon",
                  "Konaklama", "EkHizmet", "KonaklamaHizmeti", "Odeme", "TemizlikKaydi", "IslemLog"]:
        cur.execute(f"SELECT COUNT(*) FROM {tablo}")
        print(f"{tablo:18s}: {cur.fetchone()[0]}")
    cur.execute("SELECT durum, COUNT(*) FROM Rezervasyon GROUP BY durum ORDER BY durum")
    print("\nRezervasyon durumları:", ", ".join(f"{d}={n}" for d, n in cur.fetchall()))
    cur.execute("SELECT durum, COUNT(*) FROM Oda GROUP BY durum ORDER BY durum")
    print("Oda durumları        :", ", ".join(f"{d}={n}" for d, n in cur.fetchall()))
    cur.execute("SELECT islem_turu, COUNT(*) FROM vw_bugun_giris_cikis GROUP BY islem_turu")
    print("Bugünkü giriş/çıkış  :", ", ".join(f"{t}={n}" for t, n in cur.fetchall()) or "yok")
    print("\nGiriş hesapları:")
    print("  admin@otel.com       / Admin123!       (yönetici)")
    print("  resepsiyon@otel.com  / Resepsiyon123!  (resepsiyon)")
    print("  misafir e-postaları  / Misafir123!     (örn. Kullanici tablosundan bak)")


def main():
    sifirla = "--reset" in sys.argv
    try:
        conn = baglan()
    except mysql.connector.Error as hata:
        print(f"MySQL'e bağlanılamadı: {hata}")
        print(".env dosyasındaki DB_PASSWORD değerini ve MySQL servisinin açık olduğunu kontrol et.")
        sys.exit(1)

    cur = conn.cursor(buffered=True)
    try:
        cur.execute("SELECT COUNT(*) FROM Misafir")
        if cur.fetchone()[0] > 0 and not sifirla:
            print("Veritabanında zaten veri var. Silip yeniden üretmek için:")
            print("    python database/seed_data.py --reset")
            return
        if sifirla:
            tablolari_bosalt(cur)

        print("Temel veriler ekleniyor...")
        tipler = oda_tiplerini_ekle(cur)
        odalar = odalari_ekle(cur, tipler)
        sezon_fiyatlarini_ekle(cur, tipler)
        personel = personeli_ekle(cur)
        hizmetler = hizmetleri_ekle(cur)
        misafirler = misafirleri_ekle(cur)
        kullanicilari_ekle(cur, personel, misafirler)

        ctx = Baglam(
            misafirler=[m["id"] for m in misafirler],
            resepsiyon=[p["id"] for p in personel if p["gorev"] == "resepsiyon"],
            kat_gorevlileri=[p["id"] for p in personel if p["gorev"] == "kat_gorevlisi"],
            hizmetler=hizmetler,
            bugun=date.today(),
        )

        print(f"{REZERVASYON_SAYISI} rezervasyon üretiliyor (trigger'lar çakışmayı denetler)...")
        rezervasyonlari_uret(cur, ctx, odalar)
        oda_durumlarini_ayarla(cur, ctx.bugun)

        conn.commit()
        ozet_yazdir(cur)
        print("\nÖrnek veri başarıyla yüklendi.")
    except mysql.connector.Error as hata:
        conn.rollback()
        print(f"\nVeritabanı hatası, işlem geri alındı: {hata}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()