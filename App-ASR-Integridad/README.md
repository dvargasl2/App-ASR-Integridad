# ASR de Integridad – Guía Completa del Experimento

Este documento explica **cómo crear la infraestructura**, **preparar las instancias**, **entender el código que permite verificar el ASR**, y finalmente **cómo ejecutar el experimento completo** (app + locust).

---

# 1. Objetivo del ASR

El sistema debe **validar la coherencia e integridad de la información** recibida entre microservicios antes de almacenarla o procesarla, garantizando que **nunca se registren datos corruptos**.

Se valida mediante:
- `/health/` → confirma disponibilidad.
- `/integridad/event/` → valida datos correctos vs corruptos.
- Locust → envía miles de requests válidos y corruptos.

---

# 2. Arquitectura General del Experimento

El experimento utiliza **tres instancias EC2 en AWS**:

| Instancia | Rol | Puertos |
|----------|------|---------|
| `int-app` | Ejecuta Django + ASR | 8080 |
| `int-db` | PostgreSQL | 5432 |
| `int-locust` | Cliente Locust para pruebas | 8089 |

---

# 3. CREACIÓN DE INSTANCIAS (DOS MÉTODOS)

Aquí tienes ambas opciones para crear la infraestructura:

---

# 3.1 MÉTODO A — CREACIÓN CON TERRAFORM (Automatizado)

Este método crea automáticamente:

- 1 instancia app  
- 1 instancia db  
- 1 instancia jmeter/locust  
- Seguridad, puertos, user-data, carpetas, etc.

## 3.1.1 Clonar el repositorio
```
git clone https://github.com/dvargasl2/App-ASR-Integridad.git
cd App-ASR-Integridad
```

## 3.1.2 Inicializar Terraform
```
terraform init
```

## 3.1.3 Revisar el plan
```
terraform plan -var="key_name=vockey"
```

## 3.1.4 Aplicar despliegue
```
terraform apply -var="key_name=vockey"
```

## 3.1.5 Obtener IPs públicas
```
terraform output
```

Ejemplo:
```
app_public_ip = "35.175.171.75"
jmeter_public_ip = "54.198.105.209"
db_public_ip = "3.80.177.165"
```

Si Terraform no funciona (por falta de espacio en AWS CloudShell), usa el método manual.

---

# 3.2 MÉTODO B — CREACIÓN MANUAL EN AWS (Sin Terraform)

---

## 3.2.1 Instancia APP (Django)

- AMI: Ubuntu 24.04 LTS  
- Tipo: t2.nano  
- Disco: 8 GB  
- Puertos inbound: 22, 8080  
- Nombre: `int-app`

---

## 3.2.2 Instancia DB (PostgreSQL)

- AMI: Ubuntu 24.04  
- Tipo: t2.nano  
- Disco: 8 GB  
- Puertos inbound: 22, 5432  
- Nombre: `int-db`

Instalar PostgreSQL:
```
sudo apt update -y
sudo apt install -y postgresql postgresql-contrib
```

Configurar PostgreSQL:
```
sudo -u postgres psql -c "CREATE USER appuser WITH PASSWORD 'appPass';"
sudo -u postgres createdb -O appuser appdb
```

---

## 3.2.3 Instancia LOCUST

- AMI: Ubuntu 24.04  
- Tipo: t2.nano  
- Puertos inbound: 22, 8089  
- Nombre: `int-locust`

---

# 4. PREPARACIÓN DE LAS INSTANCIAS

# 4.1 Preparar la instancia APP (Django)

Conectarse:
```bash
ssh -i vockey.pem ubuntu@APP_PUBLIC_IP
```

Crear carpeta y clonar repo:
```bash
sudo mkdir -p /labs
sudo chown ubuntu:ubuntu /labs
cd /labs
git clone https://github.com/dvargasl2/App-ASR-Integridad.git
cd App-ASR-Integridad/App-ASR-Integridad
```

