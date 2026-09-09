"""Acceso a datos de `Tipo_Documento_Comercial`. Filtrado por empresa."""

from comun.tipos_documento.models import TipoDocumentoComercial


def obtener(tipo_id: int) -> TipoDocumentoComercial | None:
    return TipoDocumentoComercial.objects.filter(pk=tipo_id).first()


def obtener_varios(tipo_ids) -> dict[int, TipoDocumentoComercial]:
    return {
        t.pk: t for t in TipoDocumentoComercial.objects.filter(pk__in=list(tipo_ids))
    }


def listar() -> list[TipoDocumentoComercial]:
    return list(TipoDocumentoComercial.objects.all())


def existe_codigo(codigo: str, excluir_id: int | None = None) -> bool:
    qs = TipoDocumentoComercial.objects.filter(codigo=codigo)
    if excluir_id is not None:
        qs = qs.exclude(pk=excluir_id)
    return qs.exists()


def crear(**campos) -> TipoDocumentoComercial:
    return TipoDocumentoComercial.objects.create(**campos)


def actualizar(fila: TipoDocumentoComercial, **campos) -> TipoDocumentoComercial:
    for campo, valor in campos.items():
        setattr(fila, campo, valor)
    fila.save(update_fields=list(campos))
    return fila
