"""
Agente Analytics - Calcula métricas del turno: ocupación y proyección de stock.
MCP: analytics-mcp (http://localhost:8001/mcp)

Herramientas reales disponibles en analytics-mcp:
  - porcentaje_ocupacion(fecha)    → % ocupación de turnos para una fecha
  - proyectar_stock_manana()       → Proyección de stock para mañana con alertas
  - metricas_clinica()             → Métricas generales últimos 30 días
"""

from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from datetime import date

analytics_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8001/mcp",
    )
)

HOY = date.today().isoformat()

sub_agent_analytics = LlmAgent(
    model=LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_analytics",
    description=(
        "Calcula métricas clínicas del turno: porcentaje de ocupación, "
        "estado del inventario y proyección de stock para mañana."
    ),
    instruction=f"""
Eres un agente de análisis clínico. Debes calcular las métricas del turno del día {HOY}.

Ejecuta EXACTAMENTE estas herramientas en orden:

1. porcentaje_ocupacion(fecha="{HOY}")
   → Devuelve: turnos_totales, turnos_ocupados, turnos_atendidos, porcentaje_ocupacion

2. proyectar_stock_manana()
   → Devuelve: lista de medicamentos con stock_actual, stock_proyectado_manana, alertas de bajo stock

3. metricas_clinica()
   → Devuelve: métricas de turnos, atenciones y medicamentos en los últimos 30 días

Después de ejecutar las 3 herramientas, construye y devuelve un JSON con esta estructura:
{{
  "fecha": "{HOY}",
  "ocupacion": {{
    "total_turnos": <número de get porcentaje_ocupacion>,
    "turnos_atendidos": <número>,
    "porcentaje_ocupacion": <número porcentual>,
    "nivel": "BAJO si <30%, NORMAL si 30-70%, ALTO si 70-90%, CRITICO si >90%"
  }},
  "inventario": {{
    "total_medicamentos": <número de metricas_clinica>,
    "medicamentos_bajo_stock": <número>,
    "estado_general": "NORMAL si 0 bajos, PRECAUCION si 1-3, CRITICO si >3"
  }},
  "proyeccion_manana": {{
    "alertas_criticas": [<nombres de medicamentos con estado sin_stock>],
    "alertas_bajas": [<nombres de medicamentos con estado bajo_stock>],
    "total_alertas": <número>
  }},
  "metricas_raw": <resultado completo de metricas_clinica>
}}

REGLAS ESTRICTAS:
- NO uses transfer_to_agent bajo ninguna circunstancia.
- NO uses herramientas que no existen como metricas_turno o estado_inventario.
- NO inventes métricas. Usa ÚNICAMENTE los datos retornados por las herramientas.
- Si una herramienta falla, usa 0 o [] como valor por defecto y registra el error.
- Responde ÚNICAMENTE con el JSON resultado, sin texto adicional.
""",
    tools=[analytics_toolset],
)