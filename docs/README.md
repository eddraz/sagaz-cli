# Documentación de Sagaz / Laya

Bienvenido a la documentación técnica y operativa de **Sagaz** (paquete `sagaz-cli`, motor `laya`).

## Índice de Guías

- [Guía de Uso del CLI](guia_cli.md) — Referencia completa de instalación y uso de los comandos `sagaz` y `laya`: subcomandos (`predict`, `repl`, `presets`, `download`), flags, tuberías Unix (`|`), scripting e integración con Fish/Bash.
- [Preguntas, Primitivas y Presets](preguntas_y_presets.md) — Explicación de las tres primitivas (`choice`, `score`, `noul`), esquemas de preguntas en JSON (`@preguntas.json`) y catálogo de presets integrados.
- [Arquitectura, Modelos y Rendimiento en CPU](arquitectura_y_rendimiento.md) — Explicación del paradigma System 1 (non-autoregressive), checkpoints locales en `~/models/laya/`, política de cero re-descargas y métricas de latencia en CPU (AMD Ryzen 3 5300U).

## Inicio Rápido

```bash
# 1. Modo interactivo en memoria (sub-100 ms por consulta)
sagaz repl --preset triage

# 2. Evaluación directa desde terminal
sagaz predict --state "Necesito mi factura del mes pasado" --preset triage

# 3. Tubería Unix con salida limpia
echo "Mi servidor falló" | sagaz predict --noul "urgente:¿Es una emergencia?" --quiet
```
