from typing import Any


class Donusturucu:
    def __init__(self, kok_tablo_adi: str = "ana"):
        self.tablolar: dict[str, dict] = {}
        self.kok_tablo = kok_tablo_adi
        self._id_sayaclari: dict[str, int] = {}

    def analiz_et(self, veri: Any) -> None:
        if isinstance(veri, list):
            for oge in veri:
                if isinstance(oge, dict):
                    self._obje_isle(
                        oge, self.kok_tablo, ebeveyn_id=None, ebeveyn_tablo=None
                    )
                else:
                    satir_id = self._sonraki_id(self.kok_tablo)
                    self._tabloyu_hazirla(self.kok_tablo, ebeveyn=None)
                    self._sutun_ekle(self.kok_tablo, "deger", oge)
                    self.tablolar[self.kok_tablo]["satirlar"].append(
                        {"id": satir_id, "deger": oge}
                    )
        elif isinstance(veri, dict):
            self._obje_isle(
                veri, self.kok_tablo, ebeveyn_id=None, ebeveyn_tablo=None
            )
        else:
            satir_id = self._sonraki_id(self.kok_tablo)
            self._tabloyu_hazirla(self.kok_tablo, ebeveyn=None)
            self._sutun_ekle(self.kok_tablo, "deger", veri)
            self.tablolar[self.kok_tablo]["satirlar"].append(
                {"id": satir_id, "deger": veri}
            )

    def _obje_isle(self, obje: dict, tablo_adi: str, ebeveyn_id: int | None, ebeveyn_tablo: str | None) -> int:
        self._tabloyu_hazirla(tablo_adi, ebeveyn=ebeveyn_tablo)
        satir_id = self._sonraki_id(tablo_adi)
        duz_satir: dict[str, Any] = {"id": satir_id}
        if ebeveyn_id is not None:
            duz_satir["ebeveyn_id"] = ebeveyn_id
            self._sutun_ekle(tablo_adi, "ebeveyn_id", ebeveyn_id)

        islenecek_diziler: list[tuple[str, list]] = []

        for anahtar, deger in obje.items():
            self._satira_duzlestir(
                anahtar, deger, duz_satir, tablo_adi, islenecek_diziler
            )

        for sutun, deger in duz_satir.items():
            self._sutun_ekle(tablo_adi, sutun, deger)

        self.tablolar[tablo_adi]["satirlar"].append(duz_satir)

        for dizi_anahtari, dizi_degeri in islenecek_diziler:
            alt_tablo = f"{tablo_adi}_{dizi_anahtari}"
            self._dizi_isle(
                dizi_degeri,
                alt_tablo,
                ebeveyn_id=satir_id,
                ebeveyn_tablo=tablo_adi,
            )

        return satir_id

    def _satira_duzlestir(self, anahtar: str, deger: Any, duz_satir: dict, tablo_adi: str, islenecek_diziler: list, onek: str = "") -> None:

        tam_anahtar = f"{onek}{anahtar}" if onek else anahtar
        # Sütun adındaki boşlukları alt çizgiye çevir (SQL uyumu için)
        tam_anahtar = tam_anahtar.replace(" ", "_")

        if isinstance(deger, dict):
            for ic_anahtar, ic_deger in deger.items():
                self._satira_duzlestir(
                    ic_anahtar,
                    ic_deger,
                    duz_satir,
                    tablo_adi,
                    islenecek_diziler,
                    onek=f"{tam_anahtar}_",
                )
        elif isinstance(deger, list):
            islenecek_diziler.append((tam_anahtar, deger))
        else:
            duz_satir[tam_anahtar] = deger

    def _dizi_isle(self, dizi: list, tablo_adi: str, ebeveyn_id: int, ebeveyn_tablo: str) -> None:
        if not dizi:
            return
        self._tabloyu_hazirla(tablo_adi, ebeveyn=ebeveyn_tablo)
        for eleman in dizi:
            if isinstance(eleman, dict):
                self._obje_isle(
                    eleman,
                    tablo_adi,
                    ebeveyn_id=ebeveyn_id,
                    ebeveyn_tablo=ebeveyn_tablo,
                )
            elif isinstance(eleman, list):
                daha_derin_tablo = f"{tablo_adi}_oge"
                satir_id = self._sonraki_id(tablo_adi)
                self._sutun_ekle(tablo_adi, "ebeveyn_id", ebeveyn_id)
                self.tablolar[tablo_adi]["satirlar"].append(
                    {"id": satir_id, "ebeveyn_id": ebeveyn_id}
                )
                self._dizi_isle(
                    eleman,
                    daha_derin_tablo,
                    ebeveyn_id=satir_id,
                    ebeveyn_tablo=tablo_adi,
                )
            else:
                satir_id = self._sonraki_id(tablo_adi)
                self._sutun_ekle(tablo_adi, "ebeveyn_id", ebeveyn_id)
                self._sutun_ekle(tablo_adi, "deger", eleman)
                self.tablolar[tablo_adi]["satirlar"].append(
                    {"id": satir_id, "ebeveyn_id": ebeveyn_id, "deger": eleman}
                )

    def _tabloyu_hazirla(self, ad: str, ebeveyn: str | None) -> None:
        if ad not in self.tablolar:
            self.tablolar[ad] = {
                "sutunlar": {"id": {"_birincil_anahtar_"}},
                "satirlar": [],
                "ebeveyn": ebeveyn,
            }

    def _sutun_ekle(self, tablo: str, sutun: str, ornek_deger: Any) -> None:
        sutunlar = self.tablolar[tablo]["sutunlar"]
        if sutun not in sutunlar:
            sutunlar[sutun] = set()
        if sutun == "id":
            sutunlar[sutun].add("_birincil_anahtar_")
        elif sutun == "ebeveyn_id":
            sutunlar[sutun].add("_yabanci_anahtar_")
        else:
            sutunlar[sutun].add(self._python_tip_adi(ornek_deger))

    def _sonraki_id(self, tablo: str) -> int:
        self._id_sayaclari[tablo] = self._id_sayaclari.get(tablo, 0) + 1
        return self._id_sayaclari[tablo]

    @staticmethod
    def _python_tip_adi(deger: Any) -> str:
        if deger is None:
            return "null"
        if isinstance(deger, bool):
            return "bool"
        if isinstance(deger, int):
            return "int"
        if isinstance(deger, float):
            return "float"
        return "str"

    def sema_cikar(self) -> dict[str, dict]:
        nihai: dict[str, dict] = {}
        for t_ad, t_bilgi in self.tablolar.items():
            nihai_sutunlar = []
            goruldu = set()  # Aynı isimli sütunu iki kez eklememek için
            for sutun, tipler in t_bilgi["sutunlar"].items():
                # SQLite sütun adlarını büyük/küçük harf duyarsız karşılaştırır,
                # bu yüzden küçük harfe çevirip çakışma kontrolü yapıyoruz
                sutun_kucuk = sutun.lower()
                if sutun_kucuk in goruldu:
                    continue
                goruldu.add(sutun_kucuk)

                if "_birincil_anahtar_" in tipler:
                    nihai_sutunlar.append((sutun, "INTEGER", "PRIMARY KEY"))
                elif "_yabanci_anahtar_" in tipler:
                    ebeveyn = t_bilgi["ebeveyn"]
                    yabanci_anahtar = (
                        f"REFERENCES {ebeveyn}(id)" if ebeveyn else ""
                    )
                    nihai_sutunlar.append((sutun, "INTEGER", yabanci_anahtar))
                else:
                    sql_tipi = self._sql_tipine_karar_ver(tipler)
                    nihai_sutunlar.append((sutun, sql_tipi, ""))
            nihai[t_ad] = {
                "sutunlar": nihai_sutunlar,
                "ebeveyn": t_bilgi["ebeveyn"],
                "satirlar": t_bilgi["satirlar"],
            }
        return nihai

    @staticmethod
    def _sql_tipine_karar_ver(python_tipleri: set[str]) -> str:
        null_olmayan = python_tipleri - {"null"}
        if not null_olmayan:
            return "TEXT"
        if null_olmayan == {"bool"}:
            return "INTEGER"  # SQLite'da bool -> 0/1
        if null_olmayan <= {"int", "bool"}:
            return "INTEGER"
        if null_olmayan <= {"int", "float", "bool"}:
            return "REAL"
        # Karışık veya string varsa TEXT en güvenlisi
        return "TEXT"
