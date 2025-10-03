#!/bin/bash
# Script para automatizar a instalação do MeuConversorTTS em Linux (Debian/Ubuntu)

# --- INÍCIO DO SCRIPT ---

# Garante que o script pare se algum comando falhar
set -e

# Passo 1: Atualizar e instalar dependências do sistema com APT
echo ">>> (1/5) Atualizando pacotes do sistema (APT)..."
sudo apt update -y && sudo apt upgrade -y

echo ">>> (2/5) Instalando dependências (python3, git, ffmpeg, poppler, venv)..."
# Em desktops, o python3-venv costuma ser um pacote separado
sudo apt install -y python3 git ffmpeg poppler-utils python3-venv

# Passo 2: Baixar o projeto do GitHub
# Vai para o diretório inicial do usuário para organizar
cd ~
echo ">>> (3/5) Baixando o projeto do GitHub..."
# Verifica se a pasta já existe
if [ -d "MeuConversorTTS" ]; then
    echo "A pasta 'MeuConversorTTS' já existe. Pulando o download."
else
    git clone https://github.com/JonJonesBR/MeuConversorTTS.git
fi

# Entra na pasta do projeto
cd MeuConversorTTS

# Passo 3: Configurar o ambiente Python
echo ">>> (4/5) Criando e ativando o ambiente virtual..."
# Usa 'python3' para garantir que é a versão correta
python3 -m venv venv

echo ">>> (5/5) Instalando as dependências Python do projeto..."
source venv/bin/activate
pip install -r requirements.txt

# Mensagem final
echo ""
echo "--- INSTALAÇÃO CONCLUÍDA! ---"
echo ""
echo "Para começar a usar, siga os próximos passos:"
echo "1. Navegue até a pasta do projeto: cd ~/MeuConversorTTS"
echo "2. Ative o ambiente virtual com o comando:"
echo "   source venv/bin/activate"
echo "3. Execute o programa principal com:"
echo "   python3 main.py"
echo ""

<<<<<<< HEAD
# --- FIM DO SCRIPT ---
=======
# --- FIM DO SCRIPT ---
>>>>>>> bb19449059105991693c172edf8db34073a419fe
