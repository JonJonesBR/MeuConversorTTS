# -*- coding: utf-8 -*-
"""
Módulo de utilitários para interagir com o FFmpeg.
Contém funções para manipulação de áudio e vídeo, como normalização,
redução de ruído, concatenação e reprodução.
"""
import subprocess
import os
from pathlib import Path

import system_utils

__all__ = [
    'verificar_ffmpeg',
    'reduzir_ruido_ffmpeg',
    'normalizar_audio_ffmpeg',
    'unificar_arquivos_audio_ffmpeg',
    'reproduzir_audio',
    'criar_video_a_partir_de_audio'
]

def _obter_caminho_ffmpeg() -> str:
    """Retorna o nome do executável do FFmpeg/FFplay baseado no sistema."""
    return 'ffmpeg.exe' if system_utils.detectar_sistema()['windows'] else 'ffmpeg'

def _obter_caminho_ffplay() -> str:
    """Retorna o nome do executável do FFplay baseado no sistema."""
    return 'ffplay.exe' if system_utils.detectar_sistema()['windows'] else 'ffplay'

def verificar_ffmpeg() -> bool:
    """Verifica se o FFmpeg está instalado e acessível no PATH do sistema."""
    try:
        comando = [_obter_caminho_ffmpeg(), "-version"]
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return "ffmpeg version" in resultado.stdout.lower()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def _executar_comando_ffmpeg(comando: list) -> bool:
    """Função auxiliar para executar comandos FFmpeg e tratar saídas."""
    try:
        # Usamos CREATE_NO_WINDOW no Windows para evitar que uma janela de console apareça
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.run(comando, check=True, capture_output=True, creationflags=flags)
        return True
    except FileNotFoundError:
        print(f"❌ Erro: O executável '{comando[0]}' não foi encontrado.")
        print("   Por favor, verifique se o FFmpeg está instalado e no PATH do sistema.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar o comando FFmpeg:")
        print(f"   Comando: {' '.join(comando)}")
        print(f"   Erro: {e.stderr.decode('utf-8', errors='ignore')}")
        return False

def reduzir_ruido_ffmpeg(caminho_entrada: str, caminho_saida: str) -> bool:
    """Aplica um filtro de redução de ruído simples a um arquivo de áudio/vídeo."""
    print("Reduzindo ruído...")
    comando = [
        _obter_caminho_ffmpeg(),
        '-i', caminho_entrada,
        '-af', 'afftdn',  # Filtro de redução de ruído FFT
        '-y',
        caminho_saida
    ]
    return _executar_comando_ffmpeg(comando)

def normalizar_audio_ffmpeg(caminho_entrada: str, caminho_saida: str) -> bool:
    """Normaliza o volume de um arquivo de áudio/vídeo para -14 LUFS."""
    print("Normalizando áudio...")
    comando = [
        _obter_caminho_ffmpeg(),
        '-i', caminho_entrada,
        '-af', 'loudnorm=I=-14:TP=-2:LRA=11',
        '-y',
        caminho_saida
    ]
    return _executar_comando_ffmpeg(comando)

def unificar_arquivos_audio_ffmpeg(lista_arquivos: list, caminho_saida: str) -> bool:
    """Concatena uma lista de arquivos de áudio em um único arquivo."""
    if not lista_arquivos:
        return False

    print("Unificando arquivos de áudio...")
    # Cria um arquivo de lista temporário para o FFmpeg
    caminho_lista = Path(caminho_saida).parent / "concat_list.txt"
    with open(caminho_lista, "w", encoding='utf-8') as f:
        for arquivo in lista_arquivos:
            f.write(f"file '{Path(arquivo).as_posix()}'\n")

    comando = [
        _obter_caminho_ffmpeg(),
        '-f', 'concat',
        '-safe', '0',
        '-i', str(caminho_lista),
        '-c', 'copy',  # Copia o codec sem re-encoder
        '-y',
        caminho_saida
    ]
    sucesso = _executar_comando_ffmpeg(comando)
    caminho_lista.unlink()  # Remove o arquivo de lista temporário
    return sucesso

def reproduzir_audio(caminho_audio: str):
    """Reproduz um arquivo de áudio usando FFplay."""
    try:
        comando = [_obter_caminho_ffplay(), '-nodisp', '-autoexit', caminho_audio]
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.run(comando, check=True, capture_output=True, creationflags=flags)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"❌ Não foi possível reproduzir o áudio. Verifique se o FFplay está instalado.")
        print(f"   Erro: {e}")

def criar_video_a_partir_de_audio(caminho_audio: str, caminho_saida: str, resolucao: str) -> bool:
    """
    Cria um vídeo com tela preta a partir de um arquivo de áudio.
    **CORRIGIDO**: Garante que a duração do vídeo seja igual à do áudio.
    """
    print("Gerando vídeo a partir de áudio...")
    comando = [
        _obter_caminho_ffmpeg(),
        '-f', 'lavfi',                 # Define o formato de entrada como lavfi (filtro)
        '-i', f'color=c=black:s={resolucao}:r=30', # Gera um input de vídeo com tela preta
        '-i', caminho_audio,           # Define o arquivo de áudio como segundo input
        '-c:v', 'libx264',             # Codec de vídeo
        '-tune', 'stillimage',         # Otimiza para imagem estática
        '-c:a', 'aac',                 # Codec de áudio
        '-b:a', '192k',                # Bitrate do áudio
        '-shortest',                   # **A CORREÇÃO!** Finaliza quando o input mais curto (o áudio) terminar
        '-y',                          # Sobrescreve o arquivo de saída se existir
        caminho_saida
    ]
    return _executar_comando_ffmpeg(comando)
