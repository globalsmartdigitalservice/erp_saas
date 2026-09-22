import { Eye, EyeOff, TriangleAlert } from "lucide-react";
import {
  useId,
  useState,
  type ComponentProps,
  type KeyboardEvent,
} from "react";
import { useTranslation } from "react-i18next";

import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupInput,
} from "@/shared/components/ui/input-group";

type Props = Omit<ComponentProps<typeof InputGroupInput>, "type">;

/** Campo de contraseña con el botón para verla y el aviso de Bloq Mayús. */
export function PasswordInput({
  "aria-describedby": externalDescribedBy,
  onKeyDown,
  onKeyUp,
  onBlur,
  ...props
}: Props) {
  const { t } = useTranslation();
  const capsLockHintId = useId();
  const [isVisible, setIsVisible] = useState(false);
  const [isCapsLockOn, setIsCapsLockOn] = useState(false);

  const readCapsLock = (e: KeyboardEvent<HTMLInputElement>) =>
    setIsCapsLockOn(e.getModifierState("CapsLock"));

  const describedBy =
    [externalDescribedBy, isCapsLockOn ? capsLockHintId : undefined]
      .filter(Boolean)
      .join(" ") || undefined;

  return (
    <>
      <InputGroup className="h-10 bg-background shadow-none ring-offset-background has-[[data-slot=input-group-control]:focus-visible]:ring-2 has-[[data-slot=input-group-control]:focus-visible]:ring-offset-2">
        <InputGroupInput
          {...props}
          className="h-full focus-visible:ring-offset-0"
          type={isVisible ? "text" : "password"}
          aria-describedby={describedBy}
          onKeyDown={(e) => {
            readCapsLock(e);
            onKeyDown?.(e);
          }}
          onKeyUp={(e) => {
            readCapsLock(e);
            onKeyUp?.(e);
          }}
          onBlur={(e) => {
            setIsCapsLockOn(false);
            onBlur?.(e);
          }}
        />
        <InputGroupAddon align="inline-end">
          <InputGroupButton
            size="icon-xs"
            aria-label={t("comun.mostrarPassword")}
            aria-pressed={isVisible}
            onClick={() => setIsVisible((previous) => !previous)}
          >
            {isVisible ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>

      {isCapsLockOn && (
        <p id={capsLockHintId} className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <TriangleAlert aria-hidden="true" className="size-3.5 shrink-0" />
          {t("comun.mayusculasActivadas")}
        </p>
      )}
    </>
  );
}
