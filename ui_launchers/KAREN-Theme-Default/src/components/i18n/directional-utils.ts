const RTL_LOCALES = new Set([
  "ar",
  "arc",
  "dv",
  "fa",
  "ha",
  "he",
  "khw",
  "ks",
  "ku",
  "ps",
  "ur",
  "yi",
]);

export function isRTLLocale(locale: string): boolean {
  const baseLocale = locale.split("-")[0].toLowerCase();
  return RTL_LOCALES.has(baseLocale);
}
