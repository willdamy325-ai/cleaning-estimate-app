import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createEmptyQuantities } from "@/domain/quote";

const { saveMock, notificationMock } = vi.hoisted(() => ({
  saveMock: vi.fn(),
  notificationMock: vi.fn(),
}));

vi.mock("@/infrastructure/repositories/neonQuoteRepository", () => ({
  NeonQuoteRepository: class {
    save = saveMock;
  },
}));

vi.mock("@/infrastructure/email/resendNotification", () => ({
  sendAdminQuoteNotification: notificationMock,
}));

import { POST } from "@/app/api/quotes/route";

const customer = {
  name: "山田 太郎",
  phone: "090-1234-5678",
  email: "taro@example.com",
  address: "東京都渋谷区1-2-3",
  preferredDate: "2099-09-20",
  notes: "",
};

describe("POST /api/quotes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    saveMock.mockImplementation(async (quote) => ({
      ...quote,
      status: "new",
      updatedAt: quote.createdAt,
    }));
    notificationMock.mockResolvedValue({ sent: true });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("検証・再計算した依頼を保存し通知する", async () => {
    const quantities = createEmptyQuantities();
    quantities["standard-ac"] = 2;

    const response = await POST(
      new Request("http://localhost/api/quotes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quantities, customer }),
      }),
    );
    const body = await response.json();

    expect(response.status).toBe(201);
    expect(body.quote.total).toBe(14000);
    expect(body.notificationSent).toBe(true);
    expect(saveMock).toHaveBeenCalledOnce();
    expect(notificationMock).toHaveBeenCalledOnce();
  });

  it("不正な依頼は保存しない", async () => {
    const response = await POST(
      new Request("http://localhost/api/quotes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quantities: {}, customer }),
      }),
    );

    expect(response.status).toBe(400);
    expect(saveMock).not.toHaveBeenCalled();
    expect(notificationMock).not.toHaveBeenCalled();
  });

  it("メール通知が失敗しても保存済み依頼は成功にする", async () => {
    const quantities = createEmptyQuantities();
    quantities.toilet = 1;
    notificationMock.mockRejectedValueOnce(new Error("mail unavailable"));

    const response = await POST(
      new Request("http://localhost/api/quotes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quantities, customer }),
      }),
    );
    const body = await response.json();

    expect(response.status).toBe(201);
    expect(body.quote.total).toBe(6000);
    expect(body.notificationSent).toBe(false);
  });
});
