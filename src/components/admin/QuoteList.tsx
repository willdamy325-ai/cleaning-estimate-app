import Link from "next/link";
import type { ManagedQuoteRequest } from "@/domain/types";
import { StatusBadge } from "@/components/admin/StatusBadge";
import { formatDateTimeJa, formatYen } from "@/lib/format";

function serviceSummary(quote: ManagedQuoteRequest): string {
  return quote.items
    .map((item) => `${item.service.name} × ${item.quantity}`)
    .join("、");
}

export function QuoteList({ quotes }: { quotes: ManagedQuoteRequest[] }) {
  if (quotes.length === 0) {
    return (
      <div className="rounded-3xl border border-gold-soft bg-paper px-5 py-14 text-center shadow-card">
        <p className="font-serif text-xl text-pine-deep">見積依頼はまだありません</p>
        <p className="mt-2 text-sm text-clay">新しい依頼が届くと、ここに表示されます。</p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-3 md:hidden">
        {quotes.map((quote) => (
          <Link
            key={quote.id}
            href={`/admin/${encodeURIComponent(quote.id)}`}
            className="block rounded-3xl border border-gold-soft bg-paper p-5 shadow-card transition active:scale-[0.99]"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-serif text-base text-pine-deep">{quote.customer.name} 様</p>
                <p className="mt-1 text-xs text-clay">{formatDateTimeJa(quote.createdAt)}</p>
              </div>
              <StatusBadge status={quote.status} />
            </div>
            <p className="mt-4 line-clamp-2 text-sm leading-6 text-clay">{serviceSummary(quote)}</p>
            <div className="mt-4 flex items-end justify-between border-t border-gold-pale pt-3">
              <p className="text-xs text-clay">{quote.id}</p>
              <p className="font-serif text-xl text-pine">{formatYen(quote.total)}</p>
            </div>
          </Link>
        ))}
      </div>

      <div className="hidden overflow-hidden rounded-3xl border border-gold-soft bg-paper shadow-card md:block">
        <table className="w-full text-sm">
          <thead className="bg-mist text-left text-xs tracking-wider text-clay">
            <tr>
              <th className="px-5 py-4 font-medium">受付日時・番号</th>
              <th className="px-5 py-4 font-medium">お客様</th>
              <th className="px-5 py-4 font-medium">サービス</th>
              <th className="px-5 py-4 text-right font-medium">合計</th>
              <th className="px-5 py-4 font-medium">ステータス</th>
              <th className="px-5 py-4" aria-label="詳細" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gold-pale">
            {quotes.map((quote) => (
              <tr key={quote.id} className="transition hover:bg-mist/60">
                <td className="px-5 py-4">
                  <p className="text-ink">{formatDateTimeJa(quote.createdAt)}</p>
                  <p className="mt-1 text-xs text-clay">{quote.id}</p>
                </td>
                <td className="px-5 py-4">
                  <p className="font-medium text-ink">{quote.customer.name} 様</p>
                  <a href={`tel:${quote.customer.phone}`} className="mt-1 block text-xs text-pine hover:underline">
                    {quote.customer.phone}
                  </a>
                </td>
                <td className="max-w-64 px-5 py-4 text-clay">
                  <p className="line-clamp-2 leading-6">{serviceSummary(quote)}</p>
                </td>
                <td className="whitespace-nowrap px-5 py-4 text-right font-serif text-lg text-pine">
                  {formatYen(quote.total)}
                </td>
                <td className="px-5 py-4">
                  <StatusBadge status={quote.status} />
                </td>
                <td className="px-5 py-4 text-right">
                  <Link
                    href={`/admin/${encodeURIComponent(quote.id)}`}
                    className="text-sm font-medium text-pine underline-offset-4 hover:underline"
                  >
                    詳細
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
