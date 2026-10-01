import base64
import json
import os
import requests
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Gerenciador de Propostas Político",
    page_icon="🗳️",
    layout="wide",
)

PRIMARY_COLOR = "#016F80"
SECONDARY_COLOR = "#556373"

st.markdown(
    f"""
    <style>
    .stButton>button {{
        background-color: {PRIMARY_COLOR};
        color: white;
        border-radius: 4px;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: #014d59;
        color: white;
    }}
    h1, h2, h3 {{
        color: {SECONDARY_COLOR};
    }}
    </style>
""",
    unsafe_allow_html=True,
)

DATA_FILE = "dados_eleicoes.json"


def carregar_dados():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      pass
  return {"temas": [], "cargos": [], "candidatos": []}


def salvar_e_sincronizar_dados(dados):
  # 1. Salva localmente
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)

  # 2. Sincroniza automaticamente com o GitHub usando os Secrets configurados
  if "GITHUB_TOKEN" in st.secrets:
    try:
      token = st.secrets["GITHUB_TOKEN"]
      repo = st.secrets["GITHUB_REPO"]
      branch = st.secrets.get("GITHUB_BRANCH", "main")

      url = f"https://api.github.com/repos/{repo}/contents/{DATA_FILE}"
      headers = {
          "Authorization": f"Bearer {token}",
          "Accept": "application/vnd.github+json",
      }

      response_get = requests.get(url, headers=headers)
      sha = (
          response_get.json().get("sha")
          if response_get.status_code == 200
          else None
      )

      conteudo_str = json.dumps(dados, ensure_ascii=False, indent=4)
      conteudo_base64 = base64.b64encode(conteudo_str.encode("utf-8")).decode(
          "utf-8"
      )

      payload = {
          "message": (
              "Atualização automática de propostas via Streamlit [skip ci]"
          ),
          "content": conteudo_base64,
          "branch": branch,
      }
      if sha:
        payload["sha"] = sha

      response_put = requests.put(url, headers=headers, json=payload)
      if response_put.status_code in [200, 201]:
        st.toast(
            "✅ Dados salvos e sincronizados com o GitHub com sucesso!",
            icon="🚀",
        )
      else:
        st.warning(
            "⚠️ Dados salvos localmente, mas a sincronização com o GitHub"
            f" retornou erro: {response_put.status_code}"
        )
    except Exception as e:
      st.error(f"Erro ao sincronizar com o GitHub: {e}")
  else:
    st.toast("✅ Dados salvos localmente!", icon="💾")


if "dados" not in st.session_state:
  st.session_state["dados"] = carregar_dados()

dados = st.session_state["dados"]

# Menu lateral de navegação
st.sidebar.title("🗳️️ Gestão de Propostas")
menu = st.sidebar.selectbox(
    "Navegar para",
    [
        "Visualizar Embed / App Final",
        "1. Gerenciar Temas",
        "2. Gerenciar Cargos",
        "3. Cadastrar e Editar Candidatos",
    ],
)

# ---------------------------------------------------------
# 1. CRIAÇÃO DE TEMAS
# ---------------------------------------------------------
if menu == "1. Gerenciar Temas":
  st.header("1. Criação e Gestão de Temas")

  novo_tema = st.text_input(
      "Nome do Tema (ex: 1. Economia, Trabalho e Responsabilidade Fiscal)",
      key="input_novo_tema",
  )
  if st.button("Adicionar Tema"):
    if novo_tema:
      if novo_tema not in dados["temas"]:
        dados["temas"].append(novo_tema)
        salvar_e_sincronizar_dados(dados)
        st.success(f"Tema '{novo_tema}' cadastrado com sucesso!")
        st.rerun()
      else:
        st.warning("Este tema já está cadastrado.")
    else:
      st.error("Digite o nome do tema.")

  st.subheader("Temas Cadastrados:")
  if dados["temas"]:
    for i, t in enumerate(dados["temas"]):
      col1, col2 = st.columns([0.8, 0.2])
      col1.write(f"- {t}")
      if col2.button("Excluir", key=f"del_tema_{i}"):
        dados["temas"].pop(i)
        salvar_e_sincronizar_dados(dados)
        st.rerun()
  else:
    st.info("Nenhum tema cadastrado ainda.")

