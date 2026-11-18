#!/bin/sh
set -e

echo ">> Aplicando migraciones..."
python manage.py migrate --noinput

# Crea el superusuario automáticamente si están definidas las variables en .env
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py createsuperuser --noinput 2>/dev/null \
    && echo ">> Superusuario '$DJANGO_SUPERUSER_USERNAME' creado" \
    || echo ">> El superusuario ya existe"
fi

# Datos de ejemplo para la demo (SEED_DEMO=1 en .env)
if [ "$SEED_DEMO" = "1" ]; then
  python manage.py seed_demo
fi

echo ">> Iniciando servidor..."
exec "$@"
