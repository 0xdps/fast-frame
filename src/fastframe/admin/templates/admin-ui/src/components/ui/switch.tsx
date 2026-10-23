import * as SwitchPrimitive from "@radix-ui/react-switch";
import type { ComponentProps } from "react";

import { cn } from "../../lib/cn";

export function Switch({ className, ...props }: ComponentProps<typeof SwitchPrimitive.Root>) {
  return (
    <SwitchPrimitive.Root
      className={cn(
        "inline-flex h-4 w-7 shrink-0 cursor-pointer items-center rounded-full bg-border transition-colors focus-visible:outline-none focus-visible:shadow-[var(--shadow-focus)] data-[state=checked]:bg-primary disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb className="pointer-events-none block size-3 translate-x-0.5 rounded-full bg-card shadow transition-transform data-[state=checked]:translate-x-3" />
    </SwitchPrimitive.Root>
  );
}
