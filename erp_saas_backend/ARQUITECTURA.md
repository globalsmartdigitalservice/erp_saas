# Arquitectura del backend

Este documento explica **dónde vive cada cosa y por qué**. Si vas a escribir
un módulo nuevo, leelo entero una vez: son quince minutos y te ahorra los tres
o cuatro errores que el proyecto detecta con tests y que si no vas a descubrir
cuando algo se ponga rojo sin que sepas por qué.

Es un ERP **multiempresa (SaaS)**: una sola instalación atiende a muchos
clientes, y los datos de uno no pueden verse desde otro. Casi todas las
decisiones raras de acá abajo salen de esa frase.

---

## 1. Las capas

En la raíz hay siete carpetas. Cuatro tienen código hoy y tres están
reservadas:

```
core/            CAPA 1   infraestructura sin negocio
comun/           CAPA 2   lo que usa todo el ERP
servicios/       CAPA 3   servicios de plataforma
dominios/        CAPA 4   el negocio

procesos/                 (reservada) procesos largos: cierres, importaciones
complementos/             (reservada) integraciones opcionales
proveedor/                (reservada) el panel del proveedor del SaaS
```

Y aparte:

```
config/          settings, el schema raíz de GraphQL, las urls
requirements/    las dependencias
```

### Qué va en cada una

**`core/` — CAPA 1.** Mecanismos, no reglas de negocio. No sabe qué es una
venta ni un cliente. Hoy tiene:

| | |
|---|---|
| `core/tenancy/` | el aislamiento entre empresas. **Lo más importante del proyecto.** |
| `core/graphql/` | qué se le cuenta al cliente cuando algo falla, y la paginación que ve el frontend |
| `core/idioma/` | en qué idioma se está mostrando el sistema |
| `core/red.py` | de qué IP viene una petición |
| `core/paginacion.py` | cortar una lista larga en páginas |
| `core/tests/` | las redes de seguridad que vigilan a todo el proyecto |

**`comun/` — CAPA 2.** Tablas que usan todos los módulos. Empresas, usuarios,
membresías, tipologías, geografía, monedas, idiomas, catálogo de módulos,
tipos de documento.

**`servicios/` — CAPA 3.** Servicios de plataforma que un dominio consume pero
que no son de ningún dominio: la numeración de documentos, las referencias
cruzadas entre módulos.

**`dominios/` — CAPA 4.** El negocio. Hoy `entidades` (clientes, proveedores)
y `seguridad` (roles y permisos). Acá van a vivir ventas, compras, inventario
y los demás.

### La regla que ordena todo: las dependencias solo bajan

Una app puede usar las capas de número **menor**, nunca las de número mayor.
`dominios/ventas` puede importar de `comun/empresas`; al revés no.

De ahí salen dos cosas que vas a ver en el código y que si no las conocés
parecen caprichos:

**Las FK de `core/` se declaran por nombre, no importando la clase:**

```python
# core/tenancy/modelos.py
empresa = models.ForeignKey("empresas.Empresa", ...)   # ← el string, no la clase
```

Importar `Empresa` sería que CAPA 1 dependa de CAPA 2. Django resuelve el
nombre al arrancar y en la base queda una FK real igual.

**Si una tabla recibe una FK desde una capa más baja, la tabla sube de capa.**
Es lo que le pasó a `comun/tipos_documento`: nació en un dominio, pero
`servicios/numeracion` (CAPA 3) le apunta, y una dependencia hacia arriba
rompería la regla. Lo mismo con `Entidad` y `Licencia`.

⚠️ El nombre de la tabla en la base **conserva el prefijo de su módulo de
origen** (`vent_tipo_documento`), no el de la carpeta donde vive. La app se
movió por una regla de capas; la tabla sigue siendo del módulo de ventas.

---

## 2. Cómo está armada una app

Todas tienen la misma forma. Ésta es `dominios/entidades/`:

```
dominios/entidades/
├── models/          las tablas
├── repository/      las consultas. SIN reglas de negocio
├── services/        las reglas de negocio: valida y escribe
├── api.py           la superficie pública
├── graphql/         types, inputs, queries, mutations
└── tests/
```

