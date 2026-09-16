import type { QuoteRequest } from "@/domain/types";
import type { QuoteRepository } from "@/infrastructure/repositories/quoteRepository";

const STORAGE_KEY = "sumiya.quotes";
const LAST_ID_KEY = "sumiya.lastQuoteId";

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function readAll(): QuoteRequest[] {
  if (!canUseStorage()) {
    return [];
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as QuoteRequest[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeAll(quotes: QuoteRequest[]): void {
  if (!canUseStorage()) {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(quotes));
}

export class LocalQuoteRepository implements QuoteRepository {
  async save(request: QuoteRequest): Promise<QuoteRequest> {
    const quotes = readAll().filter((item) => item.id !== request.id);
    quotes.unshift(request);
    writeAll(quotes);
    if (canUseStorage()) {
      window.sessionStorage.setItem(LAST_ID_KEY, request.id);
    }
    return request;
  }

  async findById(id: string): Promise<QuoteRequest | null> {
    return readAll().find((item) => item.id === id) ?? null;
  }

  async list(): Promise<QuoteRequest[]> {
    return readAll();
  }
}

export function getLastQuoteId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.sessionStorage.getItem(LAST_ID_KEY);
}

export const LAST_QUOTE_ID_KEY = LAST_ID_KEY;
