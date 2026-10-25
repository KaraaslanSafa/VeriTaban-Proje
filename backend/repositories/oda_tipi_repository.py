"""OdaTipi tablosuna erişim."""
from models.oda_tipi import OdaTipi
from repositories.base_repository import BaseRepository


class OdaTipiRepository(BaseRepository):
    def tum(self):
        satirlar = self._tum("SELECT * FROM OdaTipi ORDER BY temel_fiyat")
        return [OdaTipi.satirdan(s) for s in satirlar]
