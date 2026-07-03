# 🤖 Implantando um Chatbot GenAI Open Source na Oracle Cloud com NVIDIA e Streamlit

> Relatório da atividade prática da disciplina **Produtos de GenAI** — Pós-Graduação em GenAI.
>
> 🔗 **Aplicação em produção:** http://147.15.15.118:8501

---

## Introdução

### Objetivo da atividade

O objetivo desta atividade foi **desenvolver e implantar um chatbot de Inteligência Artificial Generativa** utilizando um modelo *open source* disponibilizado pela NVIDIA, escrito em Python com Streamlit e publicado em uma máquina virtual na Oracle Cloud Infrastructure (OCI). Ao final, o chatbot precisava estar acessível publicamente por um endereço IP e permitir a interação de usuários diretamente pelo navegador.

### Visão geral da solução

A solução é um **assistente especializado em Engenharia de Prompt**: o usuário faz perguntas sobre LLMs, RAG, agentes, avaliação de prompts e afins, e o chatbot responde de forma técnica e objetiva.

A aplicação é uma interface web em Streamlit que mantém o histórico da conversa e, a cada mensagem, envia o contexto para o modelo **Llama 3.3 70B Instruct** hospedado na nuvem da NVIDIA. Um ponto central do desenho: **a inferência do modelo acontece na infraestrutura da NVIDIA**, não na VM. A máquina virtual apenas serve o frontend e faz a chamada à API, o que permitiu rodar tudo em uma instância *Always Free* mínima.

---

## Infraestrutura

| Item | Especificação |
|---|---|
| Provedor | Oracle Cloud Infrastructure (OCI) |
| Shape da VM | `VM.Standard.E2.1.Micro` (Always Free) |
| Sistema operacional | Ubuntu 24.04 LTS |
| vCPU | 1 OCPU (AMD, x86_64) |
| Memória | 1 GB RAM |
| Porta exposta | 8501 (TCP) |
| Acesso | IP público direto via navegador |

Como o modelo roda remotamente na NVIDIA, uma instância de **1 OCPU e 1 GB de RAM** foi suficiente para hospedar a aplicação.

---

## Modelo Escolhido

- **Nome:** `meta/llama-3.3-70b-instruct`
- **Provedor de inferência:** NVIDIA API (`https://integrate.api.nvidia.com/v1`), endpoint compatível com o padrão OpenAI.

### Justificativa da escolha

- É um modelo **open source** (família Llama, da Meta), atendendo ao requisito da atividade.
- Disponibilizado gratuitamente via **NVIDIA API Catalog**, o que elimina a necessidade de GPU própria e permite hospedar a aplicação em uma VM mínima.
- A versão **Instruct** já é ajustada para seguir instruções e conversar, ideal para um assistente de perguntas e respostas.
- O endpoint compatível com OpenAI simplifica a integração com bibliotecas do ecossistema Python.

### Principais características

- 70 bilhões de parâmetros, bom equilíbrio entre qualidade de resposta e disponibilidade.
- Forte capacidade de raciocínio, seguimento de instruções e geração de texto técnico em português.
- Janela de contexto ampla, adequada para manter o histórico da conversa.

---

## Desenvolvimento

### Arquitetura da aplicação

O código principal está em [`app.py`](app.py), um script Streamlit linear (reexecutado a cada interação do usuário):

1. **Cliente LLM** — `chatlas.ChatOpenAICompletions` apontando para o endpoint da NVIDIA, configurado com o modelo Llama 3.3 70B e a `NVIDIA_API_KEY`.
2. **System prompt** — define o papel do assistente (especialista em Engenharia de Prompt).
3. **Estado da conversa** — o histórico é mantido em `st.session_state.chat_history` como uma lista de mensagens `{"role", "content"}`; o botão *"Limpar conversa"* reinicia o estado.
4. **Fluxo de resposta** — a cada pergunta, o histórico é concatenado ao system prompt e enviado em uma única chamada `chat.chat(...)`; a resposta é exibida e salva no histórico.

> O arquivo `app_old_langchain.py` é uma implementação legada (LangChain/FastAPI) mantida apenas como referência histórica e **não** faz parte da aplicação em produção.

### Bibliotecas utilizadas

| Biblioteca | Papel |
|---|---|
| `streamlit` | Interface web / chat e gerenciamento de estado da sessão |
| `chatlas` | Abstração de cliente de chat para o LLM |
| `openai` | SDK compatível usado pelo endpoint da NVIDIA |
| `python-dotenv` | Carregamento de variáveis de ambiente a partir do `.env` |

### Estratégia de gerenciamento de credenciais

- A chave de API é lida da variável de ambiente **`NVIDIA_API_KEY`** via `python-dotenv` (`load_dotenv()`), **nunca** ficando hardcoded no código.
- Um arquivo [`.env.example`](.env.example) documenta as variáveis necessárias, mas **sem** valores reais.
- O arquivo `.env` (com a chave real) está listado no [`.gitignore`](.gitignore), garantindo que credenciais não sejam versionadas no GitHub.
- Em produção, a aplicação é executada num diretório que contém o `.env` local, mantendo o segredo fora do repositório.

