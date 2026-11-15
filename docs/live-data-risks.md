# Canlı maç takibine geçişin riskleri

**Bugün:** Zamanlayıcı her sabah, ayardaki sezonun (`DEFAULT_SEASON`) maçlarını lig başına tek
istekle çekiyor. Aynı anda tek güncelleme çalışabiliyor. Kullanıcılar API'ye değil, bizim
veritabanımıza bakıyor.

## Öncelik sırası

| #   | Risk                                         | Etkisi                            | Bizde  |
| --- | -------------------------------------------- | --------------------------------- | ------ |
| 1   | Canlı ve günlük güncelleme çakışıyor         | Yanlış veya donmuş skor           | Yok    |
| 2   | Yeni sezona geçilmiyor                       | Site sessizce eski sezonda kalır  | Yok    |
| 3   | İstek hakkı gün bitmeden tükeniyor           | Akşam maçları güncellenmez        | Kısmen |
| 4   | Takip durmuş ama ekran güncel görünüyor      | Kullanıcı eski skoru canlı sanır  | Kısmen |
| 5   | Maç "canlı" durumunda takılı kalıyor         | Bitmiş maç canlı görünür          | Kısmen |
| 6   | Sonradan gelen düzeltmeler kaçırılıyor       | Puan tablosu kalıcı olarak yanlış | Kısmen |

İlk ikisi önce gelir: biri sessizce yanlış veri üretir, diğeri her sezon başında kesin yaşanır.

## Riskler

### 1. Canlı ve günlük güncelleme çakışıyor

- **Örnek:** Canlı takip 20:31'de 2-1 yazıyor; 20:30'da başlayan yavaş sezon güncellemesi 20:32'de
  eski skoru, 1-1'i yazıyor. Ya da tek kilit yüzünden canlı skor uzun güncellemeyi bekleyip donuyor.
- **Tespit:** Değişiklik geçmişinde (`fixture_changes`) skorun ileri-geri gitmesi; uzun süren ve
  "başka güncelleme çalışıyor" hatası alan güncellemeler.
- **Önleme / toparlanma:** Canlı skor için ayrı ve hızlı bir yol; her maça "API'den ne zaman
  alındı" bilgisi eklenir, eski bilgi yenisinin üstüne yazılamaz. Hatalı maç tek başına yeniden
  çekilir.
- **Bizde:** Yok. Bugün tek güncelleme çalıştığı için çakışma olmuyor, ama canlı skor da sırada
  bekliyor.

### 2. Yeni sezona geçilmiyor

- **Örnek:** Ağustosta yeni sezon başlıyor; zamanlayıcı hâlâ ayardaki eski sezona bakıp "bütün
  maçlar bitmiş" diyerek atlıyor.
- **Tespit:** Günde bir kez "API'deki güncel sezon bizde yüklü mü?" kontrolü.
- **Önleme / toparlanma:** Sezon ayardan değil API'den (`/leagues?current=true`) alınır, yeni sezon
  otomatik yüklenir. Kaçırılırsa ilk yükleme komutuyla düzeltilir.
- **Bizde:** Yok. Yeni takımlar ise sorun değil, maç verisinden otomatik ekleniyor.

### 3. İstek hakkı gün bitmeden tükeniyor

- **Örnek:** Gece gündüz 10 saniyede bir sormak günde 8.640 istek eder; 7.500'lük hak UTC 20:50'de,
  akşam maçlarının ortasında biter. Backend iki sunucuya çıkarılırsa zamanlayıcı ikisinde de
  çalışır ve hak iki kat hızlı biter.
