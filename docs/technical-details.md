# Teknik ayrıntılar

README'deki özetin arkasındaki ayrıntılar: endpoint'ler, ayarlar, limit ve hata yönetimi, mimari,
lig kuralları katmanı, veri bütünlüğü ve teknoloji seçimleri. Veritabanı için:
[database-schema.md](database-schema.md).

## İçindekiler

- [Backend API](#backend-api)
- [Ortam değişkenleri](#ortam-değişkenleri)
- [API kullanımı: gereksiz istekleri azaltma](#api-kullanımı-gereksiz-istekleri-azaltma)
- [Limit ve hata yönetimi](#limit-ve-hata-yönetimi)
- [Otomatik güncelleme](#otomatik-güncelleme)
- [Mimari](#mimari)
- [Lig kuralları katmanı](#lig-kuralları-katmanı)
- [Veri doğruluğu ve temizleme](#veri-doğruluğu-ve-temizleme)
- [Maç istatistikleri (Bonus B)](#maç-istatistikleri-bonus-b)
- [AI karşılaştırma (Bonus C)](#ai-karşılaştırma-bonus-c)
- [Docker](#docker)
- [Teknoloji seçimleri](#teknoloji-seçimleri)
- [Testler ve CI](#testler-ve-ci)

## Backend API

| Endpoint | Açıklama |
|---|---|
| `GET /api/v1/leagues`, `GET /api/v1/leagues/{id}`, `GET /api/v1/leagues/{id}/seasons` | Lig ve sezon seçimi (yalnızca verisi olan sezonlar) |
| `GET /api/v1/leagues/{id}/teams` | Takım listesi |
| `GET /api/v1/leagues/{id}/fixtures` | Maç listesi; `team_id`, `date_from`, `date_to`, `status`, `order`, sayfalama |
| `GET /api/v1/fixtures/{id}` | Maç detayı ve değişiklik geçmişi |
| `GET /api/v1/fixtures/{id}/statistics` | Maç istatistikleri (Bonus B) |
| `GET /api/v1/leagues/{id}/teams/{team_id}/stats` | Takım performans istatistikleri |
| `GET /api/v1/leagues/{id}/standings` | Puan tablosu |
| `GET /api/v1/leagues/{id}/overview` | Genel görünüm özeti |
| `GET /api/v1/leagues/{id}/rules` | Ligin uygulanan kuralları (sıralama kriterleri, bölgeler, cezalar) |
| `POST /api/v1/sync` | Veri güncelleme (isteğe bağlı `X-Sync-Token` ile korunur) |
| `GET /api/v1/sync/status`, `GET /api/v1/sync/usage` | Son senkronizasyon durumu, geçmiş, zamanlama, günlük API kotası |
| `GET /api/v1/insights/status`, `POST /api/v1/leagues/{id}/insights` | AI karşılaştırma (Bonus C) |

Sezon parametresi (`?season=2023`) verilmezse verisi olan en güncel sezon kullanılır. Hatalar her
endpoint'te aynı biçimde döner: `{"error": {"code": ..., "message": ...}}`.

## Ortam değişkenleri

Hepsi [.env.example](../.env.example) içinde açıklamalarıyla yer alır. Önemli olanlar:

| Değişken | Açıklama |
|---|---|
| `API_FOOTBALL_REQUESTS_PER_MINUTE` | Dakikalık istek sınırı; istekler buna göre aralıklandırılır |
| `API_FOOTBALL_KEY` | API anahtarı. Yalnızca backend okur; frontend'e ve repoya hiç girmez |
| `TRACKED_LEAGUES` | Zamanlanmış güncellemenin takip ettiği ligler (API id listesi) |
| `DEFAULT_LEAGUE_ID`, `DEFAULT_SEASON` | Varsayılan lig ve zamanlanmış güncellemenin sezonu |
| `SCHEDULER_ENABLED`, `SYNC_CRON` | Otomatik güncelleme açık mı, ne zaman (UTC cron) |
| `SYNC_API_TOKEN` | Doluysa `POST /sync` bu token'ı `X-Sync-Token` başlığında ister |
| `STATISTICS_QUOTA_RESERVE` | Maç istatistikleri, kotanın son N isteğine dokunamaz |
| `GEMINI_API_KEY`, `OPENROUTER_API_KEY` | AI karşılaştırma; ikisi de boşsa özellik kapalı görünür |
| `AI_DAILY_LIMIT` | Günlük en fazla yeni AI analizi |

## API kullanımı: gereksiz istekleri azaltma

- **Bitmiş sezon atlanır:** sezonda sonuçlanmamış maç kalmadıysa zamanlanmış güncelleme API'ye hiç
  istek atmaz, `skipped` kaydı düşer. Elle güncelleme bu kontrolden muaftır.
- **Referans veri bir kez çekilir:** lig/sezon/takım verisi yalnızca ilk yüklemede istenir.
- **İstatistikler bir kez çekilir:** `fixtures.statistics_fetched_at` doluysa (API veri sağlamamış
  olsa bile) tekrar istenmez.
- **Değişmeyen satıra yazılmaz:** upsert yalnızca gerçekten değişen satırları günceller
  (`ON CONFLICT DO UPDATE ... WHERE ... IS DISTINCT FROM`).
- **Frontend önbelleği:** TanStack Query aynı veriyi tekrar istemez; backend zaten veritabanından
  okuduğu için sayfa gezinmesi API kotasına hiç dokunmaz.

## Limit ve hata yönetimi

| Durum | Davranış |
|---|---|
| Günlük kota yetmez | Her güncellemeden önce kaç istek gerektiği hesaplanır (`next_sync_cost`), kota yetmiyorsa istek atılmadan reddedilir (429). Kalan kota, kendi sayacımız ile API'nin `x-ratelimit-requests-remaining` başlığından küçük olanıdır |
| Kota rezervi | Maç istatistikleri kotanın son 10 isteğine dokunamaz; otomatik güncelleme her zaman çalışabilir |
| Dakikalık sınır (önlem) | İstekler süreç genelinde ortak bir kayan pencereyle aralıklandırılır: son 60 sn'de `API_FOOTBALL_REQUESTS_PER_MINUTE` (10) istek atıldıysa en eskisinin pencereden çıkması beklenir. Yeniden denemeler de bu sayıma dahildir |
| Dakikalık sınır yine aşılırsa (HTTP 429 veya yanıt içinde `rateLimit`) | Pencerenin sıfırlanması için 60 sn (veya API'nin `Retry-After` değeri kadar, en fazla 60 sn) beklenip yeniden denenir |
| 5xx, zaman aşımı, bağlantı hatası | Kısa üstel bekleme ile en fazla 3 deneme (tenacity) |
| HTTP 200 + `errors` alanı | API-Football hataları çoğunlukla böyle döner; gövde ayrıştırılıp doğru hata türüne çevrilir |
| Bozuk veya eksik kayıt | Tek kayıt yüzünden sync düşmez: kayıt atlanır, neden loglanır, güncelleme `partial` olarak işaretlenir |
| Güncelleme yarıda kalır | Transaction geri alınır, mevcut veri bozulmaz; hata `sync_runs` tablosuna yazılır, harcanan istekler yine kotaya işlenir |
| Aynı anda iki güncelleme | Veritabanı seviyesinde kilit (kısmi unique index) ikincisini 409 ile reddeder; takılı kalan kilit 30 dakika sonra otomatik açılır |

**API erişilemezse:** dashboard hiçbir zaman API-Football'a doğrudan gitmez, her şeyi
veritabanından okur. API çökse de, kota bitse de bütün ekranlar son başarılı güncellemedeki veriyle
çalışmaya devam eder. Başarısız güncelleme arayüzde uyarı olarak gösterilir.

**Kullanım takibi:** `api_usage` tablosu günlük istek sayısını tutar. Arayüzün üst kısmında kalan
kota, "Veri güncellemeleri" panelinde her güncellemenin kaç istek harcadığı, kaç kayıt eklediği ve
güncellediği ve bir sonraki otomatik güncellemenin zamanı görünür.

## Otomatik güncelleme

- **Ana mekanizma:** APScheduler, backend sürecinin içinde (`SCHEDULER_ENABLED=true`). `SYNC_CRON`
  zamanında `TRACKED_LEAGUES` içindeki her lig sırayla ve birbirinden bağımsız güncellenir; biri hata
  verirse diğerleri yine çalışır.
- **Yedek:** [.github/workflows/scheduled-sync.yml](../.github/workflows/scheduled-sync.yml). Backend
  uyuyan bir ortamda çalışıyorsa GitHub Actions cron'u `POST /sync` çağırır. Varsayılan olarak
  kapalıdır (`SCHEDULED_SYNC_ENABLED` repo değişkeni ile açılır).

## Mimari

```
backend/app
├── api/v1/         HTTP katmanı: endpoint'ler, şemalar, hata biçimi
├── services/       İş akışları: transaction sınırları, kota kontrolü, kilit
├── repositories/   Veritabanı erişimi (SQLAlchemy 2.0), idempotent upsert
├── models/         ORM modelleri
├── etl/            extract → transform → load; ham API verisini doğrulayıp temizler
├── providers/      Dış servisler: API-Football client, LLM sağlayıcıları
├── analytics/      Saf hesaplama: puan tablosu, eşitlik bozma, takım performansı, karşılaştırma
├── rules/          Lige özel kurallar (YAML spec → doğrulanmış RuleContext)
├── insights/       AI prompt'u ve sayı doğrulaması
├── scheduler/      Zamanlanmış güncelleme
└── core/           Ayarlar, veritabanı, enum'lar, hata türleri
```

Bağımlılık tek yönlüdür: `api → services → repositories → models`. `analytics` ve `rules` hiçbir
katmana bağlı değildir (veritabanı, HTTP bilmez); bu yüzden puan tablosu ve performans hesapları
saf fonksiyon olarak kolayca test edilir.

**Sağlayıcı soyutlaması:** servisler API-Football'a değil `FootballDataProvider` arayüzüne bağımlıdır.
Başka bir veri kaynağına geçmek tek bir sınıf yazmayı gerektirir; testlerde aynı arayüzün sahte
uygulaması kullanılır. Maç istatistikleri ayrı bir arayüzdedir (`MatchStatsProvider`); güncelleme
akışı ona bağımlı olmaz.

**Frontend** (`frontend/src`) özellik bazlı düzenlenmiştir (`features/overview`, `fixtures`,
`standings`, `teams`, `sync`, `dashboard`). Paylaşılan bileşenler `shared/` altındadır. API tipleri
backend'in OpenAPI şemasından **otomatik üretilir** (`make api-types`). Backend bir alanı değiştirirse
frontend derlenmez; CI bu senkronu da kontrol eder. Lig, sezon, takım ve filtreler URL'de tutulur;
her görünüm paylaşılabilir ve geri tuşu beklendiği gibi çalışır.

## Lig kuralları katmanı

Ligler puan tablosunu farklı kurallarla sıralar. Süper Lig'de puan eşitliğinde önce ikili averaja
bakılır, Premier League'de genel averaja. Bazı sezonlarda puan silme cezaları vardır. Avrupa kupası
ve küme düşme bölgeleri de ligden lige değişir. Bu farklar koda `if league == ...` olarak gömülmedi;
**katmanlı YAML spec'ler** olarak tanımlandı:

```
rules/specs/default.yaml            ortak varsayılanlar
  ← rules/specs/leagues/<id>.yaml   lige özel farklar
    ← seasons.<yıl>                 sezona özel farklar (cezalar, bölge değişiklikleri)
```

Katmanlar birleştirilir ve pydantic ile doğrulanmış tek bir `RuleContext`'e dönüşür. Uygulama
açılırken bütün spec'ler doğrulanır; hatalı bir kural (bilinmeyen kriter, geçersiz regex) uygulamayı
başlatmaz. Spec'lerin tanımladıkları:

- **Puanlama:** galibiyet / beraberlik / mağlubiyet puanı
- **Sıralama kriterleri:** isimli kriterler (`points`, `goal_difference`, `h2h_points`,
  `h2h_goal_difference`, `h2h_away_goals_for`...) istenen sırada. İkili kriterler eşit takım grubu
  içinde özyinelemeli uygulanır
- **Puan silme cezaları:** ör. Premier League 2023/24'te Everton −8, Nottingham Forest −4;
  Serie A 2022/23'te Juventus −10
- **Bölgeler:** Şampiyonlar Ligi, Avrupa Ligi, küme düşme play-off'u, küme düşme. Negatif sıra
  tablonun sonundan sayılır
- **Veri temizleme:** API durum kodlarının eşlenmesi (`FT`, `AET`, `PEN` → bitti; `PST` →
  ertelendi...), puan tablosuna sayılacak turlar (ör. Bundesliga küme play-off maçları hariç),
  maç istatistiklerinin isim eşlemesi

Yeni bir lig eklemek için kod yazmak gerekmez: `leagues/<id>.yaml` eklenir, gerekirse
`TRACKED_LEAGUES`'a yazılır. Arayüzdeki tablo bölgeleri ve açıklamaları da `GET /leagues/{id}/rules`
üzerinden bu spec'ten gelir.

## Veri doğruluğu ve temizleme

- **Tekrar kayıt oluşmaz:** her tablo API kimliğiyle (`external_id`, unique) eşlenir ve
  `INSERT ... ON CONFLICT DO UPDATE` ile yazılır. Aynı maç ikinci kez geldiğinde yeni satır açılmaz,
  mevcut satır güncellenir. Bu davranış testlerle doğrulanır (`test_upsert_idempotency.py`).
- **Değişiklik geçmişi:** bir maçın skoru, durumu veya saati değişirse eski ve yeni değer
  `fixture_changes` tablosuna, hangi güncellemede değiştiğiyle birlikte yazılır. Her güncelleme
  çalışmasının kendisi de `sync_runs` tablosunda saklanır.
- **Eksik / null veri:** API yanıt modelleri bilerek esnektir (çoğu alan opsiyonel). Kimliği veya
  takımı eksik kayıt atlanır ve raporlanır. Oynanmamış maçların skoru `NULL` tutulur ve hesaplara
  katılmaz. Bilinmeyen bir durum kodu tahminle sınıflandırılmaz; kayıt atlanır ve raporlanır.
  API'nin orijinal durum kodu her maçta ayrıca saklanır (`status_raw`).
- **Doğrulama:** hesaplanan tablolar gerçek sonuçlarla karşılaştırıldı: şampiyonlar, puanlar,
  Premier League ve Serie A puan silme cezaları, Bundesliga play-off sıraları.

## Maç istatistikleri (Bonus B)

Maç detayında şut, isabetli şut, topa sahip olma, korner, faul, kart, pas isabeti, beklenen gol (xG)
gibi 17 istatistik gösterilir. Kullanıcı bitmiş bir maçı ilk açtığında istenir, **uzun formatta**
(`fixture_statistics`: maç × takım × istatistik) saklanır ve bir daha istenmez. API'nin veri
sağlamadığı maçlar için "istatistik yok" bilgisi de saklanır; tekrar sorulmaz. Oynanmamış maçlar
için hiç istek atılmaz.

## AI karşılaştırma (Bonus C)

Takım analizi sayfasında iki takım seçilir; kısa, Türkçe, veriye dayalı bir karşılaştırma üretilir.

- **Model eğitilmedi.** Bu iş için eğitim gerekmez; hazır bir dil modeline doğru veri vermek
  yeterlidir. Bütün sayılar (puanlar, oranlar, iç saha/deplasman, son 5 maç, aralarındaki maçlar)
  `analytics` katmanında veritabanından hesaplanır ve JSON olarak modele verilir. Modelin görevi
  hesap yapmak değil, bu veriyi yorumlamaktır.
- **Sayı doğrulaması:** üretilen metindeki her sayı verilen veriyle karşılaştırılır. Veride olmayan
  bir sayı varsa metin engellenmez ama arayüzde "doğrulanamayan sayılar" uyarısı gösterilir.
- **Önbellek:** analiz, verinin özetiyle (sha256) birlikte saklanır. Veri değişmedikçe aynı
  karşılaştırma modele tekrar sorulmaz; maç sonuçları değişince otomatik yenilenir.
- **Yedekli sağlayıcı:** önce Gemini (birkaç model sırayla), yoğunluk veya hata durumunda
  OpenRouter üzerindeki ücretsiz modeller denenir. Anahtar yoksa özellik arayüzde "kapalı" görünür,
  uygulamanın geri kalanı etkilenmez. Günlük yeni analiz sınırı vardır (`AI_DAILY_LIMIT`).
- Kullanılan veri herkese açık maç sonuçlarıdır; kişisel veri gönderilmez. Gemini'nin ücretsiz
  katmanı gönderilen veriyi model geliştirme için kullanabilir. Bu veri için sorun değil, ama gizli
  veriyle kullanılacaksa ücretli katman gerekir.

## Docker

| Servis | İmaj | Not |
|---|---|---|
| `db` | `postgres:16-alpine` | Veriler `pgdata` volume'ünde; `docker compose down` verileri silmez (`-v` siler) |
| `backend` | `python:3.12-slim` üzerinde iki aşamalı derleme | Bağımlılıklar `uv.lock`'tan, dev bağımlılıkları olmadan. Açılışta `alembic upgrade head` çalışır. Root olmayan kullanıcı, `/health` sağlık kontrolü. Zamanlayıcı süreç içinde çalıştığı için tek worker |
| `frontend` | `node:20-alpine`, Next.js `standalone` çıktısı | Yalnızca çalışmaya gereken dosyalar kopyalanır |

- **Gizli bilgiler imaja girmez:** `.env` `.dockerignore`'da; backend ayarları çalışırken `env_file` ile okur.
- **Veritabanı adresi:** container içinden `localhost` değil servis adı (`db`) kullanılır; compose bunu `DATABASE_URL` ile ayarlar.
- **`NEXT_PUBLIC_API_URL` derleme anında koda gömülür.** Tarayıcının erişeceği backend adresi olmalı; değişirse frontend imajı yeniden derlenir (`docker compose up -d --build`).
- **CORS:** arayüz farklı bir adresten açılıyorsa `CORS_ORIGINS` güncellenmeli.
- Portlar `BACKEND_PORT`, `FRONTEND_PORT`, `POSTGRES_PORT` ile değiştirilebilir.

## Teknoloji seçimleri

İstenen yığın birebir kullanıldı: **Next.js + React + TypeScript, FastAPI, PostgreSQL, Tailwind CSS
+ shadcn/ui, Python**. Bunların üzerine eklenenler ve nedenleri:

| Araç | Neden |
|---|---|
| **SQLAlchemy 2.0 + Alembic** | Tipli ORM, PostgreSQL'e özel `ON CONFLICT` upsert desteği; şema değişiklikleri versiyonlu migration'larla. CI, modellerle migration'ların uyumunu da kontrol eder (`alembic check`) |
| **uv** | pip/poetry yerine: çok hızlı, kilit dosyalı (`uv.lock`), Python sürümünü de yönetir |
| **ruff** | flake8 + isort + black yerine tek ve hızlı araç |
| **httpx + tenacity** | Timeout'lu HTTP client ve hata türüne göre yeniden deneme politikası |
| **APScheduler** | Zamanlanmış güncelleme için Celery + Redis gibi ek altyapı gerekmez; günde bir iş için süreç içi scheduler yeterli. Kilit veritabanında olduğu için birden fazla süreçte de güvenli |
| **PyYAML + pydantic** | Lig kuralları kod değil veri olarak; yüklenirken şemaya göre doğrulanır |
| **TanStack Query** | Sunucu verisi için önbellek, yükleme ve hata durumları, sonsuz kaydırma (maç listesi) |
| **openapi-typescript + openapi-fetch** | Frontend tipleri backend şemasından üretilir; elle yazılan ve zamanla backend'den ayrışan tip kalmaz |
| **Recharts** (shadcn Chart üzerinden) | shadcn'in grafik bileşeni; tema ile uyumlu |
| **pnpm** | Hızlı, disk dostu, kilit dosyalı paket yöneticisi |
| **Gemini + OpenRouter** | Ücretsiz katmanları olan iki ayrı sağlayıcı; biri meşgulken diğeri devreye girer |

## Testler ve CI

```bash
make test     # backend: 243 test
make lint     # ruff + eslint + TypeScript
```

- **Birim testleri:** puan tablosu ve eşitlik bozma senaryoları (ikili averaj, üçlü eşitlik, puan
  silme), takım performansı, sezon özeti, kural motoru, API yanıtı dönüştürücüleri, durum eşleme,
  HTTP client'ın yeniden deneme ve limit davranışı, LLM yedekleme zinciri, AI sayı doğrulaması.
- **Entegrasyon testleri** (gerçek PostgreSQL, ayrı test veritabanı): upsert idempotency, değişiklik
  geçmişi, sync kilidi ve kota kontrolü, zamanlanmış görev, bütün API endpoint'leri.
- Testlerde gerçek API'ye istek atılmaz; gerçek API yanıtlarından alınmış JSON örnekleri ve sahte
  sağlayıcı kullanılır.

**CI** ([.github/workflows/ci.yml](../.github/workflows/ci.yml)) `main`'e her push'ta ve her PR'da çalışır:

- **Backend:** ruff, migration'lar ve `alembic check`, testler
- **Frontend:** üretilen API tiplerinin güncel olduğu kontrolü, lint, tip kontrolü, production build
