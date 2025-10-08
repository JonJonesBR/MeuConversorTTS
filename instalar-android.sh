#!/bin/bash
# Script para automatizar a instalação do MeuConversorTTS no Termux (Android).
# Versão final compatível, utilizando pdftotext e dependências leves.

set -e

echo ">>> (1/7) Atualizando pacotes do Termux (forçando a atualização de configs)..."
pkg update -y && pkg upgrade -y -o Dpkg::Options::="--force-confnew"

echo ">>> (2/7) Instalando dependências de sistema (Python, Git, FFmpeg, Poppler)..."
pkg install -y python git ffmpeg poppler

echo ">>> (3/7) Instalando dependências gráficas para a biblioteca Pillow..."
pkg install -y libjpeg-turbo zlib freetype libpng

echo ">>> (4/7) Solicitando permissão de armazenamento..."
termux-setup-storage
# Adiciona uma pequena pausa para o usuário ver a solicitação de permissão
sleep 3

cd ~
echo ">>> (5/7) Baixando o projeto do GitHub..."
if [ -d "MeuConversorTTS" ]; then
    echo "A pasta 'MeuConversorTTS' já existe. Pulando o download."
else
    git clone https://github.com/JonJonesBR/MeuConversorTTS.git
fi
cd MeuConversorTTS

echo ">>> (6/7) Criando e ativando o ambiente virtual..."
python -m venv venv
source venv/bin/activate

echo ">>> (7/7) Instalando as dependências Python do projeto..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo ""
echo "--- INSTALAÇÃO CONCLUÍDA COM SUCESSO! ---"
echo "Para iniciar o programa:"
echo "1) cd ~/MeuConversorTTS"
echo "2) source venv/bin/activate"
echo "3) python main.py"
