# MeuConversorTTS – Texto para Fala (PT-BR)

Um script completo e modular para converter textos em arquivos de áudio (MP3) de alta qualidade, utilizando a tecnologia Edge TTS da Microsoft. Compatível com Windows, Linux e Android (via Termux).

Este projeto foi reestruturado para ser mais robusto, fácil de manter e de evoluir. Ele oferece formatação avançada de texto, melhoria de áudio e uma interface de linha de comando intuitiva.

## ✨ Funcionalidades

- ✅ **Estrutura Modular**: Código organizado para fácil manutenção e contribuição.
- ✅ **Multiplataforma**: Scripts de instalação dedicados para Windows, Linux e Termux (Android).
- 🎙️ **Múltiplas Vozes Neurais**: Suporte às vozes em português brasileiro da Edge TTS.
- 📜 **Textos Longos**: Divisão inteligente de textos longos em parágrafos e frases para evitar erros.
- 📄 **Leitor de Arquivos**: Conversão integrada de arquivos PDF e EPUB para texto limpo e formatado.
- ⚙️ **Processamento de Texto Avançado**:
  - Expansão de abreviações (Dr. → Doutor).
  - Conversão de números cardinais e ordinais (123 → cento e vinte e três, 1º → primeiro).
  - Normalização de capítulos (Capítulo IV → CAPÍTULO 4.).
- ⚡ **Pós-processamento de Áudio**: Acelere, divida ou melhore a qualidade dos seus arquivos de áudio.
- 🎬 **Criação de Vídeo**: Converta arquivos MP3 em vídeos MP4 com uma tela preta, ideal para uploads.
- 🔧 **Gerenciamento de Dependências**: Instalação simplificada com `requirements.txt` e ambientes virtuais.

## 🚀 Guia Rápido de Instalação (Recomendado)

Use nossos scripts para automatizar todo o processo de download e configuração. Escolha o seu sistema operacional e siga os passos.

### 🪟 Windows

Abra o **Prompt de Comando (cmd)**, cole o comando abaixo e pressione Enter. Ele irá baixar e executar o instalador.

```powershell
curl -L -o instalar-windows.bat https://raw.githubusercontent.com/JonJonesBR/MeuConversorTTS/main/instalar-windows.bat && instalar-windows.bat
```
Nota: O script irá verificar se você tem Python e Git. Ele também avisará sobre a necessidade de instalar FFmpeg e Poppler manualmente.

### 🐧 Linux (Ubuntu/Debian)
Abra o terminal e execute os seguintes comandos:

```bash
# Baixa o script de instalação
curl -L -o instalar-linux.sh https://raw.githubusercontent.com/JonJonesBR/MeuConversorTTS/main/instalar-linux.sh

# Dá permissão de execução e roda o script
chmod +x instalar-linux.sh
./instalar-linux.sh
```

### 📱 Android (Termux)
Abra o Termux e execute os seguintes comandos:

```bash
# Baixa o script de instalação
curl -L -o instalar-android.sh https://raw.githubusercontent.com/JonJonesBR/MeuConversorTTS/main/instalar-android.sh

# Dá permissão de execução e roda o script
chmod +x instalar-android.sh
./instalar-android.sh
```

## ▶️ Como Executar o Programa
Após a instalação (automática ou manual), os passos para executar são sempre os mesmos:

Navegue até a pasta do projeto:

```bash
cd MeuConversorTTS
```

Ative o ambiente virtual:

- No Windows: `venv\Scripts\activate`
- No Linux/Termux: `source venv/bin/activate`

Execute o script principal:

- No Windows: `python main.py`
- No Linux/Termux: `python3 main.py`

## 🔧 Instalação Manual (Para Usuários Avançados)
<details>
<summary>Clique para expandir as instruções de instalação manual</summary>

### 1. Pré-requisitos
**Windows**:
- Instale Python (marque "Add Python to PATH").
- Instale Git.
- Instale FFmpeg e Poppler e adicione-os ao PATH do sistema.

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 git ffmpeg poppler-utils python3-venv
```

**Android (Termux):**
```bash
pkg update && pkg upgrade -y
pkg install -y python git ffmpeg poppler
termux-setup-storage
```

### 2. Comandos de Instalação
Abra o terminal/cmd, e execute os comandos abaixo, um por um.

```bash
# 1. Clone (baixe) o projeto do GitHub
git clone https://github.com/JonJonesBR/MeuConversorTTS.git

# 2. Entre na pasta do projeto que foi criada (MUITO IMPORTANTE)
cd MeuConversorTTS

# 3. Crie um ambiente virtual
# No Windows:
python -m venv venv
# No Linux/Termux:
python3 -m venv venv

# 4. Ative o ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Termux:
source venv/bin/activate

# 5. Instale as dependências Python
pip install -r requirements.txt
```
</details>

## 🔄 Como Atualizar o Projeto
Com o git, atualizar é muito simples. Abra o terminal na pasta do projeto (MeuConversorTTS) e execute o comando:

```bash
git pull origin main
```
Dica: Após atualizar, é uma boa prática reativar o ambiente virtual e reinstalar as dependências com `pip install -r requirements.txt` para garantir que todas as novas bibliotecas sejam instaladas.

## 🤝 Como Contribuir
Este projeto é aberto a contribuições! Se você encontrou um bug, tem sugestões de melhoria ou deseja adicionar novas funcionalidades, sinta-se à vontade para abrir uma Issue ou enviar um Pull Request.

<<<<<<< HEAD
Agora que o projeto é modular, ficou muito mais fácil contribuir! Se você encontrou um bug, tem sugestões de melhoria ou deseja adicionar novas funcionalidades, abra uma issue ou envie um pull request.

⭐ Se este projeto foi útil para você, deixe uma estrela no GitHub! ⭐
=======
⭐ Se este projeto foi útil para você, que tal deixar uma estrela no GitHub? Isso ajuda a dar mais visibilidade ao projeto! ⭐
>>>>>>> bb19449059105991693c172edf8db34073a419fe
