"""Misafir tablosuna erişim."""
from models.misafir import Misafir
from repositories.base_repository import BaseRepository


class MisafirRepository(BaseRepository):
    def bul_id(self, misafir_id):
        satir = self._bir("SELECT * FROM Misafir WHERE misafir_id = %s", (misafir_id,))
        return Misafir.satirdan(satir) if satir else None
