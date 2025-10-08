#!/bin/bash
# Script para automatizar a instalação do MeuConversorTTS em Linux (Debian/Ubuntu)
set -e

echo ">>> (1/5) Atualizando pacotes do sistema (APT)..."
sudo apt update -y && sudo apt upgrade -y

echo ">>> (2/5) Instalando dependências (python3, git, ffmpeg, poppler, venv)..."
sudo apt install -y python3 git ffmpeg poppler-utils python3-venv

cd ~
echo ">>> (3/5) Baixando o projeto do GitHub..."
if [ -d "MeuConversorTTS" ]; then
    echo "A pasta 'MeuConversorTTS' já existe. Pulando o download."
else
    git clone https://github.com/JonJonesBR/MeuConversorTTS.git
fi
cd MeuConversorTTS

echo ">>> (4/5) Criando e ativando o ambiente virtual..."
python3 -m venv venv

echo ">>> (5/5) Instalando as dependências Python do projeto..."
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "--- INSTALAÇÃO CONCLUÍDA! ---"
echo "1) cd ~/MeuConversorTTS"
echo "2) source venv/bin/activate"
echo "3) python3 main.py"
# --- FIM DO SCRIPT ---
