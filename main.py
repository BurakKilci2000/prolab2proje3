"""
Komut satırı test aracı.
Kullanım: python main.py <json_dosyasi> [veritabani.db]
"""

import json
import os
import sys

from donusturucu import Donusturucu
from veritabani_yazici import VeritabaniYazici


def calistir(json_yolu: str, db_yolu: str = "cikti.db") -> None:
    # JSON'u oku
    with open(json_yolu, "r", encoding="utf-8") as f:
        veri = json.load(f)

    # Eski veritabanı varsa sil ki temiz başlayalım
    if os.path.exists(db_yolu):
        os.remove(db_yolu)

    # 1) Analiz
    kok_ad = os.path.splitext(os.path.basename(json_yolu))[0]
    donusturucu = Donusturucu(kok_tablo_adi=kok_ad)
    donusturucu.analiz_et(veri)
    sema = donusturucu.sema_cikar()

    print("=" * 60)
    print("OLUSTURULAN TABLOLAR VE SUTUNLAR")
    print("=" * 60)
    for t_ad, t_bilgi in sema.items():
        ebeveyn = t_bilgi["ebeveyn"] or "-"
        print(f"\n[{t_ad}]   ebeveyn: {ebeveyn}")
        for sutun, sql_tipi, kisit in t_bilgi["sutunlar"]:
            print(f"  - {sutun:25s} {sql_tipi:8s} {kisit}")

    # 2) Veritabanına yaz
    yazici = VeritabaniYazici(db_yolu)
    create_sorgulari = yazici.tablolari_olustur(sema)
    eklenen = yazici.satirlari_ekle(sema)

    print("\n" + "=" * 60)
    print("URETILEN CREATE TABLE SORGULARI")
    print("=" * 60)
    for sql in create_sorgulari:
        print(sql + "\n")

    print("=" * 60)
    print(f"TOPLAM {eklenen} SATIR EKLENDI")
    print("=" * 60)

    # 3) Tabloları oku, göster
    print("\n" + "=" * 60)
    print("VERITABANI ICERIGI")
    print("=" * 60)
    for t_ad in yazici.tablolari_listele():
        sutunlar, satirlar = yazici.tabloyu_getir(t_ad)
        print(f"\n--- {t_ad} ---")
        print(" | ".join(sutunlar))
        print("-" * 60)
        for satir in satirlar:
            print(" | ".join(str(v) for v in satir))

    yazici.kapat()


if __name__ == "__main__":
    # IDE'den (VS Code, PyCharm vs.) veya çift tıklama ile çalıştırılırsa
    # script'in olduğu klasörü çalışma dizini yap ki test_data.json bulunabilsin
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")

    # Argüman verilmişse onu kullan, yoksa varsayılan olarak test_data.json'ı dene
    if len(sys.argv) >= 2:
        json_dosyasi = sys.argv[1]
        db_dosyasi = sys.argv[2] if len(sys.argv) > 2 else "cikti.db"
    else:
        json_dosyasi = os.path.join("test_verileri", "test_data.json")
        db_dosyasi = "cikti.db"
        print(f"(Argüman verilmedi, varsayılan: '{json_dosyasi}')\n")

    calistir(json_dosyasi, db_dosyasi)

    # Çift tıklama ile çalıştırıldığında pencere hemen kapanmasın
    input("\nÇıkmak için Enter'a basın...")
