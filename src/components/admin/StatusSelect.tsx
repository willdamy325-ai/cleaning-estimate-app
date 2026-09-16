"use client";

import { useState } from "react";
import { QUOTE_STATUS_LABELS } from "@/domain/quoteStatus";
import { QUOTE_STATUSES, type QuoteStatus } from "@/domain/types";

export function StatusSelect({
  quoteId,
  initialStatus,
}: {
  quoteId: string;
  initialStatus: QuoteStatus;
}) {
  const [status, setStatus] = useState(initialStatus);
  const [savedStatus, setSavedStatus] = useState(initialStatus);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function updateStatus(nextStatus: QuoteStatus) {
    const previous = status;
    setStatus(nextStatus);
    setSaving(true);
    setError("");

    try {
      const response = await fetch(`/api/admin/quotes/${encodeURIComponent(quoteId)}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });
      const data = (await response.json().catch(() => ({}))) as { error?: string };
      if (!response.ok) {
        setStatus(previous);
        setError(data.error ?? "更新に失敗しました");
        return;
      }
      setSavedStatus(nextStatus);
    } catch {
      setStatus(previous);
      setError("通信できませんでした");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <label htmlFor={`status-${quoteId}`} className="mb-1.5 block text-xs tracking-widest text-clay">
        対応ステータス
      </label>
      <div className="flex items-center gap-3">
        <select
          id={`status-${quoteId}`}
          value={status}
          disabled={saving}
          onChange={(event) => void updateStatus(event.target.value as QuoteStatus)}
          className="h-11 min-w-40 rounded-xl border border-gold-soft bg-paper px-3 text-sm text-ink outline-none focus:border-pine focus:ring-2 focus:ring-pine/15 disabled:opacity-60"
        >
          {QUOTE_STATUSES.map((value) => (
            <option key={value} value={value}>
              {QUOTE_STATUS_LABELS[value]}
            </option>
          ))}
        </select>
        <span aria-live="polite" className="text-xs text-clay">
          {saving ? "保存中..." : status === savedStatus ? "保存済み" : ""}
        </span>
      </div>
      {error ? <p className="mt-1.5 text-xs text-red-700">{error}</p> : null}
    </div>
  );
}
