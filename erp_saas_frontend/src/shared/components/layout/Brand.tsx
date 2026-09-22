import { Link } from "react-router-dom";

export const APP_NAME = "ERP";

export function Brand() {
  return (
    <Link
      to="/"
      className="flex min-w-0 flex-1 items-center gap-2 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <span className="font-heading text-lg font-semibold tracking-tight">
        {APP_NAME}
      </span>
    </Link>
  );
}
