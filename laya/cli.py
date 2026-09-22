#!/usr/bin/env python3
"""CLI para inferencia con modelos de decisión Laya en CPU."""
import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Optional, Tuple, Union

import torch

from .agent import Agent
from .presets import (
    email_questions,
    guard_questions,
    moderation_questions,
    router_questions,
    triage_questions,
)
from .router import Router

PRESETS = {
    "triage": ("Triage de tickets de soporte al cliente", triage_questions),
    "email": ("Clasificación de emails y detección de amenazas", email_questions),
    "guard": ("Guardrails de seguridad e inyección de prompts", guard_questions),
    "moderation": ("Moderación de contenido, toxicidad y spam", moderation_questions),
    "router": ("Enrutamiento inteligente de consultas según dificultad/dominio", router_questions),
}

MODEL_ALIASES = {
    "auto": None,
    "ml": "multilingual",
    "multi": "multilingual",
    "multilingual": "multilingual",
    "en": "english",
    "english": "english",
    "typed": "typed-decisions",
    "typed-decisions": "typed-decisions",
}


def parse_source(val: Optional[str]) -> Any:
    """Lee texto directo, JSON inline, archivo con prefijo @ o stdin si es '-'."""
    if val is None or val == "-":
        if not sys.stdin.isatty():
            raw = sys.stdin.read().strip()
            if not raw:
                raise ValueError("La entrada recibida por stdin está vacía.")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        raise ValueError("No se proporcionó entrada. Usa un texto, @archivo.json o pasa datos por pipe stdin.")

    if val.startswith("@"):
        path = val[1:]
        if not os.path.exists(path):
            raise FileNotFoundError(f"Archivo no encontrado: {path}")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content

    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return val


def parse_noul_shorthand(shorthand: str) -> Dict[str, Any]:
    """Convierte 'id:Instrucción' o 'id' en una pregunta booleana tipada (noul)."""
    parts = shorthand.split(":", 1)
    qid = parts[0].strip()
    instruction = parts[1].strip() if len(parts) > 1 else qid
    return {qid: {"type": "noul", "instructions": instruction}}


def ensure_model_available(model_choice: str) -> None:
    """Verifica si el modelo existe en ~/models/laya/ o ~/models/; si no, lo descarga por primera vez."""
    target = MODEL_ALIASES.get(model_choice, model_choice)
    model_name = target or "multilingual"

    # Si es ruta directa a un directorio existente, no hacer nada
    if os.path.isdir(model_name):
        return

    models_base_dir = os.environ.get("LAYA_MODELS_DIR", os.path.expanduser("~/models/laya"))
    os.makedirs(models_base_dir, exist_ok=True)

    # Comprobar si ya existe localmente
    for search_base in (models_base_dir, os.path.expanduser("~/models")):
        cand = os.path.join(search_base, model_name)
        if os.path.isdir(cand) and os.path.exists(os.path.join(cand, "model.safetensors")) and os.path.exists(os.path.join(cand, "rl_agent_config.json")):
            return  # Ya existe en disco, no hay nada que descargar

    # Si no existe, descargar en ~/models/laya/<model_name>
    dest_path = os.path.join(models_base_dir, model_name)
    sys.stderr.write(f"\n[Laya] Verificando checkpoints en '{models_base_dir}'...\n")
    sys.stderr.write(f"[Laya] El modelo '{model_name}' no existe en disco. Descargando por primera vez...\n")

    router = Router(default="multilingual", max_loaded=1, preload=False, device="cpu")
    router.load(model_name)
    sys.stderr.write(f"[Laya] ✓ Modelo '{model_name}' descargado exitosamente en '{dest_path}'.\n\n")


def get_engine(model_choice: str, max_loaded: int = 1) -> Tuple[Union[Router, Agent], Optional[str]]:
    """Inicializa Router o Agent con control de memoria para CPU."""
    target = MODEL_ALIASES.get(model_choice, model_choice)

    # Si es ruta local a un directorio de checkpoint
    if target and os.path.isdir(target):
        return Agent(model_id_or_path=target, device="cpu"), None

    # Router automático con límite de memoria
    router = Router(default="multilingual", max_loaded=max_loaded, preload=False, device="cpu")
    return router, target


def run_prediction(
    engine: Union[Router, Agent],
    target_model: Optional[str],
    state: Any,
    questions: Dict[str, Any],
) -> Dict[str, Any]:
    """Ejecuta la predicción y mide latencia."""
    t0 = time.perf_counter()
    if isinstance(engine, Router):
        kwargs = {"model": target_model} if target_model else {}
        result = engine.predict(state, questions, **kwargs)
    else:
        result = engine.predict(state, questions)
    t1 = time.perf_counter()
    result["latency_ms"] = round((t1 - t0) * 1000, 2)
    return result


