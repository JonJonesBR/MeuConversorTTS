# -*- coding: utf-8 -*-
"""
Módulo para interações com o sistema operacional, como deteção de SO,
verificação e instalação de dependências externas (FFmpeg, Poppler).
"""
from __future__ import annotations

import os
import sys
import platform
import subprocess
import shutil
import requests
import zipfile
from typing import Dict, Any, List, Optional

# Variável global para armazenar o SO detectado e evitar re-verificações
SISTEMA_OPERACIONAL_INFO: Dict[str, Any] = {}

def detectar_sistema() -> Dict[str, Any]:
    """Detecta o sistema operacional e ambiente (ex: Termux)."""
    global SISTEMA_OPERACIONAL_INFO
    if SISTEMA_OPERACIONAL_INFO:
        return SISTEMA_OPERACIONAL_INFO
        
    sistema = {
        'nome': platform.system().lower(), 'termux': False, 'android': False,
        'windows': False, 'linux': False, 'macos': False,
    }
    if sistema['nome'] == 'windows':
        sistema['windows'] = True
    elif sistema['nome'] == 'darwin':
        sistema['macos'] = True
    elif sistema['nome'] == 'linux':
        sistema['linux'] = True
        if 'ANDROID_ROOT' in os.environ or os.path.exists('/system/bin/app_process'):
            sistema['android'] = True
            if 'TERMUX_VERSION' in os.environ or os.path.exists('/data/data/com.termux'):
                sistema['termux'] = True
                termux_bin = '/data/data/com.termux/files/usr/bin'
                if termux_bin not in os.environ.get('PATH', ''):
                    os.environ['PATH'] = f"{os.environ.get('PATH', '')}:{termux_bin}"
    
    SISTEMA_OPERACIONAL_INFO = sistema
    return sistema

def _verificar_comando(comando_args: List[str], mensagem_sucesso: str, mensagem_falha: str, install_commands: Optional[Dict[str, List[str]]] = None) -> bool:
    """Função genérica para verificar se um comando existe no sistema."""
    try:
        subprocess.run(comando_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"{mensagem_sucesso}")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(f"{mensagem_falha}")
        sistema_atual = detectar_sistema()
        current_os_name = sistema_atual.get('nome', '')
        
        if install_commands and current_os_name:
            cmd_list = install_commands.get('termux' if sistema_atual.get('termux') else current_os_name)
            if cmd_list:
                print(f"   Sugestão de instalação: {' OR '.join(cmd_list)}")
                if sistema_atual.get('termux') and 'poppler' in mensagem_falha.lower():
                    if _instalar_dependencia_termux_auto('poppler'):
                        return True
                elif sistema_atual.get('windows') and 'poppler' in mensagem_falha.lower():
                    if instalar_poppler_windows():
                        return True
        return False

def _instalar_dependencia_termux_auto(pkg: str) -> bool:
    """Tenta instalar um pacote via 'pkg' no Termux."""
    try:
        print(f"▷ Tentando instalar '{pkg}' no Termux automaticamente...")
        subprocess.run(['pkg', 'update', '-y'], check=True, capture_output=True)
        subprocess.run(['pkg', 'install', '-y', pkg], check=True, capture_output=True)
        print(f"Pacote Termux '{pkg}' instalado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar pacote Termux '{pkg}': {e.stderr.decode() if e.stderr else e}")
    return False

