from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, APITestCase

from .models import Rol
from .permisos import (
    MATRIZ,
    Operacion,
    PermisoPorMetodo,
    operaciones_de,
    requiere,
    tiene_permiso,
)

Usuario = get_user_model()
PASSWORD = "ClaveSegura123"


# Utilidades
def crear_usuario(username, rol=Rol.CIENTIFICO_DATOS, **extra):
    extra.setdefault("email", f"{username}@biodynamics.test")
    return Usuario.objects.create_user(username=username, password=PASSWORD, rol=rol, **extra)


def resultados(respuesta):
    """Devuelve la lista de resultados con o sin paginación."""
    datos = respuesta.data
    return datos["results"] if isinstance(datos, dict) and "results" in datos else datos


class BaseAPITest(APITestCase):
    """Crea un usuario por cada rol y permite autenticarse como cualquiera."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = crear_usuario("admin1", Rol.ADMINISTRADOR, departamento="TI")
        cls.po = crear_usuario("po1", Rol.PRODUCT_OWNER, departamento="Producto")
        cls.ing = crear_usuario("ing1", Rol.INGENIERO_DATOS, departamento="Datos")
        cls.mlops = crear_usuario("mlops1", Rol.ML_OPERATOR, departamento="ML")
        cls.cient = crear_usuario("cient1", Rol.CIENTIFICO_DATOS, departamento="Datos")

    def autenticar(self, usuario):
        token, _ = Token.objects.get_or_create(user=usuario)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return token

    def assertNoAutenticado(self, respuesta):
        # 401 con TokenAuthentication primero; 403 si DRF cae en otra clase.
        self.assertIn(
            respuesta.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )


# Modelo
class UsuarioModeloTests(TestCase):
    def test_rol_por_defecto_es_el_de_menos_permisos(self):
        usuario = Usuario.objects.create_user("nuevo", "nuevo@x.test", PASSWORD)
        self.assertEqual(usuario.rol, Rol.CIENTIFICO_DATOS)

    def test_createsuperuser_asigna_rol_administrador(self):
        su = Usuario.objects.create_superuser("root", "root@x.test", PASSWORD)
        self.assertEqual(su.rol, Rol.ADMINISTRADOR)
        self.assertTrue(su.is_superuser)

    def test_createsuperuser_respeta_rol_explicito(self):
        su = Usuario.objects.create_superuser(
            "root2", "root2@x.test", PASSWORD, rol=Rol.PRODUCT_OWNER
        )
        self.assertEqual(su.rol, Rol.PRODUCT_OWNER)

    def test_email_es_unico(self):
        crear_usuario("a", email="repetido@x.test")
        with self.assertRaises(IntegrityError), transaction.atomic():
            crear_usuario("b", email="repetido@x.test")

    def test_str_incluye_username_y_rol(self):
        usuario = crear_usuario("ana", Rol.PRODUCT_OWNER)
        self.assertEqual(str(usuario), "ana (Product Owner)")

    def test_cinco_roles_definidos(self):
        self.assertEqual(
            {r.value for r in Rol},
            {
                "administrador",
                "product_owner",
                "ingeniero_datos",
                "ml_operator",
                "cientifico_datos",
            },
        )


# Matriz de permisos (lógica pura)
class MatrizPermisosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.por_rol = {rol: crear_usuario(f"u_{rol.value}", rol) for rol in Rol}

    def roles_con_permiso(self, operacion):
        return {r for r, u in self.por_rol.items() if tiene_permiso(u, operacion)}

    def test_toda_operacion_esta_en_la_matriz(self):
        for op in Operacion:
            with self.subTest(op=op):
                self.assertIn(op, MATRIZ)

    def test_no_existe_operacion_para_modificar_auditoria(self):
        valores = {op.value for op in Operacion}
        self.assertNotIn("modificar_auditoria", valores)

    def test_consultas_abiertas_a_todos_los_roles(self):
        for op in (
            Operacion.CONSULTAR_DATASETS,
            Operacion.CONSULTAR_MODELOS,
            Operacion.COMPARAR_MODELOS,
            Operacion.REGISTRAR_OBSERVACIONES,
        ):
            with self.subTest(op=op):
                self.assertEqual(self.roles_con_permiso(op), set(Rol))

    def test_gestionar_usuarios_solo_administrador(self):
        self.assertEqual(self.roles_con_permiso(Operacion.GESTIONAR_USUARIOS), {Rol.ADMINISTRADOR})

    def test_aprobar_y_cambiar_estado_solo_admin_y_po(self):
        esperado = {Rol.ADMINISTRADOR, Rol.PRODUCT_OWNER}
        self.assertEqual(self.roles_con_permiso(Operacion.APROBAR_MODELOS), esperado)
        self.assertEqual(self.roles_con_permiso(Operacion.CAMBIAR_ESTADO_MODELOS), esperado)

    def test_registrar_datasets_versiones_y_metadatos_admin_e_ingeniero(self):
        esperado = {Rol.ADMINISTRADOR, Rol.INGENIERO_DATOS}
        for op in (
            Operacion.REGISTRAR_DATASETS,
            Operacion.MODIFICAR_METADATOS,
            Operacion.REGISTRAR_VERSIONES,
            Operacion.MONITOREAR_INTEGRACION,
            Operacion.CONFIGURAR_ALMACENAMIENTO,
        ):
            with self.subTest(op=op):
                self.assertEqual(self.roles_con_permiso(op), esperado)

    def test_ejecutar_pruebas_admin_po_y_mlops(self):
        self.assertEqual(
            self.roles_con_permiso(Operacion.EJECUTAR_PRUEBAS),
            {Rol.ADMINISTRADOR, Rol.PRODUCT_OWNER, Rol.ML_OPERATOR},
        )

    def test_consultar_auditoria_admin_po_e_ingeniero(self):
        self.assertEqual(
            self.roles_con_permiso(Operacion.CONSULTAR_AUDITORIA),
            {Rol.ADMINISTRADOR, Rol.PRODUCT_OWNER, Rol.INGENIERO_DATOS},
        )

    def test_cientifico_solo_lee_compara_y_observa(self):
        permitidas = set(operaciones_de(self.por_rol[Rol.CIENTIFICO_DATOS]))
        self.assertEqual(
            permitidas,
            {
                Operacion.CONSULTAR_DATASETS.value,
                Operacion.CONSULTAR_MODELOS.value,
                Operacion.COMPARAR_MODELOS.value,
                Operacion.REGISTRAR_OBSERVACIONES.value,
            },
        )

    def test_usuario_anonimo_o_none_sin_permiso(self):
        from django.contrib.auth.models import AnonymousUser

        self.assertFalse(tiene_permiso(AnonymousUser(), Operacion.CONSULTAR_DATASETS))
        self.assertFalse(tiene_permiso(None, Operacion.CONSULTAR_DATASETS))

    def test_usuario_inactivo_sin_permiso_aunque_su_rol_lo_tenga(self):
        admin = self.por_rol[Rol.ADMINISTRADOR]
        admin.is_active = False
        self.assertFalse(tiene_permiso(admin, Operacion.GESTIONAR_USUARIOS))

    def test_operacion_desconocida_se_rechaza(self):
        self.assertFalse(tiene_permiso(self.por_rol[Rol.ADMINISTRADOR], "inventada"))

    def test_operaciones_de_esta_ordenada_y_es_lista_de_strings(self):
        ops = operaciones_de(self.por_rol[Rol.ADMINISTRADOR])
        self.assertEqual(ops, sorted(ops))
        self.assertEqual(len(ops), len(Operacion))  # el admin puede todo
        self.assertTrue(all(isinstance(o, str) for o in ops))


class ClasesDePermisoDRFTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = crear_usuario("adm", Rol.ADMINISTRADOR)
        cls.cient = crear_usuario("cie", Rol.CIENTIFICO_DATOS)
        cls.ing = crear_usuario("ing", Rol.INGENIERO_DATOS)

    def peticion(self, metodo, usuario):
        req = getattr(APIRequestFactory(), metodo.lower())("/x/")
        req.user = usuario
        return req

    def test_requiere_permite_y_niega_segun_rol(self):
        permiso = requiere(Operacion.GESTIONAR_USUARIOS)()
        self.assertTrue(permiso.has_permission(self.peticion("GET", self.admin), None))
        self.assertFalse(permiso.has_permission(self.peticion("GET", self.cient), None))

    def test_requiere_nombra_la_clase_con_la_operacion(self):
        clase = requiere(Operacion.APROBAR_MODELOS)
        self.assertIn("aprobar_modelos", clase.__name__)

    def test_permiso_por_metodo(self):
        class Vista:
            operaciones = {
                "GET": Operacion.CONSULTAR_DATASETS,
                "POST": Operacion.REGISTRAR_DATASETS,
            }

        permiso = PermisoPorMetodo()
        # Científico: puede GET (y HEAD/OPTIONS se tratan como GET), no POST.
        self.assertTrue(permiso.has_permission(self.peticion("GET", self.cient), Vista))
        self.assertTrue(permiso.has_permission(self.peticion("HEAD", self.cient), Vista))
        self.assertTrue(permiso.has_permission(self.peticion("OPTIONS", self.cient), Vista))
        self.assertFalse(permiso.has_permission(self.peticion("POST", self.cient), Vista))
        # Ingeniero: puede POST.
        self.assertTrue(permiso.has_permission(self.peticion("POST", self.ing), Vista))

    def test_permiso_por_metodo_rechaza_metodo_no_declarado(self):
        class Vista:
            operaciones = {"GET": Operacion.CONSULTAR_DATASETS}

        permiso = PermisoPorMetodo()
        self.assertFalse(permiso.has_permission(self.peticion("DELETE", self.admin), Vista))

    def test_permiso_por_metodo_sin_operaciones_rechaza(self):
        class VistaVacia:
            pass

        self.assertFalse(
            PermisoPorMetodo().has_permission(self.peticion("GET", self.admin), VistaVacia)
        )


# Login / logout / perfil
class LoginTests(BaseAPITest):
    def login(self, **datos):
        return self.client.post(reverse("auth-login"), datos, format="json")

    def test_login_correcto_devuelve_token_y_perfil(self):
        r = self.login(username="admin1", password=PASSWORD)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["token"], Token.objects.get(user=self.admin).key)
        self.assertEqual(r.data["usuario"]["username"], "admin1")
        self.assertEqual(r.data["usuario"]["rol"], Rol.ADMINISTRADOR)
        self.assertEqual(r.data["usuario"]["rol_nombre"], "Administrador")

    def test_login_incluye_operaciones_permitidas(self):
        r = self.login(username="cient1", password=PASSWORD)
        self.assertEqual(r.data["usuario"]["operaciones"], operaciones_de(self.cient))
        self.assertNotIn(Operacion.GESTIONAR_USUARIOS.value, r.data["usuario"]["operaciones"])

    def test_login_no_expone_password(self):
        r = self.login(username="admin1", password=PASSWORD)
        self.assertNotIn("password", r.data["usuario"])

    def test_login_repetido_reutiliza_el_mismo_token(self):
        t1 = self.login(username="po1", password=PASSWORD).data["token"]
        t2 = self.login(username="po1", password=PASSWORD).data["token"]
        self.assertEqual(t1, t2)
        self.assertEqual(Token.objects.filter(user=self.po).count(), 1)

    def test_password_incorrecta(self):
        r = self.login(username="admin1", password="mala")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data["detail"], "Usuario o contraseña incorrectos.")
        self.assertFalse(Token.objects.filter(user=self.admin).exists())

    def test_usuario_inexistente(self):
        r = self.login(username="fantasma", password=PASSWORD)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cuenta_inactiva_no_puede_entrar(self):
        self.ing.is_active = False
        self.ing.save()
        r = self.login(username="ing1", password=PASSWORD)
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_faltan_campos(self):
        self.assertEqual(self.login(username="admin1").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.login(password=PASSWORD).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.login().status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_no_requiere_autenticacion_previa(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token tokeninvalido")
        r = self.login(username="admin1", password=PASSWORD)
        self.assertIn(r.status_code, (status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED))

    def test_solo_post(self):
        r = self.client.get(reverse("auth-login"))
        self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class LogoutTests(BaseAPITest):
    def test_logout_borra_el_token(self):
        self.autenticar(self.admin)
        r = self.client.post(reverse("auth-logout"))
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=self.admin).exists())

    def test_token_ya_no_sirve_despues_del_logout(self):
        self.autenticar(self.admin)
        self.client.post(reverse("auth-logout"))
        r = self.client.get(reverse("auth-perfil"))
        self.assertNoAutenticado(r)

    def test_logout_sin_autenticar(self):
        self.assertNoAutenticado(self.client.post(reverse("auth-logout")))

    def test_logout_no_afecta_a_otros_usuarios(self):
        self.autenticar(self.po)
        Token.objects.create(user=self.cient)
        self.client.post(reverse("auth-logout"))
        self.assertTrue(Token.objects.filter(user=self.cient).exists())


class PerfilTests(BaseAPITest):
    def test_perfil_devuelve_datos_del_usuario_autenticado(self):
        self.autenticar(self.ing)
        r = self.client.get(reverse("auth-perfil"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["id"], self.ing.id)
        self.assertEqual(r.data["username"], "ing1")
        self.assertEqual(r.data["email"], "ing1@biodynamics.test")
        self.assertEqual(r.data["rol"], Rol.INGENIERO_DATOS)
        self.assertEqual(r.data["departamento"], "Datos")
        self.assertEqual(r.data["operaciones"], operaciones_de(self.ing))

    def test_perfil_requiere_autenticacion(self):
        self.assertNoAutenticado(self.client.get(reverse("auth-perfil")))

    def test_perfil_es_de_solo_lectura(self):
        self.autenticar(self.cient)
        r = self.client.patch(reverse("auth-perfil"), {"rol": "administrador"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.cient.refresh_from_db()
        self.assertEqual(self.cient.rol, Rol.CIENTIFICO_DATOS)


# Gestión de usuarios (solo Administrador)
class UsuarioViewSetPermisosTests(BaseAPITest):
    def test_anonimo_no_accede(self):
        self.assertNoAutenticado(self.client.get(reverse("usuario-list")))

    def test_roles_distintos_de_administrador_reciben_403(self):
        for usuario in (self.po, self.ing, self.mlops, self.cient):
            with self.subTest(rol=usuario.rol):
                self.autenticar(usuario)
                lista = self.client.get(reverse("usuario-list"))
                detalle = self.client.get(reverse("usuario-detail", args=[self.admin.id]))
                crear = self.client.post(
                    reverse("usuario-list"),
                    {"username": "x", "email": "x@x.test", "password": PASSWORD},
                    format="json",
                )
                borrar = self.client.delete(reverse("usuario-detail", args=[self.cient.id]))
                for r in (lista, detalle, crear, borrar):
                    self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Usuario.objects.get(pk=self.cient.pk).is_active)

    def test_administrador_puede_listar(self):
        self.autenticar(self.admin)
        r = self.client.get(reverse("usuario-list"))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resultados(r)), 5)

    def test_lista_no_expone_password(self):
        self.autenticar(self.admin)
        for item in resultados(self.client.get(reverse("usuario-list"))):
            self.assertNotIn("password", item)


class UsuarioViewSetFiltrosTests(BaseAPITest):
    def setUp(self):
        self.autenticar(self.admin)

    def usernames(self, **params):
        r = self.client.get(reverse("usuario-list"), params)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        return {u["username"] for u in resultados(r)}

    def test_filtro_por_rol(self):
        self.assertEqual(self.usernames(rol="ml_operator"), {"mlops1"})

    def test_filtro_por_departamento_no_distingue_mayusculas(self):
        self.assertEqual(self.usernames(departamento="datos"), {"ing1", "cient1"})
        self.assertEqual(self.usernames(departamento="DATOS"), {"ing1", "cient1"})

    def test_filtros_combinados(self):
        self.assertEqual(self.usernames(rol="ingeniero_datos", departamento="Datos"), {"ing1"})

    def test_filtro_sin_coincidencias(self):
        self.assertEqual(self.usernames(rol="administrador", departamento="Inexistente"), set())

    def test_sin_filtros_devuelve_todos(self):
        self.assertEqual(len(self.usernames()), 5)


class UsuarioViewSetCrudTests(BaseAPITest):
    def setUp(self):
        self.autenticar(self.admin)

    def datos_nuevo(self, **extra):
        datos = {
            "username": "nuevo",
            "email": "nuevo@biodynamics.test",
            "password": "OtraClave123",
            "rol": Rol.ML_OPERATOR,
            "departamento": "ML",
        }
        datos.update(extra)
        return datos

    # crear
    def test_crear_usuario(self):
        r = self.client.post(reverse("usuario-list"), self.datos_nuevo(), format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", r.data)
        usuario = Usuario.objects.get(username="nuevo")
        self.assertEqual(usuario.rol, Rol.ML_OPERATOR)
        self.assertTrue(usuario.is_active)

    def test_la_password_se_guarda_cifrada(self):
        self.client.post(reverse("usuario-list"), self.datos_nuevo(), format="json")
        usuario = Usuario.objects.get(username="nuevo")
        self.assertNotEqual(usuario.password, "OtraClave123")
        self.assertTrue(usuario.check_password("OtraClave123"))

    def test_usuario_creado_puede_iniciar_sesion(self):
        self.client.post(reverse("usuario-list"), self.datos_nuevo(), format="json")
        self.client.credentials()  # sin token
        r = self.client.post(
            reverse("auth-login"),
            {"username": "nuevo", "password": "OtraClave123"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_crear_sin_password_falla(self):
        datos = self.datos_nuevo()
        datos.pop("password")
        r = self.client.post(reverse("usuario-list"), datos, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", r.data)
        self.assertFalse(Usuario.objects.filter(username="nuevo").exists())

    def test_password_corta_falla(self):
        r = self.client.post(
            reverse("usuario-list"), self.datos_nuevo(password="corta"), format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", r.data)

    def test_email_duplicado_falla(self):
        r = self.client.post(
            reverse("usuario-list"),
            self.datos_nuevo(email="po1@biodynamics.test"),
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", r.data)

    def test_username_duplicado_falla(self):
        r = self.client.post(
            reverse("usuario-list"), self.datos_nuevo(username="admin1"), format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", r.data)

    def test_rol_invalido_falla(self):
        r = self.client.post(
            reverse("usuario-list"), self.datos_nuevo(rol="superheroe"), format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rol", r.data)

    def test_crear_sin_rol_usa_el_de_menos_permisos(self):
        datos = self.datos_nuevo()
        datos.pop("rol")
        r = self.client.post(reverse("usuario-list"), datos, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["rol"], Rol.CIENTIFICO_DATOS)

    #  leer
    def test_detalle_de_usuario(self):
        r = self.client.get(reverse("usuario-detail", args=[self.po.id]))
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["username"], "po1")
        self.assertIn("date_joined", r.data)
        self.assertIn("last_login", r.data)

    def test_detalle_inexistente(self):
        r = self.client.get(reverse("usuario-detail", args=[999999]))
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    # actualizar
    def test_patch_cambia_rol_y_departamento(self):
        r = self.client.patch(
            reverse("usuario-detail", args=[self.cient.id]),
            {"rol": Rol.INGENIERO_DATOS, "departamento": "Ingeniería"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.cient.refresh_from_db()
        self.assertEqual(self.cient.rol, Rol.INGENIERO_DATOS)
        self.assertEqual(self.cient.departamento, "Ingeniería")

    def test_patch_sin_password_no_la_cambia(self):
        antes = Usuario.objects.get(pk=self.cient.pk).password
        self.client.patch(
            reverse("usuario-detail", args=[self.cient.id]), {"first_name": "Ana"}, format="json"
        )
        self.cient.refresh_from_db()
        self.assertEqual(self.cient.password, antes)
        self.assertEqual(self.cient.first_name, "Ana")
        self.assertTrue(self.cient.check_password(PASSWORD))

    def test_patch_con_password_la_actualiza_cifrada(self):
        r = self.client.patch(
            reverse("usuario-detail", args=[self.cient.id]),
            {"password": "NuevaClave456"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertNotIn("password", r.data)
        self.cient.refresh_from_db()
        self.assertTrue(self.cient.check_password("NuevaClave456"))
        self.assertFalse(self.cient.check_password(PASSWORD))

    def test_put_completo_sin_password_es_valido(self):
        datos = {
            "username": "cient1",
            "email": "cient1@biodynamics.test",
            "rol": Rol.CIENTIFICO_DATOS,
            "departamento": "Nuevo",
        }
        r = self.client.put(reverse("usuario-detail", args=[self.cient.id]), datos, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.cient.refresh_from_db()
        self.assertEqual(self.cient.departamento, "Nuevo")

    def test_campos_de_solo_lectura_no_se_modifican(self):
        id_original = self.cient.id
        self.client.patch(
            reverse("usuario-detail", args=[self.cient.id]),
            {"id": 12345, "date_joined": "2000-01-01T00:00:00Z"},
            format="json",
        )
        self.cient.refresh_from_db()
        self.assertEqual(self.cient.id, id_original)
        self.assertNotEqual(self.cient.date_joined.year, 2000)

    def test_cambio_de_rol_se_refleja_en_los_permisos_del_perfil(self):
        self.client.patch(
            reverse("usuario-detail", args=[self.cient.id]),
            {"rol": Rol.ADMINISTRADOR},
            format="json",
        )
        self.autenticar(self.cient)
        r = self.client.get(reverse("auth-perfil"))
        self.assertIn(Operacion.GESTIONAR_USUARIOS.value, r.data["operaciones"])

    # eliminar (desactivar)
    def test_delete_desactiva_y_no_borra(self):
        r = self.client.delete(reverse("usuario-detail", args=[self.ing.id]))
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Usuario.objects.filter(pk=self.ing.pk).exists())
        self.ing.refresh_from_db()
        self.assertFalse(self.ing.is_active)

    def test_delete_revoca_el_token(self):
        Token.objects.create(user=self.ing)
        self.client.delete(reverse("usuario-detail", args=[self.ing.id]))
        self.assertFalse(Token.objects.filter(user=self.ing).exists())

    def test_usuario_desactivado_no_puede_iniciar_sesion(self):
        self.client.delete(reverse("usuario-detail", args=[self.ing.id]))
        self.client.credentials()
        r = self.client.post(
            reverse("auth-login"), {"username": "ing1", "password": PASSWORD}, format="json"
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_desactivado_aparece_con_is_active_false(self):
        self.client.delete(reverse("usuario-detail", args=[self.ing.id]))
        r = self.client.get(reverse("usuario-detail", args=[self.ing.id]))
        self.assertFalse(r.data["is_active"])


# Integración de rutas
class RutasTests(SimpleTestCase):
    def test_los_nombres_de_ruta_resuelven(self):
        for nombre in ("auth-login", "auth-logout", "auth-perfil", "usuario-list"):
            with self.subTest(nombre=nombre):
                self.assertTrue(reverse(nombre))
        self.assertTrue(reverse("usuario-detail", args=[1]))
