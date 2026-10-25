"""Oda tablosunun Entity sınıfı (oda tipi bilgisiyle birlikte)."""
from dataclasses import asdict, dataclass


@dataclass
class Oda:
    oda_id: int
    oda_no: str
    kat: int
    durum: str
    tip_id: int
    tip_adi: str
    kapasite: int

    @classmethod
    def satirdan(cls, satir):
        return cls(
            oda_id=satir["oda_id"],
            oda_no=satir["oda_no"],
            kat=satir["kat"],
            durum=satir["durum"],
            tip_id=satir["tip_id"],
            tip_adi=satir["tip_adi"],
            kapasite=satir["kapasite"],
        )

    def sozluk(self):
        return asdict(self)
