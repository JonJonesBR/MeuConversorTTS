# -*- coding: utf-8 -*-
"""
Módulo para operações avançadas de áudio e vídeo usando FFmpeg.
"""
import subprocess
import os
from pathlib import Path
import shutil
import json

# Importa as configurações do nosso arquivo config.py
import config

def unificar_arquivos_audio_ffmpeg(lista_arquivos_entrada: list[str], caminho_saida: str) -> bool:
    """
    Une múltiplos arquivos de áudio em um único arquivo usando FFmpeg.
    """
    if len(lista_arquivos_entrada) == 0:
        print("❌ Nenhum arquivo de entrada fornecido para unificação.")
        return False
    
    if len(lista_arquivos_entrada) == 1:
        # Se só tem um arquivo, apenas copia com o novo nome
        import shutil
        shutil.copy2(lista_arquivos_entrada[0], caminho_saida)
        return True

    # Cria um arquivo temporário de lista para o FFmpeg
    arquivo_lista = Path(caminho_saida).with_name("temp_lista_arquivos.txt")
    try:
        with open(arquivo_lista, 'w', encoding='utf-8') as f:
            for arquivo in lista_arquivos_entrada:
                # Escapa os caminhos com aspas e barras duplas
                f.write(f"file '{Path(arquivo).as_posix()}'\n")
        
        # Executa o FFmpeg para concatenar
        cmd = [
            config.FFMPEG_BIN, 
            '-f', 'concat', 
            '-safe', '0', 
            '-i', str(arquivo_lista),
            '-c', 'copy',  # Cópia direta, sem re-encode
            '-y',  # Substitui o arquivo de saída se já existir
            caminho_saida
        ]
        
        # Executa o comando e verifica o resultado
        result = subprocess.run(cmd, capture_output=True, text=True)
        success = result.returncode == 0
        
        if not success:
            print(f"❌ Erro ao unificar arquivos com FFmpeg: {result.stderr}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro inesperado ao unificar arquivos: {e}")
        return False
    finally:
        # Limpa o arquivo temporário
        if arquivo_lista.exists():
            arquivo_lista.unlink()

<<<<<<< HEAD
def aplicar_efeito_audibilizar(caminho_entrada: str, caminho_saida: str, velocidade: float) -> bool:
    """
    Aplica um efeito de velocidade a um arquivo de áudio/vídeo.
    """
    try:
        cmd = [
            config.FFMPEG_BIN,
            '-i', caminho_entrada,
            '-filter:a', f'atempo={velocidade}',  # Ajusta velocidade do áudio
            '-y',
            caminho_saida
=======
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
>>>>>>> bb19449059105991693c172edf8db34073a419fe
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        success = result.returncode == 0
        
        if not success:
            print(f"❌ Erro ao aplicar efeito de velocidade: {result.stderr}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro inesperado ao aplicar efeito de velocidade: {e}")
        return False

def criar_video_a_partir_de_audio(caminho_audio: str, caminho_saida: str, resolucao: str) -> bool:
    """
    Cria um vídeo (MP4) com tela preta e o áudio fornecido.
    """
    try:
        # Extrai o diretório e nome base do arquivo
        dir_saida = Path(caminho_saida).parent
        nome_arquivo = Path(caminho_saida).name
        
        # Cria um vídeo preto com o áudio do arquivo
        cmd = [
            config.FFMPEG_BIN,
            '-f', 'lavfi',  # Fonte de vídeo virtual (cor)
            '-i', f'color=c=black:s={resolucao}:d=10',  # Cria um vídeo preto com duração de 10 segundos
            '-i', caminho_audio,  # Arquivo de áudio
            '-shortest',  # Usa o comprimento do arquivo mais curto (áudio)
            '-c:v', 'libx264',  # Codec de vídeo
            '-c:a', 'aac',      # Codec de áudio
            '-y',  # Substitui o arquivo de saída
            caminho_saida
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        success = result.returncode == 0
        
        if not success:
            print(f"❌ Erro ao criar vídeo a partir de áudio: {result.stderr}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro inesperado ao criar vídeo: {e}")
        return False

def aplicar_normalizacao_volume(caminho_entrada: str, caminho_saida: str) -> bool:
    """
    Normaliza o volume de um arquivo de áudio.
    """
    try:
        cmd = [
            config.FFMPEG_BIN,
            '-i', caminho_entrada,
            '-af', 'loudnorm',  # Filtro de normalização de volume
            '-y',
            caminho_saida
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        success = result.returncode == 0
        
        if not success:
            print(f"❌ Erro ao normalizar volume: {result.stderr}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro inesperado ao normalizar volume: {e}")
        return False

def dividir_arquivo_audio_video(caminho_entrada: str, pasta_saida: str, duracao_partes_segundos: int) -> bool:
    """
    Divide um arquivo de áudio/vídeo em partes menores com base em duração especificada.
    """
    try:
        nome_base = Path(caminho_entrada).stem
        extensao = Path(caminho_entrada).suffix
        
        cmd = [
            config.FFMPEG_BIN,
            '-i', caminho_entrada,
            '-c', 'copy',  # Cópia direta sem re-encode
            '-segment_time', str(duracao_partes_segundos),
            '-f', 'segment',  # Formato de segmento
            '-y',
            os.path.join(pasta_saida, f"{nome_base}_parte_%03d{extensao}")
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        success = result.returncode == 0
        
        if not success:
            print(f"❌ Erro ao dividir arquivo: {result.stderr}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erro inesperado ao dividir arquivo: {e}")
        return False

def obter_duracao_arquivo(caminho_arquivo: str) -> float:
    """
    Obtém a duração de um arquivo de mídia em segundos.
    """
    try:
        cmd = [
            config.FFPROBE_BIN,
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            caminho_arquivo
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
        else:
            print(f"⚠️ Não foi possível obter duração do arquivo: {caminho_arquivo}")
            return 0.0
            
    except Exception as e:
        print(f"⚠️ Erro ao obter duração do arquivo: {e}")
        return 0.0