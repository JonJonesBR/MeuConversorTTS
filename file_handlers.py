# -*- coding: utf-8 -*-
"""
Módulo para manipulação de arquivos: ler, salvar, converter PDF/EPUB
e outras operações de I/O.
"""
import os
import re
import unicodedata
import zipfile
import subprocess
from pathlib import Path
import shutil  # <- LINHA ADICIONADA AQUI

import chardet
import html2text
from bs4 import BeautifulSoup
from tqdm import tqdm

# Importa de nossos outros módulos
import config
import system_utils

def detectar_encoding_arquivo(caminho_arquivo: str) -> str:
    """Detecta o encoding de um arquivo de texto com alta probabilidade."""
    try:
        with open(caminho_arquivo, 'rb') as f:
            raw_data = f.read(50000)
        resultado = chardet.detect(raw_data)
        encoding = resultado['encoding']
        if encoding and resultado['confidence'] > 0.7:
            return encoding
        # Fallback para tentativas manuais
        for enc_try in config.ENCODINGS_TENTATIVAS:
            try:
                with open(caminho_arquivo, 'r', encoding=enc_try) as f_test:
                    f_test.read(1024)
                return enc_try
            except (UnicodeDecodeError, TypeError):
                continue
        return 'utf-8' # Padrão final
    except Exception as e:
        print(f"⚠️ Erro ao detectar encoding: {e}. Usando 'utf-8' como padrão.")
        return 'utf-8'

def ler_arquivo_texto(caminho_arquivo: str) -> str:
    """Lê um arquivo de texto usando o encoding detectado."""
    encoding = detectar_encoding_arquivo(caminho_arquivo)
    try:
        with open(caminho_arquivo, 'r', encoding=encoding, errors='replace') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Erro ao ler arquivo '{caminho_arquivo}': {e}")
        return ""

def salvar_arquivo_texto(caminho_arquivo: str, conteudo: str):
    """Salva uma string em um arquivo de texto com encoding UTF-8."""
    try:
        os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"Arquivo salvo: {caminho_arquivo}")
    except Exception as e:
        print(f"Erro ao salvar arquivo '{caminho_arquivo}': {e}")

def limpar_nome_arquivo(nome: str) -> str:
    """Limpa e sanitiza um nome de arquivo, removendo caracteres especiais."""
    nome_sem_ext, ext = os.path.splitext(nome)
    nome_normalizado = unicodedata.normalize('NFKD', nome_sem_ext).encode('ascii', 'ignore').decode('ascii')
    nome_limpo = re.sub(r'[^\w\s-]', '', nome_normalizado).strip()
    nome_limpo = re.sub(r'[-\s]+', '_', nome_limpo)
    return nome_limpo + ext if ext else nome_limpo

def converter_pdf_para_txt(caminho_pdf: str, caminho_txt: str) -> bool:
    """Converte um arquivo PDF para TXT usando a ferramenta pdftotext."""
    sistema = system_utils.detectar_sistema()
    pdftotext_cmd = "pdftotext.exe" if sistema['windows'] else "pdftotext"

    # Tenta instalar a dependência se não for encontrada
    if not Path(pdftotext_cmd).is_file() and not shutil.which(pdftotext_cmd):
        if sistema['windows']:
            if not system_utils.instalar_poppler_windows(): return False
        elif sistema['termux']:
            if not system_utils._instalar_dependencia_termux_auto("poppler"): return False

    if not os.path.isfile(caminho_pdf):
        print(f"❌ Arquivo PDF não encontrado: {caminho_pdf}")
        return False

    try:
        comando = [pdftotext_cmd, "-layout", "-enc", "UTF-8", caminho_pdf, caminho_txt]
        subprocess.run(comando, check=True, capture_output=True)
        print(f"PDF convertido para TXT: {caminho_txt}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao converter PDF: {e.stderr.decode(errors='ignore')}")
        return False
    except FileNotFoundError:
        print(f"Comando '{pdftotext_cmd}' nao encontrado. A instalacao pode ter falhado.")
        return False
    except Exception as e:
        print(f"Erro inesperado ao converter PDF: {e}")
        return False

def extrair_texto_de_epub(caminho_epub: str) -> str:
    """Extrai e limpa todo o conteúdo textual de um arquivo EPUB."""
    print(f"\n📖 Extraindo conteúdo de: {caminho_epub}")
    try:
        with zipfile.ZipFile(caminho_epub, 'r') as epub_zip:
            # Lógica para encontrar a ordem dos arquivos (spine)
            container = epub_zip.read('META-INF/container.xml').decode('utf-8')
            match = re.search(r'full-path="([^\"]+)"', container)
            if match is None:
                print("⚠️ Não foi possível encontrar o caminho do arquivo OPF no EPUB.")
                return ""
            opf_path = match.group(1)
            opf_content = epub_zip.read(opf_path).decode('utf-8')
            opf_dir = os.path.dirname(opf_path)
            
            spine_ids = [m.group(1) for m in re.finditer(r'<itemref\s+idref="([^\"]+)"', opf_content)]
            manifest_files = {m.group(1): m.group(2) for m in re.finditer(r'<item\s+id="([^\"]+)"\s+href="([^\"]+)"\s+media-type="application/xhtml\+xml"', opf_content)}
            
            arquivos_ordenados = []
            for item_id in spine_ids:
                if item_id in manifest_files:
                    path_relativo = manifest_files[item_id]
                    path_final = os.path.normpath(os.path.join(opf_dir, path_relativo))
                    arquivos_ordenados.append(path_final)
            
            # Se a leitura da spine falhar, tenta ler todos os arquivos HTML/XHTML
            if not arquivos_ordenados:
                print("⚠️ Falha ao ler 'spine' do EPUB. Tentando todos os arquivos de conteúdo...")
                arquivos_ordenados = sorted([f.filename for f in epub_zip.infolist() if f.filename.lower().endswith(('.html', '.xhtml'))])

            # Processamento do HTML
            texto_completo = ""
            h_parser = html2text.HTML2Text()
            h_parser.ignore_links = True
            h_parser.ignore_images = True
            h_parser.body_width = 0

            for nome_arquivo in tqdm(arquivos_ordenados, desc="Processando capítulos"):
                html_bytes = epub_zip.read(nome_arquivo)
                encoding = chardet.detect(html_bytes)['encoding'] or 'utf-8'
                html_texto = html_bytes.decode(encoding, errors='replace')
                
                soup = BeautifulSoup(html_texto, 'html.parser')
                # Remove tags irrelevantes para o conteúdo de áudio
                for tag in soup(['nav', 'header', 'footer', 'style', 'script', 'figure', 'aside']):
                    tag.decompose()
                
                content_tag = soup.find('body') or soup
                texto_completo += h_parser.handle(str(content_tag)) + "\n\n"
        
        return texto_completo.strip()

    except Exception as e:
        print(f"❌ Erro geral ao processar EPUB: {e}")
        return ""