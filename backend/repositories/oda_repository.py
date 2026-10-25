"""Oda ile ilgili veritabanı erişimi."""
from models.bos_oda import BosOda
from repositories.base_repository import BaseRepository


class OdaRepository(BaseRepository):
    def bos_odalar(self, giris, cikis, tip_id=None, kisi=None):
        """sp_bos_odalar prosedürünü çağırır. Çakışma ve fiyat hesabı veritabanında yapılır."""
        _, kumeler = self._prosedur("sp_bos_odalar", (giris, cikis, tip_id, kisi))
        satirlar = kumeler[0] if kumeler else []
        return [BosOda.satirdan(s) for s in satirlar]
