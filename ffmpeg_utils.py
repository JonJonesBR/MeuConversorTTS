# -*- coding: utf-8 -*-
"""
Utilitários para interação com o FFmpeg.
- Normalização de áudio
- Redução de ruído
- Reprodução de áudio
- Concatenação de faixas
- Geração de vídeo (imagem estática + áudio) com barra de progresso
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, IO, cast

from tqdm import tqdm

# Importar a função limpar_nome_arquivo de file_handlers
from file_handlers import limpar_nome_arquivo
import system_utils

# ----------------------------------------------------------------------
# Helpers básicos
# ----------------------------------------------------------------------

def _obter_caminho_executavel(nome: str) -> str:
    """Retorna o nome do executável; ajuste aqui se precisar apontar para caminhos absolutos."""
    return nome

def _executar_comando_simples(comando: List[str]) -> bool:
    """Executa um comando FFmpeg e exibe indicador de atividade."""
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        
        # Executar o processo e capturar stdout e stderr
        process = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True, encoding='utf-8', errors='ignore',
                                   creationflags=flags)
        
        stderr_output = ""
        activity_indicator_time = time.monotonic() # Para o indicador de atividade simples
        
        # Loop para ler stderr e mostrar indicador de atividade
        while process.poll() is None: # Enquanto o processo estiver rodando
            # Se NÃO temos duração (ex: unificação), imprimimos um ponto periodicamente
            current_time_loop = time.monotonic()
            if current_time_loop - activity_indicator_time > 1.0: # A cada 1 segundo
                sys.stdout.write(".") # Imprime um ponto
                sys.stdout.flush()    # Garante que apareça
                activity_indicator_time = current_time_loop
            time.sleep(0.1) # Pausa curta para não sobrecarregar o loop while

        # Processo terminou
        print() # Para que a próxima mensagem não fique na mesma linha dos pontos

        # Coleta o restante do stderr após o loop (importante para mensagens de erro completas)
        stdout_final, stderr_final = process.communicate()
        stderr_output += stderr_final
        
        return_code = process.returncode # Pega o código de retorno após communicate

        if return_code != 0:
            print(f"\nX Erro durante execucao do comando FFmpeg (codigo {return_code}):")
            error_lines = stderr_output.strip().splitlines()
            relevant_errors = [ln for ln in error_lines[-20:] if 'error' in ln.lower() or ln.strip().startswith('[') or "failed" in ln.lower()]
            if not relevant_errors: relevant_errors = error_lines[-10:]
            print("\n".join(f"   {line}" for line in relevant_errors))
            return False

        print(f"OK Comando FFmpeg concluido com sucesso.")
        return True

    except FileNotFoundError:
        from system_utils import instalar_ffmpeg_windows
        sistema = system_utils.detectar_sistema()
        if sistema['windows']:
            if instalar_ffmpeg_windows():
                # Tenta executar novamente após a instalação
                try:
                    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    process = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                               universal_newlines=True, encoding='utf-8', errors='ignore',
                                               creationflags=flags)
                    
                    stderr_output = ""
                    activity_indicator_time = time.monotonic()
                    
                    while process.poll() is None:
                        current_time_loop = time.monotonic()
                        if current_time_loop - activity_indicator_time > 1.0:
                            sys.stdout.write(".")
                            sys.stdout.flush()
                            activity_indicator_time = current_time_loop
                        time.sleep(0.1)

                    print()

                    stdout_final, stderr_final = process.communicate()
                    stderr_output += stderr_final
                    
                    return_code = process.returncode

                    if return_code != 0:
                        print(f"\nX Erro durante execucao do comando FFmpeg (codigo {return_code}):")
                        error_lines = stderr_output.strip().splitlines()
                        relevant_errors = [ln for ln in error_lines[-20:] if 'error' in ln.lower() or ln.strip().startswith('[') or "failed" in ln.lower()]
                        if not relevant_errors: relevant_errors = error_lines[-10:]
                        print("\n".join(f"   {line}" for line in relevant_errors))
                        return False

                    print(f"OK Comando FFmpeg concluido com sucesso.")
                    return True
                except FileNotFoundError:
                    print(obter_mensagem_ffmpeg_nao_encontrado())
                    return False
            else:
                print(obter_mensagem_ffmpeg_nao_encontrado())
                return False
        else:
            print(obter_mensagem_ffmpeg_nao_encontrado())
            return False
    except Exception as e:
        print(f"X Erro inesperado durante execucao do comando FFmpeg: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def _remover_args_progresso(cmd: List[str]) -> List[str]:
    """Remove '-progress' e seu argumento seguinte, além de '-nostats'."""
    novo = []
    skip_next = False
    for arg in cmd:
        if skip_next:
            skip_next = False
            continue
        if arg == '-progress':
            skip_next = True
            continue
        if arg == '-nostats':
            continue
        novo.append(arg)
    return novo

def _executar_com_progresso(comando: List[str], duracao_total: float, desc: str) -> bool:
    """
    Executa um comando FFmpeg e exibe uma barra de progresso a partir de 'out_time_ms'
    emitido pelo parâmetro '-progress pipe:1'. Se a duração for inválida, executa sem barra.
    """
    if duracao_total is None or duracao_total <= 0:
        print("⚠️ Não foi possível determinar a duração. Executando sem barra de progresso.")
        return _executar_comando_simples(_remover_args_progresso(comando))

    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    try:
        processo = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore',
            creationflags=flags
        )
    except FileNotFoundError:
        from system_utils import instalar_ffmpeg_windows
        sistema = system_utils.detectar_sistema()
        if sistema['windows']:
            if instalar_ffmpeg_windows():
                # Tenta executar novamente após a instalação
                flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                try:
                    processo = subprocess.Popen(
                        comando,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        encoding='utf-8',
                        errors='ignore',
                        creationflags=flags
                    )
                except FileNotFoundError:
                    print(obter_mensagem_ffmpeg_nao_encontrado())
                    return False
            else:
                print(obter_mensagem_ffmpeg_nao_encontrado())
                return False
        else:
            print(obter_mensagem_ffmpeg_nao_encontrado())
            return False

        # --- Correção para o Pylance: stdout/stderr são Optional; afirmar que não são None ---
        if processo.stdout is None or processo.stderr is None:
            # Algo deu errado na criação dos pipes; encerra com erro para evitar AttributeError
            processo.wait()
            print("❌ Falha ao criar pipes de progresso do FFmpeg (stdout/stderr vazios).")
            return False
        out_stream: IO[str] = cast(IO[str], processo.stdout)
        err_stream: IO[str] = cast(IO[str], processo.stderr)
        # -------------------------------------------------------------------------------------

        total_us = int(duracao_total * 1_000_000)
        ok = True
        stderr_output = ""

        with tqdm(total=total_us, desc=desc, unit='s', unit_scale=1/1_000_000,
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                  ncols=80) as pbar:
            # Consome stdout (progress)
            for linha in iter(out_stream.readline, ''):
                if 'out_time_ms' in linha:
                    try:
                        tempo_atual_us = int(linha.strip().split('=')[1])
                        avanco = tempo_atual_us - pbar.n
                        if avanco > 0:
                            pbar.update(avanco)
                    except (ValueError, IndexError):
                        continue

            # Finaliza processo
            stderr_output = err_stream.read()
            processo.wait()
            if processo.returncode != 0:
                ok = False
                print(f"\n❌ Erro ao executar o comando FFmpeg (código: {processo.returncode}).")
                if stderr_output:
                    print(f"   Detalhes: {stderr_output.strip()}")
            else:
                if pbar.n < pbar.total:
                    pbar.update(pbar.total - pbar.n)

        return ok

    # --- Correção para o Pylance: stdout/stderr são Optional; afirmar que não são None ---
    if processo.stdout is None or processo.stderr is None:
        # Algo deu errado na criação dos pipes; encerra com erro para evitar AttributeError
        processo.wait()
        print("❌ Falha ao criar pipes de progresso do FFmpeg (stdout/stderr vazios).")
        return False
    out_stream: IO[str] = cast(IO[str], processo.stdout)
    err_stream: IO[str] = cast(IO[str], processo.stderr)
    # -------------------------------------------------------------------------------------

    total_us = int(duracao_total * 1_000_000)
    ok = True
    stderr_output = ""

    with tqdm(total=total_us, desc=desc, unit='s', unit_scale=1/1_000_000,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
              ncols=80) as pbar:
        # Consome stdout (progress)
        for linha in iter(out_stream.readline, ''):
            if 'out_time_ms' in linha:
                try:
                    tempo_atual_us = int(linha.strip().split('=')[1])
                    avanco = tempo_atual_us - pbar.n
                    if avanco > 0:
                        pbar.update(avanco)
                except (ValueError, IndexError):
                    continue

        # Finaliza processo
        stderr_output = err_stream.read()
        processo.wait()
        if processo.returncode != 0:
            ok = False
            print(f"\n❌ Erro ao executar o comando FFmpeg (código: {processo.returncode}).")
            if stderr_output:
                print(f"   Detalhes: {stderr_output.strip()}")
        else:
            if pbar.n < pbar.total:
                pbar.update(pbar.total - pbar.n)

    return ok

def obter_duracao_com_ffprobe(caminho_arquivo: str) -> float:
    """Retorna a duração (segundos) usando o ffprobe. 0.0 se não disponível."""
    comando = [
        _obter_caminho_executavel('ffprobe'),
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        caminho_arquivo
    ]
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True, creationflags=flags)
        return float(resultado.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return 0.0

def verificar_ffmpeg() -> bool:
    """Verifica se o FFmpeg está instalado e acessível no PATH do sistema."""
    try:
        comando = [_obter_caminho_executavel('ffmpeg'), "-version"]
        subprocess.run(comando, check=True, capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Tenta instalar automaticamente no Windows
        sistema = system_utils.detectar_sistema()
        if sistema['windows']:
            from system_utils import instalar_ffmpeg_windows
            return instalar_ffmpeg_windows()
        return False

def obter_mensagem_ffmpeg_nao_encontrado() -> str:
    """Retorna uma mensagem detalhada sobre como instalar o FFmpeg."""
    sistema = system_utils.detectar_sistema()
    
    if sistema['windows']:
        mensagem = (
            "❌ FFmpeg não encontrado no sistema.\n"
            "Para instalar no Windows:\n"
            "1. Baixe o FFmpeg em https://www.gyan.dev/ffmpeg/builds/\n"
            "2. Extraia o conteúdo em uma pasta (ex: C:\\ffmpeg)\n"
            "3. Adicione o caminho 'C:\\ffmpeg\\bin' ao PATH do sistema:\n"
            "   - Abra o Painel de Controle > Sistema > Configurações Avançadas do Sistema\n"
            "   - Clique em 'Variáveis de Ambiente'\n"
            "   - Na seção 'Variáveis do Sistema', encontre e selecione 'Path', clique em 'Editar'\n"
            "   - Clique em 'Novo' e adicione o caminho 'C:\\ffmpeg\\bin'\n"
            "   - Clique em 'OK' para fechar todas as janelas\n"
            "4. Reinicie o terminal ou o computador para aplicar as alterações"
        )
    elif sistema['linux']:
        mensagem = (
            "❌ FFmpeg não encontrado no sistema.\n"
            "Para instalar no Linux (Ubuntu/Debian):\n"
            "  sudo apt update && sudo apt install ffmpeg\n\n"
            "Para outras distribuições, verifique o gerenciador de pacotes correspondente."
        )
    elif sistema['termux'] or sistema['android']:
        mensagem = (
            "❌ FFmpeg não encontrado no sistema.\n"
            "Para instalar no Termux:\n"
            "  pkg install ffmpeg"
        )
    else:  # macOS
        mensagem = (
            "❌ FFmpeg não encontrado no sistema.\n"
            "Para instalar no macOS:\n"
            "  1. Instale o Homebrew (caso ainda não tenha): /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n"
            "  2. Instale o FFmpeg: brew install ffmpeg"
        )
    
    return mensagem

# ----------------------------------------------------------------------
# Operações de áudio
# ----------------------------------------------------------------------

def reduzir_ruido_ffmpeg(caminho_entrada: str, caminho_saida: str) -> bool:
    """Aplica um filtro de redução de ruído simples (FFT Denoise)."""
    print("🔧 Reduzindo ruído...")
    comando = [
        _obter_caminho_executavel('ffmpeg'),
        '-y',
        '-i', caminho_entrada,
        '-af', 'afftdn',
        caminho_saida
    ]
    return _executar_comando_simples(comando)

def normalizar_audio_ffmpeg(caminho_entrada: str, caminho_saida: str) -> bool:
    """Normaliza o áudio usando loudnorm."""
    print("🎚️ Normalizando áudio...")
    comando = [
        _obter_caminho_executavel('ffmpeg'),
        '-y',
        '-i', caminho_entrada,
        '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
        caminho_saida
    ]
    return _executar_comando_simples(comando)

def reproduzir_audio(caminho_audio: str) -> bool:
    """Reproduz audio utilizando ffplay."""
    print("▶️ Reproduzindo áudio...")
    comando = [
        _obter_caminho_executavel('ffplay'),
        '-nodisp', '-autoexit',
        caminho_audio
    ]
    return _executar_comando_simples(comando)

def unificar_arquivos_audio_ffmpeg(lista_arquivos: List[str], caminho_saida: str) -> bool:
    """
    Concatena múltiplos áudios (mesmo codec) usando concat demuxer.
    Cria arquivo temporário com a lista de arquivos.
    """
    if not lista_arquivos:
        print("⚠️ Lista de arquivos vazia.")
        return False
    
    # Cria um arquivo de lista para o FFmpeg concat demuxer
    # Usar caminhos absolutos e sanitizados para o file list
    dir_saida = os.path.dirname(caminho_saida)
    os.makedirs(dir_saida, exist_ok=True) # Garante que o diretório de saída existe
    # Limpa o nome do arquivo de lista para evitar caracteres problemáticos
    nome_lista_limpo = limpar_nome_arquivo(f"_{Path(caminho_saida).stem}_filelist.txt")
    caminho_lista = Path(dir_saida) / nome_lista_limpo

    try:
        with open(caminho_lista, "w", encoding='utf-8') as f_list:
            for temp_file in lista_arquivos:
                # FFmpeg concat demuxer precisa de caminhos 'safe'
                # Escapar caracteres especiais para o formato do arquivo de lista
                safe_path = str(Path(temp_file).resolve()).replace("'", r"\'")
                f_list.write(f"file '{safe_path}'\n")
        
        comando = [
            _obter_caminho_executavel('ffmpeg'),
            '-y',
            '-f', 'concat',
            '-safe', '0', # -safe 0 é necessário para caminhos absolutos
            '-i', str(caminho_lista),
            '-c', 'copy', # Copia os codecs sem reencodar
            caminho_saida
        ]
        # A unificação com -c copy é rápida e não fornece progresso útil por tempo
        return _executar_comando_simples(comando)
    except IOError as e:
        print(f"❌ Erro ao criar arquivo de lista para FFmpeg: {e}")
        return False
    finally:
        # Remove o arquivo de lista temporário
        if caminho_lista.exists():
            try:
                caminho_lista.unlink()
            except Exception as e_unlink:
                print(f"⚠️ Não foi possível remover o arquivo de lista temporário {caminho_lista}: {e_unlink}")

# ----------------------------------------------------------------------
# Geração de vídeo (imagem estática + áudio)
# ----------------------------------------------------------------------

def criar_video_a_partir_de_audio(caminho_audio: str, caminho_saida: str, resolucao_str: str = "640x360") -> bool:
    """
    Gera um vídeo MP4 a partir de um arquivo de áudio (com tela preta estática),
    com barra de progresso baseada na duração do áudio.
    """
    duracao = obter_duracao_com_ffprobe(caminho_audio)

    comando = [
        _obter_caminho_executavel('ffmpeg'),
        '-y',
        '-f', 'lavfi', '-i', f"color=c=black:s={resolucao_str}:r=1:d={duracao:.3f}",
        '-i', caminho_audio,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'stillimage',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        caminho_saida
    ]
    return _executar_com_progresso(comando, duracao, "🎬 Gerando Vídeo")
