"""Kullanici tablosunun Entity sınıfı."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Kullanici:
    kullanici_id: int
    kullanici_adi: str
    sifre_hash: str
    rol: str
    misafir_id: Optional[int] = None
    personel_id: Optional[int] = None

    @classmethod
    def satirdan(cls, satir):
        """Veritabanından gelen sözlüğü nesneye çevirir."""
        return cls(
            kullanici_id=satir["kullanici_id"],
            kullanici_adi=satir["kullanici_adi"],
            sifre_hash=satir["sifre_hash"],
            rol=satir["rol"],
            misafir_id=satir["misafir_id"],
            personel_id=satir["personel_id"],
        )

    def genel_bilgi(self):
        """İstemciye gönderilebilecek bilgiler. Parola özeti ASLA dahil edilmez."""
        return {
            "kullanici_id": self.kullanici_id,
            "kullanici_adi": self.kullanici_adi,
            "rol": self.rol,
            "misafir_id": self.misafir_id,
            "personel_id": self.personel_id,
        }
