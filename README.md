<div align="center">

# Sagaz CLI (`sagaz-cli`)

**Motor de decisiones System 1 no autorregresivo, rápido y tipado para la terminal.**

[![Licencia](https://img.shields.io/badge/Licencia-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![Powered by](https://img.shields.io/badge/Motor-Laya%20RLCD-orange.svg)](https://github.com/NandhaKishorM/laya)
[![GitHub](https://img.shields.io/badge/GitHub-eddraz%2Flaya-black.svg)](https://github.com/eddraz/laya)

</div>

---

> [!NOTE]
> **Sobre este proyecto:**
> **Sagaz** es una herramienta de línea de comandos y SDK construida sobre la tecnología de **[Laya](https://github.com/NandhaKishorM/laya)** (desarrollado por Convai Innovations / Nandha Kishor M). Utiliza los modelos de decisión multilingües de Laya entrenados con aprendizaje por refuerzo y reglas de puntuación estrictamente propias (RLCD), adaptándolos para ejecución local eficiente en CPU y GPU, con persistencia centralizada en disco y soporte completo para flujos de trabajo en terminal y tuberías Unix.

---

## ⚡ ¿Qué es Sagaz?

A diferencia de los LLMs tradicionales (System 2) que son autorregresivos, lentos y propensos a alucinaciones de formato, **Sagaz** implementa un enfoque de **decisiones System 1**:

- **Evaluación en una sola pasada (*Single Forward Pass*)**: Evalúa múltiples preguntas tipadas simultáneamente sin generar texto palabra por palabra.
- **0% de Alucinaciones**: Solo produce probabilidades matemáticas sobre las opciones o rúbricas suministradas.
- **Decisiones Tipadas**:
  - **`choice`**: Clasificación categórica (intenciones, departamentos, temas).
  - **`score`**: Escalas ordinales continuas (frustración 0-3, gravedad, urgencia).
  - **`noul`**: Probabilidad booleana estrictamente calibrada $P(\text{true}) \in [0.0, 1.0]$ (phishing, spam, riesgo de churn).
- **100% Offline tras el primer uso**: Almacena los checkpoints en `~/models/laya/` con política estricta de cero re-descargas.
- **Inferencia en Memoria con REPL**: En CPU, evita el tiempo de carga en frío (~22 s) y responde en **~89 ms** por consulta manteniendo los pesos residentes en RAM (~1.28 GB).
- **Diseñado para Tuberías Unix**: Integración transparente con `stdin`, `stdout`, `jq` y scripts en Bash/Fish con `--json` y `--get`.

---

## 📚 Documentación Detallada

Para consultar especificaciones a fondo, revisa las guías en [`docs/`](docs/):

- 📖 **[Guía Completa de la CLI](docs/guia_cli.md)**: Manual detallado de comandos, flags, scripting y ejemplos avanzados.
- 🎯 **[Preguntas, Primitivas y Presets](docs/preguntas_y_presets.md)**: Especificación de formatos (`choice`, `score`, `noul`), JSON schemas y los 5 presets integrados.
- ⚙️ **[Arquitectura y Rendimiento en CPU](docs/arquitectura_y_rendimiento.md)**: Detalles del modelo mmBERT/ModernBERT, almacenamiento local y benchmarks en AMD Ryzen.
- 📊 **[Reporte de Benchmarks](BENCHMARKS.md)**: Comparativas completas de precisión, calibración y velocidad frente a otros motores.

---

## 🚀 Instalación y Puesta en Marcha

### Requisitos del Sistema
- **Python**: `>= 3.10`
- **Hardware**: Compatible con CPU estándar (AMD Zen / Intel Core) o GPU NVIDIA con CUDA.
- **RAM recomendada**: Al menos 4 GB (el modelo en ejecución ocupa ~1.28 GB).

### Paso 1: Clonar el repositorio
```bash
git clone https://github.com/eddraz/laya.git
cd laya
```

### Paso 2: Crear el entorno e instalar

#### Con `uv` (Recomendado, ultra rápido):
```bash
uv venv

# Si usas Fish shell:
source .venv/bin/activate.fish

# Si usas Bash o Zsh:
source .venv/bin/activate

uv pip install -e .
```

#### Con `venv` tradicional de Python:
```bash
python3 -m venv .venv

# Si usas Fish shell:
source .venv/bin/activate.fish

# Si usas Bash o Zsh:
source .venv/bin/activate

pip install -e .
```

*(Nota: También puedes ejecutar cualquier comando directamente sin activar el entorno anteponiendo `uv run`: ej. `uv run sagaz predict ...`)*

---

## 💾 Gestión de Modelos Locales y Modo Offline

Sagaz almacena los modelos de forma centralizada en tu directorio de usuario:
`~/models/laya/multilingual/` (~644 MB) y `~/models/laya/english/` (~842 MB).

1. **Auto-descarga en primer uso**: La primera vez que ejecutas un comando de inferencia, Sagaz verifica si los modelos existen. Si no están en disco, los descarga automáticamente informando en la terminal.
2. **Cero Re-Descargas**: Una vez descargados, Sagaz nunca vuelve a contactar a Hugging Face ni a internet. Funciona de manera 100% offline.
3. **Pre-descarga manual**: Si vas a trabajar sin conexión, puedes descargarlos con anticipación:
   ```bash
   sagaz download -m multilingual
   ```

---

## 🛠️ Guía de Uso del CLI (`sagaz` / `laya`)

> [!TIP]
> Puedes invocar la herramienta utilizando tanto el comando principal **`sagaz`** como el alias compatible **`laya`**. Ambos son completamente intercambiables.

### 1. Inferencia Directa (`sagaz predict`)

#### A. Usando Presets Integrados
Sagaz incluye 5 presets preconfigurados listos para producción:
- **`triage`**: Triaje de atención al cliente (intención, urgencia, frustración, devolución, riesgo de churn).
- **`email`**: Clasificación de correos, detección de phishing y spam.
- **`guard`**: Guardrails de seguridad contra inyecciones de prompts y jailbreaks para LLMs.
- **`moderation`**: Moderación de contenido (toxicidad, acoso, amenazas).
- **`router`**: Enrutamiento de prompts hacia modelos pequeños vs modelos frontera.

```bash
# Ejemplo: Triage de soporte al cliente
sagaz predict --state "Hola, me cobraron dos veces la suscripción este mes. Devuélvanme el dinero o cancelo." --preset triage

# Ejemplo: Clasificación de seguridad de emails
sagaz predict --state "Su cuenta ha sido suspendida. Verifique sus claves en http://banco-fake.xyz" --preset email
```

#### B. Preguntas Rápidas en Línea
Puedes evaluar preguntas tipadas ad-hoc sin necesidad de archivos de configuración:
```bash
# Pregunta booleana calibrada (--noul):
sagaz predict --state "El servidor principal se cayó y la base de datos no responde" \
  --noul "emergencia:¿Es una emergencia técnica crítica?"

# Pregunta de selección categórica (--choice):
sagaz predict --state "Somos una empresa de 100 empleados y queremos una cotización anual" \
  --choice "area:ventas,soporte,facturacion:¿A qué departamento corresponde?"

# Pregunta de escala o nivel ordinal (--score):
sagaz predict --state "¡El servicio sigue caído y nadie me responde, son unos estafadores!" \
  --score "enojo:0=calmado,1=molesto,2=furioso:¿Nivel de frustración del usuario?"
```

#### C. Lectura desde Archivos
```bash
# Estado desde archivo de texto o JSON:
sagaz predict --state @ticket.txt --preset triage

# Preguntas complejas desde un archivo JSON:
sagaz predict --state @lead.json --questions @preguntas_personalizadas.json
```

#### D. Tuberías Unix (Pipes) y Automatización en Scripts
```bash
# Salida JSON cruda para procesar con jq:
echo "Quiero cancelar mi suscripción" | sagaz predict --preset triage --json | jq .answers.intent.choice
# -> "cancellation"

# Extraer un valor único directamente con --get (ideal para variables en Bash/Fish):
INTENCION=$(sagaz predict --state "Necesito mi factura de agosto" --preset triage --get intent)
echo "Intención detectada: $INTENCION"

# Modo silencioso (-q / --quiet, omite banners y decoraciones visuales):
echo "Caída de servicio" | sagaz predict --noul "alerta:¿Requiere guardia?" -q
```

---

### 2. Modo Interactivo Ultrarrápido (`sagaz repl`)

En CPU, deserializar los 322M parámetros desde el disco a la memoria RAM toma ~22 segundos (*cold-start*).

El comando **`sagaz repl`** mantiene el modelo cargado de forma permanente en memoria RAM (~1.28 GB). De esta forma, cada consulta subsiguiente se evalúa en apenas **~89 ms**:

```bash
sagaz repl --preset triage
```

**Comandos útiles dentro del REPL:**
- Escribe cualquier texto o frase y presiona `Enter` para evaluarlo de inmediato.
- `/preset <nombre>`: Cambia de preset en caliente (ej: `/preset email`, `/preset guard`) sin recargar el modelo.
- `/clear`: Limpia la pantalla.
- `/help`: Muestra la ayuda interactiva.
- `/exit` o `Ctrl+C`: Cierra la sesión interactiva.

---

### 3. Explorar Presets (`sagaz presets`)

```bash
# Listar todos los presets disponibles:
sagaz presets

# Inspeccionar el esquema JSON exacto de un preset:
sagaz presets triage --show
sagaz presets guard --show
```

---

## 🐍 Uso como Biblioteca Python

Además del CLI, puedes integrar Sagaz directamente en tus aplicaciones Python:

```python
from laya import Router

# Pre-cargar modelos en memoria para inferencia en tiempo real (<35 ms en GPU / ~89 ms en CPU)
router = Router(preload=True)

# 1. Estado en cualquier idioma (texto, ticket, correo, etc.)
state = {"body": "Hola, me cobraron dos veces la factura este mes."}

# 2. Preguntas tipadas
questions = {
    "departamento": {
        "type": "choice",
        "instructions": "¿A qué departamento corresponde esta solicitud?",
        "criteria": {
            "facturacion": "Pagos, cobros dobles, facturas o reembolsos",
            "soporte": "Problemas técnicos, bugs o caídas",
            "ventas": "Precios, planes y cotizaciones"
        }
    },
    "es_urgente": {
        "type": "noul",
        "instructions": "¿El usuario exige atención inmediata?"
    }
}

# 3. Inferencia multilingüe en una sola pasada
result = router.predict(state, questions)

print("Departamento:", result["answers"]["departamento"]["choice"])
print("Confianza   :", result["answers"]["departamento"]["confidence"])
print("Es urgente  :", result["answers"]["es_urgente"]["noul"] >= 0.5)
print("Modelo usado:", result["routing"]["model"])  # -> multilingual
```

---

## 🤝 Reconocimientos y Base Tecnológica

**Sagaz** es un proyecto derivado y potenciado por la tecnología de **Laya**:
- **Tecnología base**: [NandhaKishorM/laya](https://github.com/NandhaKishorM/laya)
- **Creador original de Laya**: Nandha Kishor M ([Convai Innovations](https://huggingface.co/convaiinnovations))
- **Modelos de pesos y arquitectura RLCD**: `convaiinnovations/laya` y `convaiinnovations/laya-multilingual` en Hugging Face.
- **Licencia**: Apache 2.0.

---

## 📄 Licencia

Distribuido bajo la licencia [Apache-2.0](LICENSE).
