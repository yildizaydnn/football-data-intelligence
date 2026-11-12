import Link from "next/link";

import { TopBar } from "@/features/dashboard/dashboard-shell";
import { Pitch } from "@/features/dashboard/hero";

export default function NotFound() {
  return (
    <div className="min-h-dvh">
      <TopBar />
      <Pitch>
        <div className="flex h-full flex-col justify-center">
          <p className="text-sm font-bold uppercase tracking-[0.18em]">404 · Ofsayt</p>
          <h1 className="font-display mt-2 text-6xl font-extrabold uppercase">Sayfa bulunamadı</h1>
          <Link href="/" className="mt-4 w-fit rounded-xl bg-lime px-4 py-2.5 font-bold text-pitch-900">
            Ana sayfaya dön
          </Link>
        </div>
      </Pitch>
    </div>
  );
}
