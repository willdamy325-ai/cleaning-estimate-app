import type { Quote } from "@/domain/types";
import { formatYen } from "@/lib/format";

type QuoteSummaryProps = {
  quote: Quote;
};

export function QuoteSummary({ quote }: QuoteSummaryProps) {
  const empty = quote.lines.length === 0;

  return (
    <section className="rounded-3xl border border-gold-soft bg-paper p-5 shadow-card">
      <h2 className="font-serif text-xl text-pine-deep">お見積内容</h2>
      <p className="mt-1 text-sm text-clay">選択中のサービスと金額</p>

      {empty ? (
        <p className="mt-6 rounded-2xl bg-mist px-4 py-6 text-center text-sm text-clay">
          サービスを選択すると、ここに数量・小計・合計が表示されます。
        </p>
      ) : (
        <ul className="mt-5 divide-y divide-gold-pale">
          {quote.lines.map((line) => (
            <li key={line.service.id} className="flex items-start justify-between gap-3 py-3">
              <div>
                <p className="text-sm font-medium text-ink">{line.service.name}</p>
                <p className="mt-0.5 text-xs text-clay">
                  {formatYen(line.service.price)} × {line.quantity}
                  {line.service.unitLabel}
                </p>
              </div>
              <p className="shrink-0 font-serif text-pine">{formatYen(line.subtotal)}</p>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-5 flex items-end justify-between border-t border-gold-soft pt-4">
        <span className="text-sm tracking-widest text-clay">合計金額</span>
        <strong className="font-serif text-3xl text-pine-deep" aria-live="polite">
          {formatYen(quote.total)}
        </strong>
      </div>
    </section>
  );
}
