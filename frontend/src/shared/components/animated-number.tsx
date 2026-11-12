"use client";

import { useEffect, useRef, useState } from "react";

/** Sayıyı 0'dan hedefe yumuşakça sayar. Hareket azaltma açıksa doğrudan gösterir. */
export function AnimatedNumber({
  value,
  decimals = 0,
  duration = 900,
  format,
}: {
  value: number;
  decimals?: number;
  duration?: number;
  format?: (n: number) => string;
}) {
  const [shown, setShown] = useState(value);
  const from = useRef(0);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setShown(value);
      return;
    }
    const start = performance.now();
    const initial = from.current;
    let frame = requestAnimationFrame(function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setShown(initial + (value - initial) * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
    });
    from.current = value;
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  const text = format ? format(shown) : formatNumber(shown, decimals);
  return <span className="tabular">{text}</span>;
}

function formatNumber(n: number, decimals: number) {
  return n.toLocaleString("tr-TR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}
