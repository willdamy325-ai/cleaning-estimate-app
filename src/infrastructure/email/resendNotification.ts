import type { ManagedQuoteRequest } from "@/domain/types";
import { formatDateJa, formatDateTimeJa, formatYen } from "@/lib/format";

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getAppUrl(): string {
  if (process.env.APP_URL) {
    return process.env.APP_URL.replace(/\/$/, "");
  }
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`;
  }
  return "";
}

export type NotificationResult =
  | { sent: true }
  | { sent: false; reason: "not_configured" | "request_failed" };

export async function sendAdminQuoteNotification(
  quote: ManagedQuoteRequest,
): Promise<NotificationResult> {
  const apiKey = process.env.RESEND_API_KEY;
  const from = process.env.EMAIL_FROM;
  const recipients = process.env.ADMIN_NOTIFICATION_EMAIL?.split(",")
    .map((email) => email.trim())
    .filter(Boolean);

  if (!apiKey || !from || !recipients?.length) {
    return { sent: false, reason: "not_configured" };
  }

  const appUrl = getAppUrl();
  const detailUrl = appUrl ? `${appUrl}/admin/${encodeURIComponent(quote.id)}` : "";
  const serviceRows = quote.items
    .map(
      (item) => `
        <tr>
          <td style="padding:8px;border-bottom:1px solid #eee">${escapeHtml(item.service.name)}</td>
          <td style="padding:8px;border-bottom:1px solid #eee">${item.quantity}${escapeHtml(item.service.unitLabel)}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;text-align:right">${formatYen(item.subtotal)}</td>
        </tr>`,
    )
    .join("");

  const html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1c1b19;line-height:1.7">
      <h1 style="font-size:20px;color:#163834">新しい見積依頼が届きました</h1>
      <p><strong>受付番号:</strong> ${escapeHtml(quote.id)}<br>
      <strong>受付日時:</strong> ${escapeHtml(formatDateTimeJa(quote.createdAt))}</p>
      <table style="width:100%;border-collapse:collapse">
        <thead><tr style="background:#f4f1ea">
          <th style="padding:8px;text-align:left">サービス</th>
          <th style="padding:8px;text-align:left">数量</th>
          <th style="padding:8px;text-align:right">小計</th>
        </tr></thead>
        <tbody>${serviceRows}</tbody>
      </table>
      <p style="font-size:18px;color:#163834"><strong>合計: ${formatYen(quote.total)}</strong></p>
      <hr style="border:0;border-top:1px solid #e8d9c4">
      <p>
        <strong>お名前:</strong> ${escapeHtml(quote.customer.name)}<br>
        <strong>電話番号:</strong> ${escapeHtml(quote.customer.phone)}<br>
        <strong>メール:</strong> ${escapeHtml(quote.customer.email)}<br>
        <strong>住所:</strong> ${escapeHtml(quote.customer.address)}<br>
        <strong>希望作業日:</strong> ${escapeHtml(formatDateJa(quote.customer.preferredDate))}<br>
        <strong>備考:</strong> ${escapeHtml(quote.customer.notes || "なし")}
      </p>
      ${detailUrl ? `<p><a href="${escapeHtml(detailUrl)}" style="display:inline-block;background:#1f4a45;color:#fff;padding:10px 18px;border-radius:999px;text-decoration:none">管理画面で確認する</a></p>` : ""}
    </div>
  `;

  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      "Idempotency-Key": `quote-${quote.id}`,
    },
    body: JSON.stringify({
      from,
      to: recipients,
      subject: `【新規見積】${quote.customer.name}様・${formatYen(quote.total)}（${quote.id}）`,
      html,
    }),
    signal: AbortSignal.timeout(8_000),
  });

  if (!response.ok) {
    console.error("Resend notification failed", {
      status: response.status,
      quoteId: quote.id,
    });
    return { sent: false, reason: "request_failed" };
  }

  return { sent: true };
}
