from locust import HttpUser, task, between
import random

class IntegridadUser(HttpUser):
    """
    Usuario de prueba que simula:
    - Lecturas de /health/
    - Envió de eventos válidos a /integridad/event/
    - Envió de eventos corruptos (para probar integridad)
    """
    wait_time = between(0.5, 1.5)

    # ---------- Helpers ----------

    def _payload_valido(self):
        return {
            "pedido_id": random.randint(1, 100000),
            "tipo": random.choice(["pago", "devolucion", "pedido"]),
            "monto": random.randint(1000, 500000),
            "estado": random.choice(["APROBADO", "RECHAZADO", "PENDIENTE"]),
        }

    def _payload_corrupto_dict(self):
        # Datos "corruptos" pero en JSON válido (los valida tu endpoint)
        return random.choice([
            {},  # sin campos
            {"pedido_id": "abc", "monto": -10},  # tipos y valores inválidos
            {"tipo": "pago"},  # faltan campos
        ])

    # ---------- Tareas ----------

    @task(2)
    def health_check(self):
        """
        Verifica que el endpoint /health/ responda 200 y un JSON con status=ok.
        """
        with self.client.get(
            "/health/",
            name="GET /health/",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Status inesperado en /health/: {resp.status_code}")
                return
            try:
                data = resp.json()
                if data.get("status") != "ok":
                    resp.failure(f"Payload inesperado en /health/: {data}")
            except Exception as e:
                resp.failure(f"No se pudo parsear JSON en /health/: {e}")

    @task(3)
    def enviar_evento_valido(self):
        """
        Envía un evento válido a /integridad/event/ que debería ser aceptado (201).
        """
        payload = self._payload_valido()
        with self.client.post(
            "/integridad/event/",
            json=payload,
            name="POST /integridad/event/ (valido)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 201:
                resp.failure(
                    f"Evento válido rechazado: status={resp.status_code}, body={resp.text}"
                )

    @task(1)
    def enviar_evento_corrupto_dict(self):
        """
        Envía un JSON con estructura incorrecta / incompleta.
        Debe ser rechazado con 400 (validación de integridad).
        """
        payload = self._payload_corrupto_dict()
        with self.client.post(
            "/integridad/event/",
            json=payload,
            name="POST /integridad/event/ (corrupto-dict)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 400:
                resp.failure(
                    f"Evento corrupto (dict) NO fue rechazado correctamente: "
                    f"status={resp.status_code}, body={resp.text}"
                )

    @task(1)
    def enviar_evento_corrupto_string(self):
        """
        Envía un body que ni siquiera es JSON válido (string bruto).
        El servidor debería lanzar error de parseo y responder 400.
        """
        payload = "no-es-json"

        with self.client.post(
            "/integridad/event/",
            data=payload,
            headers={"Content-Type": "application/json"},
            name="POST /integridad/event/ (corrupto-string)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 400:
                resp.failure(
                    f"Evento corrupto (string) NO fue rechazado correctamente: "
                    f"status={resp.status_code}, body={resp.text}"
                )