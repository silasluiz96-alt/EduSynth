import time

from agents.researcher import pesquisar
from agents.critic import analisar
from agents.synthesizer import sintetizar
from agents.strategist import Strategist
from agents.performance_analyst import PerformanceAnalyst


def _tempo(inicio: float) -> str:
    return f"{time.time() - inicio:.1f}s"


class EduSynth:
    """
    Orquestrador principal do pipeline EduSynth.

    Coordena os 5 agentes em sequência e expõe as funções de dica
    e gabarito do Estrategista para uso sob demanda.

    Uso típico:
        edu = EduSynth()
        resultado = edu.estudar("fordismo")

        # Quando o estudante pedir dica:
        dica = edu.request_hint("fordismo", resultado["material_final"]["questao_enem"], 1)
        gabarito = edu.request_gabarito("fordismo", resultado["material_final"]["questao_completa"])
    """

    def __init__(self):
        # Instâncias únicas para toda a sessão
        self._analista = PerformanceAnalyst()
        self._estrategista = Strategist()

    # ── Fluxo principal ───────────────────────────────────────────────────────

    def estudar(self, tema: str, area: str = "não informada") -> dict:
        """
        Executa o pipeline completo para um tema:
        Pesquisador → Crítico → Sintetizador → Analista (registro)

        Retorna dict com status, outputs de cada agente e tempos de execução.
        """
        resultado = {
            "tema": tema,
            "sucesso": False,
            "etapas": {
                "pesquisa": {"status": None, "tempo": None, "erro": None},
                "critica":  {"status": None, "tempo": None, "erro": None},
                "sintese":  {"status": None, "tempo": None, "erro": None},
                "registro": {"status": None, "tempo": None, "erro": None},
            },
            "resultado_pesquisador": None,
            "resultado_critico": None,
            "material_final": None,
        }

        # ── Passo 1: Pesquisador ──────────────────────────────────────────────
        print("🔍 Pesquisando conteúdo...")
        t0 = time.time()
        try:
            resultado_pesquisa = pesquisar(tema)
            resultado["etapas"]["pesquisa"]["tempo"] = _tempo(t0)

            if resultado_pesquisa.get("tipo_busca") == "erro":
                raise RuntimeError(resultado_pesquisa.get("erro", "erro na pesquisa"))

            resultado["etapas"]["pesquisa"]["status"] = "sucesso"
            resultado["resultado_pesquisador"] = resultado_pesquisa
            fontes = (
                len(resultado_pesquisa.get("conteudo_didatico", [])) +
                len(resultado_pesquisa.get("noticias_relevantes", [])) +
                len(resultado_pesquisa.get("referencias_academicas", []))
            )
            print(
                f"   ✓ {fontes} fontes encontradas "
                f"(modo: {resultado_pesquisa.get('tipo_busca', '')}) "
                f"— {resultado['etapas']['pesquisa']['tempo']}"
            )
        except Exception as e:
            resultado["etapas"]["pesquisa"]["status"] = "erro"
            resultado["etapas"]["pesquisa"]["erro"] = str(e)
            resultado["etapas"]["pesquisa"]["tempo"] = _tempo(t0)
            print(f"   ✗ Erro na pesquisa: {e}")
            return resultado

        # ── Passo 2: Crítico ──────────────────────────────────────────────────
        print("🧠 Analisando criticamente...")
        t0 = time.time()
        try:
            resultado_critica = analisar(resultado_pesquisa)
            resultado["etapas"]["critica"]["tempo"] = _tempo(t0)

            if resultado_critica.get("erro"):
                raise RuntimeError(resultado_critica["erro"])

            resultado["etapas"]["critica"]["status"] = "sucesso"
            resultado["resultado_critico"] = resultado_critica
            print(
                f"   ✓ Prioridade: {resultado_critica.get('nivel_prioridade', '—')} "
                f"| {resultado_critica.get('tokens_usados', 0)} tokens "
                f"— {resultado['etapas']['critica']['tempo']}"
            )
        except Exception as e:
            resultado["etapas"]["critica"]["status"] = "erro"
            resultado["etapas"]["critica"]["erro"] = str(e)
            resultado["etapas"]["critica"]["tempo"] = _tempo(t0)
            print(f"   ✗ Erro na análise crítica: {e}")
            return resultado

        # ── Passo 3: Sintetizador ─────────────────────────────────────────────
        print("📝 Gerando material de estudo...")
        t0 = time.time()
        try:
            snapshot = self._analista.snapshot()
            resultado_sintese = sintetizar(resultado_pesquisa, resultado_critica, snapshot)
            resultado["etapas"]["sintese"]["tempo"] = _tempo(t0)

            if resultado_sintese.get("erro"):
                raise RuntimeError(resultado_sintese["erro"])

            resultado["etapas"]["sintese"]["status"] = "sucesso"
            resultado["material_final"] = resultado_sintese
            print(
                f"   ✓ Material gerado "
                f"| {resultado_sintese.get('tokens_usados', 0)} tokens "
                f"— {resultado['etapas']['sintese']['tempo']}"
            )
        except Exception as e:
            resultado["etapas"]["sintese"]["status"] = "erro"
            resultado["etapas"]["sintese"]["erro"] = str(e)
            resultado["etapas"]["sintese"]["tempo"] = _tempo(t0)
            print(f"   ✗ Erro na síntese: {e}")
            return resultado

        # ── Passo 4: Analista registra a pesquisa ─────────────────────────────
        print("📊 Registrando sessão...")
        t0 = time.time()
        try:
            self._analista.register_search(tema, area)
            resultado["etapas"]["registro"]["status"] = "sucesso"
            resultado["etapas"]["registro"]["tempo"] = _tempo(t0)
        except Exception as e:
            # Falha no registro não interrompe o fluxo
            resultado["etapas"]["registro"]["status"] = "erro"
            resultado["etapas"]["registro"]["erro"] = str(e)
            resultado["etapas"]["registro"]["tempo"] = _tempo(t0)

        resultado["sucesso"] = True
        print("✅ Material pronto!")
        return resultado

    # ── Estrategista — ativado sob demanda ───────────────────────────────────

    def request_hint(self, tema: str, questao: dict, level: int) -> dict:
        """
        Solicita uma dica do Estrategista para a questão.

        Registra automaticamente o uso da dica no Analista de Desempenho.

        Parâmetros:
            tema: tema do material (para rastreamento)
            questao: dict com enunciado, alternativas etc. (questao_enem do material)
            level: nível da dica (1, 2 ou 3)
        """
        resultado = self._estrategista.get_hint(level, questao)

        if not resultado.get("erro"):
            try:
                self._analista.register_hint(tema, level)
            except Exception:
                pass

        return resultado

    def request_gabarito(self, tema: str, questao: dict) -> dict:
        """
        Solicita o gabarito comentado do Estrategista.

        Só é liberado após as 3 dicas terem sido apresentadas.
        Se o estudante pular as dicas, registra no Analista.

        Parâmetros:
            tema: tema do material (para rastreamento)
            questao: dict com enunciado e alternativas (questao_completa do material)
        """
        resultado = self._estrategista.get_gabarito(questao)

        if not resultado.get("erro"):
            try:
                # Se bloqueado, significa que pulou as dicas
                if resultado.get("bloqueado"):
                    self._analista.register_gabarito(tema)
            except Exception:
                pass

        return resultado

    # ── Relatório e utilitários ───────────────────────────────────────────────

    def relatorio_sessao(self) -> dict:
        """Gera o relatório completo de desempenho da sessão atual."""
        print("📊 Gerando relatório da sessão...")
        return self._analista.generate_report()

    def snapshot_sessao(self) -> dict:
        """Retorna o estado atual da sessão sem chamar a API."""
        return self._analista.snapshot()

    def status_dicas(self, questao: dict) -> dict:
        """Retorna quantas dicas foram dadas para uma questão e se o gabarito está disponível."""
        return self._estrategista.status(questao)


if __name__ == "__main__":
    edu = EduSynth()

    print(f"\nTema: fordismo\n{'─' * 50}\n")
    resultado = edu.estudar("fordismo", area="Ciências Humanas")

    print(f"\n{'─' * 50}")
    print("RESUMO DA EXECUÇÃO")
    print(f"{'─' * 50}")
    for etapa, dados in resultado["etapas"].items():
        status = dados.get("status", "—")
        tempo = dados.get("tempo", "—")
        erro = f"  ⚠ {dados['erro']}" if dados.get("erro") else ""
        print(f"  {etapa:<10} → {status:<8} ({tempo}){erro}")

    if resultado["sucesso"]:
        mat = resultado["material_final"]
        print(f"\n{'═' * 50}")
        print(f"INTRODUÇÃO:\n{mat.get('introducao', '')[:400]}...")
        print(f"\nQUESTÃO (sem gabarito):")
        q = mat.get("questao_enem", {})
        print(q.get("enunciado", ""))
        for letra, texto in q.get("alternativas", {}).items():
            print(f"  {letra}) {texto}")

        print(f"\n{'─' * 50}")
        print("Solicitando dica nível 1...")
        dica1 = edu.request_hint("fordismo", mat.get("questao_enem", {}), 1)
        if not dica1.get("erro"):
            print(dica1["dica"][:300] + "...")

        print(f"\nSnapshot da sessão: {edu.snapshot_sessao()}")