### Qué hace cada capa, en una línea

| Carpeta | Su trabajo | Lo que NO hace |
|---|---|---|
| `models/` | declarar la tabla y sus constraints | validar reglas que la base no puede |
| `repository/` | consultar y escribir en la base | decidir si algo se puede hacer |
| `services/` | los invariantes: valida y después escribe | consultar directo, saltándose el repository |
| `api.py` | lo único que ven las otras apps | tener lógica propia: delega |
| `graphql/` | traducir de HTTP al dominio y viceversa | decidir nada; llama a `api.py` |

### `api.py` es la única puerta

Otra app escribe:

```python
from comun.empresas import api as empresas

ambito = empresas.ids_del_ambito(empresa_id)
```

**Nunca** `from comun.empresas.repository import ...`. El interior de una app
se puede reescribir entero mientras `api.py` responda igual.

### Toda consulta tiene versión por lote

Por cada `obtener_x(id)` hay un `obtener_varios_x(ids)`. **Es obligatorio.**

```python
def obtener_empresa(empresa_id: int) -> Empresa | None: ...
def obtener_empresas(empresa_ids) -> dict[int, Empresa]: ...
```

El motivo es el N+1: en GraphQL, una consulta que devuelve 400 filas y
resuelve un campo por cada una dispara 401 consultas. Con la versión por lote
son 2.

⚠️ El proyecto **no usa DataLoader**: el batch se arma a mano en la capa de
queries, y los tipos de GraphQL reciben todo ya resuelto. Un `type` que salga
a buscar datos por su cuenta es justamente el error que esto evita. Hay tests
que cuentan consultas y se ponen rojos si aparece.

---

## 3. El aislamiento entre empresas

Es lo que hay que entender antes de escribir la primera tabla.

Los datos de un cliente no pueden verse desde otro, y **el filtro no se
escribe a mano**. Si dependiera de que el desarrollador se acuerde, un solo
olvido sería una fuga de datos entre clientes.

Una tabla que guarda datos de un cliente hereda de `ModeloTenant`:

```python
class Venta(ModeloTenant):     # trae empresa_id y filtra sola
    ...

class Pais(models.Model):      # global: igual para todos los clientes
    ...
```

`ModeloTenant` aporta tres cosas: la columna `empresa`, un manager que le
agrega `WHERE empresa_id = ...` a **cada** consulta, y un `save()` que
completa la empresa desde el contexto de la petición.

### Cuando la tabla cuelga de otra que ya está aislada

No se repite la columna: la empresa se **deriva** siguiendo el camino al
padre.

```python
class DetallePedido(ModeloTenantDerivado):
    RUTA_A_EMPRESA = "pedido"          # admite saltos: "documento__pedido"
    pedido = models.ForeignKey("ventas.Pedido", ...)
```

Son unas 79 tablas de detalle en todo el ERP. Repetirles la columna sería
desnormalizar.

### La empresa activa vive en un `ContextVar`

No en una variable global ni en un thread-local. El servidor es ASGI y un
mismo hilo atiende varias peticiones a la vez: con un thread-local, la empresa
de un usuario se le mezclaría a otro — exactamente la fuga que todo esto
evita.

### Sin empresa activa, revienta

Consultar una tabla con empresa cuando no hay empresa en el contexto lanza
`SinEmpresaEnContexto`. **No devuelve vacío a propósito:** un listado vacío se
confunde con "este cliente no tiene datos" y puede costar días encontrarlo. Un
error se ve en el momento.

Cuando de verdad hay que cruzar empresas —el login, que consulta a qué
empresas pertenece alguien antes de saber cuál es— existe una puerta de
salida que se escribe a mano y por eso es auditable:

```python
with sin_filtro_de_empresa():
    membresias = UsuarioEmpresa.objects.filter(usuario=usuario)
```

### La red de seguridad

