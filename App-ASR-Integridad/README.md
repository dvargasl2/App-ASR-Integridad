# ASR de Integridad – Infraestructura, Implementación y Pruebas

Este proyecto implementa y prueba un **Atributo de Calidad (ASR) de Integridad de Datos** en un sistema basado en Django.  
El experimento se ejecuta en **AWS usando Terraform**, y las pruebas de carga e integridad se realizan usando **Locust**.

---

## 1. ASR de Integridad (Descripción)

> Yo como **Administrador del sistema**,  
> dado que el sistema recibe y almacena información de pedidos, pagos y devoluciones entre diferentes microservicios,  
> cuando se intercambien o registren datos críticos,  
> quiero que el sistema valide que la información sea coherente y completa antes de guardarla,  
> para evitar inconsistencias o registros corruptos que afecten el funcionamiento general.  
> Esto debe cumplirse en el **100 % de los casos**, garantizando la integridad de los datos entre microservicios y base de datos.

Este ASR se valida con:
- Un endpoint `/health/` para verificar disponibilidad.
- Un endpoint `/integridad/event/` que valida datos **correctos** vs **corruptos**.
- Pruebas masivas de carga enviando ambos tipos de datos.

---

## 2. Arquitectura del Experimento

Terraform crea **3 instancias EC2**:

| Instancia | Propósito | Puerto |
|----------|-----------|--------|
| `int-app` | Ejecuta Django + ASR | 8080 |
| `int-db` | PostgreSQL configurado | 5432 |
| `int-jmeter` | Corre Locust para pruebas | 8089 (UI) |

**Componentes clave:**

- Django con validaciones estrictas.
- PostgreSQL configurado automáticamente via user-data.
- Clonado automático del repositorio en la instancia `app`.
- Locust con 3 tipos de tráfico:
  - Requests válidos
  - Requests con payload corrupto tipo diccionario
  - Requests corruptos tipo string

---

## 3. Requisitos Previos

1. **AWS CLI instalado y configurado**
aws configure
2. **Terraform instalado**
3. **Llave SSH de AWS** (ejemplo: `vockey.pem`)
4. **Repositorio correctamente subido a GitHub:**
https://github.com/dvargasl2/App-ASR-Integridad
---

## 4. Despliegue de Infraestructura con Terraform

### 4.1. Clonar el repositorio y entrar al proyecto
git clone https://github.com/dvargasl2/App-ASR-Integridad.git
cd App-ASR-Integridad
### 4.2. Inicializar Terraform
terraform init
### 4.3. Revisar el plan
terraform plan -var=“key_name=vockey”
### 4.4. Aplicar el despliegue
terraform apply -var=“key_name=vockey”
Responder `yes`.

### 4.5. Obtener las IPs públicas
terraform output

Ejemplo de lo que devuelve:
app_public_ip = “35.175.171.75”
jmeter_public_ip = “54.198.105.209”
db_public_ip = “3.80.177.165”

---

## 5. Verificar que la App se Levantó Correctamente

Abrir en navegador: http://APP_PUBLIC_IP:8080/health/
Debe responder:
{“status”:“ok”,“message”:“ASR Integridad online”}

---

## 6. Ejecución de Pruebas de Integridad con Locust

### 6.1. Conectarse a la instancia de pruebas
ssh -i ~/Downloads/vockey.pem ubuntu@JEMTER_PUBLIC_IP
### 6.2. Activar entorno virtual de Locust
source ~/locust-venv/bin/activate
Si no existe:
python3 -m venv locust-venv
source locust-venv/bin/activate
pip install locust
### 6.3. Entrar al proyecto
cd /labs/App-ASR-Integridad/App-ASR-Integridad
### 6.4. Ejecutar Locust en modo UI
locust -f locustfile.py –host http://APP_PUBLIC_IP:8080
Verás: Starting web interface at http://0.0.0.0:8089
### 6.5. Abrir la interfaz de Locust

En tu PC abre: http://JEMTER_PUBLIC_IP:8089

### 6.6. Configurar valores en la interfaz

- Number of users: `100`
- Ramp up: `5`
- Host: `http://APP_PUBLIC_IP:8080`
- Run time: `1m` (opcional)

Clic **START**.

---

## 7. Exportar Resultados

Locust genera automáticamente:

- `asr_integridad_stats.csv`
- `asr_integridad_failures.csv`
- `asr_integridad_exceptions.csv`
- `asr_integridad_stats_history.csv`

Para descargarlos:
scp -i ~/Downloads/vockey.pem 
ubuntu@JEMTER_PUBLIC_IP:/labs/App-ASR-Integridad/App-ASR-Integridad/asr_integridad_*.csv 
~/Downloads/

---

## 8. Limpieza de Infraestructura
terraform destroy -var=“key_name=vockey”

---

## 9. Estructura del Proyecto
App-ASR-Integridad/
├── config/
├── integridad/
├── locustfile.py
├── deployment.tf
├── requirements.txt
├── README.md
└── manage.py

---

## 10. Objetivo del Experimento

El experimento valida que:

- El sistema **acepta datos válidos**.
- El sistema **rechaza datos corruptos**.
- No se generan inconsistencias en la base de datos.
- El ASR se cumple incluso bajo alta concurrencia.