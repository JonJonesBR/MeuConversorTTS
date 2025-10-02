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
import updater

# ================== FUNÇÕES GENÉRICAS DE UI ==================

def limpar_tela():
    """Limpa a tela do terminal."""
    os.system('cls' if system_utils.detectar_sistema()['windows'] else 'clear')

async def obter_opcao_numerica(prompt: str, num_max: int, permitir_zero=False) -> int:
    """Pede ao utilizador para digitar uma opção numérica válida."""
    min_val = 0 if permitir_zero else 1
    while True:
        try:
            escolha_str = await aioconsole.ainput(f"{prompt} [{min_val}-{num_max}]: ")
            if shared_state.CANCELAR_PROCESSAMENTO: return -1
            escolha = int(escolha_str)
            if min_val <= escolha <= num_max:
                return escolha
            else:
                print(f"⚠️ Opção inválida. Escolha um número entre {min_val} e {num_max}.")
        except ValueError:
            print("⚠️ Entrada inválida. Por favor, digite um número.")
        except asyncio.CancelledError:
            shared_state.CANCELAR_PROCESSAMENTO = True
            return -1

async def obter_confirmacao(prompt: str, default_yes=True) -> bool:
    """Pede ao utilizador uma confirmação (Sim/Não)."""
    opcoes_prompt = "(S/n)" if default_yes else "(s/N)"
    while True:
        try:
            resposta = await aioconsole.ainput(f"{prompt} {opcoes_prompt}: ")
            if shared_state.CANCELAR_PROCESSAMENTO: return False
            resposta = resposta.strip().lower()
            if not resposta: return default_yes
            if resposta in ['s', 'sim']: return True
            if resposta in ['n', 'nao', 'não']: return False
            print("⚠️ Resposta inválida. Digite 's' ou 'n'.")
        except asyncio.CancelledError:
            shared_state.CANCELAR_PROCESSAMENTO = True
            return False

async def exibir_banner_e_menu(titulo_menu: str, opcoes_menu: dict):
    """Exibe o banner do programa e um menu de opções."""
    limpar_tela()
    print("╔════════════════════════════════════════════╗")
    print("║         CONVERSOR TTS COMPLETO             ║")
    print("║ Text-to-Speech + Melhoria de Áudio em PT-BR║")
    print("╚════════════════════════════════════════════╝")
    print(f"\n--- {titulo_menu.upper()} ---")
    num_opcoes = max([int(k) for k in opcoes_menu.keys() if k.isdigit()], default=0)
    for num, desc in opcoes_menu.items():
        print(f"{num}. {desc}")
    return await obter_opcao_numerica("Opção", num_opcoes, permitir_zero=('0' in opcoes_menu))

# ================== LÓGICA DE NAVEGAÇÃO E SELEÇÃO ==================

