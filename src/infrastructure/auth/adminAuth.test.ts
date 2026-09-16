import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  createAdminSessionToken,
  verifyAdminCredentials,
  verifyAdminSessionToken,
} from "@/infrastructure/auth/adminAuth";

const originalEnv = { ...process.env };

describe("adminAuth", () => {
  beforeEach(() => {
    process.env.ADMIN_USERNAME = "owner";
    process.env.ADMIN_PASSWORD = "a-strong-test-password";
    process.env.ADMIN_SESSION_SECRET = "test-session-secret-with-more-than-32-characters";
  });

  afterEach(() => {
    process.env = { ...originalEnv };
  });

  it("設定された認証情報だけを受け入れる", () => {
    expect(verifyAdminCredentials("owner", "a-strong-test-password")).toBe(true);
    expect(verifyAdminCredentials("owner", "wrong")).toBe(false);
    expect(verifyAdminCredentials("other", "a-strong-test-password")).toBe(false);
  });

  it("署名済みセッションを作成して検証する", async () => {
    const token = await createAdminSessionToken("owner");
    const session = await verifyAdminSessionToken(token);

    expect(session?.username).toBe("owner");
    expect(session?.expiresAt).toBeGreaterThan(Date.now());
  });

  it("改ざんされたセッションを拒否する", async () => {
    const token = await createAdminSessionToken("owner");
    const tampered = `${token.slice(0, -1)}x`;

    expect(await verifyAdminSessionToken(tampered)).toBeNull();
  });
});
