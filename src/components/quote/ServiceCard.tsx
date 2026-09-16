import type { Service } from "@/domain/types";
import { ServiceIcon } from "@/components/icons/ServiceIcons";
import { QuantityStepper } from "@/components/quote/QuantityStepper";
import { cn } from "@/lib/cn";
import { formatYen } from "@/lib/format";

type ServiceCardProps = {
  service: Service;
  quantity: number;
  onQuantityChange: (value: number) => void;
};

export function ServiceCard({ service, quantity, onQuantityChange }: ServiceCardProps) {
  const selected = quantity > 0;
  const subtotal = service.price * quantity;

  return (
    <article
      className={cn(
        "flex h-full flex-col rounded-3xl border bg-paper p-5 shadow-card transition",
        selected ? "border-pine/40 ring-1 ring-pine/15" : "border-gold-soft/80",
      )}
    >
      <div className="flex items-start gap-4">
        <div
          className={cn(
            "flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl",
            selected ? "bg-pine text-gold-pale" : "bg-gold-pale text-pine",
          )}
        >
          <ServiceIcon id={service.id} className="h-8 w-8" />
        </div>
        <div className="min-w-0">
          <h3 className="font-serif text-lg text-pine-deep">{service.name}</h3>
          <p className="mt-1 text-sm leading-relaxed text-clay">{service.description}</p>
        </div>
      </div>

      <div className="mt-5 flex items-end justify-between gap-3">
        <p className="text-sm text-clay">
          <span className="block font-serif text-2xl tracking-wide text-pine">
            {formatYen(service.price)}
          </span>
          <span>／ {service.unitLabel}</span>
        </p>
        <QuantityStepper
          value={quantity}
          onChange={onQuantityChange}
          label={service.name}
        />
      </div>

      <p
        className={cn(
          "mt-4 border-t border-dashed border-gold-soft pt-3 text-right text-sm",
          selected ? "text-pine" : "text-clay/70",
        )}
        aria-live="polite"
      >
        小計 {formatYen(subtotal)}
      </p>
    </article>
  );
}
