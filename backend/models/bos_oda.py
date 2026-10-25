"""sp_bos_odalar prosedürünün döndürdüğü bir satırın Entity sınıfı."""
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class BosOda:
    oda_id: int
    oda_no: str
    kat: int
    tip_id: int
    tip_adi: str
    kapasite: int
    aciklama: Optional[str]
    gece_sayisi: int
    toplam_tutar: Decimal

    @classmethod
    def satirdan(cls, satir):
        return cls(
            oda_id=satir["oda_id"],
            oda_no=satir["oda_no"],
            kat=satir["kat"],
            tip_id=satir["tip_id"],
            tip_adi=satir["tip_adi"],
            kapasite=satir["kapasite"],
            aciklama=satir["aciklama"],
            gece_sayisi=satir["gece_sayisi"],
            toplam_tutar=satir["toplam_tutar"],
        )

    def sozluk(self):
        return asdict(self)
