from locust import HttpUser, task, between
import random

class IntegridadUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def _payload_valido(self):
        return {
            "pedido_id": random.randint(1, 100000),
            "tipo": random.choice(["pago", "devolucion", "pedido"]),
            "monto": random.randint(1000, 500000),
            "estado": random.choice(["APROBADO", "RECHAZADO", "PENDIENTE"]),
        }

    def _payload_corrupto(self):
        # Varias formas de “romper” la integridad
        casos = [
            {},  # sin campos
            {"pedido_id": "abc", "monto": -10},  # tipos y valores inválidos
            {"tipo": "pago"},  # faltan campos
            "no-es-json",  # payload totalmente roto
        ]
        return random.choice(casos)

    @task(3)
    def enviar_evento_valido(self):
        payload = self._payload_valido()
        with self.client.post(
            "/integridad/event/",
            json=payload,
            name="POST /integridad/event/ (valido)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 201:
                resp.failure(f"Evento válido rechazado: {resp.status_code}, body={resp.text}")

    @task(1)
    def enviar_evento_corrupto(self):
        payload = self._payload_corrupto()

        # Caso especial: cuando el payload no es JSON válido
        if isinstance(payload, str):
            data = payload
            headers = {"Content-Type": "application/json"}
        else:
            data = self.client._serialize_json(payload)
            headers = {"Content-Type": "application/json"}

        with self.client.post(
            "/integridad/event/",
            data=data,
            headers=headers,
            name="POST /integridad/event/ (corrupto)",
            catch_response=True,
        ) as resp:
            # Aquí lo ESPERADO es 400 siempre
            if resp.status_code != 400:
                resp.failure(
                    f"Evento corrupto NO fue rechazado correctamente: {resp.status_code}, body={resp.text}"
                )