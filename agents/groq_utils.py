"""
Utilitário centralizado de chamadas a LLM com fallback automático.

Ordem de tentativa:
  1. Google Gemini gemini-2.5-flash  ← modelo principal
  2. Groq llama-3.3-70b-versatile    ← fallback

Pacotes necessários: google-genai, groq
Chaves no .env: GEMINI_API_KEY, GROQ_API_KEY

Se ambos falharem, retorna mensagem amigável sem quebrar o pipeline.
"""

import os
from dotenv import load_dotenv

load_dotenv()

_MODELO_GEMINI = "gemini-2.5-flash"
_MODELO_GROQ   = "llama-3.3-70b-versatile"
_MSG_INDISPONIVEL = (
    "⏳ Serviço temporariamente indisponível. Tente em alguns minutos."
)


def _gemini(messages: list[dict], max_tokens: int) -> dict | None:
    """
    Tenta chamar o Gemini. Retorna dict de resultado ou None se falhar.
    Converte o formato [{role, content}] para a API google-genai.
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)

        # Separa system instruction das mensagens de conversa
        system_instruction = None
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_instruction = content
            else:
                # Gemini usa "user" e "model" (não "assistant")
                gemini_role = "model" if role == "assistant" else "user"
                contents.append({"role": gemini_role, "parts": [{"text": content}]})

        config = types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )

        resposta = client.models.generate_content(
            model=_MODELO_GEMINI,
            contents=contents,
            config=config,
        )

        tokens = 0
        if hasattr(resposta, "usage_metadata") and resposta.usage_metadata:
            tokens = getattr(resposta.usage_metadata, "total_token_count", 0)

        return {
            "texto": resposta.text or "",
            "tokens_usados": tokens,
            "modelo_usado": _MODELO_GEMINI,
            "erro": None,
        }

    except Exception:
        return None


def _groq(messages: list[dict], max_tokens: int) -> dict | None:
    """
    Tenta chamar o Groq. Retorna dict de resultado ou None se falhar.
    """
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None

    try:
        from groq import Groq

        client = Groq(api_key=key)
        resposta = client.chat.completions.create(
            model=_MODELO_GROQ,
            max_tokens=max_tokens,
            messages=messages,
        )
        return {
            "texto": resposta.choices[0].message.content,
            "tokens_usados": resposta.usage.total_tokens if resposta.usage else 0,
            "modelo_usado": _MODELO_GROQ,
            "erro": None,
        }

    except Exception:
        return None


def chamar_llm(
    messages: list[dict],
    max_tokens: int = 1000,
) -> dict:
    """
    Chama o LLM com fallback automático: Gemini → Groq.

    Parâmetros:
        messages:   Lista de dicts [{role, content}]
                    role pode ser "system", "user" ou "assistant"
        max_tokens: Limite de tokens na resposta

    Retorna dict com:
        texto         — conteúdo da resposta
        tokens_usados — tokens consumidos
        modelo_usado  — nome do modelo que respondeu
        erro          — None se sucesso, mensagem amigável se falhou
    """
    resultado = _gemini(messages, max_tokens)
    if resultado:
        return resultado

    resultado = _groq(messages, max_tokens)
    if resultado:
        return resultado

    return {
        "texto": "",
        "tokens_usados": 0,
        "modelo_usado": None,
        "erro": _MSG_INDISPONIVEL,
    }


# Alias para compatibilidade com imports existentes
chamar_groq = chamar_llm
