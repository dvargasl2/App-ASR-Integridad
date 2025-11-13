from locust import HttpUser, task, between

class HealthCheckUser(HttpUser):
    # Tiempo de espera entre requests por usuario (en segundos)
    wait_time = between(1, 3)

    @task
    def health_check(self):
        """
        Verifica el endpoint /health/ del ASR de integridad.
        """
        with self.client.get("/health/", name="GET /health/", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Status inesperado: {resp.status_code}")
            else:
                try:
                    data = resp.json()
                    if data.get("status") != "ok":
                        resp.failure(f"Payload inesperado: {data}")
                except Exception as e:
                    resp.failure(f"No se pudo parsear JSON: {e}")