"use client";

import { useTransition } from "react";

import { cn } from "@/lib/utils";
import { PanelSkeleton } from "@/shared/components/panel";
import { QueryBoundary } from "@/shared/components/query-boundary";

import { useMatchFilters } from "./hooks";
import { MatchFiltersBar } from "./match-filters";
import { MatchList } from "./match-list";

export function MatchesView() {
  const { filters, setFilters } = useMatchFilters();
  const [isPending, startTransition] = useTransition();

  return (
    <div className="space-y-6">
      <QueryBoundary fallback={<PanelSkeleton className="h-[120px]" />} inline>
        <MatchFiltersBar
          filters={filters}
          onChange={(patch) => startTransition(() => setFilters(patch))}
        />
      </QueryBoundary>
      {/* Filtre değişirken eski liste soluk kalır; iskelete geri dönülmez. */}
      <div className={cn("transition-opacity", isPending && "pointer-events-none opacity-50")}>
        <QueryBoundary fallback={<MatchListSkeleton />}>
          <MatchList filters={filters} />
        </QueryBoundary>
      </div>
    </div>
  );
}

function MatchListSkeleton() {
  return (
    <div className="space-y-6">
      {Array.from({ length: 3 }, (_, i) => (
        <div key={i} className="space-y-2.5">
          <PanelSkeleton className="h-4 w-48 rounded-md" />
          <PanelSkeleton className="h-[140px]" />
        </div>
      ))}
    </div>
  );
}
