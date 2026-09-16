import { redirect } from "next/navigation";
import { AdminLoginForm } from "@/components/admin/AdminLoginForm";
import { getAdminSession } from "@/infrastructure/auth/adminAccess";

export default async function AdminLoginPage() {
  const session = await getAdminSession();
  if (session) {
    redirect("/admin");
  }

  return (
    <main className="flex min-h-dvh items-center justify-center bg-mist px-5 py-10 text-ink">
      <section className="w-full max-w-md rounded-[28px] border border-gold-soft bg-paper p-6 shadow-card sm:p-8">
        <div className="text-center">
          <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-gold/50 bg-mist text-pine">
            <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" aria-hidden="true">
              <path
                d="M8 11V8a4 4 0 0 1 8 0v3M7 11h10a2 2 0 0 1 2 2v7H5v-7a2 2 0 0 1 2-2Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <p className="mt-4 text-[11px] tracking-[0.3em] text-gold">ADMINISTRATION</p>
          <h1 className="mt-2 font-serif text-2xl text-pine-deep">見積管理ログイン</h1>
          <p className="mt-2 text-sm text-clay">管理者専用ページです</p>
        </div>
        <AdminLoginForm />
      </section>
    </main>
  );
}
