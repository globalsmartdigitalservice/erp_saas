import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/shared/components/ui/button";

export function BackButton({
  to = "..",
  children,
}: {
  to?: string;
  children: ReactNode;
}) {
  return (
    <Button asChild variant="ghost" size="sm" className="-ml-2 gap-2">
      <Link to={to}>
        <ArrowLeft aria-hidden="true" />
        {children}
      </Link>
    </Button>
  );
}
