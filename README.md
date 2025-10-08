# MeuConversorTTS – Texto para Fala (PT-BR)

Um script completo e modular para converter textos em arquivos de áudio (MP3)
de alta qualidade, utilizando a tecnologia Edge TTS da Microsoft. Compatível
com Windows, Linux e Android (via Termux).

Este projeto foi reestruturado para ser mais robusto, fácil de manter e de
evoluir. Ele oferece formatação avançada de texto, melhoria de áudio e uma
interface de linha de comando intuitiva.

## ✨ Funcionalidades

- ✅ **Estrutura Modular**: Código organizado para fácil manutenção e contribuição.
- ✅ **Multiplataforma**: Scripts de instalação dedicados para Windows, Linux e
 Termux (Android).
- 🎙️ **Múltiplas Vozes Neurais**: Suporte às vozes em português brasileiro da
  Edge TTS.
- 📜 **Textos Longos**: Divisão inteligente de textos longos em parágrafos e
  frases para evitar erros.
- 📄 **Leitor de Arquivos**: Conversão integrada de arquivos PDF e EPUB para
  texto limpo e formatado.
- ⚙️ **Processamento de Texto Avançado**:
  - Expansão de abreviações (Dr. → Doutor).
  - Conversão de números cardinais e ordinais (123 → cento e vinte e três, 1º → primeiro).
  - Normalização de capítulos (Capítulo IV → CAPÍTULO 4.).
- ⚡ **Pós-processamento de Áudio**: Acelere, divida ou melhore a qualidade dos
  seus arquivos de áudio.
- 🔄 **Unificação de Áudio Aprimorada**: Sistema robusto de fallback que
  concatena arquivos de áudio mesmo quando FFmpeg ou pydub não estão
  disponíveis ou compatíveis.
- 🎬 **Criação de Vídeo**: Converta arquivos MP3 em vídeos MP4 com uma tela
  preta, ideal para uploads.
- 🔧 **Gerenciamento de Dependências**: Instalação simplificada com
  `requirements.txt` e ambientes virtuais.

## 📦 Dependências Externas

Este programa depende do FFmpeg para funções avançadas de áudio e vídeo. Siga
as instruções abaixo para instalar o FFmpeg no seu sistema:

### Windows

1. Baixe o FFmpeg em <https://www.gyan.dev/ffmpeg/builds/>

2. Extraia o conteúdo em uma pasta (ex: C:\\ffmpeg)
3. Adicione o caminho 'C:\\ffmpeg\\bin' ao PATH do sistema:
   - Abra o Painel de Controle > Sistema > Configurações Avançadas do Sistema
   - Clique em 'Variáveis de Ambiente'
   - Na seção 'Variáveis do Sistema', encontre e selecione 'Path', clique em 'Editar'
   - Clique em 'Novo' e adicione o caminho 'C:\\ffmpeg\\bin'
   - Clique em 'OK' para fechar todas as janelas
4. Reinicie o terminal ou o computador para aplicar as alterações

### Linux (Ubuntu/Debian)

```bash
sudo apt update && sudo apt install ffmpeg
```

### macOS

Primeiro instale o Homebrew (caso ainda não tenha):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Depois instale o FFmpeg:

```bash
brew install ffmpeg
```

### Termux (Android)

```bash
pkg install ffmpeg
```

## 🚀 Guia Rápido de Instalação (Recomendado)

Use nossos scripts para automatizar todo o processo de download e configuração.
Escolha o seu sistema operacional e siga os passos.

### 🪟 Windows

Abra o **Prompt de Comando (cmd)**, cole o comando abaixo e pressione Enter.
Ele irá baixar executar o instalador.

```powershell
curl -L -o instalar-windows.bat
https://raw.githubusercontent.com/JonJonesBR/MeuConversorTTS/main/instalar-windows.bat
&& instalar-windows.bat
```

Nota: O script irá verificar se você tem Python e Git. Ele também avisará sobre
a necessidade de instalar FFmpeg e Poppler manualmente.

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

Primeiro, baixe e instale o Termux a partir do F-Droid (link direto): [https://f-droid.org/repo/com.termux_1022.apk](https://f-droid.org/repo/com.termux_1022.apk)

Após instalar o Termux, abra o aplicativo e execute os seguintes comandos:

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

**Nota:** Apenas para usuários que sabem o que estão fazendo.

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

## 🔄 Como Atualizar o Projeto

Com o git, atualizar é muito simples. Abra o terminal na pasta do projeto
(MeuConversorTTS) e execute o comando:

```bash
git pull origin main
```

Dica: Após atualizar, é uma boa prática reativar o ambiente virtual e
reinstalar as dependências com `pip install -r requirements.txt` para garantir
que todas as novas bibliotecas sejam instaladas.

## 🤝 Como Contribuir

Este projeto é aberto a contribuições! Se você encontrou um bug, tem sugestões
de melhoria ou deseja adicionar novas funcionalidades, sinta-se à vontade para
abrir uma Issue ou enviar um Pull Request.

Agora que o projeto é modular, ficou muito mais fácil contribuir! Se você
encontrou um bug, tem sugestões de melhoria ou deseja adicionar novas
funcionalidades, abra uma issue ou envie um pull request.

## 📋 Dependências Externas

Este projeto depende de programas externos como FFmpeg e Poppler. Para obter
instruções detalhadas sobre como instalá-los no seu sistema, consulte o
arquivo [DEPENDENCIAS_EXTERNAS.md](./DEPENDENCIAS_EXTERNAS.md).

Agora que o projeto é modular, ficou muito mais fácil contribuir! Se você
encontrou um bug, tem sugestões de melhoria ou deseja adicionar novas
funcionalidades, abra uma issue ou envie um pull request.

⭐ Se este projeto foi útil para você, deixe uma estrela no GitHub! ⭐
