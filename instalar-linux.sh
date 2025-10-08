#!/bin/bash
# Script para automatizar a instalação do MeuConversorTTS em Linux (Debian/Ubuntu)
set -e

echo ">>> (1/6) Atualizando pacotes do sistema (APT)..."
sudo apt update -y && sudo apt upgrade -y

echo ">>> (2/6) Instalando dependências principais..."
sudo apt install -y python3 git ffmpeg poppler-utils python3-venv

echo ">>> (3/6) Instalando dependências gráficas necessárias para Pillow/pdfplumber..."
sudo apt install -y libjpeg-dev zlib1g-dev libfreetype6-dev libpng-dev

cd ~
echo ">>> (4/6) Baixando o projeto do GitHub..."
if [ -d "MeuConversorTTS" ]; then
    echo "A pasta 'MeuConversorTTS' já existe. Pulando o download."
else
    git clone https://github.com/JonJonesBR/MeuConversorTTS.git
fi
cd MeuConversorTTS

echo ">>> (5/6) Criando e ativando o ambiente virtual..."
python3 -m venv venv
source venv/bin/activate

echo ">>> (6/6) Instalando as dependências Python do projeto..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "--- INSTALAÇÃO CONCLUÍDA COM SUCESSO! ---"
echo "Para iniciar o programa:"
echo "1) cd ~/MeuConversorTTS"
echo "2) source venv/bin/activate"
echo "3) python3 main.py"
# --- FIM DO SCRIPT ---
