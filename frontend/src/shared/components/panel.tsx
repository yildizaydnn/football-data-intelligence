import type { ComponentProps, ReactNode } from "react";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

/** Tasarımdaki koyu yeşil kart. */
export function Panel({ className, ...props }: ComponentProps<"section">) {
  return <section className={cn("rounded-[20px] border bg-card p-5 sm:p-6", className)} {...props} />;
}

export function PanelHeader({
  title,
  aside,
  className,
}: {
  title: ReactNode;
  aside?: ReactNode;
  className?: string;
}) {
  return (
    <header className={cn("mb-5 flex flex-wrap items-baseline justify-between gap-2", className)}>
      <h2 className="font-display text-2xl font-extrabold uppercase">{title}</h2>
      {aside && <div className="text-sm text-sage">{aside}</div>}
    </header>
  );
}

export function PanelSkeleton({ className }: { className?: string }) {
  return <Skeleton className={cn("rounded-[20px] bg-card", className)} />;
}
