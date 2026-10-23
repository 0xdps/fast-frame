import type { ComponentProps } from "react";

import { cn } from "../../lib/cn";

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "flex min-h-24 w-full rounded-field border border-field-border bg-field px-3 py-2 text-body text-foreground shadow-[var(--shadow-quiet)] outline-none placeholder:text-faint hover:border-[var(--field-border-hover)] focus-visible:border-primary focus-visible:shadow-[var(--shadow-focus)] disabled:cursor-not-allowed disabled:border-border disabled:bg-subtle disabled:text-faint",
        className,
      )}
      {...props}
    />
  );
}
