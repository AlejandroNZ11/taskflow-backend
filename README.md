# ✅ TaskFlow: gestor de proyectos y tareas en equipo

Proyecto final de **Backend** hecho con **Django + Django REST Framework + PostgreSQL**, con login JWT, Docker, una colección de **Bruno** para probar la API y despliegue en **AWS**.

## ¿Qué hace?

Los usuarios se registran, inician sesión, crean **proyectos**, invitan **miembros**, crean **tareas** (con estado, prioridad, responsable y fecha límite) y las **comentan**. Cada proyecto tiene **estadísticas** de avance.

| Característica | Detalle |
|---|---|
| Usuarios | Modelo `User` personalizado (email único), registro, login, perfil |
| Autenticación | **JWT** (access + refresh) para la API · sesión de Django para el frontend |
| Permisos | Cada usuario ve **solo** sus proyectos; solo el dueño edita o borra el proyecto y agrega miembros; solo el autor edita sus comentarios |
| API REST | CRUD completo, paginación, **filtros**, **búsqueda**, **ordenamiento** |
| Extras | Endpoint de estadísticas, "mis tareas", tareas vencidas, health check, rate limiting |
| Documentación | **Swagger / OpenAPI** automático en `/api/docs/` |
| Tests | 36 tests automáticos (`python manage.py test`) |
| Infraestructura | Docker + docker-compose + PostgreSQL 16 + Gunicorn + WhiteNoise |
| Despliegue | **Render** (Blueprint `render.yaml`) o **AWS** (EC2, opcional RDS) |

---

## 📁 Estructura

```
backend/
├── config/            # settings, urls principales, wsgi
├── accounts/          # usuarios: modelo, registro, perfil (API)
├── projects/          # proyectos, tareas, comentarios (API) + permisos + tests
│   └── management/commands/seed_demo.py   # datos de ejemplo
├── web/               # frontend básico (templates + Bootstrap)
├── static/            # CSS
├── bruno/TaskFlow/    # colección de Bruno para probar la API
├── Dockerfile
├── docker-compose.yml        # local: Django + PostgreSQL
├── docker-compose.prod.yml   # AWS con RDS
├── render.yaml               # despliegue en Render (Blueprint)
├── entrypoint.sh             # migraciones + superusuario + datos demo
├── requirements.txt
└── .env.example
```

---

## 🧰 PASO 1: Instalar lo que falta en la laptop

Necesitás **Python 3.14**, **Git** y **VS Code**. Te faltan estos programas. Abrí **PowerShell** y ejecutá:

```bash
winget install -e --id Docker.DockerDesktop
```

```bash
winget install -e --id Bruno.Bruno
```

```bash
winget install -e --id Amazon.AWSCLI
```

Opcional, para ver la base de datos con interfaz gráfica:

```bash
winget install -e --id dbeaver.dbeaver
```

> **Docker Desktop**: después de instalarlo **reiniciá la PC**. Si te pide activar **WSL 2**, aceptá (o ejecutá `wsl --install` en PowerShell como administrador). Abrí Docker Desktop y esperá a que diga *Engine running*.

Extensiones recomendadas de VS Code: **Python**, **Django** y **Docker**.

**PostgreSQL no hace falta instalarlo**: corre dentro de Docker.

> El proyecto usa **Python 3.14** (también funciona con 3.12 o 3.13). Verificá con `python --version`.

---

## 💻 PASO 2: Correr el proyecto en local (sin Docker, con SQLite)

Es la forma más rápida de programar y probar. Desde la carpeta del proyecto:

```bash
python -m venv venv
```

```bash
.\venv\Scripts\Activate.ps1
```

> Si PowerShell bloquea la activación, ejecutá una sola vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

```bash
pip install -r requirements.txt
```

```bash
python manage.py migrate
```

```bash
python manage.py seed_demo
```

```bash
python manage.py createsuperuser
```

```bash
python manage.py runserver
```

Abrí en el navegador:

| URL | Qué es |
|---|---|
| http://localhost:8000 | Frontend (login con `demo` / `Demo12345!`) |
| http://localhost:8000/api/docs/ | Swagger, la documentación interactiva de la API |
| http://localhost:8000/admin/ | Panel de administración de Django |
| http://localhost:8000/health/ | Health check |

Correr los tests:

```bash
python manage.py test
```

---

## 🐳 PASO 3: Correr con Docker + PostgreSQL

Esta es la forma "real", igual que en producción.

1. Copiá el archivo de variables de entorno y editalo (cambiá las contraseñas):

```bash
copy .env.example .env
```

2. Levantá todo:

```bash
docker compose up --build
```

