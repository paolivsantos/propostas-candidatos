import json
import os
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Gerenciador de Propostas Político",
    page_icon="🗳️",
    layout="wide",
)

# Paleta de Cores Customizada via CSS
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

# Arquivo de persistência local (simulando armazenamento no GitHub)
DATA_FILE = "dados_eleicoes.json"


def carregar_dados():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {"temas": [], "cargos": [], "candidatos": []}


def salvar_dados(dados):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)


dados = carregar_dados()

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

  with st.form("form_tema"):
    novo_tema = st.text_input(
        "Nome do Tema (ex: 1. Economia, Trabalho e Responsabilidade Fiscal)"
    )
    submit_tema = st.form_submit_button("Adicionar Tema")

    if submit_tema and novo_tema:
      if novo_tema not in dados["temas"]:
        dados["temas"].append(novo_tema)
        salvar_dados(dados)
        st.success(f"Tema '{novo_tema}' cadastrado com sucesso!")
        st.rerun()
      else:
        st.warning("Este tema já está cadastrado.")

  st.subheader("Temas Cadastrados:")
  if dados["temas"]:
    for i, t in enumerate(dados["temas"]):
      col1, col2 = st.columns([0.8, 0.2])
      col1.write(f"- {t}")
      if col2.button("Excluir", key=f"del_tema_{i}"):
        dados["temas"].pop(i)
        salvar_dados(dados)
        st.rerun()
  else:
    st.info("Nenhum tema cadastrado ainda.")

# ---------------------------------------------------------
# 2. CRIAÇÃO DE CARGOS
# ---------------------------------------------------------
elif menu == "2. Gerenciar Cargos":
  st.header("2. Criação e Gestão de Cargos")

  with st.form("form_cargo"):
    novo_cargo = st.text_input(
        "Nome do Cargo (ex: Presidente, Governador, Prefeito)"
    )
    submit_cargo = st.form_submit_button("Adicionar Cargo")

    if submit_cargo and novo_cargo:
      if novo_cargo not in dados["cargos"]:
        dados["cargos"].append(novo_cargo)
        salvar_dados(dados)
        st.success(f"Cargo '{novo_cargo}' cadastrado com sucesso!")
        st.rerun()
      else:
        st.warning("Este cargo já está cadastrado.")

  st.subheader("Cargos Cadastrados:")
  if dados["cargos"]:
    for i, c in enumerate(dados["cargos"]):
      col1, col2 = st.columns([0.8, 0.2])
      col1.write(f"- {c}")
      if col2.button("Excluir", key=f"del_cargo_{i}"):
        dados["cargos"].pop(i)
        salvar_dados(dados)
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
    with st.form("form_candidato"):
      st.subheader("Informações Básicas do Candidato")
      col1, col2 = st.columns(2)
      with col1:
        nome_candidato = st.text_input("Nome do Candidato")
        partido = st.text_input("Partido / Coligação")
      with col2:
        cargo_selecionado = st.selectbox("Cargo", dados["cargos"])
        foto_url = st.text_input(
            "URL da Foto (Link da imagem do candidato)",
            placeholder="https://exemplo.com/foto.jpg",
        )

      st.markdown("---")
      st.subheader("Propostas por Tema")
      st.info(
          "Adicione as propostas detalhadas do candidato para cada tema desejado."
      )

      # Dicionário dinâmico para capturar propostas por tema
      propostas_candidato = {}

      for tema in dados["temas"]:
        with st.expander(f"📌 Propostas para: {tema}"):
          # Permite adicionar múltiplas propostas por tema
          num_propostas = st.number_input(
              f"Quantas propostas para o tema '{tema}'?",
              min_value=0,
              max_value=5,
              value=1,
              key=f"num_{tema}",
          )

          lista_itens_tema = []
          for p_idx in range(int(num_propostas)):
            col_a, col_b = st.columns([0.7, 0.3])
            desc = col_a.text_input(
                f"Descrição da proposta {p_idx+1}", key=f"desc_{tema}_{p_idx}"
            )
            link = col_b.text_input(
                f"Link (opcional) {p_idx+1}",
                placeholder="Ex: página 5 ou URL",
                key=f"link_{tema}_{p_idx}",
            )
            if desc:
              lista_itens_tema.append({"descricao": desc, "referencia": link})

          if lista_itens_tema:
            propostas_candidato[tema] = lista_itens_tema

      submit_cand = st.form_submit_button("Salvar Candidato")

      if submit_cand:
        if nome_candidato and partido:
          novo_registro = {
              "nome": nome_candidato,
              "partido": partido,
              "cargo": cargo_selecionado,
              "foto": (
                  foto_url
                  if foto_url
                  else "https://via.placeholder.com/150?text=Foto"
              ),
              "propostas": propostas_candidato,
          }
          dados["candidatos"].append(novo_registro)
          salvar_dados(dados)
          st.success(
              f"Candidato {nome_candidato} cadastrado com sucesso!"
          )
        else:
          st.error("Preencha ao menos o Nome e o Partido do candidato.")

    st.markdown("---")
    st.subheader("Candidatos Já Cadastrados")
    if dados["candidatos"]:
      for idx, cand in enumerate(dados["candidatos"]):
        with st.expander(
            f"{cand['nome']} ({cand['partido']} - {cand['cargo']})"
        ):
          st.image(cand["foto"], width=100)
          st.write(f"**Cargo:** {cand['cargo']}")
          st.write(f"**Partido:** {cand['partido']}")
          st.json(cand["propostas"])
          if st.button("Remover Candidato", key=f"del_cand_{idx}"):
            dados["candidatos"].pop(idx)
            salvar_dados(dados)
            st.rerun()
    else:
      st.info("Nenhum candidato cadastrado.")

# ---------------------------------------------------------
# VISUALIZAÇÃO DO EMBED FINAL
# ---------------------------------------------------------
elif menu == "Visualizar Embed / App Final":
  st.header("🔍 Visualização do Comparador (Embed)")

  if not dados["temas"] or not dados["candidatos"]:
    st.warning(
        "Cadastre ao menos um tema e alguns candidatos para visualizar o"
        " comparador."
    )
  else:
    # Filtro de cargo para a visualização
    cargos_disponiveis = list(
        set(c["cargo"] for c in dados["candidatos"])
    )
    cargo_filtro = st.selectbox(
        "Filtrar por Cargo para Comparação:", cargos_disponiveis
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
      # Seletor de Tema estilo as setas do protótipo
      tema_selecionado = st.selectbox(
          "Selecione o Assunto / Tema:", dados["temas"]
      )

      st.markdown("---")

      # Layout em colunas divididas simulando o embed político
      cols = st.columns(len(candidatos_filtrados))

      for i, cand in enumerate(candidatos_filtrados):
        with cols[i]:
          st.markdown(
              f"""
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; border-top: 4px solid {PRIMARY_COLOR}; text-align: center;">
                        <img src="{cand['foto']}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid {SECONDARY_COLOR};">
                        <h3 style="margin: 10px 0 5px 0; font-size: 1.1rem; color: #333;">{cand['nome']}</h3>
                        <p style="margin: 0; font-size: 0.85rem; color: #666;">{cand['partido']}</p>
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
              ref_texto = (
                  f" *(Ref: {prop['referencia']})*"
                  if prop["referencia"]
                  else ""
              )
              st.markdown(f"- {prop['descricao']}{ref_texto}")
          else:
            st.info(
                "Nenhuma proposta cadastrada para este tema por este"
                " candidato."
            )
