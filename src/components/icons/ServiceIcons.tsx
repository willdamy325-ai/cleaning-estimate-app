import type { ComponentType, SVGProps } from "react";
import type { ServiceId } from "@/domain/types";

type IconProps = SVGProps<SVGSVGElement>;

function BaseIcon({ children, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export function StandardAcIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <rect x="6" y="12" width="36" height="18" rx="3" />
      <path d="M12 21h24M12 25h16" />
      <path d="M14 30v5M24 30v5M34 30v5" />
    </BaseIcon>
  );
}

export function AutoCleanAcIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <rect x="6" y="10" width="36" height="18" rx="3" />
      <path d="M12 19h24" />
      <path d="M24 32a6 6 0 1 0 0.01 0" />
      <path d="M24 28.5v-1.5M24 37.5V36M19.8 29.8l-1.1-1.1M29.3 39.3l-1.1-1.1M19.8 38.2l-1.1 1.1M29.3 28.7l-1.1 1.1" />
    </BaseIcon>
  );
}

export function BathroomIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <path d="M10 18h22a6 6 0 0 1 6 6v10H10V18Z" />
      <path d="M10 18V12h8" />
      <path d="M16 38v2M32 38v2" />
    </BaseIcon>
  );
}

export function WashbasinIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <path d="M10 24h28c0 8-6 12-14 12S10 32 10 24Z" />
      <path d="M24 14v10" />
      <path d="M20 14h8" />
      <path d="M18 38h12" />
    </BaseIcon>
  );
}

export function RangeHoodIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <path d="M18 8h12v8H18z" />
      <path d="M10 16h28l-4 12H14L10 16Z" />
      <path d="M18 32v6h12v-6" />
    </BaseIcon>
  );
}

export function KitchenIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <rect x="8" y="18" width="32" height="18" rx="2" />
      <path d="M8 26h32" />
      <circle cx="16" cy="22" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="22" cy="22" r="1.4" fill="currentColor" stroke="none" />
      <path d="M30 21h6v2h-6z" />
      <path d="M14 32h8M28 32h8" />
    </BaseIcon>
  );
}

export function ToiletIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <rect x="14" y="8" width="16" height="10" rx="2" />
      <path d="M16 18h12c4 0 8 3 8 8 0 6-6 10-12 10h-4c-6 0-12-4-12-10 0-5 4-8 8-8Z" />
      <path d="M20 38v2h8v-2" />
    </BaseIcon>
  );
}

export function WashingMachineIcon(props: IconProps) {
  return (
    <BaseIcon {...props}>
      <rect x="10" y="8" width="28" height="32" rx="3" />
      <circle cx="24" cy="26" r="8" />
      <circle cx="24" cy="26" r="3.5" />
      <circle cx="16" cy="14" r="1.2" fill="currentColor" stroke="none" />
      <circle cx="20.5" cy="14" r="1.2" fill="currentColor" stroke="none" />
    </BaseIcon>
  );
}

const ICONS: Record<ServiceId, ComponentType<IconProps>> = {
  "standard-ac": StandardAcIcon,
  "auto-clean-ac": AutoCleanAcIcon,
  bathroom: BathroomIcon,
  washbasin: WashbasinIcon,
  "range-hood": RangeHoodIcon,
  kitchen: KitchenIcon,
  toilet: ToiletIcon,
  "washing-machine": WashingMachineIcon,
};

export function ServiceIcon({ id, className }: { id: ServiceId; className?: string }) {
  const Icon = ICONS[id];
  return <Icon className={className} />;
}
