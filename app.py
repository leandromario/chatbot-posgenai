import os
import streamlit as st
from dotenv import load_dotenv

from chatlas import ChatOpenAICompletions
# =========================================================
# CONFIGURAÇÃO
# =========================================================

load_dotenv()

chat = ChatOpenAICompletions(
    model="meta/llama-3.3-70b-instruct",
    api_key=os.getenv("NVIDIA_API_KEY"),
    base_url="https://integrate.api.nvidia.com/v1"
)

SYSTEM_PROMPT = """
Você é um assistente especializado em engenharia de prompt.

Seu papel é ajudar o usuário a explorar diferentes estratégias
de construção de prompts para modelos de linguagem.

Sempre que possível:
- explique conceitos de forma objetiva;
- mostre exemplos práticos;
- compare abordagens quando solicitado;
- mantenha respostas técnicas e concisas.
"""

# =========================================================
# STREAMLIT
# =========================================================

st.set_page_config(
    page_title="Engenharia de Prompt",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Engenharia de Prompt")

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("Sobre")

    st.markdown("""
    Assistente especializado em Engenharia de Prompt.

    Faça perguntas sobre:
    - Prompt Engineering
    - LLMs
    - ChatGPT
    - Claude
    - Gemini
    - Agentes
    - RAG
    - Avaliação de prompts
    """)

    st.markdown("---")

    if st.button("Limpar conversa"):

        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "Olá! Como posso ajudar você com Engenharia de Prompt?"
            }
        ]

        st.rerun()

# =========================================================
# HISTÓRICO
# =========================================================

if "chat_history" not in st.session_state:

    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": "Olá! Como posso ajudar você com Engenharia de Prompt?"
        }
    ]

# =========================================================
# EXIBE HISTÓRICO
# =========================================================

for message in st.session_state.chat_history:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# =========================================================
# INPUT
# =========================================================

user_question = st.chat_input(
    "Digite sua pergunta..."
)

# =========================================================
# PROCESSAMENTO
# =========================================================

if user_question:

    # Exibe usuário

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": user_question
        }
    )

    with st.chat_message("user"):

        st.markdown(user_question)

    # Monta contexto

    conversation = SYSTEM_PROMPT + "\n\n"

    for msg in st.session_state.chat_history:

        conversation += (
            f"{msg['role']}: "
            f"{msg['content']}\n"
        )

    # Gera resposta

    with st.chat_message("assistant"):

        with st.spinner("Pensando..."):

            response = chat.chat(
                conversation,
                stream=False
            )

            answer = str(response)

            st.markdown(answer)

    # Salva resposta

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": answer
        }
    )
