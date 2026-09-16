import type {
  ManagedQuoteRequest,
  QuoteLineItem,
  QuoteRequest,
  QuoteStatus,
} from "@/domain/types";
import { isQuoteStatus } from "@/domain/quoteStatus";
import { getDatabase } from "@/infrastructure/database/neon";

type QuoteRow = {
  id: string;
  created_at: string | Date;
  updated_at: string | Date;
  status: string;
  items: QuoteLineItem[] | string;
  total: number | string;
  customer_name: string;
  phone: string;
  email: string;
  address: string;
  preferred_date: string | Date;
  notes: string | null;
};

function toIsoString(value: string | Date): string {
  return value instanceof Date ? value.toISOString() : new Date(value).toISOString();
}

function toDateString(value: string | Date): string {
  if (value instanceof Date) {
    return value.toISOString().slice(0, 10);
  }
  return value.slice(0, 10);
}

function mapRow(row: QuoteRow): ManagedQuoteRequest {
  const items =
    typeof row.items === "string" ? (JSON.parse(row.items) as QuoteLineItem[]) : row.items;

  return {
    id: row.id,
    createdAt: toIsoString(row.created_at),
    updatedAt: toIsoString(row.updated_at),
    status: isQuoteStatus(row.status) ? row.status : "new",
    items,
    total: Number(row.total),
    customer: {
      name: row.customer_name,
      phone: row.phone,
      email: row.email,
      address: row.address,
      preferredDate: toDateString(row.preferred_date),
      notes: row.notes ?? "",
    },
  };
}

export class NeonQuoteRepository {
  async save(request: QuoteRequest): Promise<ManagedQuoteRequest> {
    const sql = getDatabase();
    const rows = (await sql`
      INSERT INTO quote_requests (
        id,
        created_at,
        updated_at,
        status,
        items,
        total,
        customer_name,
        phone,
        email,
        address,
        preferred_date,
        notes
      ) VALUES (
        ${request.id},
        ${request.createdAt},
        ${request.createdAt},
        'new',
        ${JSON.stringify(request.items)}::jsonb,
        ${request.total},
        ${request.customer.name},
        ${request.customer.phone},
        ${request.customer.email},
        ${request.customer.address},
        ${request.customer.preferredDate},
        ${request.customer.notes || null}
      )
      RETURNING *
    `) as QuoteRow[];

    return mapRow(rows[0]);
  }

  async list(): Promise<ManagedQuoteRequest[]> {
    const sql = getDatabase();
    const rows = (await sql`
      SELECT *
      FROM quote_requests
      ORDER BY created_at DESC
      LIMIT 500
    `) as QuoteRow[];
    return rows.map(mapRow);
  }

  async findById(id: string): Promise<ManagedQuoteRequest | null> {
    const sql = getDatabase();
    const rows = (await sql`
      SELECT *
      FROM quote_requests
      WHERE id = ${id}
      LIMIT 1
    `) as QuoteRow[];
    return rows[0] ? mapRow(rows[0]) : null;
  }

  async updateStatus(id: string, status: QuoteStatus): Promise<ManagedQuoteRequest | null> {
    const sql = getDatabase();
    const rows = (await sql`
      UPDATE quote_requests
      SET status = ${status}, updated_at = NOW()
      WHERE id = ${id}
      RETURNING *
    `) as QuoteRow[];
    return rows[0] ? mapRow(rows[0]) : null;
  }
}
