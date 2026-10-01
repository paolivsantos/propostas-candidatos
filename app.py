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
st.sidebar.title("🗳️ Gestão de Propostas")
menu = st.sidebar.selectbox(
    "Navegar para",
    [
        "Visualizar Embed / App Final",
        "1. Gerenciar Temas",
        "2. Gerenciar Cargos",
        "3. Cadastrar Candidatos & Propostas",
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
# 3. CADASTRO DE CANDIDATOS E PROPOSTAS
# ---------------------------------------------------------
elif menu == "3. Cadastrar Candidatos & Propostas":
  st.header("3. Cadastro de Candidatos e Inserção de Propostas por Tema")

  if not dados["temas"] or not dados["cargos"]:
    st.warning(
        "⚠️ Cadastre pelo menos um **Tema** e um **Cargo** antes de registrar"
        " candidatos."
    )
  else:
    col1, col2, col3 = st.columns(3)
    with col1:
      nome_candidato = st.text_input("Nome do Candidato", key="cand_nome")
      numero_candidato = st.text_input("Número do Candidato", key="cand_num")
    with col2:
      partido = st.text_input("Partido / Coligação", key="cand_partido")
      sigla = st.text_input("Sigla (ex: PT, PL, MDB)", key="cand_sigla")
    with col3:
      cargo_selecionado = st.selectbox("Cargo", dados["cargos"], key="cand_cargo")
      foto_url = st.text_input(
          "URL da Foto",
          placeholder="https://exemplo.com/foto.jpg",
          key="cand_foto",
      )

    st.markdown("---")
    st.subheader("Propostas por Tema")

    propostas_candidato = {}
    for tema_idx, tema in enumerate(dados["temas"]):
      with st.expander(f"📌 Propostas para: {tema}"):
        # Gerenciamento de linhas dinâmicas por tema usando session_state
        state_key = f"propostas_lista_{tema_idx}"
        if state_key not in st.session_state:
          st.session_state[state_key] = [{"descricao": "", "links": []}]

        # Botão para adicionar nova proposta
        if st.button(f"➕ Adicionar Proposta em {tema}", key=f"add_prop_{tema_idx}"):
          st.session_state[state_key].append({"descricao": "", "links": []})

        lista_itens_tema = []
        for p_idx, prop_item in enumerate(
            st.session_state[state_key].copy()
        ):
          st.markdown(f"**Proposta {p_idx+1}**")
          desc = st.text_area(
              "Descrição da Proposta",
              value=prop_item["descricao"],
              key=f"desc_{tema_idx}_{p_idx}",
          )

          st.markdown("🔗 *Links / Referências da Proposta:*")
          links_lista = []

          # Gerenciar links internos da proposta
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

    if st.button("Salvar Candidato no Sistema"):
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
        dados["candidatos"].append(novo_registro)
        salvar_e_sincronizar_dados(dados)
        st.success(f"Candidato {nome_candidato} cadastrado com sucesso!")
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
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; border-top: 4px solid {PRIMARY_COLOR}; text-align: center;">
                        <img src="{cand['foto']}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid {SECONDARY_COLOR};">
                        <h3 style="margin: 10px 0 5px 0; font-size: 1.1rem; color: #333;">{cand['nome']} {num_str}</h3>
                        <p style="margin: 0; font-size: 0.85rem; color: #666;">{cand['partido']}{sigla_str}</p>
                    </div>
                    """,
              unsafe_allow_html=True,
          )

          st.markdown("#### Propostas:")
          propostas_do_tema = cand.get("propostas", {}).get(
              tema_selecionado, []
          )

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

              st.markdown(f"- {prop['descricao']}{links_html}", unsafe_allow_html=True)
          else:
            st.info("Nenhuma proposta cadastrada para este tema.")

      st.markdown("---")
      st.subheader("💻 Código HTML para Embedar no Portal")
      st.markdown(
          "Copie o código abaixo e cole no HTML do seu portal para exibir este"
          " aplicativo via iframe:"
      )

      # Pega a URL pública atual do app Streamlit
      app_url = st.query_params.get("embed_url", "https://seu-app.streamlit.app")

      embed_code = f"""<iframe src="{app_url}?embed=true" width="100%" height="700px" style="border:none; border-radius:8px;"></iframe>"""
      st.code(embed_code, language="html")
