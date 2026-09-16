import type { QuoteStatus } from "@/domain/types";
import { QUOTE_STATUS_LABELS } from "@/domain/quoteStatus";
import { cn } from "@/lib/cn";

const styles: Record<QuoteStatus, string> = {
  new: "bg-amber-100 text-amber-900",
  contacted: "bg-sky-100 text-sky-900",
  confirmed: "bg-indigo-100 text-indigo-900",
  completed: "bg-emerald-100 text-emerald-900",
  cancelled: "bg-stone-200 text-stone-700",
};

export function StatusBadge({ status }: { status: QuoteStatus }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-1 text-[11px] font-medium tracking-wide",
        styles[status],
      )}
    >
      {QUOTE_STATUS_LABELS[status]}
    </span>
  );
}
