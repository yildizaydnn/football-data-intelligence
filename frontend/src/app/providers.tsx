"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/api/client";

let browserQueryClient: QueryClient | undefined;

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Veri günde birkaç kez değişir; sekmeler arası geçişte tekrar istek atılmasın.
        staleTime: 60_000,
        refetchOnWindowFocus: false,
        // 4xx (ör. bulunamadı) tekrar denemeye değmez; ağ/5xx hatalarında 2 kez dene.
        retry: (failureCount, error) =>
          !(error instanceof ApiError && error.status >= 400 && error.status < 500) &&
          failureCount < 2,
      },
    },
  });
}

function getQueryClient() {
  // Sunucuda her render ayrı client; tarayıcıda cache sayfalar arası korunur.
  if (typeof window === "undefined") return makeQueryClient();
  browserQueryClient ??= makeQueryClient();
  return browserQueryClient;
}

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={getQueryClient()}>
      <TooltipProvider delayDuration={200}>
        {children}
        <Toaster position="bottom-right" theme="dark" richColors />
      </TooltipProvider>
    </QueryClientProvider>
  );
}
