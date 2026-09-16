export function createQuoteId(now = new Date()): string {
  const stamp = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0"),
  ].join("");
  const random = globalThis.crypto.randomUUID().replaceAll("-", "").slice(0, 8).toUpperCase();
  return `SQ-${stamp}-${random}`;
}
