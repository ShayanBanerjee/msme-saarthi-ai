import { cn } from "@/lib/utils";

interface BrandMarkProps {
  readonly className?: string;
  readonly size?: "sm" | "md" | "lg";
}

export function BrandMark({ className, size = "md" }: BrandMarkProps) {
  return (
    <span className={cn("brand-medallion", `brand-medallion-${size}`, className)} aria-hidden="true">
      <img
        alt=""
        decoding="async"
        height={size === "lg" ? 72 : size === "md" ? 44 : 32}
        src="/images/brand/saarthi-chariot-medallion-v1-512.png"
        width={size === "lg" ? 72 : size === "md" ? 44 : 32}
      />
    </span>
  );
}