async def _navegador_de_sistema(selecionar_pasta=False, extensoes_permitidas=None):
    """Navegador de sistema de ficheiros para selecionar um ficheiro ou pasta."""
    if extensoes_permitidas is None:
        extensoes_permitidas = ['.txt', '.pdf', '.epub']
    
    prompt_titulo = "PASTA" if selecionar_pasta else "FICHEIRO"
    prompt_formatos = "" if selecionar_pasta else f"(Formatos: {', '.join(extensoes_permitidas)})"
    
    sistema = system_utils.detectar_sistema()
    dir_atual = Path.home() / 'Downloads'
    if sistema['termux']:
        dir_atual_termux = Path.home() / 'storage' / 'shared'
        if dir_atual_termux.is_dir():
            dir_atual = dir_atual_termux
        else:
            dir_atual = Path("/storage/emulated/0")
            
    if not dir_atual.is_dir(): dir_atual = Path.home()

    while not shared_state.CANCELAR_PROCESSAMENTO:
        limpar_tela()
        print(f"📂 SELEÇÃO DE {prompt_titulo} {prompt_formatos}")
        print(f"\nDiretório atual: {dir_atual}")
        
        itens = []
        try:
            # Apenas mostra a opção de voltar se não estivermos na raiz do armazenamento
            if dir_atual.parent != dir_atual and str(dir_atual) != '/storage/emulated/0':
                if sistema['termux'] and str(dir_atual.parent) == '/storage/emulated':
                    # Não adiciona a opção de voltar se o pai for a pasta protegida
                    pass
                else:
                    itens.append(("[..] (Voltar)", dir_atual.parent, True))
            
            for item in sorted(list(dir_atual.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower())):
                if item.is_dir():
                    itens.append((f"[{item.name}]", item, True))
                elif not selecionar_pasta and item.suffix.lower() in extensoes_permitidas:
                    itens.append((item.name, item, False))
        except PermissionError:
            print(f"❌ Permissão negada para aceder: {dir_atual}")
            dir_atual = dir_atual.parent
            await asyncio.sleep(2)
            continue
        
        for i, (nome, _, _) in enumerate(itens):
            print(f"{i+1}. {nome}")
        
        print("\nOpções:")
        if selecionar_pasta:
            print("A. Selecionar esta pasta atual")
        print("V. Voltar ao menu anterior")

        try:
            escolha_str = (await aioconsole.ainput("\nEscolha um número ou opção: ")).strip().upper()
            if shared_state.CANCELAR_PROCESSAMENTO: return ""

            if escolha_str == 'V': return ""
            if selecionar_pasta and escolha_str == 'A':
                return str(dir_atual)
            
            idx_escolha = int(escolha_str) - 1
            if 0 <= idx_escolha < len(itens):
                _, path_sel, is_dir_sel = itens[idx_escolha]
                if is_dir_sel:
                    dir_atual = path_sel
                elif not selecionar_pasta:
                    return str(path_sel)
            else:
                print("❌ Opção inválida.")
        except (ValueError, IndexError):
            print("❌ Seleção inválida.")
        except asyncio.CancelledError:
            shared_state.CANCELAR_PROCESSAMENTO = True
            return ""
        await asyncio.sleep(1)

# ================== LÓGICA CENTRAL DE CONVERSÃO ==================

async def _executar_conversao_de_arquivo(caminho_arquivo: str, voz: str):
    """
    Função central que executa todo o processo de conversão para um único ficheiro.
    Retorna True em sucesso, False em falha.
    """
    print("-" * 50)
    print(f"▶️ A iniciar conversão para: {Path(caminho_arquivo).name}")

    caminho_txt = await _processar_arquivo_selecionado_para_texto(caminho_arquivo)
    if not caminho_txt or shared_state.CANCELAR_PROCESSAMENTO:
        print(f"⚠️ A saltar ficheiro (falha no pré-processamento): {Path(caminho_arquivo).name}")
        return False

    texto = file_handlers.ler_arquivo_texto(caminho_txt)
    if not texto.strip():
        print(f"⚠️ A saltar ficheiro (texto vazio): {Path(caminho_arquivo).name}")
        return False

    partes_texto = tts_service.dividir_texto_para_tts(texto)
    if not partes_texto:
        print(f"⚠️ A saltar ficheiro (sem texto para converter): {Path(caminho_arquivo).name}")
        return False

    path_txt_obj = Path(caminho_txt)
    nome_base_audio = file_handlers.limpar_nome_arquivo(path_txt_obj.stem.replace("_formatado", ""))
    dir_saida_audio = path_txt_obj.parent / f"{nome_base_audio}_AUDIO_TTS"
    dir_saida_audio.mkdir(parents=True, exist_ok=True)

    arquivos_mp3_temporarios = [str(dir_saida_audio / f"temp_{i+1:04d}.mp3") for i in range(len(partes_texto))]
    
    semaphore = asyncio.Semaphore(config.LOTE_MAXIMO_TAREFAS_CONCORRENTES)
    tarefas = []
    
    async def run_conversion(p_texto, v, caminho, i, total):
        async with semaphore:
            return await tts_service.converter_chunk_tts(p_texto, v, caminho, i, total)

    for i, parte in enumerate(partes_texto):
        tarefa = asyncio.create_task(run_conversion(parte, voz, arquivos_mp3_temporarios[i], i + 1, len(partes_texto)))
        tarefas.append(tarefa)

    with tqdm(total=len(tarefas), desc=f"   TTS para '{nome_base_audio[:15]}...'") as pbar:
        for f in asyncio.as_completed(tarefas):
            await f
            pbar.update(1)

    arquivos_sucesso = [c for c in arquivos_mp3_temporarios if Path(c).exists() and Path(c).stat().st_size > 200]

    sucesso_final = False
    if not arquivos_sucesso:
        print(f"\n❌ Nenhuma parte foi convertida com sucesso para {nome_base_audio}")
    else:
        arquivo_final_mp3 = dir_saida_audio / f"{nome_base_audio}_COMPLETO.mp3"
        if ffmpeg_utils.unificar_arquivos_audio_ffmpeg(arquivos_sucesso, str(arquivo_final_mp3)):
            print(f"✅ Conversão concluída com sucesso para: {arquivo_final_mp3.name}")
            sucesso_final = True
        else:
            print(f"❌ Falha ao unificar os áudios para {nome_base_audio}")

    for temp_f in arquivos_mp3_temporarios:
        Path(temp_f).unlink(missing_ok=True)
    
    return sucesso_final

