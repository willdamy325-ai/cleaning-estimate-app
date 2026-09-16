import { QUANTITY_MAX, QUANTITY_MIN } from "@/domain/types";
import { cn } from "@/lib/cn";

type QuantityStepperProps = {
  value: number;
  onChange: (value: number) => void;
  label: string;
};

export function QuantityStepper({ value, onChange, label }: QuantityStepperProps) {
  const decreaseDisabled = value <= QUANTITY_MIN;
  const increaseDisabled = value >= QUANTITY_MAX;

  return (
    <div className="inline-flex items-center rounded-full border border-gold-soft bg-paper p-1 shadow-sm">
      <button
        type="button"
        onClick={() => onChange(value - 1)}
        disabled={decreaseDisabled}
        aria-label={`${label}を1つ減らす`}
        className={cn(
          "flex h-11 w-11 items-center justify-center rounded-full text-xl text-pine transition",
          decreaseDisabled
            ? "cursor-not-allowed opacity-30"
            : "hover:bg-gold-pale active:scale-95",
        )}
      >
        −
      </button>
      <span
        className="min-w-10 text-center font-serif text-xl text-pine-deep"
        aria-live="polite"
        aria-label={`${label}の数量`}
      >
        {value}
      </span>
      <button
        type="button"
        onClick={() => onChange(value + 1)}
        disabled={increaseDisabled}
        aria-label={`${label}を1つ増やす`}
        className={cn(
          "flex h-11 w-11 items-center justify-center rounded-full text-xl text-pine transition",
          increaseDisabled
            ? "cursor-not-allowed opacity-30"
            : "hover:bg-gold-pale active:scale-95",
        )}
      >
        ＋
      </button>
    </div>
  );
}
