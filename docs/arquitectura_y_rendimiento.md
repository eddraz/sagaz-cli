# Arquitectura, Modelos y Rendimiento en CPU

Este documento detalla la arquitectura interna del motor Laya, la política de almacenamiento de modelos y el perfil de rendimiento medido en hardware local.

---

## 1. Arquitectura del Motor (System 1)

Laya es un motor de decisiones no autorregresivo entrenado con **RLCD** (*Reinforcement Learning from Calibrated Decisions*) mediante reglas de puntuación estrictamente propias (*strictly proper scoring rules*).

```
                      ┌────────────────────────────────────────┐
                      │            Texto / Estado              │
                      └───────────────────┬────────────────────┘
                                          │
                        Script & Language Detection (<0.5 ms)
                                          │
                         ┌────────────────┴────────────────┐
                         ▼                                 ▼
              [ laya-multilingual ]                     [ laya ]
              (mmBERT-base, 322M)               (ModernBERT-large, 421M)
                         │                                 │
                         └────────────────┬────────────────┘
                                          │
                             Single Forward Pass (Encoder)
                                          │
                         ┌────────────────┴────────────────┐
                         ▼                ▼                ▼
                     [choice]          [score]          [noul]
                   Categorías         Ordinales       Booleanas
```

### Diferencias Clave frente a LLMs Tradicionales
| Característica | LLM Tradicional (System 2) | Laya (System 1) |
|---|---|---|
| **Mecanismo** | Autorregresivo (token a token). | Pasada única hacia adelante (*Single forward pass*). |
| **Latencia** | Variable (cientos de milisegundos o segundos). | Constante (sub-100 ms en memoria). |
| **Salida** | Texto no estructurado (requiere parsing y regex). | Respuestas fuertemente tipadas (`choice`, `score`, `noul`). |
| **Alucinación** | Posible (puede inventar etiquetas o respuestas). | **0% alucinación** (solo evalúa las opciones dadas). |
| **Calibración** | Pobremente calibrados en probabilidades. | Probabilidades estadísticas calibradas con RLCD. |

---

## 2. Checkpoints Disponibles

| Checkpoint | Arquitectura Base | Parámetros | Contexto Máx. | Propósito |
|---|---|---|---|---|
| **`laya-multilingual`** | `mmBERT-base` | 322M | 1,024 tokens | **Recomendado para producción general.** Soporta más de 100 idiomas (incluyendo español). 2x más rápido en CPU. |
| **`laya`** | `ModernBERT-large` | 421M | 512 tokens | Especializado en idioma inglés de alta precisión. |
| **`laya-typed-decisions`**| `ModernBERT-large` | 421M | 1,024 tokens | Fine-tuned para flujos de trabajo B2B (facturación, observabilidad, soporte). |

---

## 3. Almacenamiento Local y Política de Cero Re-Descargas

Laya almacena los pesos de los modelos de forma centralizada en el directorio del usuario:

```
~/models/laya/
├── multilingual/
│   ├── model.safetensors        (~644 MB)
│   ├── rl_agent_config.json
│   ├── tokenizer.json
│   └── tokenizer_config.json
└── english/
    ├── model.safetensors        (~842 MB)
    ├── rl_agent_config.json
    ├── tokenizer.json
    └── tokenizer_config.json
```

### Reglas de Persistencia:
1. **Comprobación en primer uso (`ensure_model_available`):** Al ejecutar cualquier comando CLI (`predict`, `repl`), Laya verifica si el directorio local ya contiene `model.safetensors` y `rl_agent_config.json`.
2. **Descarga transparente:** Si no existen, los descarga automáticamente desde Hugging Face informando en terminal.
3. **Cero re-descargas y modo offline:** Si los archivos existen localmente, se cargan de inmediato desde el disco sin realizar peticiones de red ni consultar la API de Hugging Face.

---

## 4. Rendimiento Medido en CPU (AMD Ryzen 3 5300U)

### Perfil de Hardware de Referencia:
- **Procesador:** AMD Ryzen 3 5300U (4 núcleos / 8 hilos, arquitectura Zen 2 Lucienne, hasta 3.8 GHz).
- **Memoria RAM:** 11 GiB DDR4 compartida.
- **Gráficos:** AMD Radeon Vega 6 iGPU (sin aceleración CUDA / ROCm; inferencia 100% en CPU con PyTorch 2.14).

### Mediciones Reales de Latencia:

| Escenario | Checkpoint | Latencia Medida | Uso de Memoria |
|---|---|---|---|
| **Carga en frío desde disco** (*Cold-start*) | `laya-multilingual` | **22.1 - 25.0 segundos** | Pasa de reposo a 1.28 GB RAM |
| **Inferencia 1 pregunta** (*En memoria / REPL*) | `laya-multilingual` | **~89 ms** | 1.28 GB RAM constante |
| **Inferencia 5 preguntas (Preset Triage)** | `laya-multilingual` | **~288 ms** (~57 ms por pregunta) | 1.28 GB RAM constante |
| **Inferencia en GPU (Tesla T4 de referencia)** | `laya-multilingual` | **32.8 ms** (1 preg) / **40.1 ms** (5 preg) | VRAM dedicada |

### Conclusiones de Rendimiento:
1. **El cuello de botella en CPU es la deserialización de pesos:** Cargar 322 millones de parámetros float32/bfloat16 desde el disco a la memoria principal de la CPU toma ~23 segundos.
2. **La pasada neuronal en CPU es sumamente rápida:** Una vez los pesos están en la memoria RAM, el cálculo del transformador toma menos de 100 ms por consulta.
3. **Recomendación para desarrollo y producción:**
   - En desarrollo interactivo por terminal: usar siempre `laya repl` para mantener el modelo en memoria.
   - En servicios backend / APIs: instanciar `Router(preload=True)` en el arranque del servidor (FastAPI/Flask) para servir todas las solicitudes en sub-100 ms sin incurrir en *cold starts*.
