"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

export function AdminLoginForm() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    const form = new FormData(event.currentTarget);
    try {
      const response = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: form.get("username"),
          password: form.get("password"),
        }),
      });
      const data = (await response.json().catch(() => ({}))) as { error?: string };
      if (!response.ok) {
        setError(data.error ?? "ログインに失敗しました");
        return;
      }
      router.replace("/admin");
      router.refresh();
    } catch {
      setError("通信できませんでした。接続を確認してください");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-7 space-y-4">
      <label className="block">
        <span className="mb-1.5 block text-sm text-ink">ユーザー名</span>
        <input
          name="username"
          type="text"
          autoComplete="username"
          required
          className="h-12 w-full rounded-2xl border border-gold-soft bg-mist/60 px-4 text-base outline-none transition focus:border-pine focus:bg-paper focus:ring-2 focus:ring-pine/15"
        />
      </label>
      <label className="block">
        <span className="mb-1.5 block text-sm text-ink">パスワード</span>
        <input
          name="password"
          type="password"
          autoComplete="current-password"
          required
          className="h-12 w-full rounded-2xl border border-gold-soft bg-mist/60 px-4 text-base outline-none transition focus:border-pine focus:bg-paper focus:ring-2 focus:ring-pine/15"
        />
      </label>
      {error ? (
        <p role="alert" className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={submitting}
        className="h-12 w-full rounded-full bg-pine text-sm font-medium tracking-wide text-paper transition hover:bg-pine-deep disabled:opacity-60"
      >
        {submitting ? "ログイン中..." : "管理画面へログイン"}
      </button>
    </form>
  );
}
