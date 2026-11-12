import { RotateCcw, SearchX, WifiOff } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/client";
import { cn } from "@/lib/utils";

export function ErrorState({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  const offline = error instanceof ApiError && error.code === "network_error";
  const Icon = offline ? WifiOff : SearchX;
  return (
    <StateCard icon={<Icon className="size-5 text-loss" />} tone="error">
      <p className="font-semibold text-chalk">
        {offline ? "Sunucuya ulaşılamıyor" : "Veri yüklenemedi"}
      </p>
      <p className="text-sm text-sage">
        {offline ? "Backend çalışıyor mu? Bağlantıyı kontrol edip tekrar deneyin." : error.message}
      </p>
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-2" onClick={onRetry}>
          <RotateCcw /> Tekrar dene
        </Button>
      )}
    </StateCard>
  );
}

export function InlineError({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  const offline = error instanceof ApiError && error.code === "network_error";
  return (
    <div role="alert" className="flex items-center gap-2 rounded-xl border border-loss/25 px-3 py-2 text-sm">
      <WifiOff className="size-4 text-loss" />
      <span className="text-mist">{offline ? "Sunucuya ulaşılamıyor" : "Yüklenemedi"}</span>
      {onRetry && (
        <Button variant="ghost" size="icon-sm" onClick={onRetry} aria-label="Tekrar dene">
          <RotateCcw />
        </Button>
      )}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <StateCard icon={<SearchX className="size-5 text-moss" />}>
      <p className="font-semibold text-chalk">{title}</p>
      {hint && <p className="text-sm text-sage">{hint}</p>}
    </StateCard>
  );
}

function StateCard({
  icon,
  tone,
  children,
}: {
  icon: ReactNode;
  tone?: "error";
  children: ReactNode;
}) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "animate-fade-up flex flex-col items-center gap-1 rounded-2xl border bg-card px-6 py-10 text-center",
        tone === "error" && "border-loss/25",
      )}
    >
      <div className="mb-2 grid size-10 place-items-center rounded-full bg-white/5">{icon}</div>
      {children}
    </div>
  );
}
