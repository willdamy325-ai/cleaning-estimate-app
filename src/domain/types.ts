export type ServiceId =
  | "standard-ac"
  | "auto-clean-ac"
  | "bathroom"
  | "washbasin"
  | "range-hood"
  | "kitchen"
  | "toilet"
  | "washing-machine";

export type Service = {
  id: ServiceId;
  name: string;
  description: string;
  unitLabel: string;
  price: number;
};

export type QuoteLineItem = {
  service: Service;
  quantity: number;
  subtotal: number;
};

export type Quote = {
  lines: QuoteLineItem[];
  total: number;
};

export type CustomerInfo = {
  name: string;
  phone: string;
  email: string;
  address: string;
  preferredDate: string;
  notes: string;
};

export type QuoteRequest = {
  id: string;
  createdAt: string;
  items: QuoteLineItem[];
  total: number;
  customer: CustomerInfo;
};

export type QuantityMap = Record<ServiceId, number>;

export const QUANTITY_MIN = 0;
export const QUANTITY_MAX = 10;
