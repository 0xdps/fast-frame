import type { ComponentProps } from "react";

import { cn } from "../../lib/cn";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "flex h-9 w-full rounded-field border border-field-border bg-field px-3 text-body text-foreground shadow-[var(--shadow-quiet)] outline-none placeholder:text-faint hover:border-[var(--field-border-hover)] focus-visible:border-primary focus-visible:shadow-[var(--shadow-focus)] disabled:cursor-not-allowed disabled:border-border disabled:bg-subtle disabled:text-faint",
        className,
      )}
      {...props}
    />
  );
}
