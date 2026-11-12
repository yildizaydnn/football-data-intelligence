"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

import { useDashboardParams } from "./hooks";

const TABS = [
  { path: "", label: "Genel Görünüm" },
  { path: "/matches", label: "Maçlar" },
  { path: "/standings", label: "Puan Tablosu" },
  { path: "/teams", label: "Takım Analizi" },
] as const;

export function NavTabs() {
  const pathname = usePathname();
  const { leagueId, href } = useDashboardParams();
  const section = pathname.replace(`/leagues/${leagueId}`, "");

  return (
    <nav
      aria-label="Bölümler"
      className="relative z-10 -mt-7 inline-flex max-w-full gap-1 overflow-x-auto rounded-full border border-white/10 bg-pitch-900/95 p-1.5 shadow-[0_10px_30px_rgb(0_0_0/35%)] backdrop-blur"
    >
      {TABS.map((tab) => {
        const active = tab.path === "" ? section === "" : section.startsWith(tab.path);
        return (
          <Link
            key={tab.path}
            href={href(tab.path)}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex min-h-11 items-center whitespace-nowrap rounded-full px-4 text-sm font-semibold transition-colors sm:px-5",
              active ? "bg-lime text-pitch-900" : "text-sage hover:bg-white/5 hover:text-chalk",
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}

export function NavTabsSkeleton() {
  return <div className="relative z-10 -mt-7 h-14 w-[520px] max-w-full rounded-full border bg-pitch-900" />;
}