`core/tests/test_red_de_seguridad.py` recorre **todos** los modelos del
proyecto y le exige a cada uno una de dos cosas: o hereda de una de las clases
tenant, o está declarado ahí con el motivo escrito de por qué no.

Si tu tabla nueva lo pone rojo, preguntate: **¿esto guarda datos de un
cliente?**

```
Sí, y lleva su propia columna      → ModeloTenant
Sí, pero cuelga de otra aislada    → ModeloTenantDerivado + RUTA_A_EMPRESA
No, es catálogo del proveedor      → declaralo en EXCEPCIONES, con el motivo
```

Que el motivo sea obligatorio es la mitad del valor: agregar una tabla a esa
lista es escribir en voz alta *"esta tabla la ven todos los clientes, y lo
hago a propósito"*. Nadie escribe eso por accidente; el olvido, en cambio, es
silencioso.

⚠️ **Hasta dónde llega:** protege lo que pasa por el ORM. Una consulta en SQL
crudo lo esquiva.

---

## 4. Las listas del sistema (tipologías)

Todas las listas cortas del ERP —rubros, estados, formas de pago, tipos de
documento— viven en **una sola tabla**, `Tipologia`, agrupadas por un número.
Es el patrón OTLT, y tiene una contra: la base **no puede** validar que el
rubro de una empresa sea realmente un rubro. Un número equivocado no da error,
mezcla catálogos en silencio.

Por eso en el código nunca va un número suelto:

```python
✘  Tipologia.objects.filter(agrupador=1)
✔  Tipologia.de(AGRUPADOR.RUBRO)
```

Los agrupadores están en `comun/tipologias/constantes.py`. Se agregan al final
con el siguiente número libre, y un valor ya usado **nunca** se reutiliza ni se
renumera: quedarían filas apuntando al significado viejo.

Si tu tabla tiene un campo `estado`, casi seguro va al `ESTADO_REGISTRO`
compartido. Solo lleva agrupador propio si su estado significa algo del
negocio: `Empresa` tiene "SUSPENDIDA", un cheque tendrá "GIRADO".

⚠️ Un agrupador nuevo necesita su **cabecera en la semilla**
(`cargar_tipologias.py`) o la lista no tiene nombre que mostrar. Hay un test
que lo vigila.

---

## 5. Cómo agregar un módulo nuevo

Seis pasos. Los tres últimos son los que se descubren cuando un test se pone
rojo, así que conviene tenerlos presentes antes.

**1. Copiá la estructura de una app que ya exista.** `dominios/entidades/` es
la referencia completa: tiene modelos con y sin derivación, servicios con
invariantes, la capa GraphQL entera y sus tests.

**2. Registrala en `config/settings/base.py`**, en `APPS_PROPIAS` y en la capa
que le corresponda. Va con su ruta completa (`dominios.ventas`); las carpetas
de agrupación no son apps.

**3. Enchufala al schema** en `config/schema.py`: dos imports y dos nombres en
las listas de herencia de `Query` y `Mutation`.

⚠️ Los nombres de los campos de GraphQL son **globales**: todas las apps se
fusionan en una sola `Query`. Con 40 módulos, dos que definan `listar` chocan.
La convención es sustantivo específico: `ventas`, `facturas`, nunca genéricos.

**4. Tus modelos heredan de `ModeloTenant` o `ModeloTenantDerivado`.** Si no,
`test_red_de_seguridad` se pone rojo y te dice exactamente qué falta.

**5. Si tenés un campo `estado`**, usá el `ESTADO_REGISTRO` compartido. Si de
verdad necesitás uno propio, agregá el agrupador en `constantes.py` y su
cabecera en la semilla.

**6. Cada `obtener_x` necesita su `obtener_varios_x`**, y los tipos de GraphQL
reciben los datos ya resueltos. Si no, el test que cuenta consultas se pone
rojo.

### Los tests que te van a frenar, y qué significan

