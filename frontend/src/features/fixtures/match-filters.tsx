"use client";

import { ArrowDownWideNarrow, ArrowUpNarrowWide, X } from "lucide-react";

import { useDashboardParams } from "@/features/dashboard/hooks";
import { useTeams } from "@/features/teams/hooks";
import type { MatchStatus } from "@/lib/api/types";
import { cn } from "@/lib/utils";
import { Panel } from "@/shared/components/panel";
import { SelectField } from "@/shared/components/select-field";
import { STATUS_LABEL } from "@/shared/components/status-badge";

import type { MatchFilters } from "./hooks";

type Patch = Partial<Record<"team" | "status" | "from" | "to" | "order", string | undefined>>;

const STATUS_PILLS: (MatchStatus | undefined)[] = [undefined, "finished", "live", "scheduled", "postponed"];
const ALL = "all";

export function MatchFiltersBar({
  filters,
  onChange,
}: {
  filters: MatchFilters;
  onChange: (patch: Patch) => void;
}) {
  const { leagueId, season } = useDashboardParams();
  const teams = useTeams(leagueId, season);
  const active = Boolean(filters.teamId || filters.status || filters.from || filters.to);

  return (
    <Panel className="flex flex-wrap items-end gap-x-5 gap-y-4 p-5">
      <SelectField
        label="Takım"
        className="w-full sm:w-56"
        value={filters.teamId ? String(filters.teamId) : ALL}
        onChange={(v) => onChange({ team: v === ALL ? undefined : v })}
        options={[
          { value: ALL, label: "Tüm takımlar" },
          ...teams.map((t) => ({ value: String(t.id), label: t.name })),
        ]}
      />

      <fieldset className="flex flex-col gap-1.5">
        <legend className="mb-1.5 text-[11px] font-semibold uppercase tracking-widest text-sage">
          Tarih aralığı
        </legend>
        <div className="flex items-center gap-2">
          <DateInput label="Başlangıç" value={filters.from} max={filters.to} onChange={(v) => onChange({ from: v })} />
          <span className="text-moss">–</span>
          <DateInput label="Bitiş" value={filters.to} min={filters.from} onChange={(v) => onChange({ to: v })} />
        </div>
      </fieldset>

      <fieldset className="flex flex-col gap-1.5">
        <legend className="mb-1.5 text-[11px] font-semibold uppercase tracking-widest text-sage">Durum</legend>
        <div className="flex flex-wrap gap-1.5" role="radiogroup" aria-label="Maç durumu">
          {STATUS_PILLS.map((status) => {
            const on = filters.status === status;
            return (
              <button
                key={status ?? ALL}
                type="button"
                role="radio"
                aria-checked={on}
                onClick={() => onChange({ status })}
                className={cn(
                  "min-h-9 rounded-full border px-3.5 text-[13px] font-medium transition-colors",
                  on
                    ? "border-chalk bg-chalk text-pitch-900"
                    : "border-white/14 text-mist hover:border-white/30",
                )}
              >
                {status ? STATUS_LABEL[status] : "Tümü"}
              </button>
            );
          })}
        </div>
      </fieldset>

      <div className="ml-auto flex items-center gap-2">
        {active && (
          <button
            type="button"
            onClick={() => onChange({ team: undefined, status: undefined, from: undefined, to: undefined })}
            className="inline-flex min-h-9 items-center gap-1.5 rounded-full px-3 text-[13px] text-sage hover:text-chalk"
          >
            <X className="size-3.5" /> Filtreleri temizle
          </button>
        )}
        <button
          type="button"
          onClick={() => onChange({ order: filters.order === "desc" ? "asc" : undefined })}
          className="inline-flex min-h-9 items-center gap-1.5 rounded-full border border-white/14 px-3.5 text-[13px] font-medium text-mist hover:border-white/30"
        >
          {filters.order === "desc" ? (
            <>
              <ArrowDownWideNarrow className="size-4" /> En yeni önce
            </>
          ) : (
            <>
              <ArrowUpNarrowWide className="size-4" /> En eski önce
            </>
          )}
        </button>
      </div>
    </Panel>
  );
}

function DateInput({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value?: string;
  min?: string;
  max?: string;
  onChange: (value: string | undefined) => void;
}) {
  return (
    <input
      type="date"
      aria-label={label}
      value={value ?? ""}
      min={min}
      max={max}
      onChange={(e) => onChange(e.target.value || undefined)}
      className="tabular h-11 w-[150px] rounded-xl border border-white/14 bg-pitch-800 px-3 text-sm text-chalk outline-none focus-visible:border-lime focus-visible:ring-3 focus-visible:ring-lime/40"
    />
  );
}
