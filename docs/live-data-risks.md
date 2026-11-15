# Canlı veri akışına geçiş: riskler ve plan

## Bağlam: bugünkü yapı neden böyle

Proje, case'in ilk aşamasındaki koşullara göre bilinçli olarak tasarlandı: API-Football ücretsiz
paketi, günde 100 istek ve yalnızca bitmiş sezonlar. Bu koşullarda en doğru yapı, veriyi günde bir
kez toplu çekip kullanıcılara kendi veritabanımızdan sunmaktı. Tek kilit, tek sunucu ve sabah
zamanlayıcısı bu ihtiyaç için yeterli olduğu için basit tutuldu.

Canlı takip bu yapının küçük bir uzantısı değil, kapsamlı bir mimari değişiklik. En az şunları
gerektirir:

- Günlük toplu güncellemeden ayrı, sürekli çalışan bir canlı güncelleme servisi
- İş türüne ve lige göre ayrılmış kilitler; verinin alındığı zamana göre yazma kuralı
- Ücretli paket (günde 7.500 istek) ve bu hakkın işler arasında bölüştürülmesi
- Kullanıcıya anlık iletim (WebSocket / SSE) ve "veri gecikiyor" göstergesi
- Sezonun ayardan değil, API'den otomatik belirlenmesi
- Uzun vadede, veriyi değişince kendisi gönderen (push / WebSocket) bir canlı veri servisi

Puan tablosu hesaplama, değişiklik geçmişi ve kota takibi bu yeni katmanın arkasında olduğu gibi
kalır. Aşağıdaki "Bugünkü durum" sütunu, mevcut yapının bu ihtiyaçlardan hangilerini zaten
karşıladığını ve hangilerinin yeni iş olduğunu gösteriyor.

## Riskler (önem sırasıyla)

| #   | Risk                                 | Etkisi                           | Bugünkü durum            |
| --- | ------------------------------------ | -------------------------------- | ------------------------ |
| 1   | Canlı ve günlük güncelleme çakışır   | Yanlış veya donmuş skor          | Yeni iş                  |
| 2   | Yeni sezona geçiş elle yapılır       | Site eski sezonda kalır          | Yeni iş                  |
| 3   | İstek hakkı gün bitmeden tükenir     | Akşam maçları güncellenmez       | Kota takibi hazır        |
| 4   | Takip durur ama ekran güncel görünür | Kullanıcı eski skoru canlı sanır | Son güncelleme saati var |
| 5   | Maç "canlı" durumunda takılı kalır   | Bitmiş maç canlı görünür         | Durum kodları tanınıyor  |
| 6   | Sonradan gelen düzeltmeler kaçırılır | Puan tablosu yanlış kalır        | Kural dosyası hazır      |

İlk ikisi önce gelir: biri sessizce yanlış veri üretebilir, diğeri her sezon başında yaşanır.

### 1. Canlı ve günlük güncelleme çakışır

- **Örnek:** Canlı takip skoru 2-1 yapar, birkaç saniye sonra biten günlük güncelleme eski skoru
  (1-1) geri yazar.
- **Nasıl yakalarız:** Değişiklik geçmişinde skorun ileri-geri gitmesi.
- **Ne yaparız:** Her maça "veri ne zaman alındı" bilgisi eklenir; eski veri yenisinin üstüne
  yazılmaz. Hatalı maç tek başına yeniden çekilir.
- **Bugün:** Aynı anda tek güncelleme çalıştığı için oluşmuyor. Canlı katmanla birlikte ayrı
  kilitler ve zaman kontrolü eklenmeli.

### 2. Yeni sezona geçiş elle yapılır

- **Örnek:** Ağustosta yeni sezon başlar ama sistem ayardaki eski sezonu takip etmeye devam eder.
- **Nasıl yakalarız:** Günde bir kez "API'deki güncel sezon bizde var mı?" kontrolü.
- **Ne yaparız:** Güncel sezon API'den (`/leagues?current=true`) okunur ve otomatik yüklenir.
  Kaçırılırsa ilk yükleme komutuyla tamamlanır.
- **Bugün:** Ücretsiz pakette yeni sezon olmadığı için sezon ayardan seçiliyor; otomatik geçiş
  eklenmeli.

