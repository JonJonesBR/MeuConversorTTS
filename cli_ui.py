# -*- coding: utf-8 -*-
"""
Módulo da Interface de Utilizador de Linha de Comando (CLI-UI).
Contém todas as funções para interação com o utilizador, como menus,
seleção de ficheiros e orquestração dos fluxos de trabalho.

Versão combinada e aprimorada.
"""
import os
import asyncio
from pathlib import Path
import time

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

# Lista de funções públicas para exportação
__all__ = [
     'limpar_tela',
     'obter_opcao_numerica',
     'obter_confirmacao',
     'exibir_banner_e_menu',
     'iniciar_conversao_tts',
     'iniciar_conversao_em_lote',
     'testar_vozes_tts',
     'menu_melhorar_audio_video',
     'menu_gerenciar_configuracoes',
     'atualizar_script',
     'exibir_ajuda'
]

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
    print("║        Text-to-Speech em PT-BR║")
    print("╚════════════════════════════════════════════╝")
    print(f"\n--- {titulo_menu.upper()} ---")
    num_opcoes = max([int(k) for k in opcoes_menu.keys() if k.isdigit()], default=0)
    for num, desc in opcoes_menu.items():
        print(f"{num}. {desc}")
    return await obter_opcao_numerica("Opção", num_opcoes, permitir_zero=('0' in opcoes_menu))

# ================== LÓGICA DE NAVEGAÇÃO E SELEÇÃO ==================

async def _navegador_de_sistema(selecionar_pasta=False, extensoes_permitidas=None):
    """Navegador de sistema de ficheiros interativo para selecionar um ficheiro ou pasta."""
    if extensoes_permitidas is None:
        extensoes_permitidas = ['.txt', '.pdf', '.epub']
    
    prompt_titulo = "PASTA" if selecionar_pasta else "FICHEIRO"
    prompt_formatos = "" if selecionar_pasta else f"(Formatos: {', '.join(extensoes_permitidas)})"
    
    sistema = system_utils.detectar_sistema()
    dir_atual = Path.home() / 'Downloads'
    if sistema['termux']:
        possible_paths = [
            Path.home() / 'storage' / 'shared',
            Path("/storage/emulated/0"),
            Path.home() / 'Downloads'
        ]
        for path in possible_paths:
            if path.is_dir():
                dir_atual = path
                break
        else:
            dir_atual = Path.home()
    elif not dir_atual.is_dir():
        dir_atual = Path.home()

    while not shared_state.CANCELAR_PROCESSAMENTO:
        if not dir_atual.is_dir():
            print(f"❌ Diretório inválido: {dir_atual}. Usando diretório home.")
            dir_atual = Path.home()
            if not dir_atual.is_dir():
                print("❌ Não foi possível encontrar um diretório válido. Saindo.")
                return None
        
        limpar_tela()
        print(f"📂 SELEÇÃO DE {prompt_titulo} {prompt_formatos}")
        print(f"\nDiretório atual: {dir_atual}")
        
        itens = []
        try:
            if dir_atual.parent != dir_atual:
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
        await asyncio.sleep(0.5)

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

    with tqdm(total=len(tarefas), desc=f"   TTS para {nome_base_audio[:15]}...") as pbar:
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
    shared_state.CANCELAR_PROCESSAMENTO = False
    limpar_tela()
    print("--- 🎙️ TESTE DE VOZES TTS ---")
    
    while not shared_state.CANCELAR_PROCESSAMENTO:
        limpar_tela()
        print("Selecione uma voz da lista para ouvir um exemplo.")
        for i, voz in enumerate(config.VOZES_PT_BR):
            print(f"{i+1}. {voz.split('-')[2]}")

        escolha_idx = await obter_opcao_numerica("Escolha uma voz para testar (ou 0 para voltar)", len(config.VOZES_PT_BR), permitir_zero=True)
        if escolha_idx <= 0: return

        voz_escolhida = config.VOZES_PT_BR[escolha_idx - 1]
        velocidade_padrao = settings_manager.obter_configuracao('velocidade_padrao')

        while not shared_state.CANCELAR_PROCESSAMENTO:
            print("\n-----------------------------------")
            print(f"Voz selecionada: {voz_escolhida.split('-')[2]}")
            print(f"Velocidade: {velocidade_padrao}")
            
            texto_exemplo = await aioconsole.ainput("Digite o texto para teste (ou 'V' para voltar): ")
            if shared_state.CANCELAR_PROCESSAMENTO or texto_exemplo.strip().upper() == 'V':
                break
            
            if not texto_exemplo.strip():
                print("⚠️ Texto não pode ser vazio.")
                continue

            caminho_audio_temp = Path.home() / f"temp_tts_test_{int(time.time())}.mp3"

            print("\n🔄 A converter texto para áudio, aguarde...")
            sucesso, _ = await tts_service.converter_texto_para_audio(
                texto_exemplo, voz_escolhida, str(caminho_audio_temp), velocidade=velocidade_padrao
            )

            if sucesso:
                print("▶️ A reproduzir áudio...")
                ffmpeg_utils.reproduzir_audio(str(caminho_audio_temp))
                Path(caminho_audio_temp).unlink(missing_ok=True)
            else:
                print("\n❌ Falha ao gerar o áudio de teste. Verifique a sua ligação à internet ou as configurações.")
            
            if not await obter_confirmacao("\nDeseja testar outro texto com esta mesma voz?", default_yes=True):
                break
        
        if not await obter_confirmacao("\nDeseja testar outra voz?", default_yes=True):
            break

    await aioconsole.ainput("\nPressione ENTER para voltar ao menu principal...")

async def _processar_melhoria_de_audio_video(caminho_arquivo_entrada: str):
    """Lógica interna para o fluxo de melhoria de multimédia (versão melhorada)."""
    limpar_tela()
    print(f"--- 🛠️ A MELHORAR: {Path(caminho_arquivo_entrada).name} ---")

    opcoes_melhoria = {
        '1': "Redução de Ruído (para vozes claras)",
        '2': "Normalização de Volume (ajusta para -14 LUFS)",
        '3': "Gerar MP4 com Tela Preta (para YouTube, etc.)",
        '0': "Voltar"
    }

    from config import RESOLUCOES_VIDEO

    while not shared_state.CANCELAR_PROCESSAMENTO:
        print("\nSelecione a melhoria que deseja aplicar:")
        for k, v in opcoes_melhoria.items(): print(f"{k}. {v}")
        
        escolha = await obter_opcao_numerica("Opção", len(opcoes_melhoria) - 1, permitir_zero=True)
        if escolha <= 0: return

        path_entrada = Path(caminho_arquivo_entrada)
        sucesso = False
        caminho_arquivo_saida = None

        if escolha == 1:
            nome_saida = f"{path_entrada.stem}_melhorado_ruido{path_entrada.suffix}"
            caminho_arquivo_saida = path_entrada.parent / nome_saida
            print("\n🔄 A aplicar Redução de Ruído... (Isto pode demorar)")
            sucesso = ffmpeg_utils.reduzir_ruido_ffmpeg(caminho_arquivo_entrada, str(caminho_arquivo_saida))
        elif escolha == 2:
            nome_saida = f"{path_entrada.stem}_melhorado_normalizado{path_entrada.suffix}"
            caminho_arquivo_saida = path_entrada.parent / nome_saida
            print("\n🔄 A aplicar Normalização de Volume...")
            sucesso = ffmpeg_utils.normalizar_audio_ffmpeg(caminho_arquivo_entrada, str(caminho_arquivo_saida))
        elif escolha == 3:
            print("\nSelecione a resolução do vídeo de saída:")
            for k, (res, desc) in RESOLUCOES_VIDEO.items(): print(f"{k}. {desc} ({res})")
            
            res_escolhida = '3' # Padrão HD
            inp = await aioconsole.ainput("Escolha (1-3, padrão 3): ")
            if inp.strip() in RESOLUCOES_VIDEO:
                res_escolhida = inp.strip()

            resolucao_str = RESOLUCOES_VIDEO[res_escolhida][0]
            nome_saida = f"{path_entrada.stem}_video_preto.mp4"
            caminho_arquivo_saida = path_entrada.parent / nome_saida
            print("\n🎬 Gerando vídeo MP4 com tela preta...")
            sucesso = ffmpeg_utils.criar_video_a_partir_de_audio(str(path_entrada), str(caminho_arquivo_saida), resolucao_str)

        if sucesso and caminho_arquivo_saida:
            print(f"\n✅ Operação concluída! Ficheiro salvo como: {caminho_arquivo_saida.name}")
        else:
            print("\n❌ Falha ao aplicar a melhoria. Verifique se o FFmpeg está instalado e se o ficheiro é válido.")

        if not await obter_confirmacao("\nDeseja aplicar outra melhoria a este mesmo ficheiro original?", default_yes=False):
            break

