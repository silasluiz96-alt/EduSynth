import sys
import os
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from agents.orchestrator import EduSynth


# ── Helpers ───────────────────────────────────────────────────────────────────
def _atualizar_dicas_historico(tema: str, nivel: int):
    """Atualiza o contador de dicas no histórico da sidebar."""
    hist = st.session_state["historico"]
    nova_hist = []
    for t, a, d in hist:
        if t == tema:
            nova_hist.append((t, a, max(d, nivel)))
        else:
            nova_hist.append((t, a, d))
    st.session_state["historico"] = nova_hist


# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="EduSynth — ENEM",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  :root {
    --azul: #1e3a5f;
    --azul-medio: #2563eb;
    --azul-claro: #dbeafe;
    --verde: #16a34a;
    --verde-claro: #dcfce7;
    --cinza: #f8fafc;
  }
  .stApp { background-color: var(--cinza); }

  .header {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 55%, #16a34a 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem 1.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
    color: white;
  }
  .header h1 { font-size: 2.2rem; font-weight: 800; margin: 0 0 .4rem; color: white; }
  .header p  { font-size: 1rem; opacity: .88; margin: 0 0 1rem; color: white; }
  .badges    { display: flex; justify-content: center; gap: .6rem; flex-wrap: wrap; }
  .badge {
    background: rgba(255,255,255,.18);
    border: 1px solid rgba(255,255,255,.35);
    border-radius: 20px;
    padding: .25rem .8rem;
    font-size: .82rem;
    font-weight: 600;
    color: white;
  }

  .dica-box {
    background: white;
    border-left: 4px solid #2563eb;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: .6rem 0;
    box-shadow: 0 1px 4px rgba(0,0,0,.07);
  }
  .gabarito-box {
    background: #f0fdf4;
    border-left: 4px solid #16a34a;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: .6rem 0;
  }
  .fonte-card {
    background: white;
    border-radius: 10px;
    padding: 1rem;
    margin: .5rem 0;
    box-shadow: 0 1px 4px rgba(0,0,0,.07);
  }
  .hist-item {
    background: var(--azul-claro);
    border-radius: 8px;
    padding: .35rem .7rem;
    margin: .25rem 0;
    font-size: .85rem;
    color: var(--azul);
  }
  .preview-v2 {
    background: linear-gradient(135deg, #1e3a5f, #2563eb);
    border-radius: 12px;
    padding: 1rem;
    color: white;
    font-size: .85rem;
    margin-top: 1rem;
  }
  #MainMenu { visibility: hidden; }
  footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "edu": None,               # instância EduSynth
        "historico": [],           # [(tema, area, dicas_usadas)]
        "resultado_atual": None,   # último resultado do pipeline
        "tema_input": "",
        # controle de dicas por sessão
        "nivel_dica_atual": 0,     # 0 = nenhuma, 1-3 = dica entregue, 4 = gabarito liberado
        "dicas_texto": [],         # textos das dicas já exibidas
        "gabarito_texto": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

def _get_edu() -> EduSynth:
    """Garante instância única do orquestrador na sessão."""
    if st.session_state["edu"] is None:
        st.session_state["edu"] = EduSynth()
    return st.session_state["edu"]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header">
  <h1>🎓 EduSynth</h1>
  <p>Powered by IA Generativa — 4 agentes trabalhando para você</p>
  <div class="badges">
    <span class="badge">🔍 Pesquisador</span>
    <span class="badge">🧠 Crítico</span>
    <span class="badge">📝 Sintetizador</span>
    <span class="badge">💡 Estrategista</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📚 Sessão Atual")

    if not st.session_state["historico"]:
        st.caption("Nenhum tema pesquisado ainda.")
    else:
        for entrada in reversed(st.session_state["historico"]):
            tema_h, area_h, dicas_h = entrada
            label = f"{'💡' * min(dicas_h, 3)} {tema_h}" if dicas_h else f"📖 {tema_h}"
            if st.button(label, key=f"hist_{tema_h}", use_container_width=True):
                st.session_state["tema_input"] = tema_h
                st.rerun()

    st.divider()

    if st.button("📊 Ver relatório da sessão", use_container_width=True):
        edu = _get_edu()
        with st.spinner("Gerando relatório..."):
            relatorio = edu.relatorio_sessao()
        st.markdown("### 📊 Relatório da Sessão")
        st.markdown(relatorio.get("resumo_sessao", ""))
        fracos = relatorio.get("pontos_fracos", [])
        if fracos:
            st.markdown("**Top pontos de atenção:**")
            for pf in fracos:
                st.markdown(f"- {pf['tema']} (score: {pf['score_dificuldade']})")

    st.markdown("""
    <div class="preview-v2">
      <b>🚀 Em breve — EduSynth v2</b><br><br>
      Com Supabase integrado:<br>
      • Histórico entre sessões<br>
      • Mapa de pontos fracos<br>
      • Plano de estudos personalizado<br>
      • Alertas proativos<br><br>
      <i>Acompanhe no GitHub</i>
    </div>
    """, unsafe_allow_html=True)

# ── Exemplos clicáveis ────────────────────────────────────────────────────────
exemplos = [
    "Revolução Industrial",
    "Fotossíntese",
    "Função Quadrática",
    "Aquecimento Global",
    "Modernismo Brasileiro",
]

cols = st.columns(len(exemplos))
for col, ex in zip(cols, exemplos):
    with col:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state["tema_input"] = ex
            st.rerun()

st.markdown("")

# ── Input principal ───────────────────────────────────────────────────────────
col_inp, col_btn = st.columns([5, 1])
with col_inp:
    tema_digitado = st.text_input(
        "Tema",
        value=st.session_state["tema_input"],
        placeholder="Ex: fordismo, aquecimento global, função quadrática...",
        label_visibility="collapsed",
    )
with col_btn:
    iniciar = st.button("🚀 Estudar Agora", type="primary", use_container_width=True)

# ── Execução do pipeline ──────────────────────────────────────────────────────
if iniciar and tema_digitado.strip():
    tema = tema_digitado.strip()
    st.session_state["tema_input"] = tema
    st.session_state["nivel_dica_atual"] = 0
    st.session_state["dicas_texto"] = []
    st.session_state["gabarito_texto"] = None

    st.markdown("---")
    st.markdown(f"### Gerando material: **{tema}**")

    barra = st.progress(0, text="Iniciando...")
    status = st.empty()

    edu = _get_edu()
    erro_geral = None

    try:
        barra.progress(10, text="🔍 Passo 1 de 4 — Pesquisando conteúdo...")
        with status.container():
            st.info("🔍 **Pesquisador** buscando fontes didáticas, notícias e referências acadêmicas...")

        r_pesquisa = edu._analista  # força inicialização
        from agents.researcher import pesquisar as _pesquisar
        from agents.critic import analisar as _analisar
        from agents.synthesizer import sintetizar as _sintetizar

        r_pesquisa = _pesquisar(tema)
        if r_pesquisa.get("tipo_busca") == "erro":
            raise RuntimeError(r_pesquisa.get("erro", "Erro na pesquisa"))

        total_fontes = (
            len(r_pesquisa.get("conteudo_didatico", [])) +
            len(r_pesquisa.get("noticias_relevantes", [])) +
            len(r_pesquisa.get("referencias_academicas", []))
        )
        barra.progress(30, text="🔍 Pesquisa concluída!")
        with status.container():
            st.success(f"🔍 Pesquisa concluída — {total_fontes} fontes ({r_pesquisa.get('tipo_busca', '')})")

        barra.progress(40, text="🧠 Passo 2 de 4 — Análise crítica...")
        with status.container():
            st.info("🧠 **Crítico** analisando frequência no ENEM, erros comuns e conexões interdisciplinares...")

        r_critica = _analisar(r_pesquisa)
        if r_critica.get("erro"):
            raise RuntimeError(r_critica["erro"])

        barra.progress(60, text="🧠 Análise concluída!")
        with status.container():
            st.success(
                f"🧠 Análise concluída — prioridade: {r_critica.get('nivel_prioridade', '—')} "
                f"| {r_critica.get('tokens_usados', 0)} tokens"
            )

        barra.progress(70, text="📝 Passo 3 de 4 — Gerando material...")
        with status.container():
            st.info("📝 **Sintetizador** criando material de estudo, questão ENEM e análise de palavras-chave...")

        snapshot = edu._analista.snapshot()
        r_sintese = _sintetizar(r_pesquisa, r_critica, snapshot)
        if r_sintese.get("erro"):
            raise RuntimeError(r_sintese["erro"])

        barra.progress(90, text="📊 Passo 4 de 4 — Registrando sessão...")
        with status.container():
            st.info("📊 **Analista** registrando dados da sessão...")

        edu._analista.register_search(tema)
        barra.progress(100, text="✅ Material pronto!")
        with status.container():
            st.success(
                f"✅ Pronto! {r_sintese.get('tokens_usados', 0)} tokens usados na síntese."
            )

        st.session_state["resultado_atual"] = {
            "tema": tema,
            "pesquisa": r_pesquisa,
            "critica": r_critica,
            "sintese": r_sintese,
        }

        # Atualiza histórico
        hist = st.session_state["historico"]
        hist = [(t, a, d) for t, a, d in hist if t != tema]  # remove duplicata
        hist.append((tema, "não informada", 0))
        st.session_state["historico"] = hist

    except Exception as e:
        barra.progress(100, text="❌ Erro")
        with status.container():
            st.error(f"❌ {e}")

# ── Resultado em abas ─────────────────────────────────────────────────────────
if st.session_state["resultado_atual"]:
    res = st.session_state["resultado_atual"]
    pesquisa = res["pesquisa"]
    critica  = res["critica"]
    sintese  = res["sintese"]
    edu      = _get_edu()

    st.markdown("---")
    aba1, aba2, aba3, aba4 = st.tabs([
        "📚 Material de Estudo",
        "🔍 Fontes Pesquisadas",
        "🧠 Análise Crítica",
        "📊 Minha Sessão",
    ])

    # ── Aba 1: Material de Estudo ─────────────────────────────────────────────
    with aba1:
        st.markdown(f"## 📚 {sintese.get('tema', '').upper()}")

        intro = sintese.get("introducao", "")
        if intro:
            st.markdown("### 🔍 Introdução")
            st.markdown(intro)

        pontos = sintese.get("pontos_essenciais", [])
        if pontos:
            st.markdown("### ⭐ Pontos Essenciais")
            for p in pontos:
                enem = " *(mais cobrado no ENEM)*" if p.get("cobrado_enem") else ""
                st.markdown(f"**{p.get('conceito', '')}**{enem}")
                st.markdown(f"> {p.get('definicao', '')}")
                st.caption(f"Exemplo: {p.get('exemplo', '')}")

        conexoes = sintese.get("conexoes_interdisciplinares", [])
        if conexoes:
            st.markdown("### 🔗 Conexões Interdisciplinares")
            for c in conexoes:
                with st.expander(f"📌 {c.get('disciplina', '')}"):
                    st.markdown(c.get("como_se_conecta", ""))
                    if c.get("exemplo_enem"):
                        st.caption(f"ENEM: {c['exemplo_enem']}")

        dicas_prova = sintese.get("dicas_de_prova", [])
        if dicas_prova:
            st.markdown("### 🎯 Dicas de Prova")
            for d in dicas_prova:
                st.markdown(f"- {d}")

        leituras = sintese.get("leituras_recomendadas", {})
        if leituras:
            st.markdown("### 📖 Leituras Recomendadas")
            for ind in leituras.get("indicacoes", []):
                st.markdown(f"- **{ind.get('tipo', '')}**: {ind.get('titulo', '')} — {ind.get('onde_encontrar', '')}")
            kws = leituras.get("palavras_chave_scholar", [])
            if kws:
                st.caption(f"Google Scholar: {', '.join(kws)}")
            ex_busca = leituras.get("exemplo_busca", "")
            if ex_busca:
                st.caption(f"Como buscar: {ex_busca}")

        # Questão ENEM
        questao = sintese.get("questao_enem", {})
        if questao:
            st.markdown("---")
            st.markdown("### 📝 Questão Estilo ENEM")

            if questao.get("texto_apoio"):
                st.info(questao["texto_apoio"])

            st.markdown(f"**{questao.get('enunciado', '')}**")
            for letra in ["A", "B", "C", "D", "E"]:
                texto_alt = questao.get("alternativas", {}).get(letra, "")
                if texto_alt:
                    st.markdown(f"**{letra})** {texto_alt}")

            # Análise de palavras-chave
            analise_kw = sintese.get("analise_palavras_chave", {})
            if analise_kw:
                with st.expander("🔎 Análise de Palavras-Chave"):
                    enunciado_kw = analise_kw.get("no_enunciado", {})
                    if enunciado_kw:
                        st.markdown("**No enunciado:**")
                        for c in enunciado_kw.get("conectivos", []):
                            st.markdown(f"- 🔄 {c}")
                        for d in enunciado_kw.get("delimitadores", []):
                            st.markdown(f"- ⏱️ {d}")
                        if enunciado_kw.get("comando"):
                            st.markdown(f"- 🎯 Comando: {enunciado_kw['comando']}")
                    alts_kw = analise_kw.get("nas_alternativas", {})
                    if alts_kw:
                        st.markdown("**Nas alternativas:**")
                        for a in alts_kw.get("absolutismo_armadilha", []):
                            st.markdown(f"- 🚨 {a}")
                        for p in alts_kw.get("pegadinhas_vocabulario", []):
                            st.markdown(f"- 🎭 {p}")
                        if alts_kw.get("marcadores_correto"):
                            st.markdown(f"- ✔️ {alts_kw['marcadores_correto']}")

            # ── Seção de dicas do Estrategista ────────────────────────────────
            st.markdown("---")
            st.markdown("#### 💡 Precisa de ajuda para resolver?")

            nivel = st.session_state["nivel_dica_atual"]
            dicas_exibidas = st.session_state["dicas_texto"]

            # Exibe dicas já obtidas
            for i, texto_dica in enumerate(dicas_exibidas, start=1):
                st.markdown(
                    f'<div class="dica-box"><b>💡 Dica {i}</b><br>{texto_dica}</div>',
                    unsafe_allow_html=True,
                )

            # Exibe gabarito se liberado
            if st.session_state["gabarito_texto"]:
                st.markdown(
                    f'<div class="gabarito-box"><b>✅ Gabarito Comentado</b><br>'
                    f'{st.session_state["gabarito_texto"]}</div>',
                    unsafe_allow_html=True,
                )

            # Botões progressivos
            if nivel == 0:
                if st.button("💡 Preciso de uma dica", key="btn_dica_1"):
                    with st.spinner("Preparando dica 1..."):
                        r = edu.request_hint(res["tema"], questao, 1)
                    if not r.get("erro"):
                        st.session_state["dicas_texto"].append(r["dica"])
                        st.session_state["nivel_dica_atual"] = 1
                        _atualizar_dicas_historico(res["tema"], 1)
                    st.rerun()

            elif nivel == 1:
                if st.button("💡 Mais uma dica", key="btn_dica_2"):
                    with st.spinner("Preparando dica 2..."):
                        r = edu.request_hint(res["tema"], questao, 2)
                    if not r.get("erro"):
                        st.session_state["dicas_texto"].append(r["dica"])
                        st.session_state["nivel_dica_atual"] = 2
                        _atualizar_dicas_historico(res["tema"], 2)
                    st.rerun()

            elif nivel == 2:
                if st.button("💡 Mais uma dica", key="btn_dica_3"):
                    with st.spinner("Preparando dica 3..."):
                        r = edu.request_hint(res["tema"], questao, 3)
                    if not r.get("erro"):
                        st.session_state["dicas_texto"].append(r["dica"])
                        st.session_state["nivel_dica_atual"] = 3
                        _atualizar_dicas_historico(res["tema"], 3)
                    st.rerun()

            elif nivel == 3 and not st.session_state["gabarito_texto"]:
                questao_completa = sintese.get("questao_completa", questao)
                if st.button("✅ Ver gabarito", key="btn_gabarito"):
                    with st.spinner("Carregando gabarito..."):
                        r = edu.request_gabarito(res["tema"], questao_completa)
                    if not r.get("erro") and not r.get("bloqueado"):
                        st.session_state["gabarito_texto"] = r["gabarito"]
                        st.session_state["nivel_dica_atual"] = 4
                    st.rerun()

    # ── Aba 2: Fontes Pesquisadas ─────────────────────────────────────────────
    with aba2:
        st.markdown(f"### 🔍 Fontes Pesquisadas — {pesquisa.get('tipo_busca', '')}")
        resumo = pesquisa.get("resumo", "")
        if resumo:
            st.info(resumo)

        grupos = [
            ("📘 Conteúdo Didático", pesquisa.get("conteudo_didatico", [])),
            ("📰 Notícias Recentes", pesquisa.get("noticias_relevantes", [])),
            ("🎓 Referências Acadêmicas", pesquisa.get("referencias_academicas", [])),
        ]
        for titulo, fontes in grupos:
            if fontes:
                st.markdown(f"#### {titulo} ({len(fontes)})")
                for f in fontes:
                    with st.expander(f.get("titulo", "Sem título")):
                        st.markdown(f"🔗 [{f.get('url', '')}]({f.get('url', '')})")
                        st.markdown(f.get("conteudo", ""))

        lacunas = pesquisa.get("lacunas_e_aprofundamento", [])
        if lacunas:
            st.markdown("#### ⚠️ Lacunas Identificadas")
            for l in lacunas:
                with st.expander(f"Camada: {l.get('camada', '')}"):
                    st.markdown(l.get("descricao", ""))
                    kw_pt = l.get("palavras_chave_pt", [])
                    kw_en = l.get("palavras_chave_en", [])
                    if kw_pt:
                        st.caption(f"Buscar em PT: {', '.join(kw_pt)}")
                    if kw_en:
                        st.caption(f"Buscar em EN: {', '.join(kw_en)}")

    # ── Aba 3: Análise Crítica ────────────────────────────────────────────────
    with aba3:
        st.markdown("### 🧠 Análise Crítica do Professor")
        prioridade_cor = {"alta": "🔴", "média": "🟡", "baixa": "🟢"}.get(
            critica.get("nivel_prioridade", "").lower(), "⚪"
        )
        st.markdown(
            f"**Prioridade de estudo:** {prioridade_cor} {critica.get('nivel_prioridade', '—').upper()}"
            f" — {critica.get('justificativa_prioridade', '')}"
        )

        freq = critica.get("frequencia_enem", {})
        if freq:
            st.markdown("#### 📊 Frequência no ENEM")
            st.markdown(freq.get("descricao", ""))
            areas = freq.get("areas", [])
            if areas:
                st.caption(f"Áreas: {' | '.join(areas)} — Profundidade: {freq.get('profundidade', '')}")

        erros = critica.get("erros_comuns", [])
        if erros:
            st.markdown("#### ⚠️ Erros Mais Comuns")
            for e in erros:
                with st.expander(f"❌ {e.get('erro', '')}"):
                    st.markdown(f"**Por que acontece:** {e.get('explicacao', '')}")
                    st.markdown(f"**Como evitar:** {e.get('como_evitar', '')}")

        conexoes_c = critica.get("conexoes_interdisciplinares", [])
        if conexoes_c:
            st.markdown("#### 🔗 Conexões Interdisciplinares")
            for c in conexoes_c:
                with st.expander(f"📌 {c.get('disciplina', '')}"):
                    st.markdown(c.get("conexao", ""))
                    if c.get("exemplo_enem"):
                        st.caption(f"ENEM: {c['exemplo_enem']}")

        criticos = critica.get("pontos_criticos", [])
        if criticos:
            st.markdown("#### 🎯 Pontos Críticos Obrigatórios")
            for p in criticos:
                ancora = " 🔑" if p.get("ancora") else ""
                imp = p.get("importancia", "")
                st.markdown(f"**{p.get('conceito', '')}**{ancora} *({imp})*")
                st.markdown(f"> {p.get('descricao', '')}")

        ctx = critica.get("contexto_atual", {})
        if ctx:
            st.markdown("#### 🌍 Contexto Atual")
            if ctx.get("eventos_recentes"):
                st.markdown(f"**Eventos:** {ctx['eventos_recentes']}")
            if ctx.get("dados_estatisticos"):
                st.markdown(f"**Dados:** {ctx['dados_estatisticos']}")
            if ctx.get("debate_atual"):
                st.markdown(f"**Debate:** {ctx['debate_atual']}")

    # ── Aba 4: Minha Sessão ───────────────────────────────────────────────────
    with aba4:
        st.markdown("### 📊 Minha Sessão")
        snap = edu.snapshot_sessao()
        temas_sess = snap.get("temas_estudados", [])
        difs = snap.get("dificuldade_por_tema", {})

        if temas_sess:
            st.markdown(f"**Temas estudados:** {len(temas_sess)}")
            st.markdown(f"**Duração:** {snap.get('duracao_min', 0):.1f} min")
            for t in temas_sess:
                dif = difs.get(t, "—")
                icone = {"fácil": "🟢", "médio": "🟡", "difícil": "🔴"}.get(dif, "⚪")
                st.markdown(f"{icone} **{t}** — {dif}")
        else:
            st.info("Nenhum dado de sessão ainda.")

        if st.button("📊 Gerar Relatório Completo", key="btn_relatorio_aba4"):
            with st.spinner("Gerando relatório com IA..."):
                relatorio = edu.relatorio_sessao()
            st.markdown(relatorio.get("resumo_sessao", ""))
            st.markdown(f"\n\n*{relatorio.get('preview_v2', '')}*")

elif not iniciar:
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem;color:#64748b;">
      <div style="font-size:3.5rem">🎓</div>
      <h3 style="color:#64748b">Como o EduSynth funciona</h3>
      <p>Digite um tema do ENEM ou clique em um exemplo acima.<br>
      Quatro agentes de IA trabalham em sequência para criar seu material.</p>
      <br>
      <div style="display:flex;justify-content:center;gap:1.5rem;flex-wrap:wrap">
        <div style="background:white;border-radius:12px;padding:1rem 1.5rem;box-shadow:0 2px 8px rgba(0,0,0,.08);min-width:140px">
          <div style="font-size:1.8rem">🔍</div><b>Pesquisador</b><br>
          <small>3 camadas: didático, notícias e acadêmico</small>
        </div>
        <div style="background:white;border-radius:12px;padding:1rem 1.5rem;box-shadow:0 2px 8px rgba(0,0,0,.08);min-width:140px">
          <div style="font-size:1.8rem">🧠</div><b>Crítico</b><br>
          <small>Frequência no ENEM, erros e conexões</small>
        </div>
        <div style="background:white;border-radius:12px;padding:1rem 1.5rem;box-shadow:0 2px 8px rgba(0,0,0,.08);min-width:140px">
          <div style="font-size:1.8rem">📝</div><b>Sintetizador</b><br>
          <small>Material + questão + análise de palavras</small>
        </div>
        <div style="background:white;border-radius:12px;padding:1rem 1.5rem;box-shadow:0 2px 8px rgba(0,0,0,.08);min-width:140px">
          <div style="font-size:1.8rem">💡</div><b>Estrategista</b><br>
          <small>3 dicas progressivas antes do gabarito</small>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
