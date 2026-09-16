import { cn } from "@/lib/cn";
import { formatYen } from "@/lib/format";

type StickyQuoteBarProps = {
  total: number;
  disabled: boolean;
  label: string;
  onAction: () => void;
};

export function StickyQuoteBar({ total, disabled, label, onAction }: StickyQuoteBarProps) {
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-gold-soft bg-paper/95 px-4 py-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] shadow-lift backdrop-blur-md lg:hidden">
      <div className="mx-auto flex max-w-content items-center gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-[11px] tracking-widest text-clay">合計金額</p>
          <p className="truncate font-serif text-2xl leading-tight text-pine-deep" aria-live="polite">
            {formatYen(total)}
          </p>
        </div>
        <button
          type="button"
          onClick={onAction}
          disabled={disabled}
          className={cn(
            "min-h-12 shrink-0 rounded-full px-5 text-sm font-medium tracking-wide whitespace-nowrap transition",
            disabled
              ? "cursor-not-allowed bg-gold-soft text-clay"
              : "bg-pine text-paper shadow-card hover:bg-pine-deep",
          )}
        >
          {label}
        </button>
      </div>
    </div>
  );
}
