import pytest
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.test.utils import isolate_apps

from core.tenancy import ModeloTenant, ModeloTenantDerivado


PREFIJOS_DEL_PROYECTO = (
    "core.",
    "comun.",
    "servicios.",
    "dominios.",
    "procesos.",
    "complementos.",
    "proveedor.",
)



EXCEPCIONES = {
    # ─── Es el tenant, no puede tener un tenant ───
    "core_empresa": (
        "ES la tabla de empresas. Un empresa_id acá apuntaría a sí misma. "
        "El aislamiento de la jerarquía matriz→sucursal se resuelve en el "
        "service, no con el manager."
    ),
    # ─── Identidad: la cuenta es de un CLIENTE, no de una empresa ───
    "segu_usuario": (
        "La cuenta es de un CLIENTE, no de una empresa: eso lo dice la "
        "columna `matriz`. En qué empresas del grupo trabaja vive en "
        "Usuario_Empresa, que sí es tenant."
    ),
    # ─── No es una tabla ───
    "seguridad_permisodenegocio": (
        "NO EXISTE COMO TABLA: es `managed = False`. Existe solo para que los "
        "permisos de negocio tengan a qué ContentType colgarse, porque "
        "auth_permission lo exige y 'anular factura' no es el CRUD de ninguna "
        "tabla. No guarda ni una fila, así que no hay nada que aislar. Ver "
        "dominios/seguridad/models/permiso_de_negocio.py."
    ),
    # ─── Catálogos del proveedor: iguales para todos los clientes ───
    "core_pais": "Catálogo del proveedor. Bolivia es Bolivia para todos.",
    "core_ubicacion_geografica": (
        "Catálogo del proveedor: departamentos, provincias, municipios."
    ),
    "core_moneda": (
        "Catálogo del proveedor. Qué monedas usa cada empresa —y cuál es su "
        "base— vive en core_empresa_moneda, que SÍ es tenant."
    ),
    "idio_idioma": (
        "Catálogo del proveedor: el español es el mismo para todos. Qué "
        "idioma usa cada empresa es una FK en core_empresa, no una fila acá."
    ),
    "idio_recurso_texto": (
        "Textos de la interfaz del sistema, no datos de clientes."
    ),
    "prov_modulo_sistema": (
        "Catálogo del proveedor: qué módulos existe el ERP y cuáles son "
        "vendibles. Es el mismo para todos los clientes. Quién tiene "
        "contratado qué es otra cosa y vive en el módulo 25."
    ),
    "prov_sub_modulo": (
        "Catálogo del proveedor: LAS PANTALLAS del ERP, que son las mismas "
        "para todos los clientes. Qué pantallas ve cada empresa se decide "
        "por sus módulos contratados (módulo 25) y por los permisos de sus "
        "grupos, no cambiando estas filas."
    ),
    "prov_funcionalidad": (
        "Catálogo del proveedor: LAS ACCIONES de cada pantalla, una por "
        "permiso de auth_permission. Le pone nombre y pantalla a un permiso "
        "que en Django es solo un codename suelto. A QUIÉN se le da ese "
        "permiso es otra cosa y vive en Grupo_Empresa_Permiso, que sí es "
        "por empresa."
    ),
    "prov_modulo_dependencia": (
        "Catálogo del proveedor: qué módulo necesita a cuál (Farmacia "
        "depende de Inventario). Son pares de filas de prov_modulo_sistema, "
        "que tampoco es tenant."
    ),
    # ─── Tienen empresa, pero NO el manager estándar ───
    "conf_tipologia": (
        "Tiene manager propio (`TipologiaManager`): además de lo de la "
        "empresa deja ver el catálogo de fábrica y lo heredado de la casa "
        "matriz, y descuenta lo oculto. El TenantManager filtra por "
        "igualdad exacta y no serviría."
    ),
    "conf_tipologia_oculta": (
        "Tiene empresaId pero la escribe TAMBIÉN el proveedor desde su "
        "panel, sin empresa en el contexto. Con ModeloTenant el save() "
        "tomaría la empresa de un contexto vacío. El filtro lo pone el "
        "manager de Tipologia al excluir."
    ),
    "conf_empresa_agrupador": (
        "Tiene empresaId pero la escribe el PROVEEDOR sobre un cliente, no "
        "el cliente sobre sí mismo: es el permiso de ampliar una lista."
    ),
    "segu_grupo_empresa": (
        "Tiene empresaId pero manager propio (`GrupoEmpresaManager`), por lo "
        "mismo que conf_tipologia: un ROL es CONFIGURACIÓN y la configuración "
        "BAJA de la casa matriz a sus sucursales. El "
        "TenantManager filtra por igualdad exacta y dejaría a cada sucursal "
        "definiendo su propio 'Cajero'. Que la sucursal no pueda EDITAR el rol "
        "heredado lo valida el service, igual que en Tipologia."
    ),
    "idio_traduccion": (
        "Tiene manager propio (`TraduccionManager`), por lo mismo que "
        "conf_tipologia: deja ver las traducciones de fábrica y las "
        "heredadas de la casa matriz, y el TenantManager filtra por "
        "igualdad exacta. Y NO puede ser ModeloTenantDerivado aunque "
        "cuelgue de otra fila: el padre es POLIMÓRFICO (entidad_tipo es "
        "texto y entidad_id un número, sin FK), así que no hay ninguna "
        "RUTA_A_EMPRESA que seguir. Por eso lleva su propia columna."
    ),
}



