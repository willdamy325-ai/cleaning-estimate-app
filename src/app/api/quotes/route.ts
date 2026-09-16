import { NextResponse } from "next/server";
import {
  createQuoteRequestFromInput,
  InvalidQuoteRequestError,
} from "@/application/createQuoteRequest";
import { DatabaseConfigurationError } from "@/infrastructure/database/neon";
import { sendAdminQuoteNotification } from "@/infrastructure/email/resendNotification";
import { NeonQuoteRepository } from "@/infrastructure/repositories/neonQuoteRepository";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const contentLength = Number(request.headers.get("content-length") ?? 0);
  if (contentLength > 32_000) {
    return NextResponse.json({ error: "送信内容が大きすぎます" }, { status: 413 });
  }

  try {
    const body: unknown = await request.json();
    const quoteRequest = createQuoteRequestFromInput(body);
    const repository = new NeonQuoteRepository();
    const saved = await repository.save(quoteRequest);

    let notificationSent = false;
    try {
      const result = await sendAdminQuoteNotification(saved);
      notificationSent = result.sent;
    } catch (error) {
      console.error("Quote was saved but notification could not be sent", {
        quoteId: saved.id,
        error,
      });
    }

    return NextResponse.json({ quote: saved, notificationSent }, { status: 201 });
  } catch (error) {
    if (error instanceof InvalidQuoteRequestError) {
      return NextResponse.json({ error: error.message }, { status: 400 });
    }
    if (error instanceof SyntaxError) {
      return NextResponse.json({ error: "送信内容を確認してください" }, { status: 400 });
    }
    if (error instanceof DatabaseConfigurationError) {
      console.error("Quote database is not configured");
      return NextResponse.json(
        { error: "現在、見積依頼を受け付けられません。しばらくしてからお試しください。" },
        { status: 503 },
      );
    }

    console.error("Failed to create quote request", error);
    return NextResponse.json(
      { error: "見積依頼の送信に失敗しました。時間をおいて再度お試しください。" },
      { status: 500 },
    );
  }
}
