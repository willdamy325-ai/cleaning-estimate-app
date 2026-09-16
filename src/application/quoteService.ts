import { sanitizeCustomer, validateCustomer, hasCustomerErrors } from "@/domain/customer";
import { calculateQuote } from "@/domain/quote";
import type { CustomerInfo, QuantityMap, QuoteRequest } from "@/domain/types";
import { createQuoteId } from "@/infrastructure/id";
import type { QuoteRepository } from "@/infrastructure/repositories/quoteRepository";
import { LocalQuoteRepository } from "@/infrastructure/repositories/localQuoteRepository";

/**
 * アプリケーションサービス。
 * UI はここを通して見積作成を行う。
 * 将来の予約管理・顧客管理・外部API連携は、この層にユースケースを追加する。
 */
export class QuoteService {
  constructor(private readonly quotes: QuoteRepository) {}

  preview(quantities: QuantityMap) {
    return calculateQuote(quantities);
  }

  async submit(quantities: QuantityMap, customer: CustomerInfo): Promise<QuoteRequest> {
    const quote = calculateQuote(quantities);
    if (quote.lines.length === 0) {
      throw new Error("サービスを1つ以上選択してください");
    }

    const cleaned = sanitizeCustomer(customer);
    const errors = validateCustomer(cleaned);
    if (hasCustomerErrors(errors)) {
      throw new Error("お客様情報の入力内容を確認してください");
    }

    return this.quotes.save({
      id: createQuoteId(),
      createdAt: new Date().toISOString(),
      items: quote.lines,
      total: quote.total,
      customer: cleaned,
    });
  }
}

let singleton: QuoteService | null = null;

export function getQuoteService(): QuoteService {
  if (!singleton) {
    singleton = new QuoteService(new LocalQuoteRepository());
  }
  return singleton;
}
