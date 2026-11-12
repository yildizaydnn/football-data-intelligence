import type { SVGProps } from "react";

/** Klasik siyah-beyaz top. */
export function FootballIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 64 64" aria-hidden {...props}>
      <circle cx="32" cy="32" r="30" fill="#fff" stroke="#0a1a10" strokeWidth="2" />
      <path d="M32 18l10 7-4 12H26l-4-12z" fill="#0a1a10" />
      <path
        d="M32 2v16M42 25l15-6M38 37l9 14M26 37l-9 14M22 25L7 19"
        stroke="#0a1a10"
        strokeWidth="2"
        fill="none"
      />
      <path d="M57 19l5 15-9 9M7 19L2 34l9 9M17 51l15 11 15-11" fill="#0a1a10" opacity=".9" />
    </svg>
  );
}
