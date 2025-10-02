# -*- coding: utf-8 -*-
"""
Módulo da Interface de Utilizador de Linha de Comando (CLI-UI).
Contém todas as funções para interação com o utilizador, como menus,
seleção de ficheiros e orquestração dos fluxos de trabalho.
"""
import os
import sys
import asyncio
import subprocess
import shutil
from pathlib import Path
import time
import requests

import aioconsole
from tqdm import tqdm

# Importa de todos os nossos outros módulos
import config
import shared_state
import system_utils
import file_handlers
import text_processing
import tts_service
import ffmpeg_utils
import settings_manager
import updater # <- NOVA IMPORTAÇÃO

# ... (todo o resto do seu código cli_ui.py permanece igual) ...

# SUBSTITUA A FUNÇÃO ANTIGA "atualizar_script" POR ESTA NOVA VERSÃO
async def atualizar_script():
    """Verifica por atualizações no repositório GitHub de forma segura."""
    limpar_tela()
    print("🔄 ATUALIZAÇÃO DO SCRIPT")
    
    if not updater.is_git_repository():
        print("\n⚠️ Esta instalação não foi feita via 'git clone'.")
        print("A verificação automática não é possível.")
        print("\nPara atualizar, por favor, siga estes passos:")
        print("1. Faça backup do seu ficheiro 'settings.ini'.")
        print(f"2. Apague a pasta atual do projeto.")
        print(f"3. Reinstale o projeto seguindo as instruções no README.")
        print(f"\nRepositório: {updater.REPO_URL}")
    else:
        status, mensagem = updater.check_for_updates_git()
        print(f"\n{mensagem}")

        if status == "atualizacao_disponivel":
            print("\nPara atualizar, siga estes passos no seu terminal:")
            print("1. Certifique-se de que o ambiente virtual (venv) está desativado.")
            print("2. Navegue até à pasta do projeto.")
            print("3. Execute o comando: git pull")
            print("\nApós a atualização, lembre-se de reativar o venv e verificar se há novas dependências:")
            print("pip install -r requirements.txt")

    await aioconsole.ainput("\nPressione ENTER para voltar ao menu...")


# ... (o resto das suas funções, como menu_gerenciar_configuracoes, etc., continuam aqui)