Crear entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate
```

Instalar dependencias (Ubuntu 24.04 requiere `--break-system-packages`):
```bash
pip install --upgrade pip --break-system-packages
pip install -r requirements.txt --break-system-packages
```

---

# 4.2 Preparar la instancia LOCUST

Conectarse:
```bash
ssh -i vockey.pem ubuntu@LOCUST_PUBLIC_IP
```

Instalar dependencias:
```bash
sudo apt update -y
sudo apt install -y python3-pip python3-venv git
```

Crear entorno virtual:
```bash
python3 -m venv ~/locust-venv
source ~/locust-venv/bin/activate
pip install --upgrade pip --break-system-packages
pip install locust --break-system-packages
```

### (Opcional pero recomendado) Actualizar Locust a la última versión

Una vez instalado Locust, puedes actualizarlo fácilmente dentro del entorno virtual:

```bash
source ~/locust-venv/bin/activate
pip install --upgrade pip --break-system-packages
pip install --upgrade locust --break-system-packages
```

Verifica la versión instalada:

```bash
locust --version
```

Si aparece algún error por restricciones de Ubuntu, usa:

```bash
pip install -U locust --break-system-packages --force-reinstall
```

Clonar el repositorio:
```bash
sudo mkdir -p /labs
sudo chown ubuntu:ubuntu /labs
cd /labs
git clone https://github.com/dvargasl2/App-ASR-Integridad.git
```

---

# 5. EXPLICACIÓN DEL CÓDIGO QUE GARANTIZA EL ASR

## 5.1. `views.py` – Validación estricta de integridad

El endpoint `/integridad/event/`:

- valida campos obligatorios:  
  `pedido_id`, `monto`, `estado`, `tipo`
- valida tipos de datos correctos
- valida valores permitidos del estado
- retorna 400 si algo es corrupto
- retorna 200 si el evento es válido

Esto garantiza el ASR porque **ningún dato erróneo entra al sistema**.

---

## 5.2. `locustfile.py` – Generación de carga y datos corruptos

Locust envía 3 tipos de tráfico:

1. **Eventos válidos**
2. **Eventos corruptos tipo diccionario**
3. **Eventos corruptos tipo string**

Esto permite demostrar:
- qué porcentaje de tráfico inválido es rechazado
- que el sistema sigue funcionando correctamente bajo carga
- que no se corrompe la base de datos

---

## 5.3. Otras piezas del proyecto

- `config/settings.py` → habilita `ALLOWED_HOSTS`
- `urls.py` → conecta `/health/` y `/integridad/event/`
- `requirements.txt` → dependencias
- `deployment.tf` → infraestructura (**opcional si se usa manual**)

---

# 6. EJECUTAR LA APLICACIÓN (INSTANCIA APP)

Activar entorno virtual:
```bash
cd /labs/App-ASR-Integridad/App-ASR-Integridad
source venv/bin/activate
```

Ejecutar servidor:
```bash
python3 manage.py runserver 0.0.0.0:8080
```

Verificar:
```
http://APP_PUBLIC_IP:8080/health/
```

---

# 7. EJECUTAR LAS PRUEBAS (INSTANCIA LOCUST)

Activar entorno virtual:
```bash
source ~/locust-venv/bin/activate
```

Entrar al proyecto:
```bash
cd /labs/App-ASR-Integridad/App-ASR-Integridad
```

Ejecutar Locust:
```bash
locust -f locustfile.py --host http://APP_PUBLIC_IP:8080
```

Abrir interfaz desde tu PC:
```
http://LOCUST_PUBLIC_IP:8089
```

Configurar:
- **Number of users:** 100  
- **Spawn rate:** 5  
- **Host:** http://APP_PUBLIC_IP:8080

Clic **Start**.

---

# 8. EXPORTAR RESULTADOS

Locust genera:
```
asr_integridad_stats.csv
asr_integridad_failures.csv
asr_integridad_exceptions.csv
asr_integridad_stats_history.csv
```

Para descargarlos:
```bash
scp -i vockey.pem ubuntu@LOCUST_PUBLIC_IP:/labs/App-ASR-Integridad/App-ASR-Integridad/asr_integridad_*.csv ~/Downloads/
```

---

# 9. OBJETIVO DEL EXPERIMENTO

✔ El sistema acepta datos válidos  
✔ El sistema rechaza datos corruptos  
✔ No se genera inconsistencia en la BD  
✔ Todo sigue funcionando bajo carga  
✔ El ASR de integridad se cumple al 100%
