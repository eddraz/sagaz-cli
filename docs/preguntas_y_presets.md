# Guía de Preguntas, Primitivas y Presets en Laya

Laya es un motor de decisiones no autorregresivo (System 1). A diferencia de los LLMs tradicionales que generan texto palabra por palabra, Laya evalúa **preguntas fuertemente tipadas** en una sola pasada hacia adelante (*single forward pass*).

---

## Las 3 Primitivas de Decisión

Laya trabaja con tres tipos fundamentales de preguntas:

| Primitiva | Tipo de Salida | Casos de Uso Típicos |
|---|---|---|
| **`choice`** | Selección de una categoría dentro de un conjunto cerrado de opciones con probabilidades calibradas. | Enrutamiento de tickets, clasificación de intenciones, tipificación de solicitudes. |
| **`noul`** | Probabilidad booleana calibrada $P(\text{true}) \in [0.0, 1.0]$. | Detección de fraude, phishing, spam, urgencia crítica, riesgo de churn. |
| **`score`** | Distribución de probabilidad sobre una escala ordinal (0 a N) con valor esperado continuo. | Niveles de frustración (0=calmado, 3=furioso), prioridad (baja/alta), severidad. |

---

## 1. Primitiva `choice` (Clasificación Categórica)

Evalúa cuál de las opciones disponibles describe mejor el estado de entrada.

### Estructura en JSON
```json
{
  "tipo_solicitud": {
    "type": "choice",
    "instructions": "¿A qué departamento debe asignarse este mensaje?",
    "criteria": {
      "facturacion": "Cobros, facturas pendientes, problemas de tarjeta o pagos",
      "soporte_tecnico": "Caídas de servicio, errores de software o bugs",
      "ventas": "Cotizaciones, demostraciones comerciales o nuevos planes",
      "general": "Otras consultas informativas"
    }
  }
}
```

### Respuesta del Modelo
```json
{
  "type": "choice",
  "choice": "facturacion",
  "probabilities": {
    "facturacion": 0.985,
    "soporte_tecnico": 0.005,
    "ventas": 0.008,
    "general": 0.002
  },
  "confidence": 0.985
}
```

> [!TIP]
> **Presupuesto de tokens:** Se recomienda entre 2 y 20 opciones por pregunta para mantener la máxima precisión. Las descripciones en `criteria` ayudan al modelo a desambiguar casos límite.

---

## 2. Primitiva `noul` (Decisión Booleana Calibrada)

Evalúa la probabilidad de que una afirmación sea verdadera o falsa. El nombre `noul` proviene del formato interno probabilístico calibrado con reglas de puntuación estrictamente propias (RLCD).

### Estructura en JSON
```json
{
  "es_urgente": {
    "type": "noul",
    "instructions": "¿El usuario expresa una emergencia o bloqueo total del servicio?"
  },
  "riesgo_churn": {
    "type": "noul",
    "instructions": "¿El cliente amenaza explícitamente con cancelar su suscripción o irse a la competencia?"
  }
}
```

### Respuesta del Modelo
```json
{
  "type": "noul",
  "noul": 0.942,
  "confidence": 0.942
}
```
- Si `noul >= 0.5`, la decisión es afirmativa (`true`).
- `confidence` mide la certeza de la decisión (distancia al umbral neutro).

---

## 3. Primitiva `score` (Escalas Ordinales)

Evalúa un nivel dentro de una jerarquía ordenada de intensidad o severidad. A diferencia de un promedio simple, Laya calcula la distribución completa sobre los niveles ordinales y devuelve tanto las probabilidades por nivel como el valor esperado continuo.

### Estructura en JSON
```json
{
  "nivel_frustracion": {
    "type": "score",
    "instructions": "¿Qué nivel de enojo o frustración expresa el cliente?",
    "criteria": [
      "tranquilo y neutro",
      "preocupado pero respetuoso",
      "claramente molesto o impaciente",
      "extremadamente furioso o usando lenguaje hostil"
    ]
  }
}
```

