import Link from "next/link";

export function AdminHeader({ username }: { username: string }) {
  return (
    <header className="border-b border-gold-soft/70 bg-paper">
      <div className="mx-auto flex max-w-content items-center justify-between gap-4 px-5 py-4">
        <div className="min-w-0">
          <Link href="/admin" className="font-serif text-lg tracking-[0.16em] text-pine-deep">
            澄屋 管理
          </Link>
          <p className="mt-0.5 truncate text-[11px] text-clay">{username} としてログイン中</p>
        </div>
        <form action="/api/admin/logout" method="post">
          <button
            type="submit"
            className="h-10 shrink-0 rounded-full border border-pine/25 px-4 text-xs text-pine transition hover:bg-gold-pale"
          >
            ログアウト
          </button>
        </form>
      </div>
    </header>
  );
}