Esto crea 2 contenedores: **db** (PostgreSQL 16) y **web** (Django + Gunicorn). Al arrancar, automáticamente:
- aplica las migraciones,
- crea el superusuario definido en `.env`,
- carga los datos de demo (si `SEED_DEMO=1`).

3. Entrá a http://localhost:8000

Comandos útiles:

```bash
docker compose ps
```

```bash
docker compose logs -f web
```

```bash
docker compose exec web python manage.py test
```

```bash
docker compose exec db psql -U taskflow -d taskflow
```

```bash
docker compose down
```

> `docker compose down -v` borra también el volumen y, con él, **todos los datos** de la base.

Para conectarte con **DBeaver**: host `localhost`, puerto `5432` y el usuario, la contraseña y la base que pusiste en `.env`.

---

## 🧪 PASO 4: Probar la API con Bruno

1. Abrí Bruno → **Open Collection** → elegí la carpeta `bruno/TaskFlow`.
2. Arriba a la derecha seleccioná el environment **Local**.
3. Ejecutá **01 Auth → Login**. El token JWT se guarda solo en `{{accessToken}}`.
4. Probá el resto de los requests en orden, o hacé clic derecho en la colección → **Run** para correr todo con los tests.

| Carpeta | Requests |
|---|---|
| 01 Auth | Registro, Login (JWT), Refresh token, Mi perfil, Sin token (401) |
| 02 Proyectos | Crear, Listar, Detalle, Editar, Agregar / Quitar miembro, Estadísticas |
| 03 Tareas | Crear, Listar con filtros, Buscar, Mis tareas, Cambiar estado |
| 04 Comentarios | Comentar, Listar por tarea |
| 05 Limpieza | Eliminar tarea, Eliminar proyecto |

---

## 📡 Endpoints de la API

Todos requieren el header `Authorization: Bearer <token>` salvo registro, login y refresh.

| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/api/auth/register/` | Registrar usuario |
| POST | `/api/auth/login/` | Login → devuelve `access` y `refresh` |
| POST | `/api/auth/refresh/` | Renovar el token `access` |
| GET / PATCH | `/api/auth/me/` | Ver o editar mi perfil |
| GET / POST | `/api/projects/` | Listar (`?search=`, `?ordering=`) / crear proyectos |
| GET / PUT / PATCH / DELETE | `/api/projects/{id}/` | Detalle / editar / borrar (solo el dueño edita) |
| POST | `/api/projects/{id}/members/add/` | Agregar miembro `{"username": "ana"}` |
| POST | `/api/projects/{id}/members/remove/` | Quitar miembro |
| GET | `/api/projects/{id}/stats/` | Estadísticas del proyecto |
| GET / POST | `/api/tasks/` | Listar / crear tareas |
| GET / PUT / PATCH / DELETE | `/api/tasks/{id}/` | Detalle / editar / borrar |
| GET | `/api/tasks/mine/` | Mis tareas asignadas |
| GET / POST | `/api/comments/?task={id}` | Comentarios de una tarea |
| GET / PATCH / DELETE | `/api/comments/{id}/` | Solo el autor modifica |

**Filtros de tareas:** `?project=1&status=todo&priority=3&assigned_to=2&due_date__lte=2026-12-31&search=docker&ordering=-priority`

Estados: `todo`, `in_progress`, `done` · Prioridades: `1` Baja, `2` Media, `3` Alta

---

## 🗂️ Subir a GitHub

```bash
git init
```

```bash
git add .
```

```bash
git commit -m "Proyecto final: TaskFlow"
```

Creá un repositorio vacío en GitHub y seguí las instrucciones que te muestra (`git remote add origin ...` y `git push -u origin main`). El `.env` **no se sube** porque está en `.gitignore`.

---

## 🚀 PASO 5A: Desplegar en Render (lo más fácil, gratis y con HTTPS)

El proyecto ya trae un archivo [`render.yaml`](render.yaml) (Blueprint) que crea **la base PostgreSQL y la app** de una sola vez, usando el mismo `Dockerfile`.

1. Subí el proyecto a **GitHub** (sección anterior).
2. Entrá a https://render.com y **registrate con tu cuenta de GitHub**.
3. **New +** → **Blueprint** → elegí tu repositorio → Render detecta el `render.yaml`.
4. Te va a pedir el valor de `DJANGO_SUPERUSER_PASSWORD`: poné una contraseña para el admin.
5. **Apply / Deploy**. Esperá unos minutos a que el build termine; los logs se ven en vivo.
6. Tu app queda en `https://taskflow-xxxx.onrender.com` 🎉
   - En Bruno, cambiá el `baseUrl` del environment **AWS** (o creá uno "Render") por esa URL.

