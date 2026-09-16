import { notFound } from "next/navigation";
import { AdminHeader } from "@/components/admin/AdminHeader";
import { AdminQuoteDetail } from "@/components/admin/AdminQuoteDetail";
import { requireAdmin } from "@/infrastructure/auth/adminAccess";
import { NeonQuoteRepository } from "@/infrastructure/repositories/neonQuoteRepository";

export const dynamic = "force-dynamic";

export default async function AdminQuoteDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await requireAdmin();
  const { id } = await params;

  let quote;
  try {
    quote = await new NeonQuoteRepository().findById(id);
  } catch (error) {
    console.error("Failed to load admin quote detail", error);
    return (
      <div className="min-h-dvh bg-mist text-ink">
        <AdminHeader username={session.username} />
        <main className="mx-auto max-w-content px-5 py-10">
          <div className="rounded-3xl border border-amber-300 bg-amber-50 px-5 py-5 text-sm leading-7 text-amber-900">
            見積依頼を取得できませんでした。データベース設定を確認してください。
          </div>
        </main>
      </div>
    );
  }

  if (!quote) {
    notFound();
  }

  return (
    <div className="min-h-dvh bg-mist text-ink">
      <AdminHeader username={session.username} />
      <main className="mx-auto max-w-4xl px-5 py-7 sm:py-10">
        <AdminQuoteDetail quote={quote} />
      </main>
    </div>
  );
}
