"use client";

import { TriangleAlert } from "lucide-react";

import { formatDateTime } from "@/shared/lib/format";

import { useSyncStatus } from "./hooks";

/** Son senkronizasyon başarısızsa: kullanıcıya eski veri gösterildiğini söyler. */
export function SyncAlert() {
  const { recent } = useSyncStatus();
  const last = recent[0];
  if (!last || last.status !== "failed") return null;

  const lastGood = recent.find((run) => run.status === "success" || run.status === "partial");
  return (
    <div
      role="alert"
      className="animate-fade-up mt-6 flex items-start gap-3 rounded-2xl border border-amber/30 bg-amber/10 px-4 py-3 text-sm"
    >
      <TriangleAlert className="mt-0.5 size-4 shrink-0 text-amber" />
      <p>
        <b className="font-semibold text-[#ffc877]">Son güncelleme başarısız oldu.</b>{" "}
        <span className="text-mist">
          {last.error_message ?? "Veri sağlayıcıya ulaşılamadı."} Veritabanındaki son veriler
          gösteriliyor{lastGood ? ` (${formatDateTime(lastGood.started_at)})` : ""}.
        </span>
      </p>
    </div>
  );
}
