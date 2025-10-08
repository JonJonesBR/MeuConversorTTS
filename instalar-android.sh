#!/bin/bash
# Script para automatizar a instalação do MeuConversorTTS no Termux
set -e

echo ">>> (1/6) Atualizando pacotes do Termux..."
pkg update -y && pkg upgrade -y

echo ">>> (2/6) Instalando dependências do sistema (python, git, ffmpeg, poppler)..."
pkg install -y python git ffmpeg poppler

echo ">>> (3/6) Solicitando permissão de armazenamento..."
echo "!!! IMPORTANTE: Conceda permissão de armazenamento ao Termux quando solicitado."
read -p "Digite 'sim' para conceder e continuar: " confirmacao
[ "$confirmacao" = "sim" ] || { echo "Instalação cancelada."; exit 1; }
termux-setup-storage

cd ~
echo ">>> (4/6) Baixando o projeto do GitHub..."
if [ -d "MeuConversorTTS" ]; then
    echo "A pasta 'MeuConversorTTS' já existe. Pulando o download."
else
    git clone https://github.com/JonJonesBR/MeuConversorTTS.git
fi
cd MeuConversorTTS

echo ">>> (5/6) Criando e ativando o ambiente virtual..."
python -m venv venv

echo ">>> (6/6) Instalando as dependências Python do projeto..."
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "--- INSTALAÇÃO CONCLUÍDA! ---"
echo "1) cd MeuConversorTTS"
echo "2) source venv/bin/activate"
echo "3) python main.py"
# --- FIM DO SCRIPT ---
