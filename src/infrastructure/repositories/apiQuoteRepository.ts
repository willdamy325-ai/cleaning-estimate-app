import { createEmptyQuantities } from "@/domain/quote";
import type { QuoteRequest } from "@/domain/types";
import type { QuoteRepository } from "@/infrastructure/repositories/quoteRepository";
import { LocalQuoteRepository } from "@/infrastructure/repositories/localQuoteRepository";

type CreateQuoteResponse = {
  quote?: QuoteRequest;
  error?: string;
};

export class ApiQuoteRepository implements QuoteRepository {
  private readonly local = new LocalQuoteRepository();

  async save(request: QuoteRequest): Promise<QuoteRequest> {
    const quantities = createEmptyQuantities();
    for (const item of request.items) {
      quantities[item.service.id] = item.quantity;
    }

    let response: Response;
    try {
      response = await fetch("/api/quotes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quantities,
          customer: request.customer,
        }),
      });
    } catch {
      throw new Error("通信できませんでした。接続を確認して再度お試しください。");
    }

    const data = (await response.json().catch(() => ({}))) as CreateQuoteResponse;
    if (!response.ok || !data.quote) {
      throw new Error(data.error ?? "見積依頼の送信に失敗しました");
    }

    await this.local.save(data.quote);
    return data.quote;
  }

  async findById(id: string): Promise<QuoteRequest | null> {
    return this.local.findById(id);
  }

  async list(): Promise<QuoteRequest[]> {
    return this.local.list();
  }
}
