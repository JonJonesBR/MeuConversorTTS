# -*- coding: utf-8 -*-
"""
Ponto de entrada principal para a aplicação Conversor TTS.
Este script inicializa a aplicação, gere o loop principal do menu
e delega as tarefas para os módulos apropriados.
"""
import asyncio
import signal
import sys
from pathlib import Path
import aioconsole

# Importa dos nossos outros módulos
import cli_ui
import shared_state
import system_utils
import settings_manager

def verificar_permissoes_termux():
    """Verifica se as permissões de armazenamento estão concedidas no Termux."""
    sistema = system_utils.detectar_sistema()
    if sistema['termux']:
        # Check multiple possible storage paths
        possible_paths = [Path("/storage/emulated/0"), Path("/storage/emulated")]
        storage_accessible = any(path.is_dir() for path in possible_paths)
        
        if not storage_accessible:
            print("❌ Permissão de armazenamento não concedida no Termux.")
            print("Para conceder, execute no Termux: termux-setup-storage")
            print("E responda 'Allow' quando solicitado pelo sistema.")
            input("Pressione ENTER após conceder a permissão para continuar...")
            # Verifica novamente após o usuário conceder
            storage_accessible = any(path.is_dir() for path in possible_paths)
            if not storage_accessible:
                print("❌ Ainda não foi possível acessar o armazenamento. Certifique-se de conceder as permissões e tente novamente.")
                sys.exit(1)
        else:
            print("✅ Permissões de armazenamento verificadas.")

def handler_sinal(signum, frame):
    """Lida com o sinal de interrupção (CTRL+C)."""
    if not shared_state.CANCELAR_PROCESSAMENTO:
        print("\n🚫 Operação cancelada pelo utilizador. Aguarde a finalização da tarefa atual...")
        shared_state.CANCELAR_PROCESSAMENTO = True
    else:
        print("\n🚫 A forçar o encerramento...")
        sys.exit(1)


async def main_loop():
    """O loop principal que exibe o menu e direciona para as funções corretas."""
    opcoes_principais = {
        '1': "🚀 CONVERTER UM ÚNICO FICHEIRO",
        '2': "📚 CONVERTER PASTA INTEIRA (LOTE)",
        '3': "🎙️ TESTAR VOZES TTS",
        '4': "⚡ MELHORAR ÁUDIO/VÍDEO",
        '5': "⚙️ CONFIGURAÇÕES (Voz e Velocidade Padrão)",
        '6': "🔄 ATUALIZAR SCRIPT (Verificar por Novidades)",
        '7': "❓ AJUDA",
        '0': "🚪 SAIR"
    }
    
    while True:
        shared_state.CANCELAR_PROCESSAMENTO = False
        try:
            escolha = await cli_ui.exibir_banner_e_menu("MENU PRINCIPAL", opcoes_principais)

            if escolha == 1:
                await cli_ui.iniciar_conversao_tts()
            elif escolha == 2:
                await cli_ui.iniciar_conversao_em_lote()  # <- NOVA CHAMADA
            elif escolha == 3:
                await cli_ui.testar_vozes_tts()
            elif escolha == 4:
                await cli_ui.menu_melhorar_audio_video()
            elif escolha == 5:
                await cli_ui.menu_gerenciar_configuracoes()
            elif escolha == 6:
                await cli_ui.atualizar_script()
            elif escolha == 7:
                await cli_ui.exibir_ajuda()
            elif escolha == 0:
                print("\n👋 Obrigado por usar o Conversor TTS Completo!")
                break
            elif escolha == -1:  # Opção para quando o utilizador cancela a seleção
                continue

        except asyncio.CancelledError:
            print("\n🚫 Operação cancelada no menu. A voltar...")
            await asyncio.sleep(1)
        except Exception as e_main:
            print(f"\n❌ Ocorreu um erro inesperado no loop principal: {e_main}")
            import traceback
            traceback.print_exc()
            await aioconsole.ainput("Pressione ENTER para tentar continuar...")

if __name__ == "__main__":
    if Path(__file__).name == "code.py":
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ERRO DE NOME: Renomeie este ficheiro para 'main.py' para evitar conflitos!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        sys.exit(1)
        
    signal.signal(signal.SIGINT, handler_sinal)

    # ---- Bloco de inicialização ----
    settings_manager.carregar_configuracoes()
    system_utils.verificar_dependencias_essenciais()
    verificar_permissoes_termux()
    # ------------------------------------

    try:
        print("A iniciar aplicação...")
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrompido.")
    finally:
        print("🔚 Script finalizado.")
