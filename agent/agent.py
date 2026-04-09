"""
Agente Orquestador para Cierre de Turno - Clínica Centro Médico Norte
Orquesta los MCPs disponibles para generar el cierre de turno
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioServerParameters
from datetime import datetime

HOY = datetime.now().strftime("%Y-%m-%d")

mcp_tools = McpToolset(
    connection_params=StdioServerParameters(
        command="python",
        args=["-m", "mcp.crud.server", "--port", "8000"],
    )
)

root_agent = LlmAgent(
    model=LiteLlm(model="ollama_chat/qwen2.5:7b-instruct"),
    name="orquestador_cierre_turno",
    description="Orquesta MCPs para generar cierre de turno",
    instruction=f"""
Eres el agente orquestador que debe usar las herramientas MCP disponibles para generar el cierre de turno.

Objetivo: Generar el cierre del turno de hoy ({HOY}) para la clínica "Centro Médico Norte"

Debes ejecutar estas herramientas EN ORDEN:

1. list_clinicas(nombre="Centro Médico Norte") → obtener ID de la clínica
2. list_turnos(fecha="{HOY}", clinica_id=ID_OBTENIDO) → turnos del día
3. list_atenciones() → diagnósticos de pacientes
4. list_medicamentos(low_stock=True) → inventario
5. porcentaje_ocupacion(fecha="{HOY}") → % ocupación
6. proyectar_stock_manana() → proyección stock
7. clima_actual(ciudad="Bogotá") → clima
8. calidad_aire(ciudad="Bogotá") → calidad del aire
9. Generar reporte Markdown con toda la información
10. write_file(path="cierre_{HOY}_Centro_Medico_Norte.md", content=REPORTE)

El reporte debe incluir:
- Resumen del turno (pacientes atendidos, turnos, hora inicio/cierre)
- Top 3 diagnósticos del día
- Estado del inventario (NORMAL/BAJO/CRÍTICO)
- Proyección de stock para mañana
- Alertas sanitarias (clima, calidad del aire)
- Recomendaciones

Usa SOLO los datos reales devueltos por las herramientas. NO inventes información.
""",
    tools=[mcp_tools],
)