import type { CustomerInfo } from "@/domain/types";

export const EMPTY_CUSTOMER: CustomerInfo = {
  name: "",
  phone: "",
  email: "",
  address: "",
  preferredDate: "",
  notes: "",
};

export type CustomerField = keyof CustomerInfo;
export type CustomerErrors = Partial<Record<CustomerField, string>>;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function normalizePhone(value: string): string {
  return value.replace(/[-ー−\s]/g, "");
}

export function isValidPhone(value: string): boolean {
  return /^0\d{9,10}$/.test(normalizePhone(value));
}

export function isValidEmail(value: string): boolean {
  return EMAIL_PATTERN.test(value.trim());
}

export function isValidPreferredDate(value: string, today = new Date()): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return false;
  }
  const selected = new Date(`${value}T00:00:00`);
  if (Number.isNaN(selected.getTime())) {
    return false;
  }
  const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  return selected.getTime() >= startOfToday.getTime();
}

export function validateCustomer(customer: CustomerInfo, today = new Date()): CustomerErrors {
  const errors: CustomerErrors = {};
  const name = customer.name.trim();
  const phone = customer.phone.trim();
  const email = customer.email.trim();
  const address = customer.address.trim();
  const preferredDate = customer.preferredDate.trim();
  const notes = customer.notes.trim();

  if (!name) {
    errors.name = "お名前を入力してください";
  } else if (name.length > 50) {
    errors.name = "お名前は50文字以内で入力してください";
  }

  if (!phone) {
    errors.phone = "電話番号を入力してください";
  } else if (!isValidPhone(phone)) {
    errors.phone = "電話番号は0から始まる10〜11桁で入力してください";
  }

  if (!email) {
    errors.email = "メールアドレスを入力してください";
  } else if (!isValidEmail(email)) {
    errors.email = "正しいメールアドレスを入力してください";
  }

  if (!address) {
    errors.address = "住所を入力してください";
  } else if (address.length > 120) {
    errors.address = "住所は120文字以内で入力してください";
  }

  if (!preferredDate) {
    errors.preferredDate = "希望作業日を選択してください";
  } else if (!isValidPreferredDate(preferredDate, today)) {
    errors.preferredDate = "希望作業日は本日以降の日付を選択してください";
  }

  if (notes.length > 500) {
    errors.notes = "備考は500文字以内で入力してください";
  }

  return errors;
}

export function hasCustomerErrors(errors: CustomerErrors): boolean {
  return Object.keys(errors).length > 0;
}

export function sanitizeCustomer(customer: CustomerInfo): CustomerInfo {
  return {
    name: customer.name.trim(),
    phone: customer.phone.trim(),
    email: customer.email.trim(),
    address: customer.address.trim(),
    preferredDate: customer.preferredDate.trim(),
    notes: customer.notes.trim(),
  };
}
