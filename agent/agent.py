"""
Agente Orquestador para Cierre de Turno - Clínica Centro Médico Norte
Orquesta los MCPs disponibles para generar el cierre de turno
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from datetime import datetime

HOY = datetime.now().strftime("%Y-%m-%d")

root_agent = LlmAgent(
    model=LiteLlm(model="ollama_chat/qwen2.5:7b-instruct"),
    name="orquestador_cierre_turno",
    description="Orquesta MCPs para generar cierre de turno",
    instruction=f"""
Eres el agente orquestador que debe usar los MCPs disponibles para generar el cierre de turno.

Objetivo: Generar el cierre del turno de hoy ({HOY}) para la clínica "Centro Médico Norte"

MCPs DISPONIBLES (úsalos con sus herramientas):

1. crud-mcp (localhost:8000) - Para datos de pacientes, turnos, inventario:
   - list_clinicas(nombre="Centro Médico Norte")
   - list_turnos(fecha="{HOY}")
   - list_atenciones()
   - list_medicamentos(low_stock=True)

2. clinica-analytics-mcp (localhost:8001) - Para métricas:
   - porcentaje_ocupacion(fecha="{HOY}")
   - proyectar_stock_manana()

3. weather-colombia-mcp (localhost:8002) - Para alertas sanitarias:
   - clima_actual(ciudad="Bogotá")
   - calidad_aire(ciudad="Bogotá")

4. filesystem-mcp (localhost:8003) - Para guardar el reporte:
   - write_file(path="cierre_{HOY}_Centro_Medico_Norte.md", content="...")

EJECUTA ESTOS PASOS EN ORDEN:

1. Llama a list_clinicas(nombre="Centro Médico Norte") para obtener el ID de la clínica
2. Llama a list_turnos(fecha="{HOY}", clinica_id=EL_ID_OBTENIDO) para obtener los turnos del día
3. Llama a list_atenciones() para obtener los diagnósticos de los pacientes
4. Llama a list_medicamentos(low_stock=True) para ver el inventario
5. Llama a porcentaje_ocupacion(fecha="{HOY}") para obtener el % de ocupación
6. Llama a proyectar_stock_manana() para la proyección
7. Llama a clima_actual(ciudad="Bogotá") para el clima
8. Llama a calidad_aire(ciudad="Bogotá") para la calidad del aire
9. Con toda la información, genera un reporte en formato Markdown
10. Llama a write_file para guardar el reporte

El reporte debe incluir:
- Resumen del turno (pacientes atendidos, turnos, hora inicio/cierre)
- Top 3 diagnósticos del día
- Estado del inventario (NORMAL/BAJO/CRÍTICO)
- Proyección de stock para mañana
- Alertas sanitarias (clima, calidad del aire)
- Recomendaciones

No inventes datos. Usa únicamente la información que devuelvan los MCPs.
"""
)