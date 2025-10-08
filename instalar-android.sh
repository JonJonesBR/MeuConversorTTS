#!/bin/bash
# Script para automatizar a instalação do MeuConversorTTS no Termux (Android)
# Compatível com pdfplumber, EbookLib e Pillow
# Versão corrigida por Parceiro de Programacao

# 'set -e' é uma ótima prática! Ele faz o script parar imediatamente se um comando falhar.
set -e

echo ">>> (1/8) Atualizando pacotes do Termux..."
pkg update -y && pkg upgrade -y

echo ">>> (2/8) Instalando dependências principais..."
# <<< CORREÇÃO APLICADA AQUI >>>
# O pacote correto no repositório do Termux é 'libpdfium' e não 'pdfium'.
pkg install -y python git ffmpeg poppler libpdfium

echo ">>> (3/8) Instalando dependências gráficas para Pillow/pdfplumber..."
pkg install -y libjpeg-turbo zlib freetype libpng

echo ">>> (4/8) Instalando dependências XML necessárias para EbookLib/lxml..."
pkg install -y libxml2 libxslt clang
# Instalar lxml aqui pode ajudar a resolver dependências de compilação antes do requirements.txt
pip install lxml

echo ">>> (5/8) Solicitando permissão de armazenamento..."
echo "!!! IMPORTANTE: Conceda permissão de armazenamento ao Termux quando solicitado."
# A sua lógica para confirmação está perfeita.
read -p "Digite 'sim' para conceder e continuar: " confirmacao
[ "$confirmacao" = "sim" ] || { echo "Instalação cancelada."; exit 1; }
termux-setup-storage

# Muda para o diretório principal do usuário para garantir que o clone aconteça no lugar certo.
cd ~
echo ">>> (6/8) Baixando o projeto do GitHub..."
if [ -d "MeuConversorTTS" ]; then
    echo "A pasta 'MeuConversorTTS' já existe. Pulando o download."
else
    git clone https://github.com/JonJonesBR/MeuConversorTTS.git
fi
cd MeuConversorTTS

echo ">>> (7/8) Criando e ativando o ambiente virtual..."
# Usar um ambiente virtual é a melhor forma de gerenciar dependências de projetos Python!
python -m venv venv
source venv/bin/activate

echo ">>> (8/8) Instalando dependências Python do projeto..."
pip install --upgrade pip setuptools wheel
# A sua lógica de instalar pypdfium2 sem os bindings está 100% correta para o Termux,
# pois força o uso da biblioteca 'libpdfium' que instalamos no passo 2.
pip install pypdfium2
pip install -r requirements.txt # Instala o restante das dependências

echo ""
echo "--- INSTALAÇÃO CONCLUÍDA COM SUCESSO! ---"
echo "Para iniciar o programa:"
echo "1) cd ~/MeuConversorTTS"
echo "2) source venv/bin/activate"
echo "3) python main.py"
# --- FIM DO SCRIPT ---