async def _processar_arquivo_selecionado_para_texto(caminho_arquivo_orig: str) -> str:
    """Orquestra a conversão (PDF/EPUB -> TXT) e formatação do texto."""
    if not caminho_arquivo_orig: return ""
    
    path_obj = Path(caminho_arquivo_orig)
    nome_base_limpo = file_handlers.limpar_nome_arquivo(path_obj.stem)
    dir_saida = path_obj.parent
    caminho_txt_formatado = dir_saida / f"{nome_base_limpo}_formatado.txt"

    if caminho_txt_formatado.exists() and not await obter_confirmacao(f"Ficheiro '{caminho_txt_formatado.name}' já existe. Reprocessar?", default_yes=False):
        return str(caminho_txt_formatado)

    texto_bruto = ""
    extensao = path_obj.suffix.lower()
    if extensao == '.pdf':
        caminho_txt_temp = dir_saida / f"{nome_base_limpo}_tempExtraido.txt"
        if not file_handlers.converter_pdf_para_txt(str(path_obj), str(caminho_txt_temp)): return ""
        texto_bruto = file_handlers.ler_arquivo_texto(str(caminho_txt_temp))
        Path(caminho_txt_temp).unlink(missing_ok=True)
    elif extensao == '.epub':
        texto_bruto = file_handlers.extrair_texto_de_epub(str(path_obj))
    elif extensao == '.txt':
        texto_bruto = file_handlers.ler_arquivo_texto(str(path_obj))
    
    if not texto_bruto.strip():
        print("❌ Conteúdo do ficheiro de origem está vazio.")
        return ""
        
    texto_final = text_processing.formatar_texto_para_tts(texto_bruto)
    file_handlers.salvar_arquivo_texto(str(caminho_txt_formatado), texto_final)
    return str(caminho_txt_formatado)

# ================== FLUXOS DE TRABALHO PRINCIPAIS (MENU) ==================

async def iniciar_conversao_tts():
    """Fluxo para a opção 'Converter um Único Ficheiro'."""
    shared_state.CANCELAR_PROCESSAMENTO = False
    caminho_arquivo_orig = await _navegador_de_sistema(selecionar_pasta=False)
    if not caminho_arquivo_orig or shared_state.CANCELAR_PROCESSAMENTO: return

    voz_padrao = settings_manager.obter_configuracao('voz_padrao')
    voz_padrao_nome = voz_padrao.split('-')[2]
    
    if await obter_confirmacao(f"\nUsar a voz padrão ({voz_padrao_nome})?", default_yes=True):
        voz_escolhida = voz_padrao
    else:
        limpar_tela()
        print("\n--- SELECIONAR VOZ ---")
        for i, voz in enumerate(config.VOZES_PT_BR): print(f"{i+1}. {voz.split('-')[2]}")
        escolha_idx = await obter_opcao_numerica("Escolha uma voz", len(config.VOZES_PT_BR))
        if escolha_idx == -1: return
        voz_escolhida = config.VOZES_PT_BR[escolha_idx - 1]

    await _executar_conversao_de_arquivo(caminho_arquivo_orig, voz_escolhida)
    await aioconsole.ainput("\nPressione ENTER para voltar ao menu...")


