import type { ComponentProps } from "react";

import { cn } from "../../lib/cn";

export function Badge({ className, ...props }: ComponentProps<"span">) {
  return (
    <span
      className={cn(
        "pill tone-3",
        className,
      )}
      {...props}
    />
  );
}
