# -*- coding: utf-8 -*-
"""
Módulo de utilitários para interagir com o FFmpeg.
Contém funções para manipulação de áudio e vídeo, como normalização,
redução de ruído, concatenação, reprodução e geração de vídeo com
barra de progresso.
"""
import subprocess
import os
import re
from pathlib import Path
from tqdm import tqdm

import system_utils

__all__ = [
    'verificar_ffmpeg',
    'reduzir_ruido_ffmpeg',
    'normalizar_audio_ffmpeg',
    'unificar_arquivos_audio_ffmpeg',
    'reproduzir_audio',
    'criar_video_a_partir_de_audio'
]

def _obter_caminho_executavel(nome: str) -> str:
    """Retorna o nome do executável com .exe no Windows."""
    return f'{nome}.exe' if system_utils.detectar_sistema()['windows'] else nome

def _executar_comando_simples(comando: list) -> bool:
    """Executa um comando FFmpeg simples, sem barra de progresso."""
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        resultado = subprocess.run(
            comando, check=True, capture_output=True, text=True,
            encoding='utf-8', errors='ignore', creationflags=flags
        )
        return True
    except FileNotFoundError:
        print(f"❌ Erro: O executável '{comando[0]}' não foi encontrado.")
        print("   Por favor, verifique se o FFmpeg está instalado e no PATH do sistema.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar o comando FFmpeg:")
        print(f"   Comando: {' '.join(comando)}")
        print(f"   Erro: {e.stderr}")
        return False

def _executar_com_progresso(comando: list, duracao_total: float, desc: str) -> bool:
    """Executa um comando FFmpeg e exibe uma barra de progresso."""
    if duracao_total <= 0:
        print(f"⚠️ Não foi possível determinar a duração. Executando sem barra de progresso.")
        comando_simples = [arg for arg in comando if not ('-progress' in arg or '-nostats' in arg)]
        return _executar_comando_simples(comando_simples)

    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    processo = subprocess.Popen(
        comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True, encoding='utf-8', errors='ignore', creationflags=flags
    )

    total_us = int(duracao_total * 1_000_000)
    with tqdm(total=total_us, desc=desc, unit='s', unit_scale=1/1000000,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]', ncols=80) as pbar:
        for linha in iter(processo.stdout.readline, ''):
            if 'out_time_ms' in linha:
                try:
                    tempo_atual_us = int(linha.strip().split('=')[1])
                    avanco = tempo_atual_us - pbar.n
                    if avanco > 0:
                        pbar.update(avanco)
                except (ValueError, IndexError):
                    continue
    
    stderr_output = processo.stderr.read()
    processo.wait()

    if processo.returncode != 0:
        print(f"\n❌ Erro ao executar o comando FFmpeg (código: {processo.returncode}).")
        if stderr_output:
            print(f"   Detalhes: {stderr_output.strip()}")
        return False
    
    if pbar.n < pbar.total:
        pbar.update(pbar.total - pbar.n)
    pbar.close()
    
    return True

def obter_duracao_midia(caminho_arquivo: str) -> float:
    """Obtém a duração de um arquivo de mídia em segundos usando ffprobe."""
    comando = [
        _obter_caminho_executavel('ffprobe'),
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        caminho_arquivo
    ]
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        resultado = subprocess.run(
            comando, check=True, capture_output=True, text=True, creationflags=flags
        )
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

def reduzir_ruido_ffmpeg(caminho_entrada: str, caminho_saida: str) -> bool:
    """Aplica um filtro de redução de ruído simples."""
    print("Reduzindo ruído...")
    comando = [
        _obter_caminho_executavel('ffmpeg'), '-i', caminho_entrada, '-af', 'afftdn', '-y', caminho_saida
    ]
    return _executar_comando_simples(comando)

def normalizar_audio_ffmpeg(caminho_entrada: str, caminho_saida: str) -> bool:
    """Normaliza o volume para -14 LUFS."""
    print("Normalizando áudio...")
    comando = [
        _obter_caminho_executavel('ffmpeg'), '-i', caminho_entrada, '-af', 'loudnorm=I=-14:TP=-2:LRA=11', '-y', caminho_saida
    ]
    return _executar_comando_simples(comando)

def unificar_arquivos_audio_ffmpeg(lista_arquivos: list, caminho_saida: str) -> bool:
    """Concatena uma lista de arquivos de áudio."""
    if not lista_arquivos: return False

    caminho_lista = Path(caminho_saida).parent / "concat_list.txt"
    try:
        # **BARRA DE PROGRESSO ADICIONADA AQUI**
        # Mostra o progresso da escrita do arquivo de lista para o FFmpeg.
        with open(caminho_lista, "w", encoding='utf-8') as f:
            for arquivo in tqdm(lista_arquivos, desc="🎼 Unificando arquivos de áudio", unit=" arq", ncols=80):
                f.write(f"file '{Path(arquivo).as_posix()}'\n")

        comando = [
            _obter_caminho_executavel('ffmpeg'), '-f', 'concat', '-safe', '0', '-i',
            str(caminho_lista), '-c', 'copy', '-y', caminho_saida
        ]
        sucesso = _executar_comando_simples(comando)
        return sucesso
    finally:
        # Garante que o arquivo de lista seja sempre excluído
        if os.path.exists(caminho_lista):
             caminho_lista.unlink()


def reproduzir_audio(caminho_audio: str):
    """Reproduz um arquivo de áudio usando FFplay."""
    try:
        comando = [_obter_caminho_executavel('ffplay'), '-nodisp', '-autoexit', caminho_audio]
        _executar_comando_simples(comando)
    except Exception:
        print(f"❌ Não foi possível reproduzir o áudio. Verifique se o FFplay está instalado.")

def criar_video_a_partir_de_audio(caminho_audio: str, caminho_saida: str, resolucao: str) -> bool:
    """Cria um vídeo com tela preta a partir de um áudio, otimizado para tamanho mínimo."""
    duracao = obter_duracao_midia(caminho_audio)
    
    comando = [
        _obter_caminho_executavel('ffmpeg'),
        '-y',                          # Overwrite output
        '-f', 'lavfi',                 # Input format is a filter
        '-i', f'color=c=black:s={resolucao}', # Generate a single black frame
        '-i', caminho_audio,           # Second input is the audio file
        '-c:v', 'libx264',             # Video codec
        '-preset', 'ultrafast',        # Use a fast encoding preset
        '-tune', 'stillimage',         # Optimize for a static image (no motion)
        '-crf', '51',                  # Set Constant Rate Factor to max compression
        '-r', '1',                     # Set the output video framerate to 1 fps
        '-c:a', 'copy',                # Copy the audio stream directly, preserving quality
        '-shortest',                   # Ensure video duration matches audio duration
        '-nostats',
        '-progress', 'pipe:1',         # For the progress bar
        caminho_saida
    ]
    
    return _executar_com_progresso(comando, duracao, "🎬 Gerando Vídeo")

