# -*- coding: utf-8 -*-
"""
Módulo para manipulação de arquivos: ler, salvar, converter PDF/EPUB/DOCX
e outras operações de I/O.
"""
import os
import re
import unicodedata
import subprocess
from pathlib import Path
import shutil

import chardet
from bs4 import BeautifulSoup
from tqdm import tqdm

# Importações para formatos de arquivo específicos
try:
    from ebooklib import epub, ITEM_DOCUMENT
except ImportError:
    epub = None
try:
    import docx
except ImportError:
    docx = None


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
        return encoding if encoding and resultado['confidence'] > 0.7 else 'utf-8'
    except Exception:
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

    if not shutil.which(pdftotext_cmd):
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
        print(f"✅ PDF convertido para TXT com sucesso.")
        return True
    except Exception as e:
        print(f"❌ Erro inesperado ao converter PDF: {e}")
        return False

def extrair_texto_de_epub(caminho_epub: str) -> str:
    """Extrai e limpa todo o conteúdo textual de um arquivo EPUB usando ebooklib."""
    if epub is None:
        print("❌ A biblioteca 'ebooklib' é necessária para ler arquivos EPUB. Instale com: pip install EbookLib")
        return ""
        
    print(f"📖 Extraindo conteúdo de: {Path(caminho_epub).name}")
    try:
        livro = epub.read_epub(caminho_epub)
        partes_texto = []
        
        itens_documento = []
        if livro.spine:
            # Itera pelo 'spine' para manter a ordem, mas verifica se cada item existe
            for href, _ in livro.spine:
                item = livro.get_item_with_href(href)
                if item:  # Apenas adiciona à lista se o item for encontrado
                    itens_documento.append(item)
        
        # Se o spine estiver vazio ou for inválido, usa um método de fallback
        if not itens_documento:
             print("⚠️ 'Spine' do EPUB inválido ou vazio. Recorrendo à leitura de todos os documentos.")
             itens_documento = list(livro.get_items_of_type(ITEM_DOCUMENT))

        for item in tqdm(itens_documento, desc="Processando capítulos do EPUB", unit="cap", ncols=80):
            # A verificação de 'item' aqui garante que não teremos o erro
            if not item:
                continue

            soup = BeautifulSoup(item.get_content(), 'html.parser')
            # Remove tags irrelevantes
            for tag in soup(['nav', 'header', 'footer', 'style', 'script', 'figure', 'aside', 'a']):
                tag.decompose()
            
            texto_item = soup.get_text(separator='\n', strip=True)
            if texto_item:
                partes_texto.append(texto_item)
                
        return "\n\n".join(partes_texto)

    except Exception as e:
        print(f"❌ Erro ao processar EPUB: {e}")
        return ""

def extrair_texto_de_docx(caminho_docx: str) -> str:
    """Extrai texto de um arquivo .docx."""
    if docx is None:
        print("❌ A biblioteca 'python-docx' é necessária para ler arquivos DOCX. Instale com: pip install python-docx")
        return ""

    print(f"📖 Extraindo conteúdo de: {Path(caminho_docx).name}")
    try:
        documento = docx.Document(caminho_docx)
        return "\n\n".join(para.text for para in documento.paragraphs if para.text)
    except Exception as e:
        print(f"❌ Erro ao processar DOCX: {e}")
        return ""

