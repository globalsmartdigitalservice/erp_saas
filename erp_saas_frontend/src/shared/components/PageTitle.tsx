import type { ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

export function PageTitle({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <h1 className={cn("font-heading text-xl font-semibold tracking-tight", className)}>
      {children}
    </h1>
  );
}
