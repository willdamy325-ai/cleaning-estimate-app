import type { HTMLAttributes } from "react";
import type { CustomerErrors, CustomerField } from "@/domain/customer";
import type { CustomerInfo } from "@/domain/types";
import { todayIsoDate } from "@/lib/format";
import { cn } from "@/lib/cn";

type CustomerFormProps = {
  value: CustomerInfo;
  errors: CustomerErrors;
  onChange: (field: CustomerField, value: string) => void;
};

const fields: Array<{
  id: CustomerField;
  label: string;
  type: string;
  placeholder: string;
  required: boolean;
  autoComplete?: string;
  inputMode?: HTMLAttributes<HTMLInputElement>["inputMode"];
}> = [
  {
    id: "name",
    label: "お名前",
    type: "text",
    placeholder: "山田 太郎",
    required: true,
    autoComplete: "name",
  },
  {
    id: "phone",
    label: "電話番号",
    type: "tel",
    placeholder: "090-1234-5678",
    required: true,
    autoComplete: "tel",
    inputMode: "tel",
  },
  {
    id: "email",
    label: "メールアドレス",
    type: "email",
    placeholder: "example@email.com",
    required: true,
    autoComplete: "email",
    inputMode: "email",
  },
  {
    id: "address",
    label: "住所",
    type: "text",
    placeholder: "東京都渋谷区1-2-3",
    required: true,
    autoComplete: "street-address",
  },
  {
    id: "preferredDate",
    label: "希望作業日",
    type: "date",
    placeholder: "",
    required: true,
  },
];

export function CustomerForm({ value, errors, onChange }: CustomerFormProps) {
  return (
    <div className="rounded-3xl border border-gold-soft bg-paper p-5 shadow-card sm:p-7">
      <h2 className="font-serif text-xl text-pine-deep">お客様情報</h2>
      <p className="mt-1 text-sm text-clay">見積のご連絡に使用します。必須項目はすべてご入力ください。</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {fields.map((field) => (
          <label key={field.id} className={cn("block", field.id === "address" && "sm:col-span-2")}>
            <span className="mb-1.5 flex items-center gap-2 text-sm text-ink">
              {field.label}
              {field.required ? (
                <span className="rounded-full bg-pine/10 px-2 py-0.5 text-[10px] tracking-widest text-pine">
                  必須
                </span>
              ) : null}
            </span>
            <input
              id={field.id}
              name={field.id}
              type={field.type}
              value={value[field.id]}
              min={field.type === "date" ? todayIsoDate() : undefined}
              placeholder={field.placeholder}
              autoComplete={field.autoComplete}
              inputMode={field.inputMode}
              required={field.required}
              aria-invalid={Boolean(errors[field.id])}
              aria-describedby={errors[field.id] ? `${field.id}-error` : undefined}
              onChange={(event) => onChange(field.id, event.target.value)}
              className={cn(
                "h-12 w-full rounded-2xl border bg-mist/60 px-4 text-base text-ink outline-none transition placeholder:text-clay/60 focus:border-pine focus:bg-paper focus:ring-2 focus:ring-pine/15",
                errors[field.id] ? "border-red-400" : "border-gold-soft",
              )}
            />
            {errors[field.id] ? (
              <span id={`${field.id}-error`} className="mt-1 block text-xs text-red-700">
                {errors[field.id]}
              </span>
            ) : field.type === "date" ? (
              <span className="mt-1 block text-xs text-clay">本日以降の日付を選択してください</span>
            ) : null}
          </label>
        ))}

        <label className="block sm:col-span-2">
          <span className="mb-1.5 flex items-center gap-2 text-sm text-ink">
            備考
            <span className="rounded-full bg-gold-pale px-2 py-0.5 text-[10px] tracking-widest text-clay">
              任意
            </span>
          </span>
          <textarea
            id="notes"
            name="notes"
            rows={4}
            maxLength={500}
            value={value.notes}
            placeholder="駐車スペース、集合住宅の注意点、ご希望時間帯など"
            aria-invalid={Boolean(errors.notes)}
            onChange={(event) => onChange("notes", event.target.value)}
            className={cn(
              "w-full rounded-2xl border bg-mist/60 px-4 py-3 text-base text-ink outline-none transition placeholder:text-clay/60 focus:border-pine focus:bg-paper focus:ring-2 focus:ring-pine/15",
              errors.notes ? "border-red-400" : "border-gold-soft",
            )}
          />
          <span className="mt-1 flex justify-between text-xs text-clay">
            <span>{errors.notes ?? "500文字以内"}</span>
            <span>{value.notes.length}/500</span>
          </span>
        </label>
      </div>
    </div>
  );
}