async def iniciar_conversao_em_lote():
    """Fluxo para a opção 'Converter Pasta Inteira'."""
    shared_state.CANCELAR_PROCESSAMENTO = False
    caminho_pasta = await _navegador_de_sistema(selecionar_pasta=True)
    if not caminho_pasta or shared_state.CANCELAR_PROCESSAMENTO: return

    incluir_subpastas = await obter_confirmacao("Incluir subpastas na procura?", default_yes=True)
    
    print("\n🔎 A procurar ficheiros compatíveis...")
    tipos_permitidos = ('.txt', '.pdf', '.epub')
    ficheiros_a_converter = []
    if incluir_subpastas:
        for root, _, files in os.walk(caminho_pasta):
            for name in files:
                if name.lower().endswith(tipos_permitidos):
                    ficheiros_a_converter.append(os.path.join(root, name))
    else:
        for name in os.listdir(caminho_pasta):
            caminho_completo = os.path.join(caminho_pasta, name)
            if os.path.isfile(caminho_completo) and name.lower().endswith(tipos_permitidos):
                ficheiros_a_converter.append(caminho_completo)

    if not ficheiros_a_converter:
        print("❌ Nenhum ficheiro compatível encontrado na pasta selecionada.")
        await aioconsole.ainput("\nPressione ENTER para voltar...")
        return

    print(f"\n✅ {len(ficheiros_a_converter)} ficheiro(s) encontrado(s).")
    
    voz_padrao = settings_manager.obter_configuracao('voz_padrao')
    voz_nome = voz_padrao.split('-')[2]
    print(f"\nℹ️ A conversão usará a voz padrão: {voz_nome}")

    if not await obter_confirmacao("\nDeseja iniciar a conversão em lote?", default_yes=True):
        return

    sucessos = 0
    falhas = 0
    for i, ficheiro in enumerate(ficheiros_a_converter):
        if shared_state.CANCELAR_PROCESSAMENTO:
            print("\n🚫 Processo em lote cancelado pelo utilizador.")
            break
        print("\n" + "="*50)
        print(f"🔄 A processar ficheiro {i+1} de {len(ficheiros_a_converter)}")
        if await _executar_conversao_de_arquivo(ficheiro, voz_padrao):
            sucessos += 1
        else:
            falhas += 1

    print("\n" + "="*50)
    print("🎉 Processo em lote concluído!")
    print(f"   - Ficheiros convertidos com sucesso: {sucessos}")
    print(f"   - Ficheiros com falha ou ignorados: {falhas}")
    await aioconsole.ainput("\nPressione ENTER para voltar ao menu...")


async def testar_vozes_tts():
    """Fluxo completo para a opção 'Testar Vozes'."""
    # ... (código existente permanece o mesmo)
    pass


async def _processar_melhoria_de_audio_video(caminho_arquivo_entrada: str):
    """Lógica interna para o fluxo de melhoria de multimédia."""
    # ... (código existente permanece o mesmo)
    pass

async def menu_melhorar_audio_video():
    """Fluxo para a opção 'Melhorar Áudio/Vídeo'."""
    # ... (código existente permanece o mesmo)
    pass

async def exibir_ajuda():
    """Mostra a tela de ajuda com as instruções de uso."""
    # ... (código existente permanece o mesmo)
    pass

async def atualizar_script():
    """Verifica por atualizações no repositório GitHub de forma segura."""
    # ... (código existente permanece o mesmo)
    pass

async def menu_gerenciar_configuracoes():
    """Permite ao utilizador visualizar e alterar as configurações padrão."""
    # ... (código existente permanece o mesmo)
    pass
