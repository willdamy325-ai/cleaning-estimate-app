import { cn } from "@/lib/cn";

type StepIndicatorProps = {
  current: 1 | 2;
};

export function StepIndicator({ current }: StepIndicatorProps) {
  return (
    <ol className="flex items-center justify-center gap-3 text-xs tracking-widest">
      <li className={cn("flex items-center gap-2", current === 1 ? "text-pine" : "text-clay")}>
        <span
          className={cn(
            "flex h-6 w-6 items-center justify-center rounded-full border text-[11px]",
            current === 1 ? "border-pine bg-pine text-paper" : "border-gold-soft bg-paper",
          )}
        >
          1
        </span>
        サービス選択
      </li>
      <li className="h-px w-8 bg-gold-soft" aria-hidden="true" />
      <li className={cn("flex items-center gap-2", current === 2 ? "text-pine" : "text-clay")}>
        <span
          className={cn(
            "flex h-6 w-6 items-center justify-center rounded-full border text-[11px]",
            current === 2 ? "border-pine bg-pine text-paper" : "border-gold-soft bg-paper",
          )}
        >
          2
        </span>
        お客様情報
      </li>
    </ol>
  );
}
