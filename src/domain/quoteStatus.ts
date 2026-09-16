import { QUOTE_STATUSES, type QuoteStatus } from "@/domain/types";

export const QUOTE_STATUS_LABELS: Record<QuoteStatus, string> = {
  new: "新規",
  contacted: "連絡済み",
  confirmed: "予約確定",
  completed: "完了",
  cancelled: "キャンセル",
};

export function isQuoteStatus(value: unknown): value is QuoteStatus {
  return typeof value === "string" && QUOTE_STATUSES.includes(value as QuoteStatus);
}
