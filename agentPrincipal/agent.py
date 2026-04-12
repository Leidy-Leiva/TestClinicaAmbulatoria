"""
Orquestador principal del sistema de cierre de turno.
Clínica Centro Médico Norte.

Arquitectura: SequentialAgent (pipeline determinístico)
Flujo: agente_alertas → agente_datos → agente_analytics → agente_reporte

NOTA: SequentialAgent ejecuta los sub-agentes en orden secuencial.
Cada agente recibe el historial de conversación completo, lo que permite
al agente_reporte acceder a los resultados de todos los anteriores.
"""

from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from agentPrincipal import agente_alertas
from agentPrincipal import agente_datos
from agentPrincipal import agente_analytics
from agentPrincipal import agente_reporte

# ─────────────────────────────────────────────────────────────────────────────
# Intentar usar SequentialAgent (disponible en google-adk >= 0.4)
# Si no está disponible, usar LlmAgent con instrucción de pipeline explícita
# ─────────────────────────────────────────────────────────────────────────────

try:
    from google.adk.agents import SequentialAgent

    root_agent = SequentialAgent(
        name="agente_orquestador",
        description="Pipeline de cierre de turno para clínica Centro Médico Norte",
        sub_agents=[
            agente_alertas.sub_agent_alertas,
            agente_datos.sub_agent_crud,
            agente_analytics.sub_agent_analytics,
            agente_reporte.sub_agent_reporte,
        ],
    )

except ImportError:
    # Fallback: LlmAgent con herramientas de agentes como AgentTool
    # En este modo, el orquestador llama a cada sub-agente como herramienta
    # y consolida los resultados antes de pasar al siguiente
    try:
        from google.adk.tools import AgentTool

        _tool_alertas = AgentTool(agent=agente_alertas.sub_agent_alertas)
        _tool_datos = AgentTool(agent=agente_datos.sub_agent_crud)
        _tool_analytics = AgentTool(agent=agente_analytics.sub_agent_analytics)
        _tool_reporte = AgentTool(agent=agente_reporte.sub_agent_reporte)

        root_agent = LlmAgent(
            model="gemini-2.5-flash",
            # model=LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
            name="agente_orquestador",
            description="Orquestador de cierre de turno - Clínica Centro Médico Norte",
            instruction="""
Eres el orquestador del sistema de cierre de turno de la clínica Centro Médico Norte.
Tienes 4 herramientas disponibles que DEBES llamar en ESTE ORDEN EXACTO:

PASO 1: Llama a agente_alertas con el mensaje: "Obtén alertas sanitarias para Bogotá"
PASO 2: Llama a agente_datos con el mensaje: "Obtén los datos clínicos del turno de hoy"
PASO 3: Llama a agente_analytics con el mensaje: "Calcula las métricas del turno de hoy"
PASO 4: Llama a agente_reporte con el mensaje: "Genera el reporte final con todos los datos del turno"

REGLAS:
- Espera el resultado de cada herramienta antes de llamar a la siguiente.
- NO inventes datos. Usa ÚNICAMENTE lo que retorne cada herramienta.
- NO termines hasta que agente_reporte haya guardado el archivo.
- Si un agente falla, continúa con los siguientes y nota el error en el contexto.
- Al final, confirma: "Pipeline completado. Reporte generado en /workspace/cierre_YYYY-MM-DD.md"
""",
            tools=[_tool_alertas, _tool_datos, _tool_analytics, _tool_reporte],
        )

    except ImportError:
        # Último fallback: LlmAgent con sub_agents (comportamiento original)
        # pero con prompt corregido para evitar loops
        root_agent = LlmAgent(
            model="gemini-2.5-flash",
            # model=LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
            name="agente_orquestador",
            description="Orquestador de cierre de turno - Clínica Centro Médico Norte",
            instruction="""
Eres el orquestador del cierre de turno de la clínica Centro Médico Norte.

FLUJO OBLIGATORIO - ejecuta en este orden EXACTO sin desviaciones:

ETAPA 1: Transfiere a agente_alertas
  - Mensaje: "Consulta alertas_sanitarias para Bogotá y devuelve el resultado JSON completo"
  - Espera su respuesta antes de continuar

ETAPA 2: Transfiere a agente_datos  
  - Mensaje: "Ejecuta get_resumen_turno, list_atenciones y get_medicamentos_usados. Devuelve JSON."
  - Espera su respuesta antes de continuar

ETAPA 3: Transfiere a agente_analytics
  - Mensaje: "Ejecuta metricas_turno para hoy. Devuelve JSON con ocupacion, inventario y proyeccion."
  - Espera su respuesta antes de continuar

ETAPA 4: Transfiere a agente_reporte
  - Mensaje: "Genera el reporte markdown con todos los datos anteriores y guárdalo con write_file"
  - Espera su respuesta

REGLAS CRÍTICAS:
- NUNCA transfieras de vuelta al orquestador desde un sub-agente.
- SIEMPRE ejecuta los 4 sub-agentes en orden.
- El sistema SOLO termina cuando agente_reporte confirma que guardó el archivo.
- Si un sub-agente falla, continúa con el siguiente usando los datos disponibles.
""",
            sub_agents=[
                agente_alertas.sub_agent_alertas,
                agente_datos.sub_agent_crud,
                agente_analytics.sub_agent_analytics,
                agente_reporte.sub_agent_reporte,
            ],
        )