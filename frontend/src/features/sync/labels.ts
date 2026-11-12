import type { SyncRun } from "@/lib/api/types";

type Status = SyncRun["status"];
type Trigger = SyncRun["trigger"];

export const RUN_LABEL: Record<Status, { short: string; dot: string }> = {
  success: { short: "başarılı", dot: "bg-win" },
  partial: { short: "kısmi", dot: "bg-amber" },
  failed: { short: "başarısız", dot: "bg-loss" },
  running: { short: "çalışıyor", dot: "bg-lime animate-pulse" },
  skipped: { short: "atlandı", dot: "bg-moss" },
};

export const TRIGGER_LABEL: Record<Trigger, string> = {
  manual: "Manuel güncelleme",
  scheduled: "Zamanlanmış güncelleme",
  initial: "İlk veri yükleme",
};
