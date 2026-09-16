import { SERVICE_CATALOG } from "@/domain/catalog";
import type { QuantityMap, ServiceId } from "@/domain/types";
import { ServiceCard } from "@/components/quote/ServiceCard";

type ServiceListProps = {
  quantities: QuantityMap;
  onQuantityChange: (serviceId: ServiceId, value: number) => void;
};

export function ServiceList({ quantities, onQuantityChange }: ServiceListProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {SERVICE_CATALOG.map((service) => (
        <ServiceCard
          key={service.id}
          service={service}
          quantity={quantities[service.id]}
          onQuantityChange={(value) => onQuantityChange(service.id, value)}
        />
      ))}
    </div>
  );
}