HIJAS_SIN_EMPRESA = {}



HIJAS_CON_MANAGER_PROPIO = {
    "segu_grupo_empresa_permiso": (
        "No puede ser ModeloTenantDerivado: ese filtra por la empresa del "
        "padre con igualdad exacta, y con un rol heredado de la casa matriz "
        "la sucursal vería ese rol con CERO permisos, sin ningún error. "
        "Lleva `PermisoDeGrupoManager`, que filtra por "
        "VISIBILIDAD del rol delegando en `GrupoEmpresa.objects`. "
        "Lo comprueba: dominios/seguridad/tests/test_roles.py::"
        "test_otro_cliente_no_ve_los_permisos_del_rol"
    ),
}


def _modelos_del_proyecto():
    return [
        m
        for m in apps.get_models()
        if m._meta.app_config.name.startswith(PREFIJOS_DEL_PROYECTO)
    ]


def _lleva_empresa(modelo) -> bool:
    """
    ¿Esta tabla tiene la columna sobre la que se aplica el filtro?

    No alcanza con preguntar si hereda `ModeloTenant`: `conf_tipologia`,
    `conf_tipologia_oculta` y `conf_empresa_agrupador` declaran `empresa`
    a mano —porque necesitan otro manager— y para lo único que mira este
    test, que la columna exista, cuentan igual.
    """
    try:
        modelo._meta.get_field("empresa")
    except FieldDoesNotExist:
        return False
    return True


def _es_padre_aislado(modelo) -> bool:
    """
    ¿TODAS las filas de esta tabla son de un cliente?

    No alcanza con que tenga la columna: tiene que ser **obligatoria**. Y
    la diferencia no es teórica, `conf_tipologia` es el caso vivo — su
    `empresa` es nullable a propósito, porque la fila sin empresa es el
    catálogo de fábrica que ven todos los clientes.

    Si no se mirara la obligatoriedad, `Pais.estado → Tipologia` alcanzaría
    para declarar a `core_pais` "hija de una tabla aislada" y exigirle una
    columna que no le corresponde: apuntar a una tipología no convierte a
    un país en dato de un cliente. Lo que delata a una hija de verdad es
    colgar de una tabla donde **toda** fila tiene dueño.
    """
    if not _lleva_empresa(modelo):
        return False
    return not modelo._meta.get_field("empresa").null


def _padres_aislados(modelo):
    """
    Las FK de `modelo` que apuntan a una tabla donde toda fila tiene dueño.

    Se saltean dos casos que no son "colgar de un padre aislado":

    - **el campo `empresa`**: esa FK ES la columna del filtro, no un padre
      del que se pueda deducir nada.
    - **la auto-referencia** (`empresa_padre`, `division_superior`): el
      padre es la misma tabla, así que o las dos llevan la columna o
      ninguna — nunca es el caso que se persigue acá.
    """
    for campo in modelo._meta.concrete_fields:
        if not campo.is_relation or campo.name == "empresa":
            continue
        padre = campo.related_model
        if padre is modelo or not _es_padre_aislado(padre):
            continue
        yield campo, padre


def test_toda_tabla_esta_protegida_o_esta_declarada_como_excepcion():
    sin_declarar = []

    for modelo in _modelos_del_proyecto():
        if issubclass(modelo, (ModeloTenant, ModeloTenantDerivado)):
            continue
        tabla = modelo._meta.db_table
        if tabla not in EXCEPCIONES and tabla not in HIJAS_CON_MANAGER_PROPIO:
            sin_declarar.append(f"{modelo.__name__} (tabla {tabla})")

    assert not sin_declarar, (
        "Estos modelos no heredan de ModeloTenant ni de ModeloTenantDerivado, "
        "y tampoco están declarados como excepción, así que sus filas no se "
        "filtran por empresa: "
        + ", ".join(sorted(sin_declarar))
        + ". Si guardan datos de un cliente: heredá ModeloTenant si la tabla "
        "lleva empresaId propio, o ModeloTenantDerivado + RUTA_A_EMPRESA si "
        "cuelga de otra que ya está aislada. Si son un catálogo del proveedor, "
        "declaralos en EXCEPCIONES con el motivo, en "
        "core/tests/test_red_de_seguridad.py. Y si es una hija que se aísla "
        "con un manager propio —porque las dos opciones de arriba no sirven—, "
        "va en HIJAS_CON_MANAGER_PROPIO, nombrando en el motivo el test que "
        "lo comprueba."
    )


