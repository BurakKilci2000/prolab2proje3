"""
Veritabanı Yazıcı (SQLite Çalıştırıcı)
---------------------------------------
Dönüştürücü motorunun ürettiği şema bilgisine bakarak:
  - CREATE TABLE sorgularını doğru sırayla (ebeveyn -> çocuk) üretir
  - INSERT INTO sorgularını parametreli olarak çalıştırır (SQL injection güvenli)
  - DROP TABLE ile tüm tabloları silebilir (sıfırlama için)
"""

import sqlite3
from typing import Any


class VeritabaniYazici:
    def __init__(self, db_yolu: str = "cikti.db"):
        self.db_yolu = db_yolu
        self.baglanti = sqlite3.connect(db_yolu)
        # Yabancı anahtar kısıtlamalarını aktif et
        self.baglanti.execute("PRAGMA foreign_keys = ON")

    # ----------------------------------------------------------------------
    # Tabloları topolojik sırayla oluştur (ebeveyn -> çocuk)
    # ----------------------------------------------------------------------
    def tablolari_olustur(self, sema: dict[str, dict]) -> list[str]:
        """Şema sözlüğüne göre CREATE TABLE sorguları üretir ve çalıştırır."""
        sirali = self._topolojik_sirala(sema)
        calistirilan_sql = []
        imlec = self.baglanti.cursor()
        for t_ad in sirali:
            t_bilgi = sema[t_ad]
            sql = self._create_sql_uret(t_ad, t_bilgi["sutunlar"])
            calistirilan_sql.append(sql)
            imlec.execute(sql)
        self.baglanti.commit()
        return calistirilan_sql

    @staticmethod
    def _create_sql_uret(tablo_adi: str, sutunlar: list[tuple]) -> str:
        """Bir tablo için CREATE TABLE metnini üret."""
        sutun_tanimlari = []
        for sutun, sql_tipi, kisit in sutunlar:
            parcalar = [f'"{sutun}"', sql_tipi]
            if kisit:
                parcalar.append(kisit)
            sutun_tanimlari.append(" ".join(parcalar))
        return (
            f'CREATE TABLE IF NOT EXISTS "{tablo_adi}" (\n  '
            + ",\n  ".join(sutun_tanimlari)
            + "\n);"
        )

    @staticmethod
    def _topolojik_sirala(sema: dict[str, dict]) -> list[str]:
        """Önce ebeveynleri oluştur ki yabancı anahtarlar geçerli olsun."""
        sirali = []
        ziyaret_edildi = set()

        def ziyaret_et(ad: str) -> None:
            if ad in ziyaret_edildi:
                return
            ebeveyn = sema[ad]["ebeveyn"]
            if ebeveyn and ebeveyn in sema:
                ziyaret_et(ebeveyn)
            ziyaret_edildi.add(ad)
            sirali.append(ad)

        for ad in sema:
            ziyaret_et(ad)
        return sirali

    # ----------------------------------------------------------------------
    # Verileri ekle
    # ----------------------------------------------------------------------
    def satirlari_ekle(self, sema: dict[str, dict]) -> int:
        """Her tablo için satırları INSERT INTO ile ekler."""
        sirali = self._topolojik_sirala(sema)
        toplam = 0
        imlec = self.baglanti.cursor()
        for t_ad in sirali:
            t_bilgi = sema[t_ad]
            sutunlar = [s[0] for s in t_bilgi["sutunlar"]]
            for satir in t_bilgi["satirlar"]:
                # Eksik sütunlar için None koy (şema bütünlüğü korunur)
                degerler = [
                    self._normallestir(satir.get(s)) for s in sutunlar
                ]
                yer_tutucular = ",".join(["?"] * len(sutunlar))
                sutun_listesi = ",".join(f'"{s}"' for s in sutunlar)
                sql = (
                    f'INSERT INTO "{t_ad}" ({sutun_listesi}) '
                    f"VALUES ({yer_tutucular})"
                )
                imlec.execute(sql, degerler)
                toplam += 1
        self.baglanti.commit()
        return toplam

    @staticmethod
    def _normallestir(deger: Any) -> Any:
        # SQLite bool'u int olarak saklar; True/False -> 1/0
        if isinstance(deger, bool):
            return 1 if deger else 0
        return deger

    # ----------------------------------------------------------------------
    # Sıfırlama: tüm tabloları sil
    # ----------------------------------------------------------------------
    def tumunu_sil(self) -> list[str]:
        imlec = self.baglanti.cursor()
        imlec.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
        adlar = [r[0] for r in imlec.fetchall()]
        # Yabancı anahtarlar nedeniyle ters sırayla sil
        for ad in reversed(adlar):
            imlec.execute(f'DROP TABLE IF EXISTS "{ad}"')
        self.baglanti.commit()
        return adlar

    # ----------------------------------------------------------------------
    # Oluşan veriyi okuma (GUI raporlama için)
    # ----------------------------------------------------------------------
    def tabloyu_getir(self, tablo_adi: str) -> tuple[list[str], list[tuple]]:
        imlec = self.baglanti.cursor()
        imlec.execute(f'SELECT * FROM "{tablo_adi}"')
        satirlar = imlec.fetchall()
        sutun_adlari = [d[0] for d in imlec.description]
        return sutun_adlari, satirlar

    def tablolari_listele(self) -> list[str]:
        imlec = self.baglanti.cursor()
        imlec.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [r[0] for r in imlec.fetchall()]

    def kapat(self) -> None:
        self.baglanti.close()
