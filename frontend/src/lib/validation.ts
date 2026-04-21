export function isLikelyEmail(value: string): boolean {
  const v = value.trim();
  if (!v || v.includes(" ")) return false;

  const at = v.indexOf("@");
  if (at <= 0 || at !== v.lastIndexOf("@") || at === v.length - 1) {
    return false;
  }

  const domain = v.slice(at + 1);
  const dot = domain.indexOf(".");
  return dot > 0 && dot < domain.length - 1;
}
