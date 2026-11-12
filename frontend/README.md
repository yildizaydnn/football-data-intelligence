# Frontend

Next.js (App Router) + TypeScript + Tailwind + shadcn/ui + TanStack Query.

```bash
pnpm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL
pnpm dev                     # http://localhost:3000
pnpm gen:api                 # openapi.json → src/lib/api/schema.d.ts (kökten: make api-types)
```

## Yapı

```
src/
├── app/              # sadece routing; içerik features/'tan gelir
├── features/         # ekran bazlı: dashboard, overview, fixtures, standings, teams, sync
│   └── <feature>/hooks.ts   # queryOptions + useX hook'ları (veri tek yoldan gelir)
├── shared/           # projeye özel ortak bileşenler (QueryBoundary, FormChip, ...)
├── components/ui/    # shadcn (dokunulmaz)
└── lib/api/          # client.ts, endpoints.ts, types.ts, schema.d.ts (üretilir)
```

Veri akışı: `endpoints.ts` → feature hook (`useStandings`) → bileşen. Bileşenler `fetch` kullanmaz.
Her veri bölümü `QueryBoundary` ile sarılır: yükleniyor/hata durumları her ekranda aynı.
Lig ve sezon URL'de tutulur (`/leagues/1/standings?season=2024`), link paylaşılabilir.
