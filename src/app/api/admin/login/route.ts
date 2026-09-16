import { setTimeout as delay } from "node:timers/promises";
import { NextResponse } from "next/server";
import {
  ADMIN_SESSION_COOKIE,
  AdminAuthConfigurationError,
  adminSessionCookieOptions,
  createAdminSessionToken,
  verifyAdminCredentials,
} from "@/infrastructure/auth/adminAuth";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as { username?: unknown; password?: unknown };
    if (typeof body.username !== "string" || typeof body.password !== "string") {
      return NextResponse.json({ error: "ユーザー名とパスワードを入力してください" }, { status: 400 });
    }

    if (!verifyAdminCredentials(body.username, body.password)) {
      await delay(600);
      return NextResponse.json({ error: "ユーザー名またはパスワードが違います" }, { status: 401 });
    }

    const token = await createAdminSessionToken(body.username);
    const response = NextResponse.json({ success: true });
    response.cookies.set(ADMIN_SESSION_COOKIE, token, adminSessionCookieOptions);
    return response;
  } catch (error) {
    if (error instanceof SyntaxError) {
      return NextResponse.json(
        { error: "ユーザー名とパスワードを入力してください" },
        { status: 400 },
      );
    }
    if (error instanceof AdminAuthConfigurationError) {
      console.error("Admin authentication is not configured");
      return NextResponse.json(
        { error: "管理者認証が設定されていません" },
        { status: 503 },
      );
    }
    console.error("Admin login failed", error);
    return NextResponse.json({ error: "ログインに失敗しました" }, { status: 500 });
  }
}
