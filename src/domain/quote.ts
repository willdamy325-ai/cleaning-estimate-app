import { SERVICE_CATALOG } from "@/domain/catalog";
import {
  QUANTITY_MAX,
  QUANTITY_MIN,
  type QuantityMap,
  type Quote,
  type ServiceId,
} from "@/domain/types";

export function createEmptyQuantities(): QuantityMap {
  return SERVICE_CATALOG.reduce((acc, service) => {
    acc[service.id] = 0;
    return acc;
  }, {} as QuantityMap);
}

export function clampQuantity(value: number): number {
  if (!Number.isFinite(value)) {
    return QUANTITY_MIN;
  }
  return Math.min(QUANTITY_MAX, Math.max(QUANTITY_MIN, Math.round(value)));
}

export function calculateQuote(quantities: QuantityMap): Quote {
  const lines = SERVICE_CATALOG.flatMap((service) => {
    const quantity = clampQuantity(quantities[service.id] ?? 0);
    if (quantity === 0) {
      return [];
    }
    return [
      {
        service,
        quantity,
        subtotal: service.price * quantity,
      },
    ];
  });

  const total = lines.reduce((sum, line) => sum + line.subtotal, 0);
  return { lines, total };
}

export function changeQuantity(
  quantities: QuantityMap,
  serviceId: ServiceId,
  nextValue: number,
): QuantityMap {
  return {
    ...quantities,
    [serviceId]: clampQuantity(nextValue),
  };
}
