/** Tarihler UTC saklanır; Türkiye saatiyle gösterilir (sunucu ve tarayıcıda aynı sonuç). */
const TZ = "Europe/Istanbul";

const dayFormat = new Intl.DateTimeFormat("tr-TR", {
  day: "numeric",
  month: "long",
  year: "numeric",
  weekday: "long",
  timeZone: TZ,
});
const shortDayFormat = new Intl.DateTimeFormat("tr-TR", {
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: TZ,
});
const timeFormat = new Intl.DateTimeFormat("tr-TR", {
  hour: "2-digit",
  minute: "2-digit",
  timeZone: TZ,
});
const dateTimeFormat = new Intl.DateTimeFormat("tr-TR", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: TZ,
});
const isoDayFormat = new Intl.DateTimeFormat("en-CA", { timeZone: TZ }); // YYYY-MM-DD

/** "8 Kasım 2026, Pazar" */
export function formatMatchDay(iso: string) {
  const parts = dayFormat.formatToParts(new Date(iso));
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return `${get("day")} ${get("month")} ${get("year")}, ${get("weekday")}`;
}

/** "8 Kasım 2026" */
export const formatDay = (iso: string) => shortDayFormat.format(new Date(iso));

/** "19:00" */
export const formatTime = (iso: string) => timeFormat.format(new Date(iso));

/** "12 Kas 2026 17:30" */
export const formatDateTime = (iso: string) => dateTimeFormat.format(new Date(iso));

/** Gruplama anahtarı: Türkiye saatine göre gün. */
export const dayKey = (iso: string) => isoDayFormat.format(new Date(iso));

/** 0.4912 → "%49" */
export const formatPercent = (ratio: number) => `%${Math.round(ratio * 100)}`;

/** 2.9342 → "2,93" */
export const formatDecimal = (n: number, digits = 2) =>
  n.toLocaleString("tr-TR", { minimumFractionDigits: digits, maximumFractionDigits: digits });

/** "2024/25" */
export const formatSeason = (year: number) => `${year}/${String((year + 1) % 100).padStart(2, "0")}`;

/** "+5", "0", "-3" */
export const formatSigned = (n: number) => (n > 0 ? `+${n}` : String(n));
