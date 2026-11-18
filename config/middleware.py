from django.db import connection
from django.http import JsonResponse


def health_response():
    """Verifica que la app y la base de datos respondan."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    status = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "error", "database": db_ok}, status=status)


class HealthCheckMiddleware:
    """
    Responde /health/ antes que el resto de Django.

    Los chequeos de salud de Render / AWS llegan desde la red interna con un
    Host distinto (por ejemplo 10.0.0.5:10000) que no está en ALLOWED_HOSTS;
    así no son rechazados y el servicio no se marca como caído.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/health/":
            return health_response()
        return self.get_response(request)
