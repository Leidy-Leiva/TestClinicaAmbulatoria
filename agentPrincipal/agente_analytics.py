"""
Agente Analytics - Calcula métricas del turno.
MCP: analytics-mcp (http://localhost:8001/mcp)
MCP: crud-mcp (http://localhost:8000/mcp)
"""

from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from datetime import date, datetime

analytics_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8001/mcp",
    )
)

crud_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8000/mcp",
    )
)

HOY = datetime.now().strftime("%Y-%m-%d")

sub_agent_analytics = LlmAgent(
    model="gemini-2.5-flash-lite",
    name="agente_analytics",
    description=("Calcula métricas clínicas del turno."),
    instruction=f"""
Eres un agente que debe ejecutar herramientas para obtener datos reales.

El NOMBRE de la clínica viene en el mensaje del usuario.
Ejemplo: "Genera el cierre del turno de hoy para la clinica Centro Medico Norte"

EJECUTA EN ORDEN:

1. list_clinicas(nombre=[NOMBRE_DE_LA_CLINICA_DEL_USUARIO], limit=1)
   - El resultado tiene 'items' (array)
   - Del primer item, extrae: id (clinica_id), cantidad_pacientes_maximo (capacidad), nombre
   - GUARDA estos valores

2. list_medicamentos(limit=50)
   - Cuenta críticos: stock_actual = 0
   - Cuenta bajos: stock_actual <= stock_minimo (pero no críticos)
   - Lista nombres de críticos y bajos

3. proyectar_stock_manana()
   - Obtiene alertas para mañana: medicamento_nombre, stock_actual, stock_proyectado

4. porcentaje_ocupacion(fecha="{HOY}", clinica_id=[EL_CLINICA_ID_OBTENIDO])
   - Obtiene: pacientes_unicos, capacidad, porcentaje_ocupacion, nivel_ocupacion

5. list_atenciones(fecha="{HOY}", clinica_id=[EL_CLINICA_ID_OBTENIDO], limit=100)
   - Cuenta pacientes únicos atendidos

IMPORTANTE: 
- Busca la clínica PRIMERO para obtener su clinica_id
- Usa ese clinica_id en porcentaje_ocupacion y list_atenciones

LUEGO DEVUELVE JSON con datos reales:
{{
  "fecha": "{HOY}",
  "clinica_id": [EL_ID_OBTENIDO],
  "clinica_nombre": "[NOMBRE_DE_LA_CLINICA]",
  "capacidad_maxima": [CAPACIDAD_OBTENIDA],
  "ocupacion": {{
    "pacientes_unicos_turno": [NUMERO_REAL],
    "porcentaje_ocupacion": [NUMERO_REAL],
    "nivel": "[NIVEL_REAL]"
  }},
  "inventario": {{
    "total_medicamentos": [NUMERO_REAL],
    "medicamentos_criticos": [NUMERO_REAL],
    "medicamentos_bajos": [NUMERO_REAL],
    "lista_criticos": [ARRAY_DE_NOMBRES],
    "lista_bajos": [ARRAY_DE_NOMBREs],
    "estado": "[CRITICO/BAJO STOCK/OK]"
  }},
  "proyeccion_manana": {{
    "alertas": [ARRAY_DE_ALERTAS]
  }}
}}

Responde SOLO con JSON, sin texto adicional.
""",
    tools=[crud_toolset, analytics_toolset],
)
