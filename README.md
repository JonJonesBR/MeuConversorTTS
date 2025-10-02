# Conversor TTS – Texto para Fala (PT-BR)

Um script completo e modular para converter textos em arquivos de áudio (MP3) de alta qualidade, utilizando a tecnologia Edge TTS da Microsoft. Compatível com Windows, Linux e Android (via Termux).

Este projeto foi reestruturado para ser mais robusto, fácil de manter e de evoluir. Ele oferece formatação avançada de texto, melhoria de áudio e uma interface de linha de comando intuitiva.

## ✨ Funcionalidades

- ✅ Estrutura Modular: Código organizado para fácil manutenção e contribuição.
- ✅ Compatível com Windows, Linux e Termux (Android).
- 🎙️ Múltiplas vozes neurais em português brasileiro.
- 📜 Suporte a textos longos com divisão inteligente em parágrafos e frases.
- 📄 Conversão integrada de arquivos PDF e EPUB para texto limpo e formatado.
- ⚙️ Processamento de Texto Avançado:
  - Expansão de abreviações (Dr. → Doutor).
  - Conversão de números cardinais e ordinais (123 → cento e vinte e três, 1º → primeiro).
  - Normalização de capítulos (Capítulo IV → CAPÍTULO 4.).
- ⚡ Melhoria de Áudio: Acelere, converta para vídeo, ou divida arquivos longos.
- 🎬 Criação de Vídeo: Converta arquivos de áudio MP3 em vídeos MP4 com tela preta.
- 🔧 Gerenciamento de Dependências: Instalação simplificada com requirements.txt.

## ⚙️ Guia de Instalação e Uso

O processo agora utiliza as melhores práticas para projetos Python, incluindo git e ambientes virtuais.

## 🪟 Windows

### 1. Pré-requisitos (Windows)

- Python: Instale a versão mais recente a partir de [python.org](https://python.org). Marque a opção "Add Python to PATH" durante a instalação.
- Git: Instale o Git para Windows a partir de [git-scm.com](https://git-scm.com).

### 2. Instalação (Windows)

Abra o Prompt de Comando (cmd) ou PowerShell e execute os comandos abaixo, um por um.

```bash
# 1. Clone (baixe) o projeto do GitHub
git clone https://github.com/JonJonesBR/MeuConversorTTS.git

# 2. Entre na pasta do projeto que foi criada
cd Conversor_TTS

# 3. Crie um ambiente virtual para isolar as dependências
python -m venv venv

# 4. Ative o ambiente virtual
.\venv\Scripts\activate

# 5. Instale todas as dependências necessárias de uma só vez
pip install -r requirements.txt
```

### 3. Execução (Windows)

Com o ambiente virtual ainda ativo ((venv) aparecendo no terminal), execute o script principal:

```bash
python main.py
```

## 🐧 Linux / 📱 Android (Termux)

### 1. Pré-requisitos (Linux/Termux)

No seu terminal, instale as ferramentas essenciais:

```bash
# Atualize os pacotes
pkg update -y && pkg upgrade -y

# Instale as dependências de sistema
pkg install -y python git ffmpeg poppler

# Conceda permissão de acesso ao armazenamento (para Termux)
termux-setup-storage
```

### 2. Instalação (Linux/Termux)

Continue no mesmo terminal para baixar o projeto e instalar as dependências Python.

```bash
# 1. Clone (baixe) o projeto do GitHub
git clone https://github.com/JonJonesBR/MeuConversorTTS.git

# 2. Entre na pasta do projeto
cd Conversor_TTS

# 3. Crie um ambiente virtual
python -m venv venv

# 4. Ative o ambiente virtual
source venv/bin/activate

# 5. Instale as dependências Python
pip install -r requirements.txt
```

### 3. Execução (Linux/Termux)

Com o ambiente virtual ativo, execute o script:

```bash
python main.py
```

## 🔄 Como Atualizar o Script

Com o git, atualizar é muito simples. Abra o terminal na pasta do projeto (Conversor_TTS) e execute o comando:

```bash
git pull origin main
```

Isso baixará a versão mais recente de todos os arquivos do projeto.

## ❓ Problemas Comuns e Soluções

- Erro: python ou git não encontrado
  - Certifique-se de que o Python e o Git foram instalados corretamente e adicionados ao PATH do sistema.
- Erro: pip falhou ao instalar um pacote
  - Verifique sua conexão com a internet. No Linux, pode ser necessário instalar pacotes de desenvolvimento (python3-dev, build-essential).
- Erro de permissão no Termux
  - Execute o comando termux-setup-storage novamente e confirme a permissão.

## 🤝 Como Contribuir

Agora que o projeto é modular, ficou muito mais fácil contribuir! Se você encontrou um bug, tem sugestões de melhoria ou deseja adicionar novas funcionalidades, abra uma issue ou envie um pull request.

⭐ Se este projeto foi útil para você, deixe uma estrela no GitHub! ⭐
