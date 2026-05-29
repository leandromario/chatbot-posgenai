# Lembre-se de ter instalado as bibliotecas
# pip install streamlit langchain langchain-openai langchain_community

## Carregando as credenciais da OpenAI
from dotenv import load_dotenv
import os
path = "/home/wagner/chatbot_curso/.env"
#path = "/home/serverllm/chat-omega/src/.env"
load_dotenv(path)


## Streamlit
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage


## Bibliotecas para criar a API
from fastapi import FastAPI
from langchain_openai import ChatOpenAI
from langserve import add_routes
from pydantic import BaseModel

## Bibliotecas para construir o chat
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
# from langchain.chains import OpenAIModerationChain
from openai import OpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain.chains import ConversationalRetrievalChain 


### Criando a estrutura de cadeias
llm = ChatOpenAI(model_name="gpt-4-0125-preview", temperature=0)

contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""

prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
])

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()

qa_system_prompt = """Você é um assistente especializado em engenharia de prompt. \
Seu papel é ajudar o usuário a explorar diferentes estratégias de construção de \
prompts para modelos de linguagem como o GPT-4. Sempre que possível, explique o \
que está acontecendo por trás das cortinas, dando dicas sobre por que certas \
instruções funcionam melhor que outras. Mantenha suas respostas concisas, \
técnicas e com exemplos práticos. Quando o usuário pedir, compare dois prompts e \
explique por que um teve melhor desempenho.
"""


qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

def contextualized_question(input: dict):
    if input.get("chat_history"):
        return contextualize_q_chain
    else:
        return input["input"]


chain = (
    RunnablePassthrough.assign(context = contextualized_question)
    | qa_prompt
    | llm
)

# chat_history = []
# pergunta_cliente = "Por que existem tantas coisas ruins no mundo atual?"
# resposta = chain.invoke({
#             "chat_history": chat_history,
#             "input": pergunta_cliente
#             })
# resposta.content

## Footer customizado

footer="""<style>
a:link , a:visited{
color: blue;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 10;
bottom: 0;
width: 100%;
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p>Desenvolvido por Wagner Hugo Bonat · </p>
</div>
"""

st.set_page_config(page_title="Ômega Data Academy · Engenharia de prompt", page_icon="🤖")
st.title("Engenharia de prompt")

with st.sidebar:
    st.image('/home/wagner/chatbot_curso/LOGO_OMEGA.jpeg')
    st.markdown("---")
    #cliente_email = st.text_input("Por favor, insira o seu email")
    #cliente_nome = st.text_input("Por favor, insira o seu nome completo")
    st.markdown("---")
    st.markdown("# Sobre")
    st.markdown("Conheça os cursos e tudo relacionado a Ômega Data Academy usando o nosso assistente de navegação ou [Acesse o nosso site](https://escola.omegadatascience.com.br)")
    st.markdown("# Termos de uso")
    st.markdown("Ao usar o nosso assistente de navegação você aceita nossos termos de uso: \n"
                "1. **Uso do Serviço:** O Chatbot é fornecido para fins informativos e de entretenimento. Não deve ser utilizado como substituto de aconselhamento profissional. \n"
                "2. **Privacidade:** Nós valorizamos sua privacidade. As interações com o Chatbot podem ser registradas para melhorar os nossos serviço, e entrar em contato por email mas suas informações pessoais não serão compartilhadas com terceiros sem o seu consentimento. \n"
                "3. **Conduta do Usuário:** Você concorda em usar o Chatbot de maneira responsável. Isso inclui, mas não se limita a, não enviar conteúdo ofensivo, ilegal ou inapropriado. \n"
                "4. **Limitação de Responsabilidade:** O serviço é fornecido como está. Não garantimos a precisão ou a integridade das respostas fornecidas pelo Chatbot. Não nos responsabilizamos por quaisquer danos resultantes do uso do Chatbot. \n"
                "5. **Alterações nos Termos:** Reservamos o direito de alterar estes Termos de Uso a qualquer momento. As mudanças entrarão em vigor imediatamente após a publicação. \n"
                "6. **Contato:** Se você tiver dúvidas sobre estes Termos de Uso, entre em contato conosco através do nosso site.")
    st.markdown(footer,unsafe_allow_html=True)

## Gravas o histórico da conversa
#data_history = {'cliente_email': [str('')],
#                'cliente_nome': [str('')],
#                'pergunta': [str('')],
#                'resposta': [str('')]
#}
#data_pandas = pd.DataFrame(data = data_history)
#data_pandas.to_csv("historico.csv")


## Histórico da conversa
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Olá! Eu sou o chat para você aprender engenharia de prompt. Como posso te ajudar?")
    ]

#salva_resposta = ''

pergunta_cliente = st.chat_input("Digite sua pergunta...")

#if pergunta_cliente := st.chat_input("Digite sua pergunta..."):
#    if re.fullmatch(regex, cliente_email) is None:
#        st.info("Por favor, insira o seu email.")
#        st.stop()
#    if(cliente_nome is None or cliente_nome == ""):
#        st.info("Por favor, insira o seu nome.")
#        st.stop()


resposta_fora_contexto = """Pergunta fora do meu contexto. \
Tente ser específico para me ajudar a trazer informações importantes para você."""

if pergunta_cliente is not None and pergunta_cliente != "":
    #pertinencia = check_input(pergunta_cliente)
    pertinencia = 1
    if(pertinencia == 1):
        resposta = chain.invoke({
            "chat_history": st.session_state.chat_history,
            "input": pergunta_cliente
            }).content
    else:
        resposta = resposta_fora_contexto
    salva_resposta = resposta
    st.session_state.chat_history.append(HumanMessage(content = pergunta_cliente))
    st.session_state.chat_history.append(AIMessage(content = resposta))


for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.write(message.content)



#data_history = {'cliente_email': [cliente_email],
#                'cliente_nome': [cliente_nome],
#               'pergunta': [pergunta_cliente],
#                'resposta': [salva_resposta]
#}

#data_history = {'cliente_email': [str('Wagner')],
#                'cliente_nome': [str('tt')],
#                'pergunta': [str('merf')],
#                'resposta': [str('fefe')]
#}
#data_pandas = pd.DataFrame(data = data_history)
#historico = pd.read_csv('historico.csv', sep = ";")
#data_pandas = pd.concat([historico, data_pandas])
#data_pandas.to_csv("historico.csv", sep = ";", index=False)

## Deploy streamlit run app.py  --server.port 8501


