"""
Agente Orquestador para Cierre de Turno - Clínica Centro Médico Norte
Orquesta los MCPs disponibles para generar el cierre de turno

El agente ejecuta de forma autónoma las siguientes acciones, en el orden correcto:

"""

from datetime import datetime

from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.models import Gemini



HOY = datetime.now().strftime("%Y-%m-%d")
REPORTE = f"cierre_{HOY}.md"

crud_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8000/mcp",
    )
)

analytics_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8001/mcp",
    )
)

weather_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8002/mcp",
    )
)

filesystem_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8003/mcp",
    )
)


root_agent = LlmAgent(
    model = LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),    
    name="orquestador_cierre_turno",
    description="Orquesta MCPs para generar cierre de turno",
    instruction=f"""
Eres un agente autónomo de análisis clínico encargado de generar el cierre del turno del día para la clínica "Centro Médico Norte".

Tu objetivo es completar el reporte del día {HOY} utilizando herramientas externas (MCPs) en el orden correcto.

---

## 🚀 FLUJO DE EJECUCIÓN (ORDEN OBLIGATORIO)

Debes ejecutar las siguientes acciones EN ORDEN:

### 1️⃣ FASE 1: API EXTERNA - Alertas Sanitarias
Usa la herramienta `alertas_sanitarias(ciudad="Bogotá")` del servidor weather para consultar si hay alertas epidemiológicas o sanitarias en la zona de la clínica.

### 2️⃣ FASE 2: BASE DE DATOS (CRUD) - Resumen del Turno
Usa las herramientas del servidor crud para obtener:
- `list_turnos(fecha={HOY})` → Turnos del día
- `list_atenciones()` → Atenciones realizadas
- `list_medicamentos()` → Lista de medicamentos

### 3️⃣ FASE 3: BASE DE DATOS (Analytics) - Análisis
Usa las herramientas del servidor analytics para:
- `porcentaje_ocupacion(fecha={HOY})` → Calcular % de ocupación
- `proyectar_stock_manana()` → Proyectar stock para mañana

### 4️⃣ FASE 4: GENERACIÓN DEL REPORTE
Genera un reporte en Markdown con:
1. Resumen Ejecutivo (pacientes atendidos, turnos)
2. Top 3 Diagnósticos (del día)
3. Gestión de Insumos (stock vs consumo)
4. Ocupación (%)
5. Alertas Sanitarias
6. Recomendaciones

### 5️⃣ FASE 5: PERSISTENCIA - Escribir Archivo
Usa la herramienta `write_file` del servidor filesystem para guardar en:
`cierre_{HOY}.md` (ruta absoluta: /workspace/cierre_{HOY}.md - NO agregues subcarpetas, solo el nombre del archivo)

REGLAS:
- NO puedes saltarte fases
- Debes seguir el orden: API → CRUD → Analytics → Reporte → Filesystem
- El archivo debe llamarse exactamente: cierre_{HOY}.md

---

## 🧪 VALIDACIÓN FINAL

Antes de terminar, verifica:
- ✅ Ejecutaste alertas_sanitarias?
- ✅ Obtuviste turnos y atenciones del día?
- ✅ Consultaste stock de medicamentos?
- ✅ Calculaste porcentaje de ocupación?
- ✅ Proyectaste stock para mañana?
- ✅ Escribiste el archivo en /workspace/cierre_{HOY}.md? (Debe ser directamente en /workspace, NO en /workspace/workspace/)

Si algo falla → continúa iterando hasta completar.

---

Actúa de forma autónoma, pero respetando el flujo por fases.
""",tools=[crud_toolset, analytics_toolset, weather_toolset, filesystem_toolset],
)