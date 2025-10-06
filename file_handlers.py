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
import shutil

import chardet
from bs4 import BeautifulSoup
from tqdm import tqdm

try:
    from ebooklib import epub, ITEM_DOCUMENT
    from docx import Document
except ImportError:
    print("Dependências ausentes. Por favor, instale 'ebooklib', 'beautifulsoup4' e 'python-docx'.")
    exit()

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
        return 'utf-8' # Padrão final
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

def converter_pdf_para_txt(caminho_pdf: str, caminho_txt: str) -> bool:
    """Converte um arquivo PDF para TXT usando a ferramenta pdftotext."""
    print(f"📖 Extraindo conteúdo de: {Path(caminho_pdf).name}")
    try:
        comando = ["pdftotext", "-layout", "-enc", "UTF-8", caminho_pdf, caminho_txt]
        subprocess.run(comando, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao converter PDF: {e.stderr.decode(errors='ignore')}")
        return False
    except FileNotFoundError:
        print("❌ Comando 'pdftotext' não encontrado. Verifique se o Poppler está instalado e no PATH.")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado ao converter PDF: {e}")
        return False

def extrair_texto_de_epub(caminho_epub: str) -> str:
    """
    Extrai o conteúdo de texto de um arquivo EPUB, limpando as tags HTML.
    Versão robusta para lidar com EPUBs mal formatados.
    """
    print(f"📖 Extraindo conteúdo de: {Path(caminho_epub).name}")
    try:
        livro = epub.read_epub(caminho_epub)
        partes_texto = []
        
        # Tenta obter a ordem correta dos capítulos (spine)
        itens_ordenados = livro.spine
        if not itens_ordenados:
            print("⚠️ 'Spine' do EPUB não encontrado ou vazio. Tentando ler todos os documentos...")
            itens_ordenados = livro.get_items_of_type(ITEM_DOCUMENT)

        for item_id, _ in tqdm(itens_ordenados, desc="Processando capítulos do EPUB"):
            # Obtém o item do livro pelo ID
            item = livro.get_item_with_id(item_id)
            
            # Validação crucial: verifica se o item realmente existe
            if item is None:
                # print(f"Aviso: Item com id '{item_id}' listado no spine mas não encontrado no manifesto. A ignorar.")
                continue

            try:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                
                # Remove tags irrelevantes para o conteúdo de áudio
                for tag in soup(['nav', 'header', 'footer', 'style', 'script', 'figure', 'aside', 'a', 'img']):
                    tag.decompose()

                texto_item = soup.get_text(separator='\n', strip=True)
                if texto_item:
                    partes_texto.append(texto_item)
            except Exception as e_item:
                print(f"Aviso: Falha ao processar o item '{item_id}' do EPUB: {e_item}")

        return "\n\n".join(partes_texto)
    except Exception as e:
        print(f"❌ Erro ao processar EPUB: {e}")
        return ""

def extrair_texto_de_docx(caminho_docx: str) -> str:
    """Extrai o conteúdo de texto de um arquivo DOCX."""
    print(f"📖 Extraindo conteúdo de: {Path(caminho_docx).name}")
    try:
        doc = Document(caminho_docx)
        return "\n\n".join([para.text for para in doc.paragraphs if para.text])
    except Exception as e:
        print(f"❌ Erro ao processar DOCX: {e}")
        return ""