Qué hace Render automáticamente:
- Crea PostgreSQL y le pasa la conexión a Django por `DATABASE_URL`.
- Genera una `DJANGO_SECRET_KEY` aleatoria.
- Agrega el dominio `.onrender.com` a `ALLOWED_HOSTS` (variable `RENDER_EXTERNAL_HOSTNAME`).
- Corre las migraciones, crea el admin y carga los datos de demo al arrancar.
- Cada `git push` a `main` vuelve a desplegar la app.

> ⚠️ **Límites del plan gratuito de Render:** la app se "duerme" después de unos 15 minutos sin uso, y la primera visita tarda alrededor de 1 minuto en despertarla. **Abrila un rato antes de presentar.** Además, la base PostgreSQL gratuita **vence a los 30 días**: creala cerca de la fecha de entrega.

---

## ☁️ PASO 5B: Desplegar en AWS (EC2 + Docker)

### Opción A (la más simple): todo en una EC2

1. **Crear la instancia.** En la consola de AWS → **EC2** → *Launch instance*:
   - AMI: **Ubuntu Server 24.04 LTS**
   - Tipo: **t2.micro** o **t3.micro** (capa gratuita)
   - Key pair: creá uno (`taskflow-key.pem`) y guardalo
   - Security Group: abrí el puerto **22** (SSH, solo para *My IP*) y el **80** (HTTP, para *Anywhere*)

2. **Conectarte** desde PowerShell, en la carpeta donde está el `.pem`:

```bash
ssh -i taskflow-key.pem ubuntu@TU-IP-PUBLICA
```

3. **Instalar Docker** en la EC2:

```bash
curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker ubuntu && exit
```

   Volvé a conectarte por SSH para que se aplique el grupo `docker`.

4. **Bajar el proyecto** desde tu repositorio de GitHub:

```bash
git clone https://github.com/TU-USUARIO/TU-REPO.git taskflow && cd taskflow
```

5. **Crear el `.env` de producción**:

```bash
cp .env.example .env && nano .env
```

   Cambiá como mínimo:
   ```
   DJANGO_SECRET_KEY=<una clave larga y aleatoria>
   DJANGO_ALLOWED_HOSTS=TU-IP-PUBLICA
   DJANGO_CSRF_TRUSTED_ORIGINS=http://TU-IP-PUBLICA
   POSTGRES_PASSWORD=<contraseña segura>
   DJANGO_SUPERUSER_PASSWORD=<contraseña segura>
   ```
   Para generar la SECRET_KEY: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`

6. **Publicar en el puerto 80.** En `docker-compose.yml` cambiá `"8000:8000"` por `"80:8000"` y borrá el bloque `ports` del servicio `db` (la base no debe quedar expuesta a internet). Después:

```bash
docker compose up -d --build
```

7. Entrá a `http://TU-IP-PUBLICA`. 🎉 En Bruno, usá el environment **AWS** con tu IP.

### Opción B (más profesional): EC2 + RDS (PostgreSQL administrado)

1. AWS → **RDS** → *Create database* → PostgreSQL 16, plantilla **Free tier**, `db.t3.micro`. Definí usuario y contraseña. Nombre de la base inicial: `taskflow`.
2. En el Security Group de RDS, permití el puerto **5432** solo desde el Security Group de tu EC2.
3. En el `.env` de la EC2 poné `POSTGRES_HOST=<endpoint de RDS>` y el usuario y la contraseña de RDS.
4. Levantá solo la app (sin el contenedor de PostgreSQL):

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

> 💸 **Importante:** cuando termines de presentar, **detené o terminá** la EC2 y la RDS para que no te cobren.

---

## 🎤 Tips para la presentación

1. Mostrá el **modelo de datos**: User, Project (dueño + miembros M2M), Task (FK a proyecto, a responsable y a creador) y Comment.
2. Mostrá **Swagger** (`/api/docs/`): login, copiar el token, botón *Authorize* y probar endpoints.
3. Corré la colección de **Bruno** completa con *Run* para que se vean todos los tests en verde.
4. Demostrá la **seguridad**: con el usuario `ana` no podés borrar el proyecto de `demo` (403), y otro usuario no ve el proyecto (404).
5. Mostrá `docker compose ps` con los 2 contenedores y los **tests** pasando.
6. Mostrá la app funcionando en **Render** y/o **AWS**.

## 👥 Usuarios de demo

| Usuario | Contraseña | Rol |
|---|---|---|
| demo | Demo12345! | Dueño del "Proyecto Final Backend" |
| ana | Demo12345! | Miembro del proyecto |
| admin | (el de tu `.env`) | Superusuario para `/admin` |
