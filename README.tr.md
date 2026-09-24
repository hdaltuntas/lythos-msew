[English](https://github.com/hdaltuntas/lythos-msew/blob/main/README.md) | **Türkçe**

# Lythos MSEW

[![Tests](https://github.com/hdaltuntas/lythos-msew/actions/workflows/tests.yml/badge.svg)](https://github.com/hdaltuntas/lythos-msew/actions/workflows/tests.yml)

Donatılı zemin (MSE — mekanik olarak stabilize edilmiş toprak) istinat duvarları, tarayıcıdan
kullanılır. Bir kaplama, sıkıştırılmış dolgu içindeki **çelik şerit, geogrid ya da geotekstil**
donatı tabakaları ve arkasındaki dolgudan oluşan duvar; FHWA-NHI-10-024 ve AASHTO LRFD 11.10'un
yaptığı ve MSEW programının alıştırdığı biçimde tasarlanır ve kontrol edilir:

1. **Toprak basıncı** — arka dolgu ve donatılı dolgunun Coulomb / Rankine Ka katsayıları;
   eğimli yüz ve eğimli arka dolgu ile.
2. **Dış duraylılık** — tabanda kayma (dolgu içinden, temel zemini üzerinde ya da geosentetik
   boyunca), topuk etrafında devrilme, bileşkenin dışmerkezliği.
3. **Taşıma gücü** — etkin genişlik B′ = L − 2e altında; **Terzaghi, Meyerhof, Brinch Hansen,
   Vesić ve EN 1997-1** katsayılarıyla yan yana — su tablası, gömülme, yük eğimi ve topuk önündeki
   şev ile.
4. **İç duraylılık, tabaka tabaka** — AASHTO Basitleştirilmiş Yöntemi ile en büyük çekme
   kuvveti (şeritte Kr/Ka 1.7 → 1.2, geosentetikte 1); ardından her tabakanın **çekme**,
   **sıyrılma** (F*, α, aktif bölge ötesindeki Le), **bağlantı** ve **kayma** kontrolleri.
5. **Donatı** — şeritlerin **genişliği, kalınlığı, akma dayanımı ve aralığı** girilir (tasarım
   ömrü boyunca çinko ve çelik korozyonundan sonra kalan kesit hesaplanır), ya da geosentetiğin
   **nihai dayanımı ve azaltma katsayıları** RFID·RFCR·RFD.
6. **Deprem** — psödo-statik yöntem: Am = (1.45 − A)·A; dış duraylılıkta dinamik itki PAE ve
   atalet PIR, iç duraylılıkta aktif bölgenin ataleti tabakalara paylaştırılır.
7. **ASD ya da LRFD** — güvenlik sayıları ya da yük (EV, EH, ES, LS) ve direnç (φ) katsayıları.
8. **Duvarın gerektirdiği boy** — dış duraylılık ve sıyrılma kontrollerini sağlayan en kısa
   eşit donatı boyu; FHWA'nın en küçüğü (0.7·H, 2.4 m) ile birlikte.

Bunun üzerine **yükseklik çalışması**, aynı tasarım kuralını — ilk tabaka, aralık, yüksekliğin
oranı olarak boy, donatı türü — bir yükseklik aralığında çalıştırır; hangi yüksekliklerde bütün
kontrollerin sağlandığını ve her yükseklikte donatının ne kadar uzun olması gerektiğini gösterir.

Programın tamamı — her etiket, sonuç metni, şekil ve rapor — **İngilizce ve Türkçe**dir ve
çalışırken değiştirilebilir.

Arayüz, kendi bilgisayarınızda çalışan küçük bir HTTP sunucusudur ve tarayıcıdan kullanılır.
Böylece program uzak oturumda ya da bir konteyner içinde de çalışır ve standart kütüphane
dışında bağımlılık getirmez.

> [Lythos Bearing](https://github.com/hdaltuntas/lythos-bearing),
> [Lythos Settle](https://github.com/hdaltuntas/lythos-settle),
> [LythosFEA](https://github.com/hdaltuntas/lythos),
> [Lythos Kinematic](https://github.com/hdaltuntas/lythoskinematic),
> [Lythos SPWA](https://github.com/hdaltuntas/lythosspwa) ve
> [LythosLE](https://github.com/hdaltuntas/lythosle) programlarının kardeşidir; aynı mimari,
> tema ve yazı tiplerini kullanır. Taşıma gücü katsayıları Lythos Bearing'inkilerdir.

## Ekran görüntüleri

| Sonuç özeti | Tabaka tabaka |
|---|---|
| ![Özet](https://raw.githubusercontent.com/hdaltuntas/lythos-msew/main/screenshots/msew_summary.png) | ![Tabakalar](https://raw.githubusercontent.com/hdaltuntas/lythos-msew/main/screenshots/msew_layers.png) |

| Kesit, koyu tema, Türkçe | Yönteme göre taşıma gücü |
|---|---|
| ![Kesit](https://raw.githubusercontent.com/hdaltuntas/lythos-msew/main/screenshots/msew_section_dark_tr.png) | ![Taşıma gücü](https://raw.githubusercontent.com/hdaltuntas/lythos-msew/main/screenshots/msew_bearing_dark_tr.png) |

## Kurulum ve çalıştırma

Depo kopyasından, yalnızca bilimsel kütüphanelerle:

```bash
pip install numpy matplotlib reportlab
python main.py
```

ya da `pip install .` (Word raporu için `python-docx`, yükseklik çalışmasının tablo çıktısı için
`openpyxl`: `pip install ".[docx,xlsx]"`). Python 3.10+ gerekir.

## Komut satırı

```bash
lythos-msew                                   # web arayüzü (varsayılan)
lythos-msew web --port 9000 --lang tr --no-browser
lythos-msew example -o proje.msew             # örnek proje dosyası
lythos-msew run proje.msew -o rapor.pdf       # çöz, sonuçları yaz, rapor oluştur
lythos-msew heights proje.msew -o yukseklik.xlsx
```

Arayüz varsayılan olarak 8782 numaralı portu dinler.

## Girdiler

* **Duvar:** tasarım yüksekliği H, gömülme d, yüz eğimi ω, arka şev β, topuk önündeki şev,
  kaplama kalınlığı.
* **Sürşarjlar:** kalıcı ve hareketli (trafik) düzgün sürşarj; şerit yük (P, genişlik, yüzden
  uzaklık, kalıcı ya da hareketli).
* **Zeminler:** donatılı dolgu (γ, φ′), arka dolgu (γ, φ′), temel zemini (γ, γdoy, φ′, c′ — ya da
  φ = 0 ve cu), su tablasının tabandan derinliği.
* **Donatı kataloğu:** piyasadaki tipik ürünler tek tıkla tür tablosuna eklenir — nervürlü
  galvanizli çelik şeritler (S355'te HA 40×4 – 60×5, Grade 65'te 50×4), polimer şeritler (PET
  çekirdek, PE kılıf, şerit başına 20–100 kN), tek eksenli HDPE ve PET geogridler (35–200 kN/m),
  dokuma PET ve PP geotekstiller — FHWA'nın tipik azaltma katsayıları ve sıyrılma
  parametreleriyle. Genel başlangıç değerleridir: kullanılacak ürünün teknik föyüyle kontrol
  ediniz.
* **Donatı türleri** (tablo): ad, tür (çelik şerit, polimer şerit, geogrid, geotekstil); geosentetik — Tult,
  RFID, RFCR, RFD, kaplama oranı Rc, etkileşim katsayısı Ci; çelik şerit — genişlik b, kalınlık
  t, akma Fy, yatay aralık Sh, tepede F*₀; polimer şerit — şerit başına Tult, azaltma
  katsayıları, genişlik b, aralık Sh, Ci; hepsi — ölçek düzeltmesi α ve bağlantı oranı CR.
* **Tabakalar** (tablo): tesviye tabanından yükseklik z, boy L, tür. Ya da **yerleşim üreteci**
  doldursun: ilk tabaka, aralık Sv, L = oran·H (en kısa boyun altına inmeden) ya da sabit L, tür.
* **Korozyon:** tasarım ömrü, galvaniz kalınlığı, karbon çeliği kayıp hızı.
* **Tasarım yöntemi:** ASD (kayma, devrilme, dışmerkezlik, taşıma gücü, çekme, sıyrılma, bağlantı
  güvenlik sayıları; çelik için 0.55·Fy) ya da LRFD (kayma, taşıma gücü, çelik, geosentetik,
  sıyrılma için φ); aktif bölge ötesinde en küçük boy.
* **Deprem:** A, depremde F* azaltması.
* **Yükseklik çalışması:** aralık ve adım.

Formüller, kaynakları ve sınırları için
[docs/theory.md](https://github.com/hdaltuntas/lythos-msew/blob/main/docs/theory.md).

## Raporlar

Başlıktan PDF, tek dosyalık HTML ya da Word seçip *Raporu dışa aktar…* düğmesine basın. Rapor;
girdileri, toprak basıncını ve kuvvetleri kollarıyla, dış duraylılık kontrollerini, her yönteme
göre taşıma gücünü, her tabakanın çekme ve sıyrılma hesabını, depremi, gerekli boyu, şekilleri,
uyarıları, yöntem notlarını ve — çalıştırıldıysa — yükseklik çalışmasını, arayüz hangi dildeyse
o dilde içerir.

Kapsam dışı: genel ve bileşik duraylılık, oturma ve drenaj; ayrıca kontrol ediniz.

## Lisans

[MIT](https://github.com/hdaltuntas/lythos-msew/blob/main/LICENSE) © 2026 Hasan Deniz Altuntaş
