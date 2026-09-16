import { describe, expect, it } from "vitest";
import {
  EMPTY_CUSTOMER,
  hasCustomerErrors,
  isValidPhone,
  isValidPreferredDate,
  validateCustomer,
} from "@/domain/customer";

const validCustomer = {
  name: "山田 太郎",
  phone: "090-1234-5678",
  email: "taro@example.com",
  address: "東京都渋谷区1-2-3",
  preferredDate: "2026-09-20",
  notes: "",
};

describe("isValidPhone", () => {
  it("ハイフン付き携帯電話番号を受け入れる", () => {
    expect(isValidPhone("090-1234-5678")).toBe(true);
  });

  it("市外局番の固定電話を受け入れる", () => {
    expect(isValidPhone("0312345678")).toBe(true);
  });

  it("桁数が足りない番号は拒否する", () => {
    expect(isValidPhone("12345")).toBe(false);
  });
});

describe("isValidPreferredDate", () => {
  const today = new Date("2026-09-16T10:00:00");

  it("本日以降を受け入れる", () => {
    expect(isValidPreferredDate("2026-09-16", today)).toBe(true);
    expect(isValidPreferredDate("2026-09-17", today)).toBe(true);
  });

  it("過去日は拒否する", () => {
    expect(isValidPreferredDate("2026-09-15", today)).toBe(false);
  });
});

describe("validateCustomer", () => {
  it("必須項目が揃っていればエラーなし", () => {
    const errors = validateCustomer(validCustomer, new Date("2026-09-16"));
    expect(hasCustomerErrors(errors)).toBe(false);
  });

  it("空のフォームは各必須項目のエラーを返す", () => {
    const errors = validateCustomer(EMPTY_CUSTOMER, new Date("2026-09-16"));
    expect(errors.name).toBeTruthy();
    expect(errors.phone).toBeTruthy();
    expect(errors.email).toBeTruthy();
    expect(errors.address).toBeTruthy();
    expect(errors.preferredDate).toBeTruthy();
  });
});
