# Guía de Uso del CLI de Laya

Laya incluye una interfaz de línea de comandos (`laya`) diseñada para clasificar texto, evaluar intenciones y tomar decisiones en tiempo real directamente desde tu terminal o scripts de automatización.

---

## Ruta Rápida (Quick Path)

### 1. Activar el entorno virtual

Si usas **Fish shell**:
```fish
source .venv/bin/activate.fish
```

Si usas **Bash / Zsh**:
```bash
source .venv/bin/activate
```

*(O ejecuta directamente con `uv run laya <comando>` sin necesidad de activar el entorno).*

### 2. Evaluación rápida con un preset

```bash
laya predict --state "Hola, me cobraron dos veces la suscripción este mes." --preset triage
```

### 3. Modo interactivo REPL (Inferencia ultrarrápida en memoria)

```bash
laya repl --preset triage
```

---

## Comandos Disponibles

| Comando | Descripción |
|---|---|
| `laya predict` | Evalúa un estado de entrada contra un conjunto de preguntas y muestra las decisiones. |
| `laya repl` | Inicia una sesión interactiva en memoria evitando el tiempo de carga en frío en CPU (~89 ms por consulta). |
| `laya presets` | Lista o inspecciona los esquemas de preguntas preconfigurados (`triage`, `email`, `guard`, etc.). |
| `laya download` | Descarga o verifica los modelos en el directorio local centralizado (`~/models/laya/`). |

---

## 1. `laya predict`

Evalúa texto o documentos contra una o más preguntas tipadas.

### Opciones de Entrada (`--state`)

El estado a evaluar puede pasarse de tres formas:

1. **Texto directo en línea:**
   ```bash
   laya predict --state "El servidor principal se cayó y la base de datos no responde." --preset triage
   ```

2. **Desde un archivo (usando el prefijo `@`):**
   ```bash
   laya predict --state @ticket.txt --preset triage
   laya predict --state @payload.json --preset triage
   ```

3. **Desde la entrada estándar (Unix Pipe / stdin):**
   ```bash
   echo "Solicito reembolso inmediato de la compra" | laya predict --preset triage
   cat correo.eml | laya predict --preset email
   ```

---

### Definición de Preguntas

Puedes definir qué evaluar mediante presets integrados o preguntas personalizadas:

#### A. Usando Presets Integrados (`--preset`)
```bash
laya predict --state "Quiero dar de baja mi cuenta" --preset triage
```
Presets disponibles: `triage`, `email`, `guard`, `moderation`, `router`.

#### B. Preguntas Booleanas Rápidas (`--noul`)
Sintaxis: `--noul "clave:¿Pregunta a evaluar?"`
```bash
laya predict --state "El servidor se cayó" --noul "emergencia:¿Es una emergencia técnica crítica?"
```

#### C. Preguntas Categóricas Rápidas (`--choice`)
Sintaxis: `--choice "clave:opcion1,opcion2,opcion3:¿Pregunta?"`
```bash
laya predict --state "Necesito cotización para 100 usuarios" --choice "tipo:ventas,soporte,facturacion:¿A qué área pertenece?"
```

#### D. Preguntas Ordinales de Nivel/Escala (`--score`)
Sintaxis: `--score "clave:0=bajo,1=medio,2=alto:¿Pregunta?"`
```bash
laya predict --state "¡Esto es inaceptable, exijo una solución ya!" --score "enojo:0=calmado,1=molesto,2=furioso:¿Nivel de enojo?"
```

#### E. Archivo JSON de Preguntas Completo (`--questions @archivo.json`)
```bash
laya predict --state "Empresa de 50 empleados busca plan anual" --questions @preguntas.json
```

---

### Salida y Automatización en Scripts

#### Salida Formateada para Terminal (Por defecto)
Muestra una interfaz visual limpia con barras de confianza y decisiones claras:

```text
════════════════════════════════════════════════════════════
  LAYA DECISION ENGINE  •  Inferencia en CPU: 89.2 ms
  Modelo activo : multilingual (Latin script detected: 'es')
════════════════════════════════════════════════════════════

▶ [intent] (CHOICE)
   Decisión   : refund  (prob: 100.0%)
   Confianza  : [███████████████] 100.0%

▶ [refund_requested] (NOUL)
   Decisión   : SÍ (true)  (P(true) = 98.2%)
   Confianza  : [███████████████] 98.2%
```

#### Salida JSON Cruda (`--json`)
Ideal para canalizar con `jq` o integrar con APIs:
```bash
laya predict --state "Cancelar suscripción" --preset triage --json | jq .answers.intent.choice
# "cancellation"
```

#### Extracción Directa de un Valor (`--get <clave>`)
Devuelve únicamente el valor de la decisión solicitada, sin encabezados ni formato extra:
```bash
INTENT=$(laya predict --state "Necesito mi factura" --preset triage --get intent)
echo "La intención es: $INTENT"
# La intención es: billing_question
```

#### Modo Silencioso (`-q` / `--quiet`)
Omite el encabezado y banner informativo, mostrando solo las respuestas evaluadas.

---

## 2. `laya repl` (Modo Interactivo)

En procesadores CPU (como AMD Ryzen), cargar el modelo desde el disco a la memoria RAM toma entre 20 y 25 segundos (*cold start*). 

El comando `laya repl` carga el modelo una sola vez y lo mantiene residente en RAM (~1.28 GB). Las consultas subsiguientes se resuelven en **~89 ms**.

```bash
laya repl --preset triage
```

### Comandos dentro del REPL:
- Escribe cualquier texto y presiona `Enter` para evaluarlo al instante.
- `/preset <nombre>`: Cambia de preset en caliente sin recargar el modelo.
- `/clear`: Limpia la pantalla de la terminal.
- `/help`: Muestra la ayuda rápida.
- `/exit` o `Ctrl+C`: Cierra la sesión interactiva.

---

## 3. `laya presets`

Permite explorar los esquemas de preguntas incluidos en Laya:

```bash
# Listar todos los presets disponibles
laya presets

# Ver la definición completa en JSON de un preset
laya presets triage --show
laya presets email --show
```

---

## 4. `laya download` (Gestión Local de Modelos)

Laya almacena los pesos de los modelos en `~/models/laya/`:

```bash
# Descarga y valida el checkpoint multilingüe (100+ idiomas)
laya download -m multilingual

# Descarga el checkpoint especializado en inglés
laya download -m english
```

> [!NOTE]
> **Política de cero re-descargas:**
> Si los archivos `model.safetensors` y `rl_agent_config.json` ya existen en `~/models/laya/<modelo>/`, Laya opera 100% de forma local y offline, sin contactar a Hugging Face ni re-descargar nada.