async def menu_melhorar_audio_video():
    """Fluxo para a opção 'Melhorar Áudio/Vídeo'."""
    shared_state.CANCELAR_PROCESSAMENTO = False
    limpar_tela()
    print("--- ⚡ MELHORIA DE ÁUDIO/VÍDEO ---")
    print("Selecione um ficheiro de áudio ou vídeo para aplicar melhorias.")

    extensoes_media = ['.mp3', '.wav', '.m4a', '.mp4', '.mkv', '.mov', '.avi', '.ogg', '.flac']
    caminho_arquivo = await _navegador_de_sistema(selecionar_pasta=False, extensoes_permitidas=extensoes_media)

    if not caminho_arquivo or shared_state.CANCELAR_PROCESSAMENTO:
        print("\nNenhum ficheiro selecionado. A voltar ao menu...")
        await asyncio.sleep(2)
        return

    await _processar_melhoria_de_audio_video(caminho_arquivo)
    await aioconsole.ainput("\nPressione ENTER para voltar ao menu principal...")

async def exibir_ajuda():
    """Mostra a tela de ajuda com as instruções de uso."""
    limpar_tela()
    print("""
--- ❓ AJUDA E INSTRUÇÕES ---

Este script foi desenhado para facilitar a conversão de texto para áudio (TTS) e realizar melhorias em ficheiros de áudio e vídeo.

➡️ Onde colocar os seus ficheiros?
   - No telemóvel (Termux): Coloque seus ficheiros .txt, .pdf, ou .epub na pasta 'storage/shared/Download' ou qualquer outra pasta partilhada para que o script os possa encontrar.
   - No PC: Pode navegar para qualquer pasta no seu sistema.

➡️ O que cada opção faz?

1.  🚀 CONVERTER UM ÚNICO FICHEIRO:
    - Selecione um ficheiro .txt, .pdf ou .epub.
    - O script irá extrair o texto, limpá-lo e convertê-lo para um áudio MP3.
    - O ficheiro de áudio final será guardado na mesma pasta do ficheiro original, dentro de um novo subdiretório com o nome do áudio.

2.  📚 CONVERTER PASTA INTEIRA (LOTE):
    - Selecione uma pasta.
    - O script irá procurar TODOS os ficheiros compatíveis (.txt, .pdf, .epub) dentro dela (e subpastas, se assim o desejar).
    - Cada ficheiro será convertido para áudio, usando a voz e velocidade padrão definidas nas configurações.

3.  🎙️ TESTAR VOZES TTS:
    - Permite-lhe ouvir exemplos de todas as vozes disponíveis em Português do Brasil.
    - Digite um texto qualquer e o script irá gerar e reproduzir o áudio na hora.

4.  ⚡ MELHORAR ÁUDIO/VÍDEO:
    - Selecione um ficheiro de áudio ou vídeo já existente.
    - Pode aplicar melhorias como:
        - Redução de Ruído: Ideal para limpar gravações de voz com ruído de fundo.
        - Normalização de Volume: Ajusta o volume do áudio para um nível padrão, útil para juntar vários áudios.
        - Gerar MP4 com Tela Preta: Converte um áudio em vídeo MP4 com tela preta, ideal para uploads em plataformas de vídeo.

5.  ⚙️ CONFIGURAÇÕES:
    - Altere a voz padrão e a velocidade da fala que serão usadas nas conversões.

6.  🔄 ATUALIZAR SCRIPT:
    - Verifica se existe uma nova versão do script no GitHub e instala-a automaticamente.

7.  ❓ AJUDA:
    - Exibe esta tela.

0.  🚪 SAIR:
    - Encerra a aplicação.


--- DICAS ---

- CANCELAR: Pressione CTRL+C a qualquer momento para cancelar a operação atual.
- DEPENDÊNCIAS: Se algo não funcionar, certifique-se que executou o script de instalação correto (instalar-*.sh ou .bat) para instalar todas as dependências como o FFmpeg.

""")
    await aioconsole.ainput("\nPressione ENTER para voltar ao menu principal...")

