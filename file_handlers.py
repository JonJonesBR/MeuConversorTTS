# -*- coding: utf-8 -*-
"""
Manipulação de arquivos: leitura/gravação de texto, PDF→TXT via pdftotext,
extração de texto de EPUB/DOCX e utilidades.
"""
from __future__ import annotations

import os
import re
import unicodedata
import subprocess
from pathlib import Path
from typing import List, Optional

import chardet
from tqdm import tqdm

# Dependências opcionais
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None  # type: ignore

try:
    from ebooklib import epub, ITEM_DOCUMENT
except Exception:
    epub = None  # type: ignore
    ITEM_DOCUMENT = None  # type: ignore

try:
    from docx import Document
except Exception:
    Document = None  # type: ignore

# ----------------------------------------------------------------------
# I/O básico
# ----------------------------------------------------------------------

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

# ----------------------------------------------------------------------
# Conversão de PDF (pdftotext)
# ----------------------------------------------------------------------

def converter_pdf_para_txt(caminho_pdf: str, caminho_txt: str) -> bool:
    """Converte um arquivo PDF para TXT usando a ferramenta pdftotext."""
    print(f"📖 Extraindo conteúdo de: {Path(caminho_pdf).name}")
    try:
        comando = ["pdftotext", "-layout", "-enc", "UTF-8", caminho_pdf, caminho_txt]
        subprocess.run(comando, check=True, capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return True
    except FileNotFoundError:
        print("❌ 'pdftotext' não encontrado. Instale o Poppler e garanta que esteja no PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao converter PDF: {e.stderr.decode(errors='ignore') if e.stderr else e}")
        return False

# ----------------------------------------------------------------------
# EPUB
# ----------------------------------------------------------------------

def extrair_texto_de_epub(caminho_epub: str) -> str:
    """
    Extrai o conteúdo de texto de um EPUB, lidando com EPUBs sem spine.
    Dependências: ebooklib + beautifulsoup4.
    """
    print(f"📖 Extraindo conteúdo de: {Path(caminho_epub).name}")
    if epub is None or ITEM_DOCUMENT is None or BeautifulSoup is None:
        print("❌ Dependências para EPUB ausentes. Instale: pip install ebooklib beautifulsoup4")
        return ""

    try:
        livro = epub.read_epub(caminho_epub)
        partes_texto: List[str] = []

        spine = getattr(livro, "spine", None)
        if spine:
            # spine típico: lista de tuplas (idref, linear)
            iter_spine = [(idref, linear) for (idref, linear) in spine if isinstance(idref, str)]
            for item_id, _ in tqdm(iter_spine, desc="Processando capítulos do EPUB"):
                item = livro.get_item_with_id(item_id)
                if item is None:
                    continue
                try:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    for tag in soup(['nav', 'header', 'footer', 'style', 'script', 'figure', 'aside', 'a', 'img']):
                        tag.decompose()
                    texto_item = soup.get_text(separator='\n', strip=True)
                    if texto_item:
                        partes_texto.append(texto_item)
                except Exception as e_item:
                    print(f"Aviso: falha ao processar item '{item_id}': {e_item}")
        else:
            # Fallback: varre todos os documentos HTML do EPUB
            print("⚠️ 'Spine' ausente. Lendo todos os documentos (ordem pode variar).")
            for item in tqdm(livro.get_items_of_type(ITEM_DOCUMENT), desc="Processando capítulos do EPUB"):
                try:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    for tag in soup(['nav', 'header', 'footer', 'style', 'script', 'figure', 'aside', 'a', 'img']):
                        tag.decompose()
                    texto_item = soup.get_text(separator='\n', strip=True)
                    if texto_item:
                        partes_texto.append(texto_item)
                except Exception as e_item:
                    print(f"Aviso: falha ao processar um item do EPUB: {e_item}")

        return "\n\n".join(partes_texto)
    except Exception as e:
        print(f"❌ Erro ao processar EPUB: {e}")
        return ""

# ----------------------------------------------------------------------
# DOCX
# ----------------------------------------------------------------------

def extrair_texto_de_docx(caminho_docx: str) -> str:
    """Extrai o conteúdo de texto de um DOCX."""
    print(f"📖 Extraindo conteúdo de: {Path(caminho_docx).name}")
    if Document is None:
        print("❌ Dependência ausente: python-docx. Instale: pip install python-docx")
        return ""
    try:
        doc = Document(caminho_docx)
        return "\n\n".join([para.text for para in doc.paragraphs if para.text])
    except Exception as e:
        print(f"❌ Erro ao processar DOCX: {e}")
        return ""
