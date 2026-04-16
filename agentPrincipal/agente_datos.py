"""
Agente Datos - Obtiene datos clínicos del turno.
MCP: crud-mcp (http://localhost:8000/mcp)
"""

from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from datetime import date

crud_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8000/mcp",
    )
)

HOY = date.today().isoformat()

sub_agent_crud = LlmAgent(
    model="gemini-2.5-flash-lite",
    name="agente_datos",
    description=("Obtiene datos clínicos del turno."),
    instruction=f"""
Eres un agente que debe ejecutar herramientas para obtener datos reales.

El NOMBRE de la clínica viene en el mensaje del usuario. 
Ejemplo: "Genera el cierre del turno de hoy para la clinica Centro Medico Norte"
El nombre sería "Centro Medico Norte".

EJECUTA EN ORDEN:

1. list_clinicas(nombre=[NOMBRE_DE_LA_CLINICA_DEL_USUARIO], limit=1)
   - El resultado tiene 'items' (array)
   - Del primer item, extrae: id (clinica_id), cantidad_pacientes_maximo (capacidad), nombre
   - GUARDA estos valores para las siguientes llamadas

2. list_turnos(fecha="{HOY}", clinica_id=[EL_CLINICA_ID_OBTENIDO], limit=50)
   - Obtiene: total turnos, atendidos (estado='atendido'), programados (estado='programado')

3. list_atenciones(fecha="{HOY}", clinica_id=[EL_CLINICA_ID_OBTENIDO], limit=100)
   - Obtiene: total atenciones, pacientes únicos atendidos, diagnósticos

4. list_medicamentos(limit=50)
   - Obtiene: medicamentos con stock_actual y stock_minimo

IMPORTANTE: 
- Busca la clínica PRIMERO para obtener su clinica_id
- Usa ese clinica_id en TODAS las consultas de turnos y atenciones

LUEGO DEVUELVE JSON con datos reales:
{{
  "fecha": "{HOY}",
  "clinica_id": [EL_ID_OBTENIDO],
  "clinica_nombre": "[NOMBRE_DE_LA_CLINICA]",
  "capacidad": [CANTIDAD_PACIENTES_MAXIMO],
  "turnos": {{
    "total": [NUMERO_REAL],
    "atendidos": [NUMERO_REAL],
    "programados": [NUMERO_REAL]
  }},
  "atenciones": {{
    "total": [NUMERO_REAL],
    "pacientes_atendidos": [NUMERO_REAL],
    "diagnosticos": [ARRAY_DE_DIAGNOSTICOS]
  }},
  "medicamentos": [ARRAY_DE_MEDICAMENTOS]
}}

Responde SOLO con JSON, sin texto adicional.
""",
    tools=[crud_toolset],
)