### Respuesta del Modelo
```json
{
  "type": "score",
  "score": 2.378,
  "legend": {
    "0": "tranquilo y neutro",
    "1": "preocupado pero respetuoso",
    "2": "claramente molesto o impaciente",
    "3": "extremadamente furioso o usando lenguaje hostil"
  },
  "probabilities": {
    "0": 0.008,
    "1": 0.071,
    "2": 0.455,
    "3": 0.466
  },
  "confidence": 0.320
}
```
En la CLI de Laya, se renderiza automáticamente la etiqueta correspondiente al nivel más probable (ej: `Nivel 2 (claramente molesto o impaciente)`).

---

## Presets Preconfigurados

Laya incluye 5 presets listos para usar en producción:

### 1. `triage` (Triaje de Soporte y Atención al Cliente)
Diseñado para clasificar tickets entrantes en centros de ayuda.
- **`intent`** (`choice`): `refund`, `technical_help`, `billing_question`, `information`, `cancellation`, `other`.
- **`is_urgent`** (`noul`): Detección de urgencia inmediata.
- **`frustration`** (`score`): Nivel de frustración del usuario (0 a 3).
- **`refund_requested`** (`noul`): Si solicita devolución de dinero.
- **`churn_risk`** (`noul`): Si amenaza con cancelar el servicio.

### 2. `email` (Clasificación de Correos Electrónicos)
- **`category`** (`choice`): `support`, `sales`, `billing`, `security`, `notification`, `newsletter`, `personal`, `other`.
- **`is_spam`** (`noul`): Filtro de spam.
- **`is_phishing`** (`noul`): Detección de suplantación de identidad o enlaces fraudulentos.
- **`urgency`** (`score`): Nivel de urgencia del correo (0 a 3).
- **`needs_reply`** (`noul`): Si el correo requiere respuesta humana.

### 3. `guard` (Barreras de Seguridad para LLMs / Prompt Injections)
- **`is_jailbreak`** (`noul`): Intentos de eludir políticas o system prompts.
- **`is_prompt_injection`** (`noul`): Inyección indirecta de instrucciones maliciosas.
- **`risk_level`** (`score`): Nivel de riesgo de seguridad (0 a 3).

### 4. `moderation` (Moderación de Contenido)
- **`is_toxic`** (`noul`): Lenguaje ofensivo o denigrante.
- **`is_harassment`** (`noul`): Acoso dirigido a personas o grupos.
- **`is_hate_speech`** (`noul`): Discurso de odio.
- **`severity`** (`score`): Severidad del incidente de contenido.

### 5. `router` (Enrutamiento Dinámico de Modelos de Lenguaje)
Evalúa la complejidad de una solicitud para decidir si resolverla con un modelo pequeño (e.g. SLM/Haiku) o un modelo frontera (e.g. Opus/Sonnet/GPT-4o).
- **`complexity`** (`score`): Complejidad técnica y de razonamiento.
- **`requires_reasoning`** (`noul`): Si requiere cadena de pensamiento profunda.
- **`target_tier`** (`choice`): `fast_local`, `standard`, `frontier`.

---

## Ejemplo Completo: Archivo Personalizado (`preguntas.json`)

Crea un archivo `preguntas.json`:
```json
{
  "tipo_cliente": {
    "type": "choice",
    "instructions": "¿Qué tipo de cliente está escribiendo?",
    "criteria": {
      "persona": "Usuario individual o cuenta personal",
      "pyme": "Pequeño negocio o equipo reducido",
      "empresa": "Corporación, gran empresa o muchos empleados"
    }
  },
  "prioridad": {
    "type": "score",
    "instructions": "¿Qué nivel de prioridad tiene la oportunidad?",
    "criteria": [
      "baja",
      "media",
      "alta",
      "inmediata"
    ]
  },
  "pide_descuento": {
    "type": "noul",
    "instructions": "¿El cliente solicita rebajas, descuentos o precio especial?"
  }
}
```

Ejecuta en la terminal:
```bash
laya predict --state "Somos una multinacional de 500 empleados y necesitamos cotización empresarial con urgencia" --questions @preguntas.json
```
