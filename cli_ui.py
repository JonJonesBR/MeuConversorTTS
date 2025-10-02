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


def limpar_tela():
    """Limpa a tela do terminal de forma cross-platform."""
    sistema = sys.platform
    if sistema == "win32":
        subprocess.run("cls", shell=True)
    else:
        subprocess.run("clear", shell=True)

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

async def exibir_banner_e_menu(titulo, opcoes):
    """Exibe o banner e o menu principal, permitindo que o utilizador escolha uma opção."""
    limpar_tela()
    print("╔" + "═" * 60 + "╗")
    print("║{:^60}║".format(" Conversor TTS Completo "))
    print("║{:^60}║".format(" por Jonatas-Correa-Dev "))
    print("╚" + "═" * 60 + "╝")
    print(f"\n{titulo}:")
    
    for key, value in opcoes.items():
        print(f"  [{key}] {value}")
    
    print(f"\n{'─' * 50}")
    
    try:
        escolha = await aioconsole.ainput("Selecione uma opção: ")
        if escolha.isdigit():
            escolha_numero = int(escolha)
            if str(escolha_numero) in opcoes.keys():
                return escolha_numero
            else:
                print("⚠️ Opção inválida. Tente novamente.")
                await aioconsole.ainput("Pressione ENTER para continuar...")
                return -1
        else:
            print("⚠️ Por favor, insira um número válido.")
            await aioconsole.ainput("Pressione ENTER para continuar...")
            return -1
    except Exception as e:
        print(f"❌ Erro na seleção do menu: {e}")
        return -1

async def iniciar_conversao_tts():
    """Inicia o processo de conversão de texto para fala."""
    print("🚀 Iniciar conversão TTS...")
    # Implementar a lógica para conversão TTS
    print("⚠️ Função em desenvolvimento...")
    await aioconsole.ainput("Pressione ENTER para continuar...")

async def iniciar_conversao_em_lote():
    """Inicia o processo de conversão em lote."""
    print("📚 Iniciar conversão em lote...")
    # Implementar a lógica para conversão em lote
    print("⚠️ Função em desenvolvimento...")
    await aioconsole.ainput("Pressione ENTER para continuar...")

async def testar_vozes_tts():
    """Permite testar as vozes TTS disponíveis."""
    print("🎙️ Testar vozes TTS...")
    # Implementar a lógica para testar vozes
    print("⚠️ Função em desenvolvimento...")
    await aioconsole.ainput("Pressione ENTER para continuar...")

async def menu_melhorar_audio_video():
    """Exibe o menu para melhorar áudio/vídeo."""
    print("⚡ Menu para melhorar áudio/vídeo...")
    # Implementar a lógica para melhorar áudio/vídeo
    print("⚠️ Função em desenvolvimento...")
    await aioconsole.ainput("Pressione ENTER para continuar...")

async def menu_gerenciar_configuracoes():
    """Exibe o menu para gerir configurações."""
    print("⚙️ Menu de configurações...")
    # Implementar a lógica para gerir configurações
    print("⚠️ Função em desenvolvimento...")
    await aioconsole.ainput("Pressione ENTER para continuar...")

async def exibir_ajuda():
    """Exibe a ajuda do programa."""
    limpar_tela()
    print("❓ AJUDA - Conversor TTS Completo")
    print("="*60)
    print("Este programa converte textos de vários formatos (PDF, EPUB, TXT)")
    print("em ficheiros de áudio (TTS) usando as vozes da Microsoft Edge.")
    print()
    print("FUNCIONALIDADES:")
    print("• Converter ficheiros PDF, EPUB, TXT para áudio")
    print("• Converter ficheiros em lote (pasta inteira)")
    print("• Testar vozes TTS disponíveis")
    print("• Melhorar áudio/vídeo gerado")
    print("• Configurar vozes e velocidade padrão")
    print("• Atualizar automaticamente o script")
    print()
    print("SUPORTE:")
    print("• Formatos de entrada: PDF, EPUB, TXT")
    print("• Formatos de saída: MP3, WAV")
    print("• Vozes suportadas: Todas as vozes do Microsoft Edge TTS")
    print("="*60)
    
    await aioconsole.ainput("\nPressione ENTER para voltar ao menu...")

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

