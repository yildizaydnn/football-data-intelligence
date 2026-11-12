/**
 * Büyük harfe çevirme (CSS `uppercase`) sayfa diline göre yapılır: lang="tr" altında
 * "Bundesliga" → "BUNDESLİGA" olur. Yabancı lig/takım adlarına kendi dilini veririz.
 */
export const nameLang = (country: string | null | undefined) =>
  country === "Turkey" ? "tr" : "en";