---

## Implantação

### Processo de publicação na Oracle Cloud

#### 1. Preparação do ambiente

```bash
cd ~/chatbot-posgenai
pip install -r requirements.txt
```

Teste manual, aceitando conexões externas:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

> O parâmetro `--server.address 0.0.0.0` é essencial para o serviço escutar em todas as interfaces de rede da VM, e não apenas em `127.0.0.1`.

#### 2. Persistência com systemd

Para manter a aplicação rodando em segundo plano (mesmo após encerrar o SSH) e reiniciar automaticamente com a VM, foi criado um serviço systemd.

Crie `/etc/systemd/system/chatbot.service`:

```ini
[Unit]
Description=Streamlit Chatbot Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/chatbot-posgenai
ExecStart=/usr/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

> Ajuste o caminho do `ExecStart` para o local real do executável `streamlit` (verifique com `which streamlit`).

Ative e inicie o serviço:

```bash
sudo systemctl daemon-reload
sudo systemctl enable chatbot.service
sudo systemctl start chatbot.service
```

Comandos úteis de gerenciamento:

| Ação | Comando |
|---|---|
| Verificar status | `sudo systemctl status chatbot.service` |
| Reiniciar aplicação | `sudo systemctl restart chatbot.service` |
| Ver logs em tempo real | `journalctl -u chatbot.service -f` |

#### 3. Liberação da porta 8501 (rede em duas camadas)

**Camada 1 — Firewall do SO (iptables):** as instâncias Ubuntu da OCI vêm com regras nativas restritivas. É preciso inserir a liberação no topo da cadeia `INPUT`:

```bash
sudo iptables -I INPUT 1 -p tcp --dport 8501 -m state --state NEW,ESTABLISHED -j ACCEPT
sudo netfilter-persistent save
```

**Camada 2 — Security List da VCN (OCI):** no Console do OCI, na **Virtual Cloud Network (VCN)** da subnet da VM, adicione uma **Ingress Rule**:

| Campo | Valor |
|---|---|
| Source Type | CIDR |
| Source CIDR | `0.0.0.0/0` |
| IP Protocol | TCP |
| Destination Port Range | 8501 |
| Stateless | Desmarcado (stateful) |

### Principais desafios encontrados

- **Dupla camada de firewall:** liberar a porta só na Security List da OCI não bastava — o `iptables` interno do Ubuntu também bloqueava a conexão, exigindo a regra explícita e a persistência com `netfilter-persistent`.
- **Bind de rede:** por padrão o Streamlit escuta apenas em `localhost`; foi necessário forçar `--server.address 0.0.0.0` para o acesso externo funcionar.
- **Persistência do serviço:** garantir que a aplicação sobrevivesse ao fechamento da sessão SSH e a reinicializações da VM motivou a adoção do systemd em vez de rodar o processo manualmente.
- **Gestão de segredos:** manter a `NVIDIA_API_KEY` fora do repositório exigiu disciplina com `.env` + `.gitignore` e um `.env.example` apenas ilustrativo.

---

## Discussão

### Lições aprendidas

- **Separar inferência de hospedagem** é poderoso: usar a NVIDIA API para a inferência permitiu servir um modelo de 70B parâmetros a partir de uma VM *free tier* mínima.
- Publicar na nuvem envolve mais do que "rodar o código": **rede, firewall e persistência de serviço** são partes essenciais e costumam ser onde surgem os problemas.
- O **systemd** transforma um script solto em um serviço confiável, com restart automático e logs centralizados.
- Boas práticas de **gerenciamento de credenciais** desde o início evitam vazamento acidental de chaves no versionamento.

### Possíveis melhorias futuras

- Adicionar **RAG** (base de conhecimento própria) para respostas mais fundamentadas e específicas do domínio.
- Configurar **HTTPS** com um proxy reverso (Nginx/Caddy) e um domínio, em vez de expor a porta 8501 via IP.
- Implementar **streaming** das respostas para melhor experiência do usuário.
- Enviar o histórico como **lista estruturada de mensagens** (em vez de concatenar em uma única string) para melhor uso da janela de contexto.
- Adicionar **observabilidade** (métricas/logs de uso) e testes automatizados.

---

## Como executar localmente

```bash
# 1. Clonar o repositório
git clone <URL_DO_SEU_REPOSITORIO>
cd chatbot-posgenai

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Configurar as credenciais
cp .env.example .env
# edite o .env e preencha a NVIDIA_API_KEY

# 4. Executar
streamlit run app.py
```

A aplicação abre em `http://localhost:8501`.

---

*Desenvolvido como avaliação da disciplina de Produtos de GenAI — Pós-Graduação em GenAI.*
