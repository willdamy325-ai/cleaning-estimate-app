import Link from "next/link";
import type { ManagedQuoteRequest } from "@/domain/types";
import { StatusSelect } from "@/components/admin/StatusSelect";
import { formatDateJa, formatDateTimeJa, formatYen } from "@/lib/format";

export function AdminQuoteDetail({ quote }: { quote: ManagedQuoteRequest }) {
  return (
    <div className="space-y-5">
      <Link href="/admin" className="inline-flex text-sm text-pine underline-offset-4 hover:underline">
        ← 一覧へ戻る
      </Link>

      <section className="rounded-3xl border border-gold-soft bg-paper p-5 shadow-card sm:p-7">
        <div className="flex flex-col gap-4 border-b border-gold-pale pb-5 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="font-serif text-2xl text-pine-deep">{quote.customer.name} 様</h1>
            <p className="mt-2 text-sm text-clay">
              {quote.id} ・ {formatDateTimeJa(quote.createdAt)}
            </p>
          </div>
          <StatusSelect quoteId={quote.id} initialStatus={quote.status} />
        </div>

        <h2 className="mt-6 font-serif text-lg text-pine-deep">ご依頼内容</h2>
        <div className="mt-3 overflow-x-auto rounded-2xl border border-gold-pale">
          <table className="w-full min-w-[480px] text-sm">
            <thead className="bg-mist text-left text-clay">
              <tr>
                <th className="px-4 py-3 font-medium">サービス</th>
                <th className="px-4 py-3 text-right font-medium">単価</th>
                <th className="px-4 py-3 text-right font-medium">数量</th>
                <th className="px-4 py-3 text-right font-medium">小計</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gold-pale">
              {quote.items.map((item) => (
                <tr key={item.service.id}>
                  <td className="px-4 py-3 text-ink">{item.service.name}</td>
                  <td className="px-4 py-3 text-right text-clay">{formatYen(item.service.price)}</td>
                  <td className="px-4 py-3 text-right text-clay">
                    {item.quantity}{item.service.unitLabel}
                  </td>
                  <td className="px-4 py-3 text-right font-serif text-pine">
                    {formatYen(item.subtotal)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center justify-between bg-pine px-4 py-4 text-paper">
            <span className="text-sm tracking-widest">合計金額</span>
            <strong className="font-serif text-2xl">{formatYen(quote.total)}</strong>
          </div>
        </div>

        <h2 className="mt-7 font-serif text-lg text-pine-deep">お客様情報</h2>
        <dl className="mt-3 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div className="rounded-2xl bg-mist px-4 py-3">
            <dt className="text-xs tracking-widest text-clay">お名前</dt>
            <dd className="mt-1 text-ink">{quote.customer.name}</dd>
          </div>
          <div className="rounded-2xl bg-mist px-4 py-3">
            <dt className="text-xs tracking-widest text-clay">希望作業日</dt>
            <dd className="mt-1 text-ink">{formatDateJa(quote.customer.preferredDate)}</dd>
          </div>
          <div className="rounded-2xl bg-mist px-4 py-3">
            <dt className="text-xs tracking-widest text-clay">電話番号</dt>
            <dd className="mt-1">
              <a href={`tel:${quote.customer.phone}`} className="text-pine hover:underline">
                {quote.customer.phone}
              </a>
            </dd>
          </div>
          <div className="rounded-2xl bg-mist px-4 py-3">
            <dt className="text-xs tracking-widest text-clay">メールアドレス</dt>
            <dd className="mt-1 break-all">
              <a href={`mailto:${quote.customer.email}`} className="text-pine hover:underline">
                {quote.customer.email}
              </a>
            </dd>
          </div>
          <div className="rounded-2xl bg-mist px-4 py-3 sm:col-span-2">
            <dt className="text-xs tracking-widest text-clay">住所</dt>
            <dd className="mt-1 text-ink">{quote.customer.address}</dd>
          </div>
          <div className="rounded-2xl bg-mist px-4 py-3 sm:col-span-2">
            <dt className="text-xs tracking-widest text-clay">備考</dt>
            <dd className="mt-1 whitespace-pre-wrap text-ink">{quote.customer.notes || "なし"}</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
