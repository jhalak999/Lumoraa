import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-[var(--color-surface-raised)] text-[var(--color-text-secondary)]",
        amber: "border-transparent bg-[rgba(242,169,59,0.15)] text-[var(--color-amber)]",
        cyan: "border-transparent bg-[rgba(94,200,216,0.15)] text-[var(--color-cyan)]",
        danger: "border-transparent bg-[var(--color-danger-dim)] text-[var(--color-danger)]",
        outline: "border-[var(--color-border-strong)] text-[var(--color-text-secondary)]",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