# ---------------------------------------------------------
# 2. CRIAÇÃO DE CARGOS
# ---------------------------------------------------------
elif menu == "2. Gerenciar Cargos":
  st.header("2. Criação e Gestão de Cargos")

  novo_cargo = st.text_input(
      "Nome do Cargo (ex: Presidente, Governador)", key="input_novo_cargo"
  )
  if st.button("Adicionar Cargo"):
    if novo_cargo:
      if novo_cargo not in dados["cargos"]:
        dados["cargos"].append(novo_cargo)
        salvar_e_sincronizar_dados(dados)
        st.success(f"Cargo '{novo_cargo}' cadastrado com sucesso!")
        st.rerun()
      else:
        st.warning("Este cargo já está cadastrado.")
    else:
      st.error("Digite o nome do cargo.")

  st.subheader("Cargos Cadastrados:")
  if dados["cargos"]:
    for i, c in enumerate(dados["cargos"]):
      col1, col2 = st.columns([0.8, 0.2])
      col1.write(f"- {c}")
      if col2.button("Excluir", key=f"del_cargo_{i}"):
        dados["cargos"].pop(i)
        salvar_e_sincronizar_dados(dados)
        st.rerun()
  else:
    st.info("Nenhum cargo cadastrado ainda.")

# ---------------------------------------------------------
# 3. CADASTRO E EDIÇÃO DE CANDIDATOS E PROPOSTAS
# ---------------------------------------------------------
elif menu == "3. Cadastrar e Editar Candidatos":
  st.header("3. Gerenciamento de Candidatos e Propostas")

  if not dados["temas"] or not dados["cargos"]:
    st.warning(
        "⚠️ Cadastre pelo menos um **Tema** e um **Cargo** antes de registrar"
        " candidatos."
    )
  else:
    modo_edicao = False
    candidato_selecionado = None
    idx_candidato = None

    if dados["candidatos"]:
      # Exibe apenas o nome do candidato no select[cite: 6]
      nomes_candidatos = ["-- Novo Candidato --"] + [
          c["nome"] for c in dados["candidatos"]
      ]
      escolha_edicao = st.selectbox(
          "Deseja cadastrar um novo candidato ou editar um existente?",
          nomes_candidatos,
          key="select_modo_candidato",
      )
      if escolha_edicao != "-- Novo Candidato --":
        modo_edicao = True
        idx_candidato = nomes_candidatos.index(escolha_edicao) - 1
        candidato_selecionado = dados["candidatos"][idx_candidato]

    st.markdown("---")
    sub_titulo = (
        f"Editando Candidato: {candidato_selecionado['nome']}"
        if modo_edicao
        else "Cadastrar Novo Candidato"
    )
    st.subheader(sub_titulo)

    # Valores padrão para os inputs
    def_nome = candidato_selecionado["nome"] if modo_edicao else ""
    def_num = candidato_selecionado.get("numero", "") if modo_edicao else ""
    def_partido = candidato_selecionado["partido"] if modo_edicao else ""
    def_sigla = candidato_selecionado.get("sigla", "") if modo_edicao else ""
    def_cargo = (
        candidato_selecionado["cargo"]
        if modo_edicao
        else dados["cargos"][0]
    )
    def_foto = candidato_selecionado.get("foto", "") if modo_edicao else ""
    def_propostas = (
        candidato_selecionado.get("propostas", {}) if modo_edicao else {}
    )

    col1, col2, col3 = st.columns(3)
    with col1:
      nome_candidato = st.text_input(
          "Nome do Candidato", value=def_nome, key="cand_nome"
      )
      numero_candidato = st.text_input(
          "Número do Candidato", value=def_num, key="cand_num"
      )
    with col2:
      partido = st.text_input(
          "Partido / Coligação", value=def_partido, key="cand_partido"
      )
      sigla = st.text_input(
          "Sigla (ex: PT, PL, MDB)", value=def_sigla, key="cand_sigla"
      )
    with col3:
      try:
        cargo_index = dados["cargos"].index(def_cargo)
      except ValueError:
        cargo_index = 0
      cargo_selecionado = st.selectbox(
          "Cargo", dados["cargos"], index=cargo_index, key="cand_cargo"
      )
      foto_url = st.text_input(
          "URL da Foto",
          value=def_foto,
          placeholder="https://exemplo.com/foto.jpg",
          key="cand_foto",
      )

    st.markdown("---")
    st.subheader("Propostas por Tema")

    propostas_candidato = {}
    for tema_idx, tema in enumerate(dados["temas"]):
      with st.expander(f"📌 Propostas para: {tema}"):
        state_key = f"propostas_lista_{tema_idx}"

        # Inicializa o estado das propostas do tema
        if state_key not in st.session_state or (
            modo_edicao and f"loaded_{idx_candidato}_{tema}" not in st.session_state
        ):
          propostas_existentes = def_propostas.get(tema, [])
          if propostas_existentes:
            st.session_state[state_key] = [
                dict(p) for p in propostas_existentes
            ]
          else:
            st.session_state[state_key] = [{"descricao": "", "links": []}]
          if modo_edicao:
            st.session_state[f"loaded_{idx_candidato}_{tema}"] = True

        if st.button(
            f"➕ Adicionar Proposta em {tema}", key=f"add_prop_{tema_idx}"
        ):
          st.session_state[state_key].append({"descricao": "", "links": []})

        lista_itens_tema = []
        for p_idx, prop_item in enumerate(
            st.session_state[state_key].copy()
        ):
          col_p1, col_p2 = st.columns([0.9, 0.1])
          col_p1.markdown(f"**Proposta {p_idx+1}**")
          if col_p2.button(
              "🗑️", key=f"del_prop_item_{tema_idx}_{p_idx}", help="Remover proposta"
          ):
            st.session_state[state_key].pop(p_idx)
            st.rerun()

          desc = st.text_area(
              "Descrição da Proposta",
              value=prop_item.get("descricao", ""),
              key=f"desc_{tema_idx}_{p_idx}",
          )

          st.markdown("🔗 *Links / Referências da Proposta:*")
          links_lista = []

          links_state_key = f"links_lista_{tema_idx}_{p_idx}"
          if links_state_key not in st.session_state:
            st.session_state[links_state_key] = prop_item.get("links", [])

          if st.button(
              "➕ Adicionar Link", key=f"add_link_{tema_idx}_{p_idx}"
          ):
            st.session_state[links_state_key].append(
                {"label": "", "url": ""}
            )

          for l_idx, link_item in enumerate(
              st.session_state[links_state_key].copy()
          ):
            l_col1, l_col2, l_col3 = st.columns([0.4, 0.5, 0.1])
            l_label = l_col1.text_input(
                "Label (ex: Página 5)",
                value=link_item.get("label", ""),
                key=f"llabel_{tema_idx}_{p_idx}_{l_idx}",
            )
            l_url = l_col2.text_input(
                "URL ou Referência",
                value=link_item.get("url", ""),
                key=f"lurl_{tema_idx}_{p_idx}_{l_idx}",
            )
            if l_col3.button(
                "🗑️", key=f"dellink_{tema_idx}_{p_idx}_{l_idx}"
            ):
              st.session_state[links_state_key].pop(l_idx)
              st.rerun()

            if l_label or l_url:
              links_lista.append({"label": l_label, "url": l_url})

          st.markdown("---")
          if desc:
            lista_itens_tema.append({"descricao": desc, "links": links_lista})

        if lista_itens_tema:
          propostas_candidato[tema] = lista_itens_tema

    # --- BOTÃO ÚNICO DE SALVAR ---
    botao_label = (
        "Salvar Alterações do Candidato"
        if modo_edicao
        else "Salvar Novo Candidato"
    )

    if st.button(botao_label, key="btn_salvar_candidato_unico"):
      if nome_candidato and partido:
        novo_registro = {
            "nome": nome_candidato,
            "numero": numero_candidato,
            "partido": partido,
            "sigla": sigla,
            "cargo": cargo_selecionado,
            "foto": (
                foto_url
                if foto_url
                else "https://via.placeholder.com/150?text=Foto"
            ),
            "propostas": propostas_candidato,
        }

        if modo_edicao:
          dados["candidatos"][idx_candidato] = novo_registro
          st.success(f"Candidato {nome_candidato} atualizado com sucesso!")
        else:
          dados["candidatos"].append(novo_registro)
          st.success(f"Candidato {nome_candidato} cadastrado com sucesso!")
          
          # Limpa os estados temporários para esvaziar os campos após o cadastro
          for k in list(st.session_state.keys()):
            if k.startswith("propostas_lista_") or k.startswith("links_lista_"):
              del st.session_state[k]

        salvar_e_sincronizar_dados(dados)
        st.rerun()
      else:
        st.error("Preencha ao menos o Nome e o Partido do candidato.")

    st.markdown("---")
    st.subheader("Candidatos Já Cadastrados")
    if dados["candidatos"]:
      for idx, cand in enumerate(dados["candidatos"]):
        with st.expander(
            f"{cand.get('numero','')} - {cand['nome']} ({cand.get('sigla', cand['partido'])} - {cand['cargo']})"
        ):
          st.image(cand["foto"], width=80)
          st.write(f"**Cargo:** {cand['cargo']}")
          st.write(
              f"**Partido:** {cand['partido']} | **Sigla:**"
              f" {cand.get('sigla','')}"
          )
          st.write(f"**Número:** {cand.get('numero','')}")
          if st.button("Remover Candidato", key=f"del_cand_{idx}"):
            dados["candidatos"].pop(idx)
            salvar_e_sincronizar_dados(dados)
            st.rerun()
    else:
      st.info("Nenhum candidato cadastrado.")