def format_cli_output(result: Dict[str, Any], latency_ms: float, get_field: Optional[str] = None) -> None:
    """Renderiza el resultado en la terminal con formato amigable."""
    answers = result.get("answers", {})

    if get_field:
        if get_field not in answers:
            sys.stderr.write(f"Error: la pregunta '{get_field}' no existe en las respuestas.\n")
            sys.exit(1)
        ans = answers[get_field]
        if ans.get("type") == "choice":
            val = ans.get("choice")
        elif ans.get("type") == "score":
            val = ans.get("score")
        else:
            val = ans.get("noul", ans.get("p_true"))
        print(val)
        return

    # Encabezado
    print()
    print("═" * 60)
    print(f"  LAYA DECISION ENGINE  •  Inferencia en CPU: {latency_ms:.1f} ms")
    if "routing" in result:
        model_name = result["routing"].get("model", "desconocido")
        reason = result["routing"].get("reason", "")
        print(f"  Modelo activo : {model_name} ({reason})")
    print("═" * 60)

    for qid, ans in answers.items():
        qtype = ans.get("type", "unknown")
        conf = ans.get("confidence", 0.0)
        conf_pct = conf * 100

        # Barra visual de confianza
        bar_len = 15
        filled = int(round(conf * bar_len))
        bar = "█" * filled + "░" * (bar_len - filled)

        if qtype == "choice":
            decision = ans.get("choice")
            detail = f"prob: {ans.get('probabilities', {}).get(decision, 0.0):.1%}"
        elif qtype == "score":
            score_val = ans.get("score", 0.0)
            rounded_lvl = int(round(score_val))
            label = ans.get("legend", {}).get(str(rounded_lvl), "")
            label_str = f" ({label})" if label else ""
            decision = f"Nivel {rounded_lvl}{label_str}"
            detail = f"ordinal esperado: {score_val:.2f}"
        elif qtype == "noul":
            p_true = ans.get("noul", ans.get("p_true", 0.0))
            decision = "SÍ (true)" if p_true >= 0.5 else "NO (false)"
            detail = f"P(true) = {p_true:.1%}"
        else:
            decision = str(ans)
            detail = ""

        print(f"\n▶ [{qid}] ({qtype.upper()})")
        print(f"   Decisión   : {decision}  ({detail})")
        print(f"   Confianza  : [{bar}] {conf_pct:.1f}%")

    print("\n" + "─" * 60 + "\n")


def cmd_predict(args: argparse.Namespace) -> None:
    """Subcomando predict: evaluación única."""
    torch.set_num_threads(args.threads)

    # 1. Cargar Estado
    try:
        state = parse_source(args.state)
    except Exception as e:
        sys.stderr.write(f"Error al leer state: {e}\n")
        sys.exit(1)

    # 2. Cargar Preguntas
    if args.preset:
        _, fn = PRESETS[args.preset]
        questions = fn()
    elif args.noul:
        questions = parse_noul_shorthand(args.noul)
    elif args.questions:
        try:
            questions = parse_source(args.questions)
            if not isinstance(questions, dict):
                raise ValueError("El parámetro questions debe ser un diccionario JSON de preguntas tipadas.")
        except Exception as e:
            sys.stderr.write(f"Error al leer questions: {e}\n")
            sys.exit(1)
    else:
        sys.stderr.write("Error: debes proporcionar --questions, --preset o --noul.\n")
        sys.exit(1)

    # 3. Inferencia
    ensure_model_available(args.model)
    engine, target_model = get_engine(args.model, max_loaded=1)
    result = run_prediction(engine, target_model, state, questions)

    # 4. Salida
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        format_cli_output(result, result["latency_ms"], get_field=args.get)


def cmd_repl(args: argparse.Namespace) -> None:
    """Subcomando repl: sesión interactiva que mantiene el modelo cargado en RAM."""
    torch.set_num_threads(args.threads)
    print("\n" + "=" * 60)
    print(" LAYA REPL INTERACTIVO (Modelo persistente en RAM)")
    print(" Escribe un texto para evaluar. Usa 'exit' o Ctrl+C para salir.")
    print("=" * 60 + "\n")

    # Cargar preguntas
    if args.preset:
        desc, fn = PRESETS[args.preset]
        questions = fn()
        print(f"Preset activo: '{args.preset}' ({desc})")
    elif args.questions:
        questions = parse_source(args.questions)
    else:
        # Por defecto usar triage
        desc, fn = PRESETS["triage"]
        questions = fn()
        print(f"Preset por defecto: 'triage' ({desc})")

    ensure_model_available(args.model)
    engine, target_model = get_engine(args.model, max_loaded=1)
    print(f"Cargando motor de decisiones (modelo: {args.model})...")

    while True:
        try:
            user_input = input("\n[Laya Estado] > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "salir"):
                print("Hasta luego.")
                break

            result = run_prediction(engine, target_model, user_input, questions)
            format_cli_output(result, result["latency_ms"])
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            break
        except Exception as e:
            sys.stderr.write(f"Error procesando estado: {e}\n")


def cmd_download(args: argparse.Namespace) -> None:
    """Subcomando download: pre-descarga un checkpoint a ~/models/laya/ si no existe."""
    target = MODEL_ALIASES.get(args.model, args.model)
    model_name = target or "multilingual"
    models_base_dir = os.environ.get("LAYA_MODELS_DIR", os.path.expanduser("~/models/laya"))
    candidate = os.path.join(models_base_dir, model_name)

    if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, "model.safetensors")) and os.path.exists(os.path.join(candidate, "rl_agent_config.json")):
        print(f"\n✓ El checkpoint '{model_name}' ya existe en '{candidate}'. No es necesario volver a descargarlo.\n")
        return

    print(f"\nDescargando checkpoint '{model_name}' hacia '{candidate}' desde Hugging Face...")
    router = Router(default="multilingual", max_loaded=1, preload=False, device="cpu")
    router.load(model_name)
    print(f"✓ Checkpoint '{model_name}' descargado exitosamente en '{candidate}'.\n")


