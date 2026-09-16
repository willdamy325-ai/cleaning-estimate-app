import { describe, expect, it } from "vitest";
import { SERVICE_CATALOG } from "@/domain/catalog";
import {
  calculateQuote,
  changeQuantity,
  clampQuantity,
  createEmptyQuantities,
} from "@/domain/quote";

describe("clampQuantity", () => {
  it("0未満は0にする", () => {
    expect(clampQuantity(-3)).toBe(0);
  });

  it("10超は10にする", () => {
    expect(clampQuantity(15)).toBe(10);
  });

  it("非数は0にする", () => {
    expect(clampQuantity(Number.NaN)).toBe(0);
  });
});

describe("calculateQuote", () => {
  it("未選択なら合計0円", () => {
    const quote = calculateQuote(createEmptyQuantities());
    expect(quote.lines).toHaveLength(0);
    expect(quote.total).toBe(0);
  });

  it("数量変更と同時に小計・合計を計算する", () => {
    const quantities = changeQuantity(createEmptyQuantities(), "standard-ac", 2);
    const withBathroom = changeQuantity(quantities, "bathroom", 1);
    const quote = calculateQuote(withBathroom);

    expect(quote.lines).toEqual([
      {
        service: SERVICE_CATALOG[0],
        quantity: 2,
        subtotal: 14000,
      },
      {
        service: SERVICE_CATALOG[2],
        quantity: 1,
        subtotal: 12000,
      },
    ]);
    expect(quote.total).toBe(26000);
  });

  it("カタログの単価どおりに計算する", () => {
    let quantities = createEmptyQuantities();
    quantities = changeQuantity(quantities, "auto-clean-ac", 1);
    quantities = changeQuantity(quantities, "washbasin", 1);
    quantities = changeQuantity(quantities, "range-hood", 1);
    quantities = changeQuantity(quantities, "kitchen", 1);
    quantities = changeQuantity(quantities, "toilet", 1);
    quantities = changeQuantity(quantities, "washing-machine", 1);

    const quote = calculateQuote(quantities);
    expect(quote.total).toBe(68000);
  });
});
