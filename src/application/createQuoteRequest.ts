import { sanitizeCustomer, validateCustomer, hasCustomerErrors } from "@/domain/customer";
import { calculateQuote, createEmptyQuantities } from "@/domain/quote";
import type { CustomerInfo, QuantityMap, QuoteRequest, ServiceId } from "@/domain/types";
import { SERVICE_CATALOG } from "@/domain/catalog";
import { createQuoteId } from "@/infrastructure/id";

export class InvalidQuoteRequestError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InvalidQuoteRequestError";
  }
}

function parseCustomer(value: unknown): CustomerInfo {
  if (!value || typeof value !== "object") {
    throw new InvalidQuoteRequestError("お客様情報の入力内容を確認してください");
  }

  const input = value as Record<string, unknown>;
  const fields = ["name", "phone", "email", "address", "preferredDate", "notes"] as const;
  if (fields.some((field) => typeof input[field] !== "string")) {
    throw new InvalidQuoteRequestError("お客様情報の入力内容を確認してください");
  }

  return sanitizeCustomer({
    name: input.name as string,
    phone: input.phone as string,
    email: input.email as string,
    address: input.address as string,
    preferredDate: input.preferredDate as string,
    notes: input.notes as string,
  });
}

function parseQuantities(value: unknown): QuantityMap {
  if (!value || typeof value !== "object") {
    throw new InvalidQuoteRequestError("サービスを1つ以上選択してください");
  }

  const input = value as Record<string, unknown>;
  const quantities = createEmptyQuantities();

  for (const service of SERVICE_CATALOG) {
    const quantity = input[service.id];
    if (
      typeof quantity !== "number" ||
      !Number.isInteger(quantity) ||
      quantity < 0 ||
      quantity > 10
    ) {
      throw new InvalidQuoteRequestError("サービス数量は0〜10の範囲で指定してください");
    }
    quantities[service.id as ServiceId] = quantity;
  }

  return quantities;
}

export function createQuoteRequestFromInput(
  input: unknown,
  options: { now?: Date; id?: string } = {},
): QuoteRequest {
  if (!input || typeof input !== "object") {
    throw new InvalidQuoteRequestError("送信内容を確認してください");
  }

  const body = input as Record<string, unknown>;
  const customer = parseCustomer(body.customer);
  const quantities = parseQuantities(body.quantities);
  const errors = validateCustomer(customer, options.now);
  if (hasCustomerErrors(errors)) {
    throw new InvalidQuoteRequestError("お客様情報の入力内容を確認してください");
  }

  const quote = calculateQuote(quantities);
  if (quote.lines.length === 0) {
    throw new InvalidQuoteRequestError("サービスを1つ以上選択してください");
  }

  const createdAt = (options.now ?? new Date()).toISOString();
  return {
    id: options.id ?? createQuoteId(options.now),
    createdAt,
    items: quote.lines,
    total: quote.total,
    customer,
  };
}
