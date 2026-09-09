import { Link } from "react-router-dom";


export function Brand() {
  return (
    <Link
      to="/"
      className="flex min-w-0 flex-1 items-center gap-2"
      aria-label="ERP"
    >
      <span className="font-heading text-lg font-semibold tracking-tight">
        ERP
      </span>
    </Link>
  );
}
