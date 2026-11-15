# Canlı maç takibine geçişin riskleri

**Bugün:** Zamanlayıcı her sabah, ayardaki sezonun (`DEFAULT_SEASON`) bütün maçlarını lig başına
tek istekle çekip kaydediyor. Aynı anda yalnızca bir güncelleme çalışabiliyor. Kullanıcılar API'ye
değil, bizim veritabanımıza bakıyor. Devam eden sezonlar ve canlı maçlar takip edilirse bu yapı
aşağıdaki noktalarda zorlanır.

## Öncelik sırası

| #   | Risk                                    | Etkisi                            | Bizde              |
| --- | --------------------------------------- | --------------------------------- | ------------------ |
| 1   | Eski skor yeni skorun üstüne yazılıyor  | Yanlış skor ve puan tablosu       | Yok                |
| 2   | Yeni sezona geçilmiyor                  | Site sessizce eski sezonda kalır  | Yok                |
| 3   | İstek hakkı gün bitmeden tükeniyor      | Akşam maçları güncellenmez        | Kısmen             |
| 4   | Canlı skor uzun güncellemeyi bekliyor   | Skor dakikalarca donar            | Yok                |
| 5   | Takip durmuş ama ekran güncel görünüyor | Kullanıcı eski skoru canlı sanır  | Kısmen             |
| 6   | Maç "canlı" durumunda takılı kalıyor    | Bitmiş maç canlı görünür          | Kısmen             |
| 7   | Sonradan gelen düzeltmeler kaçırılıyor  | Puan tablosu kalıcı olarak yanlış | Kısmen             |
| 8   | İki sunucu aynı işi iki kez yapıyor     | Hak iki kat hızlı biter           | Bilerek tek sunucu |

İlk ikisi önce gelir: biri sessizce yanlış veri üretir, diğeri her sezon başında kesin yaşanır.

## Riskler

### 1. Eski skor yeni skorun üstüne yazılıyor
- **Örnek:** Canlı takip 20:31'de 2-1 yazıyor; 20:30'da başlamış yavaş bir sezon güncellemesi
  20:32'de bitip eski skoru, 1-1'i yazıyor.
- **Tespit:** Değişiklik geçmişinde (`fixture_changes`) skorun ileri-geri gitmesi veya bitmiş maçın
  tekrar "oynanıyor"a dönmesi.
- **Önleme / toparlanma:** Her maça "API'den ne zaman alındı" bilgisi eklenir, eski bilgi yenisinin
  üstüne yazılamaz. Skorun düşmesi tek başına hata sayılmaz (VAR). Hatalı maç tek başına yeniden
  çekilir.
- **Bizde:** Bugün tek güncelleme çalıştığı için oluşmuyor, ama Risk 4'teki ayrı canlı yolla
  birlikte ortaya çıkar; ikisi birlikte yapılmalı.

### 2. Yeni sezona geçilmiyor
- **Örnek:** Ağustosta yeni sezon başlıyor; zamanlayıcı hâlâ ayardaki eski sezona bakıyor, bütün
  maçları bittiği için "gerek yok" deyip atlıyor.
- **Tespit:** Günlük kontrol: "API'de güncel görünen sezon bizde yüklü mü?" Sezon ortasında üst üste
  "gerek yok" kaydı da şüphelidir.
- **Önleme / toparlanma:** Sezon ayardan değil API'den (`/leagues?current=true`, haftada bir) alınır;
  yeni sezon görülünce ilk yükleme otomatik yapılır. Kaçırılırsa ilk yükleme komutuyla düzeltilir.
- **Bizde:** Yok. Yeni takımlar ise sorun değil: maç verisinde olmayan takım otomatik ekleniyor.

### 3. İstek hakkı gün bitmeden tükeniyor
- **Örnek:** Gece gündüz 10 saniyede bir sormak günde 8.640 istek eder; 7.500'lük hak UTC 20:50
  civarında, akşam maçlarının ortasında biter.
- **Tespit:** Kullanılan ve kalan istek zaten izleniyor (`api_usage`, `x-ratelimit-requests-remaining`);
  "bu hızla hak saat kaçta biter?" tahmini ve %70 / %90 uyarısı eklenir.
- **Önleme / toparlanma:** Yalnızca maç saatlerinde sorulur, hak işlere bölüştürülür, hak azalınca
  sıklık düşer. Hak biterse ertesi günün güncellemesi eksikleri tamamlar.
- **Bizde:** Kısmen. Kota kontrolü ve günün son 10 isteğinin ayrılması var; bölüştürme yok.

### 4. Canlı skor uzun güncellemeyi bekliyor
- **Örnek:** Tek kilit bütün güncellemeleri sıraya sokuyor; uzun bir sezon güncellemesi sürerken
  canlı skor bekliyor. Takılan bir güncelleme en erken 30 dakikada temizleniyor.
- **Tespit:** Güncellemelerin süresi ve "başka güncelleme çalışıyor" hatalarının sayısı.
- **Önleme / toparlanma:** Canlı skor için yalnızca değişen maçları yazan ayrı, hızlı bir yol; kilit
  iş türüne ve lige göre ayrılır. Canlı sorgular geçmişi şişirmemek için ayrı, özet bir tabloda
  tutulur.
- **Bizde:** Yok.