- **Tespit:** Kullanılan ve kalan istek zaten izleniyor (`api_usage`, API'nin kalan hak başlığı);
  "bu hızla hak saat kaçta biter?" tahmini ve %70 / %90 uyarısı eklenir.
- **Önleme / toparlanma:** Yalnızca maç saatlerinde sorulur, hak işlere bölüştürülür, hak azalınca
  sıklık düşer. Zamanlayıcı tek sunucuda çalışır (PostgreSQL advisory lock). Hak biterse ertesi
  günün güncellemesi eksikleri tamamlar.
- **Bizde:** Kısmen. Kota kontrolü var, günün son 10 isteği otomatik güncellemeye ayrılmış; bilerek
  tek sunucu kullanılıyor.

### 4. Takip durmuş ama ekran güncel görünüyor

- **Örnek:** Hak bitiyor veya API çöküyor; ekran 20 dakika önceki skoru göstermeye devam ediyor.
- **Tespit:** "Son başarılı canlı güncellemeden bu yana geçen süre"; maç sırasında 60 sn'yi geçerse
  uyarı.
- **Önleme / toparlanma:** Ekranda "15 sn önce güncellendi" ve gecikmede uyarı; canlı maç varken
  ekran kendini 15 sn'de bir yeniler.
- **Bizde:** Kısmen. Son güncelleme saati var; ama ekran kendini yenilemiyor.

### 5. Maç "canlı" durumunda takılı kalıyor

- **Örnek:** Maç yağmurdan yarıda kalıyor (`SUSP`) veya API bilinmeyen bir durum kodu gönderiyor;
  maç saatlerce "canlı" görünüyor.
- **Tespit:** Başlamasının üzerinden 3 saat geçmiş ama hâlâ canlı olan maçlar.
- **Önleme / toparlanma:** Takılı maçları tek tek yeniden soran bir bekçi görevi.
- **Bizde:** Kısmen. Bilinmeyen kod tahmin edilmeden atlanıyor ve nedeni kaydediliyor; uyarı yok.

### 6. Sonradan gelen düzeltmeler kaçırılıyor

- **Örnek:** Sezon bittikten sonra bir maç hükmen 3-0 sayılıyor ya da bir takıma puan silme cezası
  veriliyor (bu bilgi API'nin maç verisinde yok).
- **Tespit:** Haftada bir kendi puan tablomuz API'nin tablosuyla karşılaştırılır (yalnızca kontrol
  için).
- **Önleme / toparlanma:** Sezon bitince bir ay daha haftalık güncelleme; ceza ve hükmen sonuçlar
  lig kuralları dosyasına eklenir, tablo kendiliğinden düzelir.
- **Bizde:** Kısmen. Kural dosyası var; ama bitmiş sezon bir daha güncellenmiyor.

## 7.500 istekle canlı maç takibi

API-Football o an oynanan bütün maçları tek istekte veriyor (`/fixtures?live=203-39-140-78-135`).
Maliyeti maç sayısı değil, sorma sıklığı belirliyor.

**Varsayımlar:** Pro paket (günde 7.500, dakikada 300 istek). 5 lig, yoğun günde ~30 maç, ~12
saatlik maç penceresi. API canlı veriyi 15 saniyede bir yeniliyor; daha sık sormak yeni bilgi
getirmez. Kullanıcı sayısı istek sayısını etkilemez.

| İş                                                   | İstek / gün |
| ---------------------------------------------------- | ----------: |
| Sabahki günlük güncelleme (5 lig)                    |           5 |
| Maç listesini 2 saatte bir kontrol (saat, erteleme)  |          60 |
| **Canlı skor: 15 saniyede bir × 12 saat**            |   **2.880** |
| Maç bitince son kontrol ve istatistikler             |         ~40 |
| Sezon ve puan tablosu kontrolü (haftalık)            |          ~2 |
| Yedek: hatalar ve tekrar denemeler (limitin ~%20'si) |       1.500 |
| **Toplam**                                           |  **~4.500** |

- **Sığıyor:** 7.500'ün rahatça altında. Ama gol ve kart bilgisi her maç için dakikada bir ayrı
  sorulursa günde ~3.600 istek daha eklenir ve sınır aşılır.
- **Hız sınırı:** Kullanıcı bir golü ortalama 20–30 sn, en kötü ~45 sn sonra görür (API gecikmesi +
  15 sn'lik sorgu + ekranın 15 sn'lik yenilemesi; Risk 4'teki yenileme yapıldığında). Anlık skor bu
  API ile mümkün değil.
- **Hak azalırsa:** 15 → 30 → 60 sn'ye çıkılır ve ekranda belirtilir.