def cmd_presets(_args: argparse.Namespace) -> None:
    """Subcomando presets: lista los conjuntos de preguntas incorporados."""
    print("\nPRESETS DE PREGUNTAS DISPONIBLES EN LAYA:")
    print("─" * 60)
    for name, (desc, fn) in PRESETS.items():
        q_dict = fn()
        print(f"\n• {name:<12} : {desc}")
        print(f"  Preguntas ({len(q_dict)}): {', '.join(q_dict.keys())}")
    print("\nUso: laya predict --preset <nombre> --state <texto>\n")


def main() -> None:
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        prog="laya",
        description="Laya CLI: Motor de decisiones System 1 no autorregresivo y calibrado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Subcomando: predict
    p_pred = subparsers.add_parser("predict", help="Evalúa un estado con preguntas tipadas")
    p_pred.add_argument("-s", "--state", type=str, default="-",
                        help="Estado a evaluar: texto directo, JSON, @archivo.json o '-' para stdin (default)")
    p_pred.add_argument("-q", "--questions", type=str,
                        help="Preguntas tipadas: JSON inline o @archivo.json")
    p_pred.add_argument("-p", "--preset", choices=list(PRESETS.keys()),
                        help="Usar preset de preguntas incorporado")
    p_pred.add_argument("--noul", type=str,
                        help="Pregunta binaria rápida (formato: 'id:Instrucción')")
    p_pred.add_argument("-m", "--model", default="auto",
                        choices=["auto", "ml", "multilingual", "en", "english", "typed", "typed-decisions"],
                        help="Checkpoint a utilizar (default: auto - detección por Router)")
    p_pred.add_argument("--threads", type=int, default=4,
                        help="Número de hilos para CPU (default: 4 para Ryzen 3 5300U)")
    p_pred.add_argument("--json", action="store_true",
                        help="Salida pura en JSON para scripts y automatización")
    p_pred.add_argument("--get", type=str,
                        help="Imprime únicamente el valor de una pregunta concreta")

    # Subcomando: repl
    p_repl = subparsers.add_parser("repl", help="Inicia sesión interactiva con el modelo persistente en RAM")
    p_repl.add_argument("-p", "--preset", choices=list(PRESETS.keys()), default="triage",
                        help="Preset a utilizar en la sesión (default: triage)")
    p_repl.add_argument("-q", "--questions", type=str,
                        help="Preguntas personalizadas (@archivo.json)")
    p_repl.add_argument("-m", "--model", default="auto",
                        choices=["auto", "ml", "multilingual", "en", "english", "typed", "typed-decisions"],
                        help="Checkpoint a utilizar (default: auto)")
    p_repl.add_argument("--threads", type=int, default=4,
                        help="Número de hilos para CPU (default: 4)")

    # Subcomando: download
    p_dl = subparsers.add_parser("download", help="Pre-descarga un checkpoint para uso offline")
    p_dl.add_argument("-m", "--model", default="multilingual",
                      choices=["multilingual", "ml", "english", "en", "typed", "typed-decisions"],
                      help="Checkpoint a descargar (default: multilingual)")

    # Subcomando: presets
    subparsers.add_parser("presets", help="Lista los presets de preguntas predefinidos")

    # Si se invoca sin subcomandos o con flags directos como --state o --preset,
    # permitir compatibilidad directa como predict
    if len(sys.argv) > 1 and sys.argv[1] not in ("predict", "repl", "presets", "download", "-h", "--help"):
        # Se asume predict
        sys.argv.insert(1, "predict")

    args = parser.parse_args()

    if args.command == "predict":
        cmd_predict(args)
    elif args.command == "repl":
        cmd_repl(args)
    elif args.command == "presets":
        cmd_presets(args)
    elif args.command == "download":
        cmd_download(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
