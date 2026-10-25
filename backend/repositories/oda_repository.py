"""Oda ile ilgili veritabanı erişimi."""
from models.bos_oda import BosOda
from models.oda import Oda
from repositories.base_repository import BaseRepository


class OdaRepository(BaseRepository):
    def bos_odalar(self, giris, cikis, tip_id=None, kisi=None):
        """sp_bos_odalar prosedürünü çağırır. Çakışma ve fiyat hesabı veritabanında yapılır."""
        _, kumeler = self._prosedur("sp_bos_odalar", (giris, cikis, tip_id, kisi))
        satirlar = kumeler[0] if kumeler else []
        return [BosOda.satirdan(s) for s in satirlar]

    _ODA_SORGUSU = (
        "SELECT o.oda_id, o.oda_no, o.kat, o.durum, ot.tip_id, ot.tip_adi, ot.kapasite "
        "FROM Oda o JOIN OdaTipi ot ON ot.tip_id = o.tip_id"
    )

    def tum(self, tip_id=None, durum=None):
        """Tüm odalar. İstenirse oda tipine ve duruma göre süzülür."""
        kosullar, parametreler = [], []
        if tip_id is not None:
            kosullar.append("o.tip_id = %s")
            parametreler.append(tip_id)
        if durum is not None:
            kosullar.append("o.durum = %s")
            parametreler.append(durum)
        sql = self._ODA_SORGUSU
        if kosullar:
            sql += " WHERE " + " AND ".join(kosullar)
        sql += " ORDER BY o.oda_no"
        return [Oda.satirdan(s) for s in self._tum(sql, parametreler)]

    def bul_id(self, oda_id):
        satir = self._bir(self._ODA_SORGUSU + " WHERE o.oda_id = %s", (oda_id,))
        return Oda.satirdan(satir) if satir else None
