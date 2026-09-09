"""
Las URLs del backend.

`/admin/`    — administración de Django
`/graphql/`  — la API. Solo se monta si `GRAPHQL_HABILITADO`.

Por qué el interruptor: todavía no hay login ni middleware de tenancy,
así que lo que se exponga queda abierto a cualquiera que llegue al
puerto. Se habilita en `local` para poder desarrollar y probar, y queda
apagado en `production` hasta que exista la autenticación.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import GraphQLView

from config.schema import schema

urlpatterns = [
    path("admin/", admin.site.urls),
]

if settings.GRAPHQL_HABILITADO:
    urlpatterns += [
        path(
            "graphql/",
            #
            csrf_exempt(
                GraphQLView.as_view(
                    schema=schema,

                    graphql_ide="graphiql" if settings.DEBUG else None,
                )
            ),
        ),
    ]
