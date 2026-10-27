"""Rezervasyon tablosunun Entity sınıfı (oda numarasıyla birlikte)."""
from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass
class Rezervasyon:
    rezervasyon_id: int
    misafir_id: int
    oda_id: int
    oda_no: str
    giris_tarihi: date
    cikis_tarihi: date
    kisi_sayisi: int
    durum: str
    olusturma_tarihi: datetime

    @classmethod
    def satirdan(cls, satir):
        return cls(
            rezervasyon_id=satir["rezervasyon_id"],
            misafir_id=satir["misafir_id"],
            oda_id=satir["oda_id"],
            oda_no=satir["oda_no"],
            giris_tarihi=satir["giris_tarihi"],
            cikis_tarihi=satir["cikis_tarihi"],
            kisi_sayisi=satir["kisi_sayisi"],
            durum=satir["durum"],
            olusturma_tarihi=satir["olusturma_tarihi"],
        )

    def sozluk(self):
        return asdict(self)
