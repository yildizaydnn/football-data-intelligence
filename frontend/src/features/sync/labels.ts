import type { SyncRun } from "@/lib/api/types";

type Status = SyncRun["status"];
type Trigger = SyncRun["trigger"];

export const RUN_LABEL: Record<Status, { short: string; dot: string; badge: string }> = {
  success: { short: "Başarılı", dot: "bg-win", badge: "bg-win/15 text-win" },
  partial: { short: "Kısmen", dot: "bg-amber", badge: "bg-amber/15 text-[#ffc877]" },
  failed: { short: "Başarısız", dot: "bg-loss", badge: "bg-loss/15 text-[#ffb3a8]" },
  running: { short: "Sürüyor", dot: "bg-lime animate-pulse", badge: "bg-lime/15 text-lime" },
  skipped: { short: "Gerek görülmedi", dot: "bg-moss", badge: "bg-white/8 text-mist" },
};

export const TRIGGER_LABEL: Record<Trigger, string> = {
  manual: "Elle güncelleme",
  scheduled: "Otomatik güncelleme",
  initial: "İlk yükleme",
};

/** Bir güncellemenin sonucunu günlük dille anlatır (teknik ayrıntı ayrı gösterilir). */
export function describeRun(run: SyncRun): string {
  if (run.status === "running") return "Veriler şu anda güncelleniyor…";
  if (run.status === "skipped") {
    return "Sezondaki tüm maçlar bittiği için veri sağlayıcıya sorulmadı; API hakkı harcanmadı.";
  }
  if (run.status === "failed") return `${failureReason(run.error_message)} Mevcut veriler korundu.`;

  const changes = [
    run.inserted && `${num(run.inserted)} yeni kayıt eklendi`,
    run.updated && `${num(run.updated)} kayıt güncellendi`,
  ].filter(Boolean);
  const summary = changes.length ? changes.join(", ") : "Yeni veri yoktu, her şey güncel";
  const skipped = run.skipped ? ` ${num(run.skipped)} hatalı kayıt atlandı.` : "";
  return `${summary}.${skipped}`;
}

export function apiUsageText(run: SyncRun): string | null {
  if (run.status === "skipped" || run.status === "running") return null;
  return run.requests_made ? `${run.requests_made} API hakkı kullanıldı` : null;
}

function failureReason(error: string | null): string {
  const text = error ?? "";
  if (text.includes("429") || /rate limit/i.test(text)) {
    return "Veri sağlayıcı o an yoğundu (dakikalık istek sınırı), güncelleme yapılamadı.";
  }
  if (/günlük|request limit/i.test(text)) return "Günlük API hakkı dolmuştu, güncelleme yapılamadı.";
  if (/bütçe|kota/i.test(text)) return "Günlük API hakkı yetmediği için güncelleme başlatılmadı.";
  return "Veri sağlayıcıya ulaşılamadı, güncelleme yapılamadı.";
}

const num = (n: number) => n.toLocaleString("tr-TR");
