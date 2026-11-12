"use client";

import { QueryErrorResetBoundary } from "@tanstack/react-query";
import { unstable_rethrow } from "next/navigation";
import { Component, Suspense, type ErrorInfo, type ReactNode } from "react";

import { ErrorState, InlineError } from "./states";

type Props = {
  /** Yüklenirken gösterilecek iskelet; her ekran kendi şeklini verir. */
  fallback: ReactNode;
  /** Dar alanlar (üst bar vb.) için tek satırlık hata görünümü. */
  inline?: boolean;
  children: ReactNode;
};

/**
 * Her veri bölümünü saran tek sınır: yükleniyor (Suspense) ve hata (ErrorBoundary)
 * durumları tüm ekranlarda aynı davranır. İçerideki bileşenler useSuspenseQuery kullanır.
 * Boş veri durumu için bileşenler <EmptyState> render eder.
 */
export function QueryBoundary({ fallback, inline, children }: Props) {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary onReset={reset} inline={inline}>
          <Suspense fallback={fallback}>{children}</Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  );
}

type BoundaryProps = { onReset: () => void; inline?: boolean; children: ReactNode };
type BoundaryState = { error: Error | null };

class ErrorBoundary extends Component<BoundaryProps, BoundaryState> {
  state: BoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): BoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("QueryBoundary yakaladı:", error, info.componentStack);
  }

  private retry = () => {
    this.props.onReset();
    this.setState({ error: null });
  };

  render() {
    const { error } = this.state;
    if (error) {
      // notFound()/redirect() gibi Next.js iç hataları yakalanmaz, Next'e geri verilir.
      unstable_rethrow(error);
      return this.props.inline ? (
        <InlineError error={error} onRetry={this.retry} />
      ) : (
        <ErrorState error={error} onRetry={this.retry} />
      );
    }
    return this.props.children;
  }
}
