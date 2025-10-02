# -*- coding: utf-8 -*-
"""
Módulo que encapsula todas as interações com as ferramentas
de linha de comando FFmpeg e FFprobe.
"""
import os
import sys
import re
import time
import platform
import subprocess
import shutil
from pathlib import Path
from math import ceil
from tqdm import tqdm

# Importa de nossos outros módulos
import config
import shared_state

# Regex pré-compilada para capturar o tempo do progresso do FFmpeg
FFMPEG_PROGRESS_RE = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")

def _parse_ffmpeg_time(time_str: str) -> float:
    """Converte tempo 'HH:MM:SS.ms' do FFmpeg para segundos."""
    match = FFMPEG_PROGRESS_RE.search(time_str)
    if match:
        h, m, s, ms = map(int, match.groups())
        return h * 3600 + m * 60 + s + ms / 100.0
    return 0.0

def _executar_ffmpeg_comando(comando_ffmpeg: list, descricao_acao: str, total_duration: float = 0.0):
    """Executa um comando FFmpeg, lida com erros e mostra progresso."""
    if shared_state.CANCELAR_PROCESSAMENTO:
        print(f"🚫 {descricao_acao} cancelada antes de iniciar.")
        return False

    print(f"⚙️ Executando: {descricao_acao}...")
    try:
        process = subprocess.Popen(
            comando_ffmpeg,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore'
        )

        with tqdm(total=100, unit="%", desc=f"   {descricao_acao[:20]}", disable=total_duration <= 0) as pbar:
            while process.poll() is None:
                if shared_state.CANCELAR_PROCESSAMENTO:
                    print("\n🚫 Recebido sinal de cancelamento. Tentando terminar o FFmpeg...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    print("🚫 Processo FFmpeg terminado.")
                    return False

                if process.stderr is None:
                    time.sleep(0.05)
                    continue
                line = process.stderr.readline()
                if not line:
                    time.sleep(0.05)
                    continue
                
                if total_duration > 0 and 'time=' in line:
                    elapsed_seconds = _parse_ffmpeg_time(line)
                    if elapsed_seconds > 0:
                        percent = min(100, (elapsed_seconds / total_duration) * 100)
                        update_value = percent - pbar.n
                        if update_value > 0:
                            pbar.update(update_value)

        return_code = process.returncode
        if return_code != 0:
            stdout, stderr = process.communicate()
            print(f"\n❌ Erro durante {descricao_acao} (código {return_code}).")
            print("   Últimas linhas do erro:", stderr.strip().splitlines()[-5:])
            return False

        print(f"✅ {descricao_acao} concluída.")
        return True

    except FileNotFoundError:
        print(f"❌ Comando '{comando_ffmpeg[0]}' não encontrado. Verifique se o FFmpeg está instalado e no PATH.")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado ao executar FFmpeg: {e}")
        return False

def obter_duracao_midia(caminho_arquivo: str) -> float:
    """Obtém a duração de um arquivo de mídia em segundos usando ffprobe."""
    if not shutil.which(config.FFPROBE_BIN):
        print(f"⚠️ {config.FFPROBE_BIN} não encontrado. Não é possível obter duração da mídia.")
        return 0.0
    
    comando = [
        config.FFPROBE_BIN, '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', caminho_arquivo
    ]
    try:
        resultado = subprocess.run(comando, stdout=subprocess.PIPE, text=True, check=True)
        return float(resultado.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        print(f"⚠️ Erro ao obter duração de '{os.path.basename(caminho_arquivo)}': {e}")
        return 0.0

def unificar_arquivos_audio_ffmpeg(lista_arquivos_temp: list, arquivo_final: str) -> bool:
    """Une arquivos de áudio temporários em um único arquivo final usando FFmpeg."""
    if not lista_arquivos_temp:
        print("⚠️ Nenhum arquivo de áudio para unificar.")
        return False
    
    dir_saida = Path(arquivo_final).parent
    dir_saida.mkdir(exist_ok=True)
    lista_txt_path = dir_saida / f"_{Path(arquivo_final).stem}_filelist.txt"

    try:
        with open(lista_txt_path, "w", encoding='utf-8') as f_list:
            for temp_file in lista_arquivos_temp:
                safe_path = str(Path(temp_file).resolve()).replace("'", r"\'")
                f_list.write(f"file '{safe_path}'\n")
        
        comando = [
            config.FFMPEG_BIN, '-y', '-f', 'concat', '-safe', '0',
            '-i', str(lista_txt_path), 
            '-c', 'copy',
            arquivo_final
        ]
        return _executar_ffmpeg_comando(comando, f"Unificação de áudio para {Path(arquivo_final).name}")
    finally:
        lista_txt_path.unlink(missing_ok=True)

def criar_video_com_audio_ffmpeg(audio_path, video_path, duracao_segundos, resolucao_str):
    """Cria um vídeo com tela preta a partir de um áudio."""
    if duracao_segundos <= 0:
        print("⚠️ Duração inválida para criar vídeo.")
        return False
    comando = [
        config.FFMPEG_BIN, '-y',
        '-f', 'lavfi', '-i', f"color=c=black:s={resolucao_str}:r=1:d={duracao_segundos:.3f}",
        '-i', audio_path,
        '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
        '-c:a', 'aac', '-b:a', '128k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        video_path
    ]
    return _executar_ffmpeg_comando(comando, f"Criação de vídeo a partir de {Path(audio_path).name}", total_duration=duracao_segundos)

def acelerar_midia_ffmpeg(input_path, output_path, velocidade, is_video):
    """Acelera um arquivo de mídia usando FFmpeg."""
    duracao_original = obter_duracao_midia(input_path)
    if duracao_original == 0:
        print("❌ Não foi possível obter a duração do arquivo de entrada para acelerar.")
        return False

    comando = [config.FFMPEG_BIN, '-y', '-i', input_path]
    
    if is_video:
        # Para vídeo, acelera vídeo (PTS) e áudio (atempo)
        # O filtro atempo só aceita valores entre 0.5 e 100.0
        # Para valores fora desse range, é preciso encadear filtros.
        atempo_filters = []
        temp_v = velocidade
        while temp_v > 2.0:
            atempo_filters.append("atempo=2.0")
            temp_v /= 2.0
        if temp_v >= 0.5:
             atempo_filters.append(f"atempo={temp_v}")

        audio_filter = ",".join(atempo_filters)
        video_filter = f"setpts={1/velocidade}*PTS"
        comando.extend(['-filter_complex', f'[0:v]{video_filter}[v];[0:a]{audio_filter}[a]', '-map', '[v]', '-map', '[a]'])
    else:
        # Para áudio, usa apenas o filtro atempo
        # (Lógica de encadeamento repetida para o caso de só áudio)
        atempo_filters = []
        temp_v = velocidade
        while temp_v > 2.0:
            atempo_filters.append("atempo=2.0")
            temp_v /= 2.0
        if temp_v >= 0.5:
             atempo_filters.append(f"atempo={temp_v}")
        
        audio_filter = ",".join(atempo_filters)
        comando.extend(['-filter:a', audio_filter])
        
    comando.append(output_path)
    
    return _executar_ffmpeg_comando(comando, f"Aceleração ({velocidade}x)", total_duration=duracao_original)

def reproduzir_audio(caminho_audio: str):
    """Reproduz um arquivo de áudio usando ffplay."""
    if not shutil.which(config.FFPLAY_BIN):
        print(f"\n⚠️  {config.FFPLAY_BIN} não encontrado. Não é possível reproduzir o áudio de teste.")
        print(f"    O ficheiro foi salvo em: {caminho_audio}")
        return

    comando = [config.FFPLAY_BIN, '-v', 'error', '-nodisp', '-autoexit', caminho_audio]
    try:
        subprocess.run(comando, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        print(f"\n⚠️  Comando '{config.FFPLAY_BIN}' não encontrado. Verifique se o FFmpeg (ffplay) está instalado.")
        print(f"    O ficheiro de teste foi salvo em: {caminho_audio}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao reproduzir áudio com {config.FFPLAY_BIN}:")
        print(e.stderr)


    num_partes = ceil(duracao_total_seg / duracao_max_parte_seg)
    print(f"\n    📄 Arquivo com {duracao_total_seg/3600:.2f}h será dividido em {num_partes} partes.")
    
    arquivos_gerados = []
    for i in range(num_partes):
        if shared_state.CANCELAR_PROCESSAMENTO:
            print("    🚫 Divisão cancelada.")
            break
            
        inicio_seg = i * duracao_max_parte_seg
        duracao_segmento_seg = min(duracao_max_parte_seg, duracao_total_seg - inicio_seg)
        if duracao_segmento_seg <= 1: continue # Evita criar partes minúsculas
             
        output_path_parte = f"{nome_base_saida}_parte{i+1}{extensao_saida}"
        comando = [
            config.FFMPEG_BIN, '-y', 
            '-ss', str(inicio_seg),
            '-i', input_path,
            '-t', str(duracao_segmento_seg),
            '-c', 'copy', # Rápido, sem reencodar
            output_path_parte
        ]
        if _executar_ffmpeg_comando(comando, f"Criação da parte {i+1}/{num_partes}"):
            arquivos_gerados.append(output_path_parte)
        else:
            print(f"    ❌ Falha ao criar parte {i+1}. A divisão será interrompida.")
            break
            
    return arquivos_gerados
