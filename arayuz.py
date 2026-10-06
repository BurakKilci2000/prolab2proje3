"""
Grafiksel Kullanıcı Arayüzü (Tkinter)
--------------------------------------
Bu modül, dönüştürücü motorunu görsel bir arayüze bağlar:
  - "JSON Yükle" : dosya seçici açar, JSON'u sol panelde ağaç olarak gösterir
  - "Dönüştür"   : motoru çalıştırır, SQLite'a yazar, sağ panelde tabloları gösterir
  - "Sıfırla"    : tüm tabloları DROP eder, arayüzü temizler
"""

import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from donusturucu import Donusturucu
from veritabani_yazici import VeritabaniYazici


class Uygulama:
    def __init__(self, ana_pencere: tk.Tk):
        self.ana_pencere = ana_pencere
        self.ana_pencere.title("NoSQL (JSON) -> SQL Dönüştürücü")
        self.ana_pencere.geometry("1100x650")
        self.ana_pencere.minsize(800, 500)

        # ttk teması: Windows'ta 'vista', diğer sistemlerde 'clam' kullan
        stil = ttk.Style()
        kullanilabilir = stil.theme_names()
        if "vista" in kullanilabilir:
            stil.theme_use("vista")
        elif "clam" in kullanilabilir:
            stil.theme_use("clam")

        # Uygulamanın iç durumu (state)
        self.json_verisi = None         # Yüklenen JSON içeriği
        self.json_dosya_yolu = None     # Yüklenen JSON'un disk yolu
        self.yazici = None              # VeritabaniYazici örneği
        self.db_yolu = "cikti.db"       # SQLite veritabanı dosyası

        self._arayuzu_olustur()

    # ----------------------------------------------------------------------
    # Arayüz iskeletini kur
    # ----------------------------------------------------------------------
    def _arayuzu_olustur(self) -> None:
        # ÜST: Buton çubuğu
        ust_cubuk = ttk.Frame(self.ana_pencere, padding=(10, 8))
        ust_cubuk.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(
            ust_cubuk, text="JSON Yükle", command=self._json_yukle, width=14
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            ust_cubuk, text="Dönüştür", command=self._donustur, width=14
        ).pack(side=tk.LEFT, padx=6)
        ttk.Button(
            ust_cubuk, text="Sıfırla", command=self._sifirla, width=14
        ).pack(side=tk.LEFT, padx=6)

        self.dosya_etiketi = ttk.Label(ust_cubuk, text="(dosya yüklenmedi)", foreground="#666")
        self.dosya_etiketi.pack(side=tk.RIGHT)

        # ORTA: Bölünmüş panel (sol JSON ağacı, sağ tablo sekmeleri)
        bolunmus = ttk.PanedWindow(self.ana_pencere, orient=tk.HORIZONTAL)
        bolunmus.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        # SOL: JSON ağaç görünümü
        sol_cerceve = ttk.LabelFrame(bolunmus, text=" JSON Ağaç Görünümü ", padding=4)
        bolunmus.add(sol_cerceve, weight=1)

        self.json_agac = ttk.Treeview(sol_cerceve, show="tree")
        sol_dikey = ttk.Scrollbar(
            sol_cerceve, orient=tk.VERTICAL, command=self.json_agac.yview
        )
        self.json_agac.configure(yscrollcommand=sol_dikey.set)
        self.json_agac.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sol_dikey.pack(side=tk.RIGHT, fill=tk.Y)

        # SAĞ: Oluşan SQL tabloları sekmeli olarak
        sag_cerceve = ttk.LabelFrame(bolunmus, text=" Oluşan SQL Tabloları ", padding=4)
        bolunmus.add(sag_cerceve, weight=2)

        self.tablo_sekmeleri = ttk.Notebook(sag_cerceve)
        self.tablo_sekmeleri.pack(fill=tk.BOTH, expand=True)

        # Boşken bilgilendirici bir mesaj gösterelim
        self._sekme_yer_tutucu_goster()

        # ALT: Durum çubuğu
        self.durum_metni = tk.StringVar(value="Hazır - başlamak için bir JSON dosyası yükleyin")
        ttk.Label(
            self.ana_pencere,
            textvariable=self.durum_metni,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(10, 4),
        ).pack(side=tk.BOTTOM, fill=tk.X)

    def _sekme_yer_tutucu_goster(self) -> None:
        """Henüz dönüşüm yapılmamışken sağ panelde bir bilgi etiketi göster."""
        cerceve = ttk.Frame(self.tablo_sekmeleri, padding=20)
        ttk.Label(
            cerceve,
            text="Henüz dönüşüm yapılmadı.\n"
            "Bir JSON dosyası yükleyip 'Dönüştür' tuşuna basın.",
            foreground="#666",
            justify=tk.CENTER,
        ).pack(expand=True)
        self.tablo_sekmeleri.add(cerceve, text="(boş)")

    def _sekmeleri_temizle(self) -> None:
        for sekme in self.tablo_sekmeleri.tabs():
            self.tablo_sekmeleri.forget(sekme)

    # ----------------------------------------------------------------------
    # JSON Yükle
    # ----------------------------------------------------------------------
    def _json_yukle(self) -> None:
        yol = filedialog.askopenfilename(
            title="JSON dosyası seçin",
            filetypes=[("JSON dosyaları", "*.json"), ("Tüm dosyalar", "*.*")],
        )
        if not yol:
            return  # Kullanıcı iptal etti

        try:
            with open(yol, "r", encoding="utf-8") as f:
                self.json_verisi = json.load(f)
        except json.JSONDecodeError as hata:
            messagebox.showerror("JSON Hatası", f"JSON ayrıştırılamadı:\n{hata}")
            return
        except Exception as hata:
            messagebox.showerror("Dosya Hatası", f"Dosya okunamadı:\n{hata}")
            return

        self.json_dosya_yolu = yol
        self.dosya_etiketi.config(text=os.path.basename(yol), foreground="black")
        self._json_agacini_doldur()
        self.durum_metni.set(
            f"'{os.path.basename(yol)}' yüklendi - dönüşüm için 'Dönüştür' tuşuna basın"
        )

    def _json_agacini_doldur(self) -> None:
        """Ağacı temizle ve JSON'u rekursif olarak ekle."""
        for oge in self.json_agac.get_children():
            self.json_agac.delete(oge)
        self._agaca_dugum_ekle("", self.json_verisi, "kök")

    def _agaca_dugum_ekle(self, ust_dugum: str, deger, anahtar: str) -> None:
        """JSON yapısını Treeview'a rekursif olarak yerleştir."""
        if isinstance(deger, dict):
            etiket = f"{anahtar}  {{ {len(deger)} alan }}"
            yeni = self.json_agac.insert(ust_dugum, "end", text=etiket, open=True)
            for alt_anahtar, alt_deger in deger.items():
                self._agaca_dugum_ekle(yeni, alt_deger, alt_anahtar)
        elif isinstance(deger, list):
            etiket = f"{anahtar}  [ {len(deger)} eleman ]"
            yeni = self.json_agac.insert(ust_dugum, "end", text=etiket, open=False)
            for indeks, eleman in enumerate(deger):
                self._agaca_dugum_ekle(yeni, eleman, f"[{indeks}]")
        else:
            # Primitif değer: anahtar: deger (tip)
            tip_adi = type(deger).__name__
            metin = repr(deger) if isinstance(deger, str) else str(deger)
            if len(metin) > 60:
                metin = metin[:57] + "..."
            self.json_agac.insert(
                ust_dugum, "end", text=f"{anahtar}: {metin}   ({tip_adi})"
            )

    # ----------------------------------------------------------------------
    # Dönüştür
    # ----------------------------------------------------------------------
    def _donustur(self) -> None:
        if self.json_verisi is None:
            messagebox.showwarning("Uyarı", "Önce bir JSON dosyası yükleyin.")
            return

        try:
            # Eski veritabanı bağlantısını kapat ve dosyayı sil (temiz başlangıç)
            if self.yazici is not None:
                self.yazici.kapat()
                self.yazici = None
            if os.path.exists(self.db_yolu):
                os.remove(self.db_yolu)

            # 1) Motor ile analiz et
            kok_ad = os.path.splitext(os.path.basename(self.json_dosya_yolu))[0]
            donusturucu = Donusturucu(kok_tablo_adi=kok_ad)
            donusturucu.analiz_et(self.json_verisi)
            sema = donusturucu.sema_cikar()

            # 2) Veritabanına yaz
            self.yazici = VeritabaniYazici(self.db_yolu)
            self.yazici.tablolari_olustur(sema)
            eklenen_satir = self.yazici.satirlari_ekle(sema)

            # 3) Sonuçları arayüzde göster
            self._tablo_sekmelerini_doldur()
            self.durum_metni.set(
                f"✓  {len(sema)} tablo, {eklenen_satir} satır oluşturuldu  |  {self.db_yolu}"
            )
        except Exception as hata:
            messagebox.showerror("Dönüşüm Hatası", str(hata))
            self.durum_metni.set("Dönüşüm başarısız")

    def _tablo_sekmelerini_doldur(self) -> None:
        """Her tabloyu ayrı bir sekmede DataGrid (Treeview) olarak göster."""
        self._sekmeleri_temizle()

        tablolar = self.yazici.tablolari_listele()
        if not tablolar:
            self._sekme_yer_tutucu_goster()
            return

        for tablo_adi in tablolar:
            sutun_adlari, satirlar = self.yazici.tabloyu_getir(tablo_adi)

            cerceve = ttk.Frame(self.tablo_sekmeleri)
            self.tablo_sekmeleri.add(cerceve, text=tablo_adi)

            # Treeview'i tablo (DataGrid) modunda kullan
            agac = ttk.Treeview(cerceve, columns=sutun_adlari, show="headings")
            for sutun in sutun_adlari:
                agac.heading(sutun, text=sutun)
                # Sütun genişliğini içeriğe göre kabaca ayarla
                en_uzun = max(
                    [len(str(sutun))]
                    + [len(str(s[sutun_adlari.index(sutun)])) for s in satirlar]
                )
                agac.column(
                    sutun, width=min(max(en_uzun * 8, 60), 250), anchor=tk.W
                )

            # Satırları ekle (None değerleri "NULL" olarak göster)
            for satir in satirlar:
                degerler = ["NULL" if v is None else str(v) for v in satir]
                agac.insert("", "end", values=degerler)

            # Kaydırma çubukları
            dikey = ttk.Scrollbar(cerceve, orient=tk.VERTICAL, command=agac.yview)
            yatay = ttk.Scrollbar(cerceve, orient=tk.HORIZONTAL, command=agac.xview)
            agac.configure(yscrollcommand=dikey.set, xscrollcommand=yatay.set)

            # Grid ile yerleştir (kaydırma çubuklarıyla doğru hizalanır)
            agac.grid(row=0, column=0, sticky="nsew")
            dikey.grid(row=0, column=1, sticky="ns")
            yatay.grid(row=1, column=0, sticky="ew")
            cerceve.grid_rowconfigure(0, weight=1)
            cerceve.grid_columnconfigure(0, weight=1)

    # ----------------------------------------------------------------------
    # Sıfırla
    # ----------------------------------------------------------------------
    def _sifirla(self) -> None:
        cevap = messagebox.askyesno(
            "Onay",
            "Veritabanındaki TÜM tablolar silinecek (DROP TABLE).\nDevam edilsin mi?",
        )
        if not cevap:
            return

        try:
            if self.yazici is not None:
                silinen = self.yazici.tumunu_sil()
                self.yazici.kapat()
                self.yazici = None
                mesaj = f"✓  {len(silinen)} tablo silindi (DROP TABLE)"
            else:
                mesaj = "Silinecek tablo yoktu"

            # Arayüzü temizle
            self._sekmeleri_temizle()
            self._sekme_yer_tutucu_goster()

            # JSON ağacını da temizle
            for oge in self.json_agac.get_children():
                self.json_agac.delete(oge)

            self.json_verisi = None
            self.json_dosya_yolu = None
            self.dosya_etiketi.config(text="(dosya yüklenmedi)", foreground="#666")
            self.durum_metni.set(mesaj)
        except Exception as hata:
            messagebox.showerror("Hata", str(hata))


def calistir() -> None:
    pencere = tk.Tk()
    Uygulama(pencere)
    pencere.mainloop()


if __name__ == "__main__":
    # Çalışma dizinini script'in olduğu klasöre ayarla
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")
    calistir()