def instalar_poppler_windows() -> bool:
    """Baixa e tenta instalar o Poppler para Windows no diretório de dados do utilizador."""
    if shutil.which("pdftotext.exe"):
        print("Poppler (pdftotext.exe) já encontrado no PATH.")
        return True
    
    print("📦 Poppler (pdftotext.exe) não encontrado. Tentando instalar automaticamente...")
    try:
        poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip"
        install_dir_base = os.environ.get('LOCALAPPDATA', os.path.join(os.path.expanduser("~"), "AppData", "Local"))
        install_dir = os.path.join(install_dir_base, 'Poppler')
        os.makedirs(install_dir, exist_ok=True)
        
        print("📥 Baixando Poppler...")
        response = requests.get(poppler_url, stream=True)
        response.raise_for_status()
        zip_path = os.path.join(install_dir, "poppler.zip")
        with open(zip_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

        print("📦 Extraindo arquivos...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
        os.remove(zip_path)

        # Encontrar a subpasta 'bin'
        bin_path = None
        for root, dirs, files in os.walk(install_dir):
            if 'pdftotext.exe' in files:
                bin_path = root
                break
        
        if not bin_path:
            print(f"Erro: 'pdftotext.exe' não encontrado após extração.")
            return False

        print(f"Poppler extraído para: {bin_path}")
        # Tenta adicionar ao PATH da sessão atual
        os.environ['PATH'] = f"{bin_path};{os.environ['PATH']}"
        if shutil.which("pdftotext.exe"):
            print("✅ Poppler agora está acessível nesta sessão.")
            print("   OBS: Pode ser necessário adicionar o diretório acima ao PATH do Windows manualmente para uso futuro.")
            return True
        else:
            print(f"⚠️ Poppler instalado, mas não está no PATH. Adicione manualmente: {bin_path}")
            return False
            
    except Exception as e:
        print(f"Erro inesperado ao instalar Poppler: {e}")
        return False

def instalar_ffmpeg_windows() -> bool:
    """Baixa e tenta instalar o FFmpeg para Windows no diretório de dados do utilizador."""
    import requests
    import zipfile
    
    # Verificar se o FFmpeg já está no PATH
    if shutil.which("ffmpeg.exe") or shutil.which("ffmpeg"):
        print("FFmpeg ja encontrado no PATH.")
        return True
    
    print("FFmpeg nao encontrado. Tentando instalar automaticamente...")
    try:
        # Primeiro tenta com o URL do ZIP
        ffmpeg_urls = [
            "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
            "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-7.1-essentials_build.zip",
            "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.zip",
            "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.zip",
            # Se os links acima não funcionarem, tentar um link alternativo
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n5.1-latest-win64-gpl-5.1.zip"
        ]
        
        ffmpeg_url = None
        for url in ffmpeg_urls:
            try:
                response_check = requests.head(url)
                if response_check.status_code < 400:
                    ffmpeg_url = url
                    print(f"Usando URL: {ffmpeg_url}")
                    break
            except:
                continue
        
        if not ffmpeg_url:
            print("Nenhum URL de FFmpeg valido encontrado.")
            return False
        
        # Diretório de instalação
        install_dir_base = os.environ.get('LOCALAPPDATA', os.path.join(os.path.expanduser("~"), "AppData", "Local"))
        install_dir = os.path.join(install_dir_base, 'FFmpeg')
        os.makedirs(install_dir, exist_ok=True)
        
        print("Baixando FFmpeg...")
        response = requests.get(ffmpeg_url, stream=True)
        response.raise_for_status()
        
        # Criar arquivo temporário para o download
        zip_path = os.path.join(install_dir, "ffmpeg.zip")
        with open(zip_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

        print("Extraindo arquivos...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Lista todos os arquivos no ZIP para encontrar a estrutura correta
            all_files = zip_ref.namelist()
            
            # Encontrar a pasta principal que contém a estrutura bin/
            bin_files = [f for f in all_files if 'bin/ffmpeg.exe' in f or 'bin/ffprobe.exe' in f or 'bin/ffplay.exe' in f]
            
            if bin_files:
                # Extrair a pasta que contém os executáveis
                root_folder = bin_files[0].split('/')[0]  # Obter a pasta raiz
                extract_to = os.path.join(install_dir, "extracted")
                os.makedirs(extract_to, exist_ok=True)
                
                # Extrair todo o conteúdo
                zip_ref.extractall(extract_to)
                
                # Encontrar a pasta bin e copiar os executáveis para o diretório de instalação
                extracted_root = os.path.join(extract_to, root_folder)
                bin_path = os.path.join(extracted_root, "bin")
                
                if os.path.exists(bin_path):
                    # Copiar os arquivos da pasta bin para o diretório de instalação
                    for file in os.listdir(bin_path):
                        if file.lower().endswith(('.exe', '.dll')):
                            src_path = os.path.join(bin_path, file)
                            dst_path = os.path.join(install_dir, file)
                            shutil.copy2(src_path, dst_path)
                
                # Remover a pasta temporária de extração
                shutil.rmtree(extract_to)
            else:
                # Se não encontrar a estrutura esperada, extrai tudo e tenta encontrar os arquivos
                zip_ref.extractall(install_dir)
                # Procura recursivamente os executáveis
                for root, dirs, files in os.walk(install_dir):
                    for file in files:
                        if file.lower() in ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]:
                            # Copia o arquivo para o diretório de instalação se ainda não estiver lá
                            src_path = os.path.join(root, file)
                            dst_path = os.path.join(install_dir, file)
                            if not os.path.exists(dst_path):
                                shutil.copy2(src_path, dst_path)
        
        # Remover o arquivo ZIP após extração
        os.remove(zip_path)
        
        # Adicionar ao PATH da sessão atual
        os.environ['PATH'] = f"{install_dir};{os.environ['PATH']}"
        
        # Verificar se os executáveis agora estão acessíveis
        ffmpeg_found = shutil.which("ffmpeg.exe") or shutil.which("ffmpeg")
        ffprobe_found = shutil.which("ffprobe.exe") or shutil.which("ffprobe")
        
        if ffmpeg_found and ffprobe_found:
            print("FFmpeg agora esta acessivel nesta sessao.")
            print("   OBS: Pode ser necessario adicionar o diretorio ao PATH do Windows manualmente para uso futuro.")
            return True
        else:
            print(f"FFmpeg instalado, mas nao esta no PATH. Adicione manualmente: {install_dir}")
            return False
            
    except Exception as e:
        print(f"Erro inesperado ao instalar FFmpeg: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_dependencias_essenciais() -> None:
    """Verifica se Poppler está instalado no sistema (FFmpeg verificado separadamente)."""
    print("\n🔍 Verificando dependências essenciais...")
    detectar_sistema()
    
    pdftotext_cmd = "pdftotext.exe" if detectar_sistema().get('windows') else "pdftotext"
    _verificar_comando(
        [pdftotext_cmd, '-v'], "Poppler (pdftotext) encontrado.",
        "Poppler (pdftotext) não encontrado. Necessário para converter PDF.",
        install_commands={
            'termux': ['pkg install poppler'],
            'linux': ['sudo apt install poppler-utils'],
            'macos': ['brew install poppler'],
            'windows': ['Tentativa de instalação automática será feita se necessário.']
        }
    )
    print("Verificação de dependências concluída.")
