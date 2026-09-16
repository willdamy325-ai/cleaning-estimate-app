import { NextResponse } from "next/server";
import { isQuoteStatus } from "@/domain/quoteStatus";
import { getAdminSession } from "@/infrastructure/auth/adminAccess";
import { DatabaseConfigurationError } from "@/infrastructure/database/neon";
import { NeonQuoteRepository } from "@/infrastructure/repositories/neonQuoteRepository";

export const runtime = "nodejs";

export async function PATCH(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const session = await getAdminSession();
  if (!session) {
    return NextResponse.json({ error: "認証が必要です" }, { status: 401 });
  }

  try {
    const { id } = await context.params;
    const body = (await request.json()) as { status?: unknown };
    if (!isQuoteStatus(body.status)) {
      return NextResponse.json({ error: "ステータスが不正です" }, { status: 400 });
    }

    const repository = new NeonQuoteRepository();
    const quote = await repository.updateStatus(id, body.status);
    if (!quote) {
      return NextResponse.json({ error: "見積依頼が見つかりません" }, { status: 404 });
    }
    return NextResponse.json({ quote });
  } catch (error) {
    if (error instanceof DatabaseConfigurationError) {
      return NextResponse.json({ error: "データベースが設定されていません" }, { status: 503 });
    }
    console.error("Failed to update quote status", error);
    return NextResponse.json({ error: "ステータスの更新に失敗しました" }, { status: 500 });
  }
}
