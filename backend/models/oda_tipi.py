"""OdaTipi tablosunun Entity sınıfı."""
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class OdaTipi:
    tip_id: int
    tip_adi: str
    kapasite: int
    aciklama: Optional[str]
    temel_fiyat: Decimal

    @classmethod
    def satirdan(cls, satir):
        return cls(
            tip_id=satir["tip_id"],
            tip_adi=satir["tip_adi"],
            kapasite=satir["kapasite"],
            aciklama=satir["aciklama"],
            temel_fiyat=satir["temel_fiyat"],
        )

    def sozluk(self):
        return asdict(self)
