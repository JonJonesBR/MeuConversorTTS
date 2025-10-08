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
from pathlib import Path
from typing import List, Optional, IO, cast

from tqdm import tqdm

# ----------------------------------------------------------------------
# Helpers básicos
# ----------------------------------------------------------------------

def _obter_caminho_executavel(nome: str) -> str:
    """Retorna o nome do executável; ajuste aqui se precisar apontar para caminhos absolutos."""
    return nome

def _executar_comando_simples(comando: List[str]) -> bool:
    """Executa um comando simples (sem leitura de progresso) e retorna True/False."""
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.run(comando, check=True, capture_output=True, text=True, creationflags=flags)
        return True
    except FileNotFoundError:
        print("❌ FFmpeg/FFprobe não encontrado no PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar o comando FFmpeg:")
        print(f"   Comando: {' '.join(comando)}")
        print(f"   Saída: {e.stderr}")
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
        print("❌ FFmpeg não encontrado no PATH.")
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
        return False

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

    caminho_lista = Path(caminho_saida).with_suffix('.txt')
    try:
        if caminho_lista.exists():
            caminho_lista.unlink()
        with open(caminho_lista, 'w', encoding='utf-8') as f:
            for p in lista_arquivos:
                f.write(f"file '{Path(p).as_posix()}'\n")

        comando = [
            _obter_caminho_executavel('ffmpeg'),
            '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(caminho_lista),
            '-c', 'copy',
            caminho_saida
        ]
        return _executar_comando_simples(comando)
    finally:
        try:
            if caminho_lista.exists():
                caminho_lista.unlink()
        except Exception:
            pass

# ----------------------------------------------------------------------
# Geração de vídeo (imagem estática + áudio)
# ----------------------------------------------------------------------

def criar_video_a_partir_de_audio(caminho_imagem: str, caminho_audio: str, caminho_saida: str) -> bool:
    """
    Gera um vídeo MP4 a partir de uma imagem estática e um arquivo de áudio,
    com barra de progresso baseada na duração do áudio.
    """
    duracao = obter_duracao_com_ffprobe(caminho_audio)

    comando = [
        _obter_caminho_executavel('ffmpeg'),
        '-y',
        '-loop', '1',
        '-i', caminho_imagem,
        '-i', caminho_audio,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-tune', 'stillimage',
        '-crf', '23',
        '-r', '1',
        '-c:a', 'copy',
        '-shortest',
        '-nostats',
        '-progress', 'pipe:1',
        caminho_saida
    ]
    return _executar_com_progresso(comando, duracao, "🎬 Gerando Vídeo")
