import { CircleAlert } from "lucide-react";

import { Alert, AlertDescription } from "@/shared/components/ui/alert";

type Props = {
  message?: string | null;
  id?: string;
};

export function ErrorAlert({ message, id }: Props) {
  if (!message) return null;

  return (
    <Alert id={id} variant="destructive" className="bg-destructive/5">
      <CircleAlert aria-hidden="true" />
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  );
}
