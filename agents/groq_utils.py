"""
Utilitário centralizado de chamadas a LLM com fallback automático.

Ordem de tentativa:
  1. Google Gemini gemini-1.5-flash  ← modelo principal
  2. Groq llama-3.3-70b-versatile    ← fallback

Se ambos falharem, retorna mensagem amigável sem quebrar o pipeline.
Chaves carregadas do .env: GEMINI_API_KEY, GROQ_API_KEY
"""

import os
from dotenv import load_dotenv

load_dotenv()

_MODELO_GEMINI = "gemini-1.5-flash"
_MODELO_GROQ   = "llama-3.3-70b-versatile"
_MSG_INDISPONIVEL = (
    "⏳ Serviço temporariamente indisponível. Tente em alguns minutos."
)


def chamar_llm(
    messages: list[dict],
    max_tokens: int = 1000,
) -> dict:
    """
    Chama o LLM com fallback automático: Gemini → Groq.

    Parâmetros:
        messages:   Lista de dicts no formato [{role, content}, ...]
                    O primeiro item com role="system" é usado como system_instruction
                    no Gemini; os demais como histórico de conversa.
        max_tokens: Limite de tokens na resposta.

    Retorna dict com:
        texto         — conteúdo da resposta (str)
        tokens_usados — total de tokens consumidos, se disponível (int)
        modelo_usado  — nome do modelo que respondeu (str)
        erro          — None se sucesso, mensagem amigável se falhou (str | None)
    """
    # ── 1ª tentativa: Gemini ─────────────────────────────────────────────────
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai

            genai.configure(api_key=gemini_key)

            # Separa system instruction das mensagens de conversa
            system_instruction = None
            conv_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                else:
                    # Gemini usa "user" e "model" (não "assistant")
                    role = "model" if msg["role"] == "assistant" else msg["role"]
                    conv_messages.append({"role": role, "parts": [msg["content"]]})

            modelo = genai.GenerativeModel(
                model_name=_MODELO_GEMINI,
                system_instruction=system_instruction,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=max_tokens,
                ),
            )

            # Usa a última mensagem como prompt, o restante como histórico
            if conv_messages:
                historico = conv_messages[:-1]
                prompt    = conv_messages[-1]["parts"][0]
                chat = modelo.start_chat(history=historico)
                resposta = chat.send_message(prompt)
            else:
                resposta = modelo.generate_content("")

            texto = resposta.text or ""
            tokens = 0
            if hasattr(resposta, "usage_metadata") and resposta.usage_metadata:
                tokens = getattr(resposta.usage_metadata, "total_token_count", 0)

            return {
                "texto": texto,
                "tokens_usados": tokens,
                "modelo_usado": _MODELO_GEMINI,
                "erro": None,
            }

        except Exception:
            pass  # Qualquer falha do Gemini → tenta Groq

    # ── 2ª tentativa: Groq ───────────────────────────────────────────────────
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq

            client  = Groq(api_key=groq_key)
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
            pass  # Groq também falhou

    # ── Ambos falharam ───────────────────────────────────────────────────────
    return {
        "texto": "",
        "tokens_usados": 0,
        "modelo_usado": None,
        "erro": _MSG_INDISPONIVEL,
    }


# Mantém chamar_groq como alias para não quebrar importações existentes
chamar_groq = chamar_llm
