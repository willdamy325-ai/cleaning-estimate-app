import type { QuoteRequest } from "@/domain/types";

/**
 * 見積依頼の永続化口。
 * 現段階はローカル保存のみ。将来は API / DB 実装に差し替える。
 */
export interface QuoteRepository {
  save(request: QuoteRequest): Promise<QuoteRequest>;
  findById(id: string): Promise<QuoteRequest | null>;
  list(): Promise<QuoteRequest[]>;
}
