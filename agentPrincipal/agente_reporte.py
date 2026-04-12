"""
Agente Reporte - Genera el reporte final de cierre de turno en Markdown.
MCP: filesystem-mcp (http://localhost:8003/mcp)

Herramienta: write_file(path="cierre_YYYY-MM-DD.md", content=<markdown>, overwrite=true)
NOTA: El filesystem-mcp tiene FS_ROOT=/workspace → path es RELATIVO (sin /workspace/).

CORRECCIONES v3:
- write_file se llama SIEMPRE como PRIMERA accion, sin verificar si existe.
- overwrite=true SIEMPRE, garantiza sobreescritura si el archivo ya existe.
- Prohibicion absoluta de get_file_info, list_directory y read_file.
- Funciona correctamente tanto en adk web como en run_pipeline.py.
"""

from google.adk.agents import LlmAgent
from google.adk.models import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from datetime import datetime, date

filesystem_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8003/mcp",
    )
)

HOY = date.today().isoformat()
HORA_ACTUAL = datetime.now().strftime("%H:%M")
NOMBRE_ARCHIVO = f"cierre_{HOY}.md"

sub_agent_reporte = LlmAgent(
    model=LiteLlm(model="bedrock/us.amazon.nova-lite-v1:0"),
    name="agente_reporte",
    description=(
        "Genera el reporte final de cierre de turno en formato Markdown "
        f"y lo guarda como '{NOMBRE_ARCHIVO}' usando el filesystem MCP. "
        "Siempre sobreescribe el archivo aunque ya exista."
    ),
    instruction=f"""Eres el agente final del pipeline de cierre de turno de la clinica Centro Medico Norte.

REGLAS ABSOLUTAS - LEER ANTES DE ACTUAR:
1. Tu PRIMERA y UNICA accion es llamar a write_file. Hazlo de inmediato.
2. NO llames a get_file_info, list_directory, read_file ni ningun otro tool.
3. NO verifiques si el archivo ya existe. SIEMPRE sobreescribe con overwrite=true.
4. NO generes el reporte como texto en el chat sin haber llamado write_file.
5. NO uses transfer_to_agent.
6. NO uses tags <thinking>.

ACCION REQUERIDA - ejecuta esto AHORA:

Llama a write_file con estos parametros EXACTOS:
- path: "{NOMBRE_ARCHIVO}"
- overwrite: true
- content: el reporte Markdown completo (ver plantilla abajo)

PLANTILLA DEL REPORTE (rellena con los datos del historial de conversacion):

# Cierre de Turno - Centro Medico Norte
**Fecha:** {HOY}
**Hora de cierre:** {HORA_ACTUAL}
**Generado por:** Sistema Automatico de Cierre de Turno 

---

## Resumen del Turno
- Total turnos del dia: [numero de turnos de agente_datos list_turnos]
- Turnos atendidos: [turnos con estado=atendido]
- Turnos programados pendientes: [turnos con estado=programado]
- Pacientes atendidos: [total_pacientes de agente_datos estadisticas]
- Porcentaje de ocupacion: [porcentaje_ocupacion de agente_analytics]%
- Nivel de ocupacion: [BAJO/NORMAL/ALTO/CRITICO de agente_analytics]

---

## Diagnosticos del Dia (Top 3)
[Extrae diagnosticos de agente_datos list_atenciones, cuenta frecuencia, ordena de mayor a menor]
- [Diagnostico mas frecuente]: [N] caso(s)
- [Segundo diagnostico]: [N] caso(s)
- [Tercer diagnostico]: [N] caso(s)

---

## Estado del Inventario de Medicamentos
**Estado general:** [estado_general de agente_analytics inventario]

### Medicamentos Criticos (stock = 0)
[Lista medicamentos con stock_actual=0 de agente_datos list_medicamentos, o escribe: Ninguno]

### Medicamentos con Stock Bajo (stock <= stock_minimo)
[Lista medicamentos bajo stock de agente_analytics proyeccion_manana alertas_bajas, o escribe: Ninguno]

### Proyeccion para Manana
[Lista alertas_criticas y alertas_bajas de agente_analytics]
- Total alertas de stock: [total_alertas]

---

## Metricas de Ocupacion
- Total turnos registrados: [turnos_totales]
- Turnos atendidos hoy: [turnos_atendidos]
- Porcentaje de ocupacion: [porcentaje_ocupacion]%
- Total atenciones registradas: [numero de items en list_atenciones]
- Medicos activos: [total_medicos de agente_datos estadisticas]

---

## Alertas Sanitarias - Bogota
**Nivel de riesgo:** [nivel_riesgo de agente_alertas]
**Alertas activas:** [alertas_activas de agente_alertas]
**Fuente:** [fuente de agente_alertas]

[Para cada alerta del array alertas de agente_alertas:]
### [titulo de la alerta]
- Tipo: [tipo]
- Nivel: [nivel]
- Descripcion: [descripcion]
- Recomendaciones: [lista de recomendaciones]

[Si agente_alertas no tiene datos: escribir "Sin alertas activas reportadas"]

---

## Recomendaciones Automaticas
[Genera recomendaciones concretas segun los datos:]
- Si Metformina 850mg u otro medicamento tiene stock=0: "URGENTE: Solicitar reposicion inmediata de [nombre]"
- Si ocupacion >= 90%: "Considerar apertura de turno adicional manana"
- Si hay alertas epidemiologicas activas: "Activar protocolo preventivo: [descripcion de la alerta]"
- Si hay medicamentos bajo stock: "Programar compra urgente de [nombres]"
- Siempre incluir: "Verificar y completar registros de atenciones del turno"
- Siempre incluir: "Entregar informe al jefe de turno entrante"

---
*Reporte generado automaticamente - Sistema de Cierre de Turno v3*
*Clinica Centro Medico Norte | {HOY} | {HORA_ACTUAL}*

INSTRUCCION FINAL:
Despues de llamar a write_file, responde UNICAMENTE con este texto:
"Reporte guardado: /workspace/{NOMBRE_ARCHIVO} ([size_bytes] bytes) - Pipeline completado."

Si write_file retorna error, responde:
"Error al guardar: [mensaje de error]. Reporte: [contenido del markdown]"
""",
    tools=[filesystem_toolset],
)