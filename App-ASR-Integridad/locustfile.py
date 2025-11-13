from locust import HttpUser, task, between
import random
import json

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
        return random.choice([
            {},  # sin campos
            {"pedido_id": "abc", "monto": -10},  # tipos y valores inválidos
            {"tipo": "pago"},  # faltan campos
            "no-es-json",  # payload totalmente roto
        ])

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

        # Caso 1: payload es un string totalmente roto -> lo mandamos tal cual como "JSON"
        if isinstance(payload, str):
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
                        f"{resp.status_code}, body={resp.text}"
                    )
        else:
            # Caso 2: dict incompleto / con tipos malos -> Locust se encarga del JSON
            with self.client.post(
                "/integridad/event/",
                json=payload,
                name="POST /integridad/event/ (corrupto-dict)",
                catch_response=True,
            ) as resp:
                if resp.status_code != 400:
                    resp.failure(
                        f"Evento corrupto (dict) NO fue rechazado correctamente: "
                        f"{resp.status_code}, body={resp.text}"
                    )