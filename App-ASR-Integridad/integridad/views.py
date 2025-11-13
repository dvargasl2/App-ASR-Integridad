from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def health(request):
    return JsonResponse(
        {
            "status": "ok",
            "message": "ASR Integridad online",
        }
    )

@csrf_exempt
def registrar_evento(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        # JSON corrupto
        return JsonResponse({"error": "JSON inválido"}, status=400)

    # Validaciones mínimas de integridad
    required_fields = ["pedido_id", "tipo", "monto", "estado"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        return JsonResponse(
            {"error": "Campos faltantes", "missing": missing},
            status=400,
        )

    if not isinstance(data["pedido_id"], int):
        return JsonResponse({"error": "pedido_id debe ser entero"}, status=400)

    if data["monto"] <= 0:
        return JsonResponse({"error": "monto debe ser positivo"}, status=400)

    if data["estado"] not in ["APROBADO", "RECHAZADO", "PENDIENTE"]:
        return JsonResponse({"error": "estado inválido"}, status=400)

    # Aquí podrías guardar en BD, por ahora simulemos:
    # Evento válido → se considera consistente
    return JsonResponse({"status": "ok", "message": "Evento registrado"}, status=201)