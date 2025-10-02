#!/bin/bash
# Script para automatizar a instalação do MeuConversorTTS no Termux

# --- INÍCIO DO SCRIPT ---

# Garante que o script pare se algum comando falhar
set -e

# Passo 1: Atualizar e instalar dependências do sistema
echo ">>> (1/6) Atualizando pacotes do Termux..."
pkg update -y && pkg upgrade -y

echo ">>> (2/6) Instalando dependências do sistema (python, git, ffmpeg, poppler)..."
pkg install -y python git ffmpeg poppler

# Passo 2: Configurar o acesso ao armazenamento
echo ">>> (3/6) Solicitando permissão de armazenamento..."
echo "!!! ATENÇÃO: Uma janela do Android vai aparecer. Por favor, clique em 'Permitir'."
termux-setup-storage

# Passo 3: Baixar o projeto do GitHub
# Primeiro, vamos para o diretório inicial para garantir que o projeto seja baixado no lugar certo.
cd ~
echo ">>> (4/6) Baixando o projeto do GitHub..."
# Verifica se a pasta já existe para não dar erro
if [ -d "MeuConversorTTS" ]; then
    echo "A pasta 'MeuConversorTTS' já existe. Pulando o download."
else
    git clone https://github.com/JonJonesBR/MeuConversorTTS.git
fi

# Entra na pasta do projeto. Note que o nome da pasta é 'MeuConversorTTS'
cd MeuConversorTTS

# Passo 4: Configurar o ambiente Python
echo ">>> (5/6) Criando e ativando o ambiente virtual..."
python -m venv venv

echo ">>> (6/6) Instalando as dependências Python do projeto..."
# Ativamos o ambiente e instalamos os pacotes dentro do próprio script
source venv/bin/activate
pip install -r requirements.txt

# Mensagem final
echo ""
echo "--- INSTALAÇÃO CONCLUÍDA! ---"
echo ""
echo "Para começar a usar, siga os próximos passos:"
echo "1. Ative o ambiente virtual com o comando:"
echo "   source venv/bin/activate"
echo "2. Execute o programa principal com:"
echo "   python main.py"
echo ""

# --- FIM DO SCRIPT ---
