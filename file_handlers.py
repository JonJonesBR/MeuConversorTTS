# -*- coding: utf-8 -*-
"""
Manipulação de arquivos: Leitura/gravação de texto, PDF via pdftotext (externo),
e extração de texto de EPUB via zipfile/html2text.
"""
from __future__ import annotations
import os
import re
import unicodedata
import subprocess
import zipfile
from pathlib import Path
from typing import List

import chardet
from tqdm import tqdm
import html2text
from bs4 import BeautifulSoup

# ================== I/O BÁSICO ==================

def ler_arquivo_texto(caminho_arquivo: str) -> str:
    """Lê um arquivo de texto tentando detectar o encoding."""
    try:
        with open(caminho_arquivo, 'rb') as f:
            dados = f.read()
        enc = chardet.detect(dados).get('encoding') or 'utf-8'
        return dados.decode(enc, errors='replace')
    except Exception as e:
        print(f"❌ Erro ao ler arquivo '{caminho_arquivo}': {e}")
        return ""

def salvar_arquivo_texto(caminho_arquivo: str, conteudo: str):
    """Salva uma string em um arquivo de texto com encoding UTF-8."""
    try:
        Path(caminho_arquivo).parent.mkdir(parents=True, exist_ok=True)
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
    except Exception as e:
        print(f"Erro ao salvar arquivo '{caminho_arquivo}': {e}")

def limpar_nome_arquivo(nome: str) -> str:
    """Limpa e sanitiza um nome de arquivo, removendo caracteres especiais."""
    nome_sem_ext, ext = os.path.splitext(nome)
    nome_normalizado = unicodedata.normalize('NFKD', nome_sem_ext).encode('ascii', 'ignore').decode('ascii')
    nome_limpo = re.sub(r'[^\w\s-]', '', nome_normalizado).strip()
    nome_limpo = re.sub(r'[-\s]+', '_', nome_limpo)
    return nome_limpo + ext if ext else nome_limpo

# ================== CONVERSÃO DE PDF (VIA pdftotext) ==================

def converter_pdf_para_txt(caminho_pdf: str, caminho_txt: str) -> bool:
    """Converte um arquivo PDF para TXT usando a ferramenta externa pdftotext."""
    print(f"📖 Extraindo conteúdo de: {Path(caminho_pdf).name}")
    try:
        # No Windows, o subprocesso não herda o PATH modificado dinamicamente,
        # então é melhor não especificar flags que possam causar problemas.
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        comando = ["pdftotext", "-layout", "-enc", "UTF-8", caminho_pdf, caminho_txt]
        subprocess.run(comando, check=True, capture_output=True, creationflags=flags)
        return True
    except FileNotFoundError:
        print("❌ 'pdftotext' não encontrado. Instale o Poppler e garanta que esteja no PATH.")
        return False
    except subprocess.CalledProcessError as e:
        stderr_decoded = e.stderr.decode(errors='ignore') if e.stderr else str(e)
        print(f"❌ Erro ao converter PDF: {stderr_decoded}")
        return False

# ================== EPUB (VIA zipfile + html2text) ==================

def extrair_texto_de_epub(caminho_epub: str) -> str:
    """Extrai texto de um EPUB usando zipfile e html2text, inspirado no script antigo."""
    print(f"📖 Extraindo conteúdo de: {Path(caminho_epub).name}")
    texto_completo = ""
    try:
        with zipfile.ZipFile(caminho_epub, 'r') as epub_zip:
            # Encontrar a ordem dos arquivos a partir do 'spine' no arquivo .opf
            container_xml = epub_zip.read('META-INF/container.xml').decode('utf-8')
            opf_path_match = re.search(r'full-path="([^"]+)"', container_xml)
            if not opf_path_match:
                raise Exception("Caminho do arquivo OPF não encontrado no container.xml.")

            opf_path = opf_path_match.group(1)
            opf_content = epub_zip.read(opf_path).decode('utf-8')
            opf_dir = os.path.dirname(opf_path)

            spine_items = [m.group(1) for m in re.finditer(r'<itemref\s+idref="([^"]+)"', opf_content)]
            manifest_hrefs = {m.group(1): m.group(2) for m in re.finditer(r'<item\s+id="([^"]+)"\s+href="([^"]+)"', opf_content)}
            
            arquivos_xhtml_ordenados = []
            for idref in spine_items:
                if idref in manifest_hrefs:
                    # Constrói o caminho relativo ao diretório do OPF
                    xhtml_path_rel = manifest_hrefs[idref]
                    xhtml_path_in_zip = os.path.normpath(os.path.join(opf_dir, xhtml_path_rel)).replace('\\', '/')
                    arquivos_xhtml_ordenados.append(xhtml_path_in_zip)

            if not arquivos_xhtml_ordenados:
                 # Fallback se a leitura do spine falhar
                arquivos_xhtml_ordenados = sorted([
                    f.filename for f in epub_zip.infolist() 
                    if f.filename.lower().endswith(('.html', '.xhtml'))
                ])
            
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            
            for nome_arquivo in tqdm(arquivos_xhtml_ordenados, desc="Processando capítulos do EPUB"):
                html_bytes = epub_zip.read(nome_arquivo)
                html_texto = html_bytes.decode(chardet.detect(html_bytes)['encoding'] or 'utf-8', errors='replace')
                
                # Usa BeautifulSoup para remover tags indesejadas antes de converter
                soup = BeautifulSoup(html_texto, 'html.parser')
                for tag in soup(['nav', 'header', 'footer', 'style', 'script', 'figure', 'aside']):
                    tag.decompose()

                texto_limpo = h.handle(str(soup))
                texto_completo += texto_limpo + "\n\n"
        
        return texto_completo.strip()
    except Exception as e:
        print(f"❌ Erro ao processar EPUB: {e}")
        return ""
