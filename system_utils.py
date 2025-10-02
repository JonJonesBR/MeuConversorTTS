# -*- coding: utf-8 -*-
"""
Módulo para interações com o sistema operacional, como deteção de SO,
verificação e instalação de dependências externas (FFmpeg, Poppler).
"""
import os
import sys
import platform
import subprocess
import shutil
import requests
import zipfile

# Importa as configurações do nosso arquivo config.py
import config

# Variável global para armazenar o SO detectado e evitar re-verificações
SISTEMA_OPERACIONAL_INFO = {}

def detectar_sistema():
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

def _verificar_comando(comando_args, mensagem_sucesso, mensagem_falha, install_commands=None):
    """Função genérica para verificar se um comando existe no sistema."""
    try:
        subprocess.run(comando_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"✅ {mensagem_sucesso}")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(f"⚠️ {mensagem_falha}")
        sistema_atual = detectar_sistema()
        current_os_name = sistema_atual.get('nome', '')
        
        if install_commands and current_os_name:
            cmd_list = install_commands.get('termux' if sistema_atual.get('termux') else current_os_name)
            if cmd_list:
                print(f"   Sugestão de instalação: {' OR '.join(cmd_list)}")
                if sistema_atual.get('termux') and 'poppler' in mensagem_falha.lower():
                    if _instalar_dependencia_termux_auto('poppler'): return True
                elif sistema_atual.get('windows') and 'poppler' in mensagem_falha.lower():
                    if instalar_poppler_windows(): return True
        return False

def _instalar_dependencia_termux_auto(pkg: str) -> bool:
    """Tenta instalar um pacote via 'pkg' no Termux."""
    try:
        print(f"▷ Tentando instalar '{pkg}' no Termux automaticamente...")
        subprocess.run(['pkg', 'update', '-y'], check=True, capture_output=True)
        subprocess.run(['pkg', 'install', '-y', pkg], check=True, capture_output=True)
        print(f"✅ Pacote Termux '{pkg}' instalado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar pacote Termux '{pkg}': {e.stderr.decode() if e.stderr else e}")
    return False

def instalar_poppler_windows():
    """Baixa e tenta instalar o Poppler para Windows no diretório de dados do utilizador."""
    if shutil.which("pdftotext.exe"):
        print("✅ Poppler (pdftotext.exe) já encontrado no PATH.")
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
        archive_root_dir_name = next((item.split('/')[0] for item in zipfile.ZipFile(zip_path, 'r').namelist() if '/' in item), None)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
        os.remove(zip_path)

        bin_path_relative = os.path.join(archive_root_dir_name, 'Library', 'bin') if archive_root_dir_name else 'bin'
        bin_path = os.path.join(install_dir, bin_path_relative)
        
        if not os.path.exists(os.path.join(bin_path, 'pdftotext.exe')):
            print(f"❌ Erro: 'pdftotext.exe' não encontrado em {bin_path} após extração.")
            return False

        print(f"✅ Poppler extraído para: {bin_path}")
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
        print(f"❌ Erro inesperado ao instalar Poppler: {e}")
        return False

def verificar_dependencias_essenciais():
    """Verifica se FFmpeg e Poppler estão instalados no sistema."""
    print("\n🔍 Verificando dependências essenciais...")
    detectar_sistema()
    
    _verificar_comando(
        [config.FFMPEG_BIN, '-version'], "FFmpeg encontrado.",
        "FFmpeg não encontrado. Necessário para manipulação de áudio/vídeo.",
        install_commands={
            'termux': ['pkg install ffmpeg'],
            'linux': ['sudo apt install ffmpeg', 'sudo yum install ffmpeg'],
            'macos': ['brew install ffmpeg'],
            'windows': ['Baixe em https://ffmpeg.org/download.html e adicione ao PATH']
        }
    )
    
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
    print("✅ Verificação de dependências concluída.")
