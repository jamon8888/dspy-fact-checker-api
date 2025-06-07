import { type VariantProps, cva } from "class-variance-authority";
import type * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 font-semibold text-xs transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        success:
          "border-transparent bg-emerald-500 text-emerald-50 hover:bg-emerald-500/80",
        warning:
          "border-transparent bg-amber-500 text-amber-50 hover:bg-amber-500/80",
        "success-subtle":
          "border-green-200 bg-green-100 text-green-700 dark:border-green-800 dark:bg-green-900/70 dark:text-green-400",
        "destructive-subtle":
          "border-red-200 bg-red-100 text-red-700 dark:border-red-800 dark:bg-red-900/70 dark:text-red-400",
        "warning-subtle":
          "border-yellow-200 bg-yellow-100 text-yellow-700 dark:border-yellow-700 dark:bg-yellow-800/70 dark:text-yellow-400",
        "outline-subtle":
          "border-neutral-200 bg-neutral-100 text-neutral-600 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
