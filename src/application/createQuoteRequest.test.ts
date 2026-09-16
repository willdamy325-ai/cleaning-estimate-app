import { describe, expect, it } from "vitest";
import {
  createQuoteRequestFromInput,
  InvalidQuoteRequestError,
} from "@/application/createQuoteRequest";
import { createEmptyQuantities } from "@/domain/quote";

const customer = {
  name: " 山田 太郎 ",
  phone: "090-1234-5678",
  email: "taro@example.com",
  address: "東京都渋谷区1-2-3",
  preferredDate: "2026-09-20",
  notes: " 午前中希望 ",
};

describe("createQuoteRequestFromInput", () => {
  it("サーバー側で料金を再計算して見積依頼を作る", () => {
    const quantities = createEmptyQuantities();
    quantities["standard-ac"] = 1;
    quantities.bathroom = 1;

    const quote = createQuoteRequestFromInput(
      { quantities, customer, total: 1 },
      { now: new Date("2026-09-16T03:00:00.000Z"), id: "SQ-TEST-0001" },
    );

    expect(quote.id).toBe("SQ-TEST-0001");
    expect(quote.total).toBe(19000);
    expect(quote.items).toHaveLength(2);
    expect(quote.customer.name).toBe("山田 太郎");
    expect(quote.customer.notes).toBe("午前中希望");
  });

  it("数量が範囲外なら拒否する", () => {
    const quantities = createEmptyQuantities();
    quantities["washing-machine"] = 11;

    expect(() =>
      createQuoteRequestFromInput(
        { quantities, customer },
        { now: new Date("2026-09-16T03:00:00.000Z") },
      ),
    ).toThrow(InvalidQuoteRequestError);
  });

  it("サービス未選択なら拒否する", () => {
    expect(() =>
      createQuoteRequestFromInput(
        { quantities: createEmptyQuantities(), customer },
        { now: new Date("2026-09-16T03:00:00.000Z") },
      ),
    ).toThrow("サービスを1つ以上選択してください");
  });

  it("不正なお客様情報を拒否する", () => {
    const quantities = createEmptyQuantities();
    quantities.toilet = 1;

    expect(() =>
      createQuoteRequestFromInput(
        { quantities, customer: { ...customer, email: "invalid" } },
        { now: new Date("2026-09-16T03:00:00.000Z") },
      ),
    ).toThrow("お客様情報の入力内容を確認してください");
  });
});