# ---------------------------------------------------------
# VISUALIZAÇÃO DO EMBED FINAL & CÓDIGO HTML
# ---------------------------------------------------------
elif menu == "Visualizar Embed / App Final":
  st.header("🔍 Visualização do Comparador (Embed)")

  if not dados["temas"] or not dados["candidatos"]:
    st.warning(
        "Cadastre ao menos um tema e alguns candidatos para visualizar o"
        " comparador."
    )
  else:
    cargos_disponiveis = list(set(c["cargo"] for c in dados["candidatos"]))
    cargo_filtro = st.selectbox(
        "Filtrar por Cargo para Comparação:",
        cargos_disponiveis,
        key="filtro_cargo",
    )

    candidatos_filtrados = [
        c for c in dados["candidatos"] if c["cargo"] == cargo_filtro
    ]

    if len(candidatos_filtrados) < 2:
      st.info(
          "Cadastre pelo menos 2 candidatos para este cargo para realizar o"
          " cruzamento de propostas."
      )
    else:
      tema_selecionado = st.selectbox(
          "Selecione o Assunto / Tema:", dados["temas"], key="filtro_tema"
      )
      st.markdown("---")

      cols = st.columns(len(candidatos_filtrados))
      for i, cand in enumerate(candidatos_filtrados):
        with cols[i]:
          num_str = (
              f" <span style='background:#ddd; padding:2px 6px; border-radius:4px; font-size:0.8rem;'>{cand.get('numero')}</span>"
              if cand.get("numero")
              else ""
          )
          sigla_str = (
              f" ({cand.get('sigla')})" if cand.get("sigla") else ""
          )

          st.markdown(
              f"""
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px 8px 0 0; border-top: 4px solid {PRIMARY_COLOR}; text-align: center; border-left: 1px solid #ddd; border-right: 1px solid #ddd;">
                        <img src="{cand['foto']}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid {SECONDARY_COLOR};">
                        <h3 style="margin: 10px 0 5px 0; font-size: 1.1rem; color: #333;">{cand['nome']} {num_str}</h3>
                        <p style="margin: 0; font-size: 0.85rem; color: #666;">{cand['partido']}{sigla_str}</p>
                    </div>
                    """,
              unsafe_allow_html=True,
          )

          propostas_do_tema = cand.get("propostas", {}).get(
              tema_selecionado, []
          )

          propostas_html_content = ""
          if propostas_do_tema:
            for prop in propostas_do_tema:
              links_html = ""
              if prop.get("links"):
                links_formatados = []
                for l in prop["links"]:
                  label = l.get("label") or l.get("url")
                  url = l.get("url") or "#"
                  if url.startswith("http"):
                    links_formatados.append(
                        f'<a href="{url}" target="_blank">{label}</a>'
                    )
                  else:
                    links_formatados.append(f"<span>{label}</span>")
                links_html = f" <i>(Ref: {' | '.join(links_formatados)})</i>"

              propostas_html_content += (
                  f"<li style='margin-bottom: 8px; font-size: 0.9rem;"
                  f" color: #444;'>{prop['descricao']}{links_html}</li>"
              )
            propostas_box = f"<ul style='padding-left: 20px; margin: 0;'>{propostas_html_content}</ul>"
          else:
            propostas_box = "<p style='font-size: 0.85rem; color: #888; font-style: italic; margin: 0;'>Nenhuma proposta cadastrada para este tema.</p>"

          st.markdown(
              f"""
                    <div style="background-color: #ffffff; padding: 15px; border-radius: 0 0 8px 8px; border: 1px solid #ddd; border-top: none; min-height: 150px;">
                        <strong style="font-size: 0.9rem; color: {SECONDARY_COLOR}; display: block; margin-bottom: 8px;">Propostas:</strong>
                        {propostas_box}
                    </div>
                    """,
              unsafe_allow_html=True,
          )

      st.markdown("---")
      st.subheader("💻 Código HTML para Embedar no Portal")
      st.markdown(
          "Copie o código abaixo e cole no HTML do seu portal para exibir este"
          " aplicativo via iframe:"
      )

      app_url = st.query_params.get("embed_url", "https://seu-app.streamlit.app")
      embed_code = f"""<iframe src="{app_url}?embed=true" width="100%" height="700px" style="border:none; border-radius:8px;"></iframe>"""
      st.code(embed_code, language="html")
