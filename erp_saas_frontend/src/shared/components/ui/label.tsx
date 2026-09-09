import * as React from "react"
import * as LabelPrimitive from "@radix-ui/react-label"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/shared/lib/utils"

const labelVariants = cva(
  "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
)

/**
 * `obligatorio` PONE EL ASTERISCO, y lo pone EN ROJO.
 *
 * Antes cada formulario escribía `{t("...")} *` a mano: el asterisco
 * quedaba del mismo color que el texto —o sea, invisible como aviso— y
 * cada pantalla podía escribirlo distinto (antes del texto, con dos
 * espacios, o no escribirlo). Acá se decide una vez.
 *
 * El asterisco NO lleva `aria-hidden`. Los inputs de este proyecto no
 * llevan el atributo `required`, así que el asterisco es la única señal
 * que existe: escondérselo a un lector de pantalla lo dejaría sin
 * enterarse. El día que los inputs marquen `required`, esto se puede
 * ocultar.
 */
type PropsDeLabel = React.ComponentPropsWithoutRef<
  typeof LabelPrimitive.Root
> &
  VariantProps<typeof labelVariants> & {
    obligatorio?: boolean
  }

const Label = React.forwardRef<
  React.ElementRef<typeof LabelPrimitive.Root>,
  PropsDeLabel
>(({ className, obligatorio, children, ...props }, ref) => (
  <LabelPrimitive.Root
    ref={ref}
    className={cn(labelVariants(), className)}
    {...props}
  >
    {children}
    {obligatorio && <span className="ml-0.5 text-destructive">*</span>}
  </LabelPrimitive.Root>
))
Label.displayName = LabelPrimitive.Root.displayName

export { Label }
