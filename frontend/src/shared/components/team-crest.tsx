import Image from "next/image";

import type { TeamRef } from "@/lib/api/types";
import { cn } from "@/lib/utils";

/** Takım logosu; logo yoksa baş harfler. */
export function TeamCrest({ team, size = 24, className }: { team: TeamRef; size?: number; className?: string }) {
  if (!team.logo_url) {
    return (
      <span
        style={{ width: size, height: size }}
        className={cn("grid shrink-0 place-items-center rounded-full bg-white/10 text-[10px] font-bold", className)}
      >
        {(team.code ?? team.name).slice(0, 3).toUpperCase()}
      </span>
    );
  }
  return (
    <Image
      src={team.logo_url}
      alt=""
      width={size}
      height={size}
      className={cn("shrink-0 object-contain", className)}
    />
  );
}