| Test | Se pone rojo cuando | Qué hacer |
|---|---|---|
| `test_red_de_seguridad` | una tabla nueva no está aislada ni declarada | elegir entre las tres opciones de arriba |
| `test_tenancy_derivado` | `RUTA_A_EMPRESA` está mal escrita | revisar el camino al padre |
| `test_referencias_pendientes` | apareció la tabla que faltaba para una FK que quedó como entero | decidir si ahora sí se convierte en FK |
| `test_traducciones_enchufadas` | una tabla traducible cuyo GraphQL no pide traducciones | copiar el patrón de `tipologias/graphql/queries.py` |
| los `django_assert_num_queries` | volvió a entrar un N+1 | agregar el `select_related` o la versión por lote |

Ninguno de esos tests existe para molestar: los cinco vigilan fallas que **no
dan error** — devuelven datos, la pantalla anda, y el problema aparece meses
después.

---

## 6. Los permisos

Cada mutation declara qué permiso necesita, y el comando los genera:

```python
@auto_permisos(recurso="VENTAS_FACTURAS")
class VentasMutations:
    def emitir_factura(self, ...): ...     → ventas_facturas_emitir_factura
    def anular_factura(self, ...): ...     → ventas_facturas_anular_factura
```

```
python manage.py generar_permisos
```

`recurso` es el `codigo` de un `Sub_Modulo` —la pantalla—, que es el
identificador estable: el nombre y la ruta cambian, y los permisos ya emitidos
no se pueden mover con ellos.

Proteger es otra cosa y va aparte. **Los dos decoradores, siempre, y el código
del permiso escrito**:

```python
@strawberry.mutation(description="...")
@requiere_autenticacion
@requiere_permiso("ventas_facturas_emitir_factura")
def emitir_factura(self, info: strawberry.Info, ...): ...
```

El código se lee arriba de la función, sin ir a buscar de dónde sale. Escribirlo
es la convención aunque `@requiere_permiso` a secas también funcione: lo deduce
del `recurso` de la clase más el nombre del método, que da lo mismo.

⚠️ **La firma necesita `info: strawberry.Info`**, y no es opcional: de ahí sale
quién está llamando. Sin él, el guard corta con un error que lo dice.

⚠️ **El permiso tiene que existir en la base**, o la operación le da `FORBIDDEN`
a todo el mundo, incluido el administrador. Lo crea `generar_permisos`, así que
después de agregar una operación hay que volver a correrlo.

⚠️ **El orden importa:** `@strawberry.mutation` va siempre arriba de todo. Si
quedara debajo, Strawberry registraría la función sin envolver y los guards no
correrían, sin dar ningún error.

⚠️ **Una mutation sin guards funciona igual.** Es deliberado: se construye
primero y se protege al final, cuando el módulo está terminado.

---

## 7. Cómo se escribe

**Comentarios.** Explican el **por qué**, no el qué. Si repiten lo que dice la
línea de abajo, sobran. Se comenta lo que falla **en silencio**; lo que se
rompe a los gritos ya avisa solo. El historial lo guarda git: en el código no
van fechas, ni qué cambió, ni cómo era antes.

**Tests.** Un test se justifica si la falla que previene sería silenciosa. Si
algo se rompe de forma ruidosa —un import que no existe, un tipo que no
compila— el test no agrega nada. Las convenciones se explican, no se testean.

**Mensajes de error.** Los redacta el backend, no el frontend, y están
escritos para no delatar datos de otras empresas: *"no existe la categoría
412"*, nunca *"esa categoría no es tuya"*. El segundo le confirma a un extraño
que el id existe.

---

## Dónde mirar cuando algo no cierra

| Pregunta | Archivo |
|---|---|
| ¿cómo se aísla una tabla? | `core/tenancy/modelos.py` |
| ¿de dónde sale la empresa activa? | `core/tenancy/contexto.py` |
| ¿cómo se ve una app completa? | `dominios/entidades/` |
| ¿cómo se arma un service con invariantes? | `comun/empresas/services/empresa.py` |
| ¿cómo se evita el N+1 en GraphQL? | `comun/tipologias/graphql/queries.py` |
| ¿qué pasa cuando algo falla? | `core/graphql/errores.py` |
