import { AdminHeader } from "@/components/admin/AdminHeader";
import { QuoteList } from "@/components/admin/QuoteList";
import type { ManagedQuoteRequest } from "@/domain/types";
import { requireAdmin } from "@/infrastructure/auth/adminAccess";
import { DatabaseConfigurationError } from "@/infrastructure/database/neon";
import { NeonQuoteRepository } from "@/infrastructure/repositories/neonQuoteRepository";
import { formatYen } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const session = await requireAdmin();
  let quotes: ManagedQuoteRequest[] = [];
  let databaseError = false;

  try {
    quotes = await new NeonQuoteRepository().list();
  } catch (error) {
    databaseError = true;
    if (!(error instanceof DatabaseConfigurationError)) {
      console.error("Failed to load admin quote list", error);
    }
  }

  const newCount = quotes.filter((quote) => quote.status === "new").length;
  const activeTotal = quotes
    .filter((quote) => quote.status !== "cancelled")
    .reduce((sum, quote) => sum + quote.total, 0);

  return (
    <div className="min-h-dvh bg-mist text-ink">
      <AdminHeader username={session.username} />
      <main className="mx-auto max-w-content px-5 py-7 sm:py-10">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-[11px] tracking-[0.28em] text-gold">QUOTE MANAGEMENT</p>
            <h1 className="mt-2 font-serif text-3xl text-pine-deep">見積依頼一覧</h1>
          </div>
          <p className="text-sm text-clay">新しい依頼から順に表示</p>
        </div>

        {databaseError ? (
          <div className="mt-7 rounded-3xl border border-amber-300 bg-amber-50 px-5 py-5 text-sm leading-7 text-amber-900">
            データベースから見積依頼を取得できませんでした。VercelのEnvironment Variablesと
            Neonのテーブル作成状況を確認してください。
          </div>
        ) : (
          <>
            <section className="mt-7 grid grid-cols-2 gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-gold-soft bg-paper p-4 shadow-card">
                <p className="text-xs tracking-widest text-clay">全依頼</p>
                <p className="mt-2 font-serif text-3xl text-pine-deep">{quotes.length}</p>
              </div>
              <div className="rounded-2xl border border-gold-soft bg-paper p-4 shadow-card">
                <p className="text-xs tracking-widest text-clay">新規</p>
                <p className="mt-2 font-serif text-3xl text-amber-800">{newCount}</p>
              </div>
              <div className="col-span-2 rounded-2xl border border-gold-soft bg-paper p-4 shadow-card sm:col-span-1">
                <p className="text-xs tracking-widest text-clay">キャンセル除外 合計</p>
                <p className="mt-2 font-serif text-2xl text-pine-deep">{formatYen(activeTotal)}</p>
              </div>
            </section>
            <section className="mt-5">
              <QuoteList quotes={quotes} />
            </section>
          </>
        )}
      </main>
    </div>
  );
}
