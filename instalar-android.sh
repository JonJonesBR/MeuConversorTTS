#!/bin/bash
# Script para automatizar a instalação do MeuConversorTTS no Termux (Android)
# Compatível com pdfplumber, EbookLib e Pillow
set -e

echo ">>> (1/8) Atualizando pacotes do Termux..."
pkg update -y && pkg upgrade -y

echo ">>> (2/8) Instalando dependências principais (python, git, ffmpeg, poppler)..."
pkg install -y python git ffmpeg poppler

echo ">>> (3/8) Instalando dependências gráficas para Pillow/pdfplumber..."
pkg install -y libjpeg-turbo zlib freetype libpng

echo ">>> (4/8) Instalando dependências XML necessárias para EbookLib/lxml..."
pkg install -y libxml2 libxslt libxml2-dev libxslt-dev clang python-dev
pip install lxml

echo ">>> (5/8) Solicitando permissão de armazenamento..."
echo "!!! IMPORTANTE: Conceda permissão de armazenamento ao Termux quando solicitado."
read -p "Digite 'sim' para conceder e continuar: " confirmacao
[ "$confirmacao" = "sim" ] || { echo "Instalação cancelada."; exit 1; }
termux-setup-storage

cd ~
echo ">>> (6/8) Baixando o projeto do GitHub..."
if [ -d "MeuConversorTTS" ]; then
    echo "A pasta 'MeuConversorTTS' já existe. Pulando o download."
else
    git clone https://github.com/JonJonesBR/MeuConversorTTS.git
fi
cd MeuConversorTTS

echo ">>> (7/8) Criando e ativando o ambiente virtual..."
python -m venv venv
source venv/bin/activate

echo ">>> (8/8) Instalando dependências Python do projeto..."
pip install --upgrade pip setuptools wheel
pip install --only-binary=:all: lxml
pip install -r requirements.txt

echo ""
echo "--- INSTALAÇÃO CONCLUÍDA COM SUCESSO! ---"
echo "Para iniciar o programa:"
echo "1) cd ~/MeuConversorTTS"
echo "2) source venv/bin/activate"
echo "3) python main.py"
# --- FIM DO SCRIPT ---
