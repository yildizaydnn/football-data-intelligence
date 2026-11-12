"use client";

import { type RefObject, useLayoutEffect, useRef } from "react";

/**
 * FLIP animasyonu: liste yeniden sıralanınca `[data-flip-key]` elemanlarını eski
 * konumlarından yenisine kaydırır. Sadece transform kullanır; hareket azaltmaya duyarlı.
 */
export function useFlip(container: RefObject<HTMLElement | null>, deps: unknown[]) {
  const previous = useRef(new Map<string, number>());

  useLayoutEffect(() => {
    const root = container.current;
    if (!root) return;
    const items = root.querySelectorAll<HTMLElement>("[data-flip-key]");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const next = new Map<string, number>();

    items.forEach((el) => {
      const key = el.dataset.flipKey!;
      const top = el.getBoundingClientRect().top;
      next.set(key, top);
      const before = previous.current.get(key);
      if (reduce || before === undefined || before === top) return;
      el.animate([{ transform: `translateY(${before - top}px)` }, { transform: "none" }], {
        duration: 450,
        easing: "cubic-bezier(0.2, 0.7, 0.2, 1)",
      });
    });
    previous.current = next;
    // deps çağıran tarafından verilir (ör. sıralamayı belirleyen veri).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
