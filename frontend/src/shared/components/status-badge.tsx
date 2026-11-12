import type { MatchStatus } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const STATUS: Record<MatchStatus, { label: string; className: string }> = {
  finished: { label: "Bitti", className: "bg-white/8 text-mist" },
  live: { label: "Canlı", className: "bg-live/15 text-[#ff9b8f]" },
  scheduled: { label: "Planlandı", className: "bg-lime/12 text-[#d7f57a]" },
  postponed: { label: "Ertelendi", className: "bg-amber/14 text-[#ffc877]" },
  cancelled: { label: "İptal", className: "bg-white/5 text-moss line-through" },
};

export const STATUS_LABEL = Object.fromEntries(
  Object.entries(STATUS).map(([key, value]) => [key, value.label]),
) as Record<MatchStatus, string>;

export function StatusBadge({ status }: { status: MatchStatus }) {
  const { label, className } = STATUS[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold",
        className,
      )}
    >
      {status === "live" && <LiveDot />}
      {label}
    </span>
  );
}

export function LiveDot() {
  return <span className="animate-live size-2 rounded-full bg-live" aria-hidden />;
}
