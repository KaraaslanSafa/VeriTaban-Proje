"""Oda tipi iş mantığı."""
from repositories.oda_tipi_repository import OdaTipiRepository


class OdaTipiService:
    def __init__(self, oda_tipi_repo=None):
        self._tipler = oda_tipi_repo or OdaTipiRepository()

    def listele(self):
        tipler = self._tipler.tum()
        return {"oda_tipi_sayisi": len(tipler), "oda_tipleri": [t.sozluk() for t in tipler]}