async def atualizar_script():
    """Verifica por atualizações no repositório GitHub de forma segura."""
    limpar_tela()
    print("--- 🔄 VERIFICAR ATUALIZAÇÕES ---")
    await updater.verificar_e_atualizar()
    await aioconsole.ainput("\nPressione ENTER para voltar ao menu principal...")

async def menu_gerenciar_configuracoes():
    """Menu para gerenciar as configurações do programa."""
    while not shared_state.CANCELAR_PROCESSAMENTO:
        limpar_tela()
        print("⚙️ MENU DE CONFIGURAÇÕES")
        voz_atual = settings_manager.obter_configuracao('voz_padrao')
        velocidade_atual = settings_manager.obter_configuracao('velocidade_padrao')
        
        print(f"\nConfigurações atuais:")
        print(f"  Voz padrão: {voz_atual}")
        print(f"  Velocidade padrão: {velocidade_atual}")
        print("\nOpções:")
        print("  1. Alterar voz padrão")
        print("  2. Alterar velocidade padrão")
        print("  0. Voltar ao menu principal")
        
        escolha = await obter_opcao_numerica("Escolha uma opção", 2, permitir_zero=True)
        
        if escolha == 0:
            break
        elif escolha == 1:
            print("\nSelecione a nova voz padrão:")
            for i, voz in enumerate(config.VOZES_PT_BR, 1):
                nome_voz = voz.split('-')[2]
                print(f"  {i}. {nome_voz}")
            
            escolha_voz = await obter_opcao_numerica("Escolha a nova voz", len(config.VOZES_PT_BR))
            if 1 <= escolha_voz <= len(config.VOZES_PT_BR):
                nova_voz = config.VOZES_PT_BR[escolha_voz - 1]
                settings_manager.salvar_configuracoes('voz_padrao', nova_voz)
                print(f"✅ Voz padrão alterada para: {nova_voz.split('-')[2]}")
        elif escolha == 2:
            try:
                nova_velocidade_str = await aioconsole.ainput(f"Nova velocidade (entre 0.5 e 2.0, atual: {velocidade_atual}): ")
                nova_velocidade = float(nova_velocidade_str.replace(',', '.'))
                if 0.5 <= nova_velocidade <= 2.0:
                    settings_manager.salvar_configuracoes('velocidade_padrao', f"x{nova_velocidade:.2f}")
                    print(f"✅ Velocidade padrão alterada para: x{nova_velocidade:.2f}")
                else:
                    print("⚠️ Velocidade fora do intervalo permitido (0.5 a 2.0).")
            except (ValueError, TypeError):
                print("⚠️ Valor inválido para velocidade.")
        
        await aioconsole.ainput("\nPressione ENTER para continuar...")

