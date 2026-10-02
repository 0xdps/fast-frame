import type { ComponentProps } from "react";

import { cn } from "../../lib/cn";

export function Badge({ className, ...props }: ComponentProps<"span">) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full bg-accent px-2 py-0.5 text-xs font-medium text-foreground",
        className,
      )}
      {...props}
    />
  );
}