def test_toda_hija_de_una_tabla_aislada_esta_protegida():
    huerfanas = []

    for modelo in _modelos_del_proyecto():
        if _lleva_empresa(modelo):
            continue
        if issubclass(modelo, ModeloTenantDerivado):
            
            continue
        if modelo._meta.db_table in HIJAS_SIN_EMPRESA:
            continue
        if modelo._meta.db_table in HIJAS_CON_MANAGER_PROPIO:
         
            continue
        for campo, padre in _padres_aislados(modelo):
            huerfanas.append(
                f"{modelo.__name__} (tabla {modelo._meta.db_table}) cuelga de "
                f"{padre.__name__} por .{campo.name}"
            )

    assert not huerfanas, (
        "Estas tablas cuelgan de una tabla aislada y no están protegidas: "
        + "; ".join(sorted(huerfanas))
        + ". Un .objects.all() sobre ellas devuelve las filas de TODOS los "
        "clientes, sin error y con datos. Elegí una:\n"
        "  · heredar ModeloTenantDerivado y declarar RUTA_A_EMPRESA con el "
        "camino al padre (lo normal para una tabla de detalle)\n"
        "  · heredar ModeloTenant, si la tabla lleva empresaId propio\n"
        "Que el padre ya esté aislado NO alcanza por sí solo, y NO es motivo "
        "válido para declararla en HIJAS_SIN_EMPRESA."
    )


def test_no_hay_excepciones_de_tablas_que_ya_no_existen():
    tablas = {m._meta.db_table for m in _modelos_del_proyecto()}
    declaradas = set(EXCEPCIONES) | set(HIJAS_SIN_EMPRESA) | set(HIJAS_CON_MANAGER_PROPIO)
    fantasmas = [t for t in declaradas if t not in tablas]

    assert not fantasmas, (
        f"Estas tablas están declaradas como excepción y ya no existen: "
        f"{sorted(fantasmas)}. Sacalas de la lista."
    )


def test_ninguna_excepcion_esta_ya_protegida():
    contradicciones = [
        m._meta.db_table
        for m in _modelos_del_proyecto()
        if issubclass(m, (ModeloTenant, ModeloTenantDerivado))
        and m._meta.db_table in EXCEPCIONES
    ]

    assert not contradicciones, (
        f"Estas tablas ya están protegidas y además figuran como excepción: "
        f"{sorted(contradicciones)}. Sacalas de la lista."
    )


def test_ninguna_hija_declarada_lleva_ya_su_empresa():
    sobran = [
        m._meta.db_table
        for m in _modelos_del_proyecto()
        if m._meta.db_table in HIJAS_SIN_EMPRESA and _lleva_empresa(m)
    ]

    assert not sobran, (
        f"Estas tablas llevan empresa y además figuran en HIJAS_SIN_EMPRESA: "
        f"{sorted(sobran)}. Sacalas de la lista."
    )


def test_ninguna_tabla_esta_en_las_dos_listas():
    pares = (
        set(EXCEPCIONES) & set(HIJAS_SIN_EMPRESA),
        set(EXCEPCIONES) & set(HIJAS_CON_MANAGER_PROPIO),
        set(HIJAS_SIN_EMPRESA) & set(HIJAS_CON_MANAGER_PROPIO),
    )
    repetidas = pares[0] | pares[1] | pares[2]

    assert not repetidas, (
        f"Estas tablas están declaradas en las dos listas: {sorted(repetidas)}. "
        f"Dejala en la que corresponda al motivo real y sacala de la otra."
    )


_MOTIVOS = sorted(
    [("EXCEPCIONES", t, m) for t, m in EXCEPCIONES.items()]
    + [("HIJAS_SIN_EMPRESA", t, m) for t, m in HIJAS_SIN_EMPRESA.items()]
    + [
        ("HIJAS_CON_MANAGER_PROPIO", t, m)
        for t, m in HIJAS_CON_MANAGER_PROPIO.items()
    ]
)


