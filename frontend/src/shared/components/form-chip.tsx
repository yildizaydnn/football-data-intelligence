import type { MatchResult } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const STYLE: Record<MatchResult, { label: string; title: string; className: string }> = {
  win: { label: "G", title: "Galibiyet", className: "bg-win text-[#05210f]" },
  draw: { label: "B", title: "Beraberlik", className: "bg-draw text-[#f1f6f2]" },
  loss: { label: "M", title: "Mağlubiyet", className: "bg-loss text-[#2a0703]" },
};

export function FormChip({
  result,
  size = "sm",
  delay = 0,
}: {
  result: MatchResult;
  size?: "sm" | "lg";
  delay?: number;
}) {
  const style = STYLE[result];
  return (
    <span
      title={style.title}
      style={{ animationDelay: `${delay}s` }}
      className={cn(
        "animate-fade-up inline-grid place-items-center font-bold",
        size === "sm" ? "size-[26px] rounded-lg text-xs" : "size-10 rounded-xl text-sm",
        style.className,
      )}
    >
      {style.label}
    </span>
  );
}

/** Son N maç rozetleri; sırayla belirir (eskiden yeniye). */
export function FormStrip({
  form,
  size,
  className,
}: {
  form: MatchResult[];
  size?: "sm" | "lg";
  className?: string;
}) {
  return (
    <div className={cn("flex gap-1.5", className)} aria-label={`Son ${form.length} maç`}>
      {form.map((result, i) => (
        <FormChip key={i} result={result} size={size} delay={i * 0.06} />
      ))}
    </div>
  );
}
