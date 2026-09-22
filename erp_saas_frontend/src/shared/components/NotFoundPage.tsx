import { ArrowLeft, FileQuestion } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import { Button } from "@/shared/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/shared/components/ui/empty";

export function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <FileQuestion aria-hidden="true" />
          </EmptyMedia>
          <EmptyTitle className="font-heading text-xl">
            {t("noEncontrada.titulo")}
          </EmptyTitle>
          <EmptyDescription>{t("noEncontrada.ayuda")}</EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button asChild>
            <Link to="/">
              <ArrowLeft aria-hidden="true" />
              {t("noEncontrada.volver")}
            </Link>
          </Button>
        </EmptyContent>
      </Empty>
    </main>
  );
}