@pytest.mark.parametrize("tabla", sorted(HIJAS_CON_MANAGER_PROPIO))
def test_las_hijas_con_manager_propio_lo_tienen_de_verdad(tabla):
    modelo = next(
        m for m in _modelos_del_proyecto() if m._meta.db_table == tabla
    )
    manager = modelo._meta.default_manager

    assert type(manager) is not models.Manager, (
        f"'{tabla}' está declarada en HIJAS_CON_MANAGER_PROPIO pero usa el "
        f"Manager pelado de Django, así que NO filtra nada: un "
        f"{modelo.__name__}.objects.all() devuelve las filas de todos los "
        f"clientes. Escribile el manager o usá ModeloTenantDerivado."
    )


@pytest.mark.parametrize("lista,tabla,motivo", _MOTIVOS)
def test_cada_excepcion_tiene_un_motivo_de_verdad(lista, tabla, motivo):
    assert len(motivo.strip()) >= 30, (
        f"La excepción de '{tabla}' en {lista} no explica nada: '{motivo}'. "
        f"Escribí por qué esa tabla NO lleva datos de un cliente."
    )


def test_las_tablas_tenant_tienen_su_columna_empresa():
    for modelo in _modelos_del_proyecto():
        if not issubclass(modelo, ModeloTenant):
            continue

        campo = modelo._meta.get_field("empresa")

        assert not campo.null, (
            f"{modelo.__name__}.empresa admite NULL. Una fila sin empresa no "
            f"la ve nadie… hasta que alguien consulta sin filtro."
        )
        assert not campo.editable, (
            f"{modelo.__name__}.empresa es editable. Tiene que salir del "
            f"contexto, nunca de un formulario."
        )


def test_hay_al_menos_una_tabla_tenant():
    """Si un refactor dejara a `ModeloTenant` sin herederos, todos los tests
    de arriba pasarían triviales y nadie se enteraría."""
    tenant = [m for m in _modelos_del_proyecto() if issubclass(m, ModeloTenant)]

    assert tenant, "No quedó ninguna tabla heredando de ModeloTenant."





@isolate_apps("comun.tipologias")
def test_el_detector_agarra_una_hija_sin_empresa():

    class Empresa(models.Model):
        class Meta:
            app_label = "tipologias"

    class Pedido(models.Model):
        empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="+")

        class Meta:
            app_label = "tipologias"

    class DetallePedido(models.Model):
        pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "tipologias"

    assert _es_padre_aislado(Pedido), (
        "Pedido tiene empresa obligatoria y el detector no lo reconoce como "
        "padre aislado. Sin eso, nada de lo de abajo puede funcionar."
    )

    padres = [padre.__name__ for _, padre in _padres_aislados(DetallePedido)]

    assert padres == ["Pedido"], (
        f"El detector no vio que DetallePedido cuelga de Pedido sin llevar "
        f"empresa. Devolvió {padres}. Mientras esto falle, el test de las "
        f"hijas está verde por no encontrar nada, no por estar bien."
    )


@isolate_apps("comun.tipologias")
def test_el_detector_no_agarra_a_las_hijas_de_un_catalogo_compartido():

    class Empresa(models.Model):
        class Meta:
            app_label = "tipologias"

    class CatalogoCompartido(models.Model):
        empresa = models.ForeignKey(
            Empresa,
            null=True,
            blank=True,
            on_delete=models.CASCADE,
            related_name="+",
        )

        class Meta:
            app_label = "tipologias"

    class Pais(models.Model):
        estado = models.ForeignKey(
            CatalogoCompartido, on_delete=models.PROTECT, related_name="+"
        )

        class Meta:
            app_label = "tipologias"

    assert not _es_padre_aislado(CatalogoCompartido), (
        "Un catálogo con empresa NULLABLE no es un padre aislado: su fila sin "
        "empresa la ven todos los clientes."
    )

    padres = [padre.__name__ for _, padre in _padres_aislados(Pais)]

    assert padres == [], (
        f"El detector trató a un catálogo compartido como padre aislado y "
        f"reportó {padres}. Tener la columna no alcanza: si es nullable, la "
        f"fila sin empresa la ven todos, y colgar de ahí no convierte a nadie "
        f"en dato de un cliente."
    )


@isolate_apps("comun.tipologias")
def test_el_detector_no_reporta_una_auto_referencia():

    class Empresa(models.Model):
        class Meta:
            app_label = "tipologias"

    class Categoria(models.Model):
        empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="+")
        padre = models.ForeignKey(
            "self", null=True, blank=True, on_delete=models.PROTECT, related_name="+"
        )

        class Meta:
            app_label = "tipologias"

    padres = [padre.__name__ for _, padre in _padres_aislados(Categoria)]

    assert padres == [], (
        f"El detector reportó {padres} por una FK de la tabla a sí misma. Una "
        f"jerarquía dentro de la misma tabla no es una hija sin columna."
    )