### 3. İstek hakkı gün bitmeden tükenir

- **Örnek:** 10 saniyede bir sormak günde 8.640 istek eder; 7.500'lük hak akşam maçlarının ortasında
  biter.
- **Nasıl yakalarız:** Kullanılan ve kalan istek zaten izleniyor; "hak saat kaçta biter?" tahmini
  ve uyarı eklenir.
- **Ne yaparız:** Yalnızca maç saatlerinde sorulur, hak azalınca sıklık düşürülür. Eksikleri ertesi
  günün güncellemesi tamamlar.
- **Bugün:** Kota kontrolü ve yedek pay hazır; canlı iş için ayrı bütçe ve kendini ayarlayan sıklık
  eklenmeli.

### 4. Takip durur ama ekran güncel görünür

- **Örnek:** API birkaç dakika yanıt vermez; kullanıcı eski skoru canlı sanar.
- **Nasıl yakalarız:** Son başarılı canlı güncellemeden bu yana geçen süre ölçülür.
- **Ne yaparız:** Ekranda "15 sn önce güncellendi" bilgisi ve gecikmede uyarı gösterilir. API
  düzelince ilk sorguda güncel skor yazılır.
- **Bugün:** Son güncelleme saati ve başarısız güncelleme uyarısı hazır; ekranın kendini
  yenilemesi ve gecikme uyarısı eklenmeli.

### 5. Maç "canlı" durumunda takılı kalır

- **Örnek:** Maç yağmurdan yarıda kalır ve saatlerce "canlı" görünür.
- **Nasıl yakalarız:** Başlamasının üzerinden 3 saat geçmiş ama hâlâ canlı olan maçlar.
- **Ne yaparız:** Bu maçları tek tek yeniden soran bir kontrol görevi; güncel durum gelince maç
  düzelir.
- **Bugün:** Canlı durum kodları tanınıyor, bilinmeyenler atlanıp nedeniyle kaydediliyor; kontrol
  görevi ve uyarı eklenmeli.

### 6. Sonradan gelen düzeltmeler kaçırılır

- **Örnek:** Bir maç sonradan hükmen sonuçlanır veya bir takıma puan cezası verilir.
- **Nasıl yakalarız:** Haftada bir kendi puan tablomuz API'nin tablosuyla karşılaştırılır.
- **Ne yaparız:** Düzeltme lig kuralları dosyasına eklenir, tablo kendiliğinden düzelir.
- **Bugün:** Kural dosyası hazır ve geçmiş sezonlarda kullanıldı; haftalık karşılaştırma ve sezon
  bittikten sonraki birkaç hafta güncelleme eklenmeli.

## 7.500 istekle canlı maç takibi

API-Football o an oynanan bütün maçları **tek istekte** veriyor. Bu yüzden maliyeti maç sayısı
değil, ne sıklıkla sorduğumuz belirliyor.

**Varsayımlar:** 5 lig, yoğun günde ~30 maç, maçlar ~12 saate yayılıyor. API canlı veriyi 15
saniyede bir yeniliyor, daha sık sormanın faydası yok.

| İş                                          | İstek / gün |
| ------------------------------------------- | ----------: |
| Canlı skor (15 saniyede bir, 12 saat)       |       2.880 |
| Maç listesi, istatistik ve diğer kontroller |        ~110 |
| Yedek (limitin ~%20'si)                     |       1.500 |
| **Toplam**                                  |  **~4.500** |

~110 isteğin dağılımı: sabah güncellemesi 5, maç listesini 2 saatte bir kontrol 60, maç sonu
kontrolü ve istatistikler ~40, haftalık sezon ve puan tablosu kontrolü ~2.

- **Sonuç:** 7.500'ün rahatça altında kalıyor. Kullanıcı sayısı artsa da istek sayısı değişmiyor.
- **Ne kadar hızlı?** Kullanıcı bir golü yaklaşık 20–30 saniye içinde görür. Daha hızlısı için push
  destekli bir veri servisi gerekir.
- **Hak azalırsa:** Sorma aralığı 15 → 30 → 60 saniyeye çıkarılır.
