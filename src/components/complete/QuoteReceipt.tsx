import type { QuoteRequest } from "@/domain/types";
import { formatDateJa, formatDateTimeJa, formatYen } from "@/lib/format";

type QuoteReceiptProps = {
  quote: QuoteRequest;
};

export function QuoteReceipt({ quote }: QuoteReceiptProps) {
  return (
    <section className="rounded-[28px] border border-gold-soft bg-paper p-5 shadow-card sm:p-8">
      <div className="flex flex-col gap-1 border-b border-gold-pale pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] tracking-[0.28em] text-gold">ESTIMATE REQUEST</p>
          <h2 className="mt-2 font-serif text-2xl text-pine-deep">見積依頼を受け付けました</h2>
        </div>
        <p className="font-serif text-lg tracking-wide text-pine">{quote.id}</p>
      </div>

      <p className="mt-4 text-sm text-clay">受付日時：{formatDateTimeJa(quote.createdAt)}</p>

      <div className="mt-6 overflow-hidden rounded-2xl border border-gold-pale">
        <table className="w-full text-sm">
          <thead className="bg-mist text-left text-clay">
            <tr>
              <th className="px-4 py-3 font-medium">サービス</th>
              <th className="px-4 py-3 font-medium">数量</th>
              <th className="px-4 py-3 text-right font-medium">小計</th>
            </tr>
          </thead>
          <tbody>
            {quote.items.map((item) => (
              <tr key={item.service.id} className="border-t border-gold-pale">
                <td className="px-4 py-3">
                  <p className="text-ink">{item.service.name}</p>
                  <p className="text-xs text-clay">{formatYen(item.service.price)} / {item.service.unitLabel}</p>
                </td>
                <td className="px-4 py-3">{item.quantity}</td>
                <td className="px-4 py-3 text-right font-serif text-pine">{formatYen(item.subtotal)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="flex items-center justify-between bg-pine px-4 py-4 text-paper">
          <span className="text-sm tracking-widest">合計金額</span>
          <strong className="font-serif text-2xl">{formatYen(quote.total)}</strong>
        </div>
      </div>

      <dl className="mt-6 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
        <div className="rounded-2xl bg-mist px-4 py-3">
          <dt className="text-xs tracking-widest text-clay">お名前</dt>
          <dd className="mt-1 text-ink">{quote.customer.name}</dd>
        </div>
        <div className="rounded-2xl bg-mist px-4 py-3">
          <dt className="text-xs tracking-widest text-clay">電話番号</dt>
          <dd className="mt-1 text-ink">{quote.customer.phone}</dd>
        </div>
        <div className="rounded-2xl bg-mist px-4 py-3">
          <dt className="text-xs tracking-widest text-clay">メールアドレス</dt>
          <dd className="mt-1 break-all text-ink">{quote.customer.email}</dd>
        </div>
        <div className="rounded-2xl bg-mist px-4 py-3">
          <dt className="text-xs tracking-widest text-clay">希望作業日</dt>
          <dd className="mt-1 text-ink">{formatDateJa(quote.customer.preferredDate)}</dd>
        </div>
        <div className="rounded-2xl bg-mist px-4 py-3 sm:col-span-2">
          <dt className="text-xs tracking-widest text-clay">住所</dt>
          <dd className="mt-1 text-ink">{quote.customer.address}</dd>
        </div>
        {quote.customer.notes ? (
          <div className="rounded-2xl bg-mist px-4 py-3 sm:col-span-2">
            <dt className="text-xs tracking-widest text-clay">備考</dt>
            <dd className="mt-1 whitespace-pre-wrap text-ink">{quote.customer.notes}</dd>
          </div>
        ) : null}
      </dl>
    </section>
  );
}