### 5. Takip durmuş ama ekran güncel görünüyor
- **Örnek:** Hak bitiyor veya API çöküyor; ekran 20 dakika önceki skoru göstermeye devam ediyor.
- **Tespit:** "Son başarılı canlı güncellemeden bu yana geçen süre" ölçülür; maç sırasında 60 sn'yi
  geçerse uyarı verilir ve `/health` bunu döner.
- **Önleme / toparlanma:** Ekranda "15 sn önce güncellendi" ve gecikmede "canlı veri gecikiyor"
  uyarısı; canlı maç varken ekran kendini 15 sn'de bir yeniler.
- **Bizde:** Kısmen. Sezonun son güncelleme saati var; ama ekran kendini yenilemiyor, `/health`
  yalnızca "ok" dönüyor.

### 6. Maç "canlı" durumunda takılı kalıyor
- **Örnek:** Maç yağmurdan yarıda kalıyor (`SUSP`) veya API bilinmeyen bir durum kodu gönderiyor;
  maç saatlerce "canlı" görünüyor.
- **Tespit:** Başlamasının üzerinden 3 saat geçmiş ama hâlâ canlı olan maçlar; atlanan kayıtlar
  zaten nedenleriyle kaydediliyor (`partial`).
- **Önleme / toparlanma:** Takılı maçları tek tek yeniden soran bir bekçi görevi; maç dakikası
  (`elapsed`) da saklanır.
- **Bizde:** Kısmen. Bilinmeyen kod tahmin edilmeden atlanıyor, bozuk kayıt güncellemeyi bozmuyor;
  uyarı yok.

### 7. Sonradan gelen düzeltmeler kaçırılıyor
- **Örnek:** Sezon bittikten sonra bir maç hükmen 3-0 sayılıyor, ya da sezon ortasında bir takıma
  puan silme cezası veriliyor (bu bilgi API'nin maç verisinde yok).
- **Tespit:** Haftada bir kendi puan tablomuz API'nin tablosuyla karşılaştırılır (yalnızca kontrol
  için, ekranda gösterilmez).
- **Önleme / toparlanma:** Sezon bitince bir ay daha haftalık güncelleme; ceza ve hükmen sonuçlar
  lig kuralları dosyasına eklenir. Tablo maç sonuçlarından hesaplandığı için kendiliğinden düzelir.
- **Bizde:** Kısmen. Kural dosyası var; ama bitmiş sezon bir daha güncellenmiyor ve hatırlatan
  bir kontrol yok.

### 8. İki sunucu aynı işi iki kez yapıyor
- **Örnek:** Backend ikiye çıkarılıyor; zamanlayıcı her sunucuda çalıştığı için ikisi de canlı skoru
  soruyor.
- **Tespit:** Saatlik istek sayısının iki katına çıkması, artan 429 hataları.
- **Önleme / toparlanma:** İşi tek sunucunun yapmasına veritabanı karar verir (PostgreSQL advisory
  lock); istek sayacı ortak tutulur.
- **Bizde:** Bilerek tek sunucu (Dockerfile'da not var); ölçeklemeden önce değiştirilmeli.

## 7.500 istekle canlı maç takibi

API-Football o an oynanan bütün maçları tek istekte veriyor (`/fixtures?live=203-39-140-78-135`).
Maliyeti maç sayısı değil, sorma sıklığı belirliyor.

**Varsayımlar:** Pro paket (günde 7.500, dakikada 300 istek; hak UTC gece yarısı yenilenir).
5 lig, yoğun günde ~30 maç, ~12 saatlik maç penceresi. API canlı veriyi 15 saniyede bir yeniliyor;
daha sık sormak yeni bilgi getirmez. Kullanıcı sayısı istek sayısını etkilemez.

| İş                                                    | İstek / gün |
| ----------------------------------------------------- | ----------: |
| Sabahki günlük güncelleme (5 lig)                     |           5 |
| Maç listesini 2 saatte bir kontrol (saat, erteleme)   |          60 |
| **Canlı skor: 15 saniyede bir × 12 saat**             |   **2.880** |
| Maç bitince son kontrol (20 maç tek istekte)          |         ~10 |
| Maç istatistikleri (maç başına 1 kez)                 |          30 |
| Sezon ve puan tablosu kontrolü (haftalık)             |          ~2 |
| Yedek: hatalar ve tekrar denemeler (limitin ~%20'si)  |       1.500 |
| **Toplam**                                            |  **~4.500** |

- **Sığıyor:** 7.500'ün rahatça altında; dakikada 4 istek, 300'lük sınırın çok altında.
- **Tuzak:** Gol ve kart bilgisi her maç için dakikada bir ayrı sorulursa günde ~3.600 istek daha
  eklenir ve sınır aşılır; bu bilgiler toplu isteklerle alınmalı.
- **Hız sınırı:** Kullanıcı bir golü ortalama 20–30 sn, en kötü ~45 sn sonra görür (API gecikmesi +
  15 sn'lik sorgu + ekranın 15 sn'lik yenilemesi). Anlık (1–2 sn) skor bu API ile mümkün değil.
  (Risk 5'teki 15 sn'lik otomatik yenileme yapıldığında.)
- **Esneklik:** Lig eklemek canlı skorun maliyetini artırmaz. Hak azalırsa 15 → 30 → 60 sn'ye
  çıkılır ve ekranda belirtilir.
