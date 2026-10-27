"""Misafir tablosunun Entity sınıfı."""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Misafir:
    misafir_id: int
    ad: str
    soyad: str
    tc_pasaport_no: str
    telefon: Optional[str]
    eposta: str
    dogum_tarihi: Optional[date]

    @classmethod
    def satirdan(cls, satir):
        return cls(
            misafir_id=satir["misafir_id"],
            ad=satir["ad"],
            soyad=satir["soyad"],
            tc_pasaport_no=satir["tc_pasaport_no"],
            telefon=satir["telefon"],
            eposta=satir["eposta"],
            dogum_tarihi=satir["dogum_tarihi"],
        )
