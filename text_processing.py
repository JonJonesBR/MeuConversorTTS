# -*- coding: utf-8 -*-
"""
Script de limpeza e formatação de texto para TTS (REV 4.2, modificado)

- Substituído PyMuPDF (fitz) por pdfplumber para extração de texto de PDFs.
- pdfplumber é mais leve, compatível com Termux e não requer compilação nativa.
"""

from __future__ import annotations

import os
import argparse
import re
import logging
import unicodedata
from typing import Optional, Any, Iterable, List

# ----------------------------------------------------------------------
# Imports opcionais
# ----------------------------------------------------------------------
import pdfplumber
docx: Optional[Any] = None
epub: Optional[Any] = None
ITEM_DOCUMENT: Optional[Any] = None
BeautifulSoup: Optional[Any] = None
num2words: Optional[Any] = None

try:
    import docx as _docx  # python-docx
    docx = _docx
except Exception:
    pass

try:
    from ebooklib import epub as _epub
    from ebooklib import ITEM_DOCUMENT as _ITEM_DOCUMENT
    epub = _epub
    ITEM_DOCUMENT = _ITEM_DOCUMENT
except Exception:
    pass

try:
    from bs4 import BeautifulSoup as _BeautifulSoup
    BeautifulSoup = _BeautifulSoup
except Exception:
    pass

try:
    from num2words import num2words as _num2words
    num2words = _num2words
except Exception:
    pass

# Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# ================== EXTRAÇÃO ==================

def extract_from_pdf(filepath: str) -> str:
    """
    Extrai texto de um arquivo PDF usando pdfplumber.
    Retorna uma string com o texto concatenado de todas as páginas.
    """
    try:
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logging.error(f"Erro ao extrair texto do PDF '{filepath}': {e}")
        return ""

# As demais funções do script permanecem inalteradas.

def extract_from_docx(filepath: str) -> str:
    if docx is None:
        logging.error("Dependência ausente: python-docx. Instale com: pip install python-docx")
        return ""
    try:
        d = docx.Document(filepath)  # type: ignore
        return "\n".join(p.text for p in d.paragraphs)
    except Exception as e:
        logging.error(f"Erro ao processar o DOCX '{filepath}': {e}")
        return ""

# --------- Utilitários de limpeza de EPUB (antes do get_text) ---------

_RE_CLASS_PAGENUM = re.compile(r'\b(page\s?num|pageno|pagebreak|page-number)\b', re.I)
_RE_ID_PAGE = re.compile(r'^(page|pg|p)_?\d+$', re.I)

def _remover_marcadores_pagina_epub(soup: Any) -> None:
    """
    Remove do DOM elementos que representam quebras/numeração de página:
    - Qualquer tag com atributo 'epub:type' contendo 'pagebreak'
    - Qualquer tag com 'role' == 'doc-pagebreak'
    - Classes/id típicos: 'pagenum', 'pageno', 'pagebreak', 'page-number'
    - Âncoras/spans/divs que carregam apenas números ou 'Página X' como texto curto
    - Para <a> genéricos, faz 'unwrap' (preserva texto) em vez de 'decompose'
    """
    if BeautifulSoup is None:
        return

    # 1) Remover por atributos semânticos (EPUB 3)
    for tag in soup.find_all(lambda t: t.has_attr('epub:type') and 'pagebreak' in str(t.get('epub:type', '')).lower()):
        tag.decompose()
    for tag in soup.find_all(lambda t: t.has_attr('role') and str(t.get('role', '')).lower() == 'doc-pagebreak'):
        tag.decompose()

    # 2) Remover por classe/id típicos  (✔️ sem any() e com bool() em Match)
    for tag in soup.find_all(lambda t: t.has_attr('class') and bool(_RE_CLASS_PAGENUM.search(' '.join(t.get('class', []))))):
        tag.decompose()
    for tag in soup.find_all(lambda t: t.has_attr('id') and bool(_RE_ID_PAGE.match(str(t.get('id', '')) or ''))):
        tag.decompose()

    # 3) Processar <a>: se for marcador de página, remove; do contrário, unwrap
    for a in soup.find_all('a'):
        if (
            (a.has_attr('epub:type') and 'pagebreak' in str(a.get('epub:type', '')).lower()) or
            (a.has_attr('role') and str(a.get('role', '')).lower() == 'doc-pagebreak') or
            (a.has_attr('class') and bool(_RE_CLASS_PAGENUM.search(' '.join(a.get('class', []))))) or
            (a.has_attr('id') and bool(_RE_ID_PAGE.match(str(a.get('id', '')) or '')))
        ):
            a.decompose()
        else:
            a.unwrap()

    # 4) Spans/Divs curtos com apenas número de página no texto
    POSSIVEIS = ('span', 'div')
    for tag in soup.find_all(POSSIVEIS):
        txt = tag.get_text(strip=True)
        # Apenas um número, ou "Página 12" / "Pág. 12" / "Page 12" (curtos, típicos de cabeçalho/rodapé)
        if re.fullmatch(r'\d{1,4}', txt) or re.fullmatch(r'(Página|Pág\.?|Page)\s*\d{1,4}(\s*de\s*\d{1,4})?', txt, flags=re.I):
            tag.decompose()

def extract_from_epub(filepath: str) -> str:
    if epub is None or ITEM_DOCUMENT is None or BeautifulSoup is None:
        logging.error("Dependências ausentes para EPUB: ebooklib e/ou beautifulsoup4. "
                      "Instale com: pip install ebooklib beautifulsoup4")
        return ""
    try:
        book = epub.read_epub(filepath)  # type: ignore
        partes: List[str] = []

        spine = getattr(book, "spine", None)
        if spine:
            # spine típico: lista de tuplas (idref, linear)
            iter_spine = [(idref, linear) for (idref, linear) in spine if isinstance(idref, str)]
            for item_id, _ in iter_spine:
                item = book.get_item_with_id(item_id)
                if not item:
                    continue
                soup = BeautifulSoup(item.get_content(), 'html.parser')  # type: ignore
                for tag in soup(['nav', 'header', 'footer', 'style', 'script', 'figure', 'aside', 'img']):
                    tag.decompose()
                _remover_marcadores_pagina_epub(soup)
                txt = soup.get_text(separator='\n', strip=True)
                if txt:
                    partes.append(txt)
        else:
            # Fallback: varre todos os documentos HTML do EPUB
            for item in book.get_items_of_type(ITEM_DOCUMENT):  # type: ignore
                soup = BeautifulSoup(item.get_content(), 'html.parser')  # type: ignore
                for tag in soup(['nav', 'header', 'footer', 'style', 'script', 'figure', 'aside', 'img']):
                    tag.decompose()
                _remover_marcadores_pagina_epub(soup)
                txt = soup.get_text(separator='\n', strip=True)
                if txt:
                    partes.append(txt)

        return "\n\n".join(partes)
    except Exception as e:
        logging.error(f"Erro ao processar o EPUB '{filepath}': {e}")
        return ""

def extract_from_txt(filepath: str) -> str:
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logging.error(f"Erro ao ler TXT '{filepath}' com '{encoding}': {e}")
            return ""
    logging.error(f"Não foi possível ler o TXT '{filepath}' com as codificações tentadas.")
    return ""


# ================== FORMATAÇÃO P/ TTS ==================

# Expansões controladas: ordem importa
EXPANSOES_REGEX = [
    # Abreviações comuns
    (re.compile(r'\bSr\.\s*', re.IGNORECASE), 'Senhor '),
    (re.compile(r'\bSra\.\s*', re.IGNORECASE), 'Senhora '),
    (re.compile(r'\bDr\.\s*', re.IGNORECASE),  'Doutor '),
    (re.compile(r'\bAv\.\s*', re.IGNORECASE),  'Avenida '),
    (re.compile(r'\bR\.\s*',  re.IGNORECASE),  'Rua '),
    (re.compile(r'\bEtc\.?\b', re.IGNORECASE), 'et cetera'),
    (re.compile(r'\bvs\.\b',   re.IGNORECASE), 'versus'),

    # "p." somente quando vier antes de dígitos (ex.: p. 23)
    (re.compile(r'\bp\.\s*(?=\d+)', re.IGNORECASE), 'página '),

    # "nº / n.º / n°" e "n." SOMENTE quando seguidos de dígitos
    (re.compile(r'\bN(?:º|°)\.?\s*(?=\d+)', re.IGNORECASE), 'número '),
    (re.compile(r'\bN\.\s*(?=\d+)',         re.IGNORECASE), 'número '),
]

# Mapa de capítulos por extenso → algarismo
CAPITULOS_EXTENSO = {
    'UM': '1', 'DOIS': '2', 'TRÊS': '3', 'TRES': '3', 'QUATRO': '4', 'CINCO': '5',
    'SEIS': '6', 'SETE': '7', 'OITO': '8', 'NOVE': '9', 'DEZ': '10', 'ONZE': '11',
    'DOZE': '12', 'TREZE': '13', 'CATORZE': '14', 'QUINZE': '15',
    'DEZESSEIS': '16', 'DEZESSETE': '17', 'DEZOITO': '18', 'DEZENOVE': '19', 'VINTE': '20'
}

def _normalizar_unicode(texto: str) -> str:
    t = unicodedata.normalize('NFKC', texto)
    t = t.replace('\u00A0', ' ')  # espaço duro → espaço normal
    # Aspas tipográficas → ASCII
    t = re.sub(r'[“”«»]', '"', t)
    t = re.sub(r"[‘’]", "'", t)
    # Dashes/hífens: uniformiza travessão
    t = t.replace('―', '—').replace('–', '—')  # variantes → travessão
    # Normaliza sublinhado residual
    t = t.replace('_', '')
    return t

def _remover_marcas_dagua_e_rodapes(texto: str) -> str:
    """
    Remove linhas de propaganda/rodapé com segurança:
    - Opera linha a linha (somente MULTILINE).
    - Usa [^\\n]* em vez de .* para não atravessar parágrafos.
    - Agora também remove 'Página 12', 'Pág. 12', 'Page 12' e 'Página 12 de 300'.
    """
    padroes = [
        re.compile(r'(?im)^[^\n]*novidade[^\n]*para você![^\n]*$'),  # ex.: "Sempre uma novidade para você!"
        re.compile(r'(?im)^\s*Distribuído gratuitamente pela [^\n]*$'),
        re.compile(r'(?im)^\s*Esse livro é protegido pelas leis [^\n]*$'),
        re.compile(r'(?m)^\s*-+\s*\d+\s*-+\s*$'),     # linhas tipo "---- 12 ----"
        re.compile(r'(?m)^\s*\d+\s*$'),               # número de página isolado
        re.compile(r'(?im)^\s*(Página|Pág\.?|Page)\s*\d{1,5}(\s*de\s*\d{1,5})?\s*$'),  # Página 12 / Pág. 12 / Page 12 [de 300]
    ]
    linhas = texto.splitlines()
    filtradas = []
    for ln in linhas:
        if any(p.search(ln) for p in padroes):
            continue
        filtradas.append(ln)
    return "\n".join(filtradas)

def _remover_hifenizacao_fim_de_linha(texto: str) -> str:
    # Junta PALAVRA-<quebra>CONTINUAÇÃO → PALAVRACONTINUAÇÃO
    return re.sub(r'(\w+)-\s*\n(\w+)', r'\1\2', texto)

def _normalizar_capitulos(texto: str) -> str:
    linhas = texto.splitlines()
    out = []
    # CAPÍTULO <extenso|dígito> <título>
    rx = re.compile(r'^\s*CAP[IÍ]TULO\s+([A-ZÇÃÕÉÍÁÚÂÊÔ]+|\d+)\s*(.*)$', re.IGNORECASE)
    for ln in linhas:
        m = rx.match(ln)
        if m:
            idx, titulo = m.groups()
            idx_upper = idx.upper()
            numero = CAPITULOS_EXTENSO.get(idx_upper, idx)  # mantém se já for dígito
            titulo = titulo.strip()
            if titulo:
                out.append(f'Capítulo {numero}: {titulo}')
            else:
                out.append(f'Capítulo {numero}')
        else:
            out.append(ln)
    return "\n".join(out)

def _aplicar_expansoes(texto: str) -> str:
    t = texto
    for rx, subst in EXPANSOES_REGEX:
        t = rx.sub(subst, t)
    return t

def _limpar_pontuacao_e_espacos(texto: str) -> str:
    t = texto
    # Elipses longas → "..."
    t = re.sub(r'\.{3,}', '...', t)

    # Remove espaço antes de pontuação comum
    t = re.sub(r'\s+([,.;:!?])', r'\1', t)

    # Garante espaço após ; : ! ? quando necessário
    t = re.sub(r'([;:!?])([^\s"\'\)\]\}])', r'\1 \2', t)

    # Para vírgula e ponto, evita inserir espaço quando estão entre dígitos (ex.: 1,5 / 1.000)
    t = re.sub(r'(?<!\d)(,)([^\s"\'\)\]\}\d])', r'\1 \2', t)
    t = re.sub(r'(?<!\d)(\.)([^\s"\'\)\]\}\d])', r'\1 \2', t)

    # Travessão de diálogo: assegura espaço depois se vier palavra
    t = re.sub(r'—(?=\S)', '— ', t)

    # Espaços múltiplos
    t = re.sub(r'[ \t]{2,}', ' ', t)

    # Linhas em branco em bloco: no máximo uma
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()

def _coagir_para_string(texto_bruto: Any) -> str:
    """Aceita str ou Iterable[str]; une capítulos quando vier em lista/tupla."""
    if isinstance(texto_bruto, str):
        return texto_bruto
    if isinstance(texto_bruto, Iterable):
        try:
            return "\n\n".join(s for s in texto_bruto if isinstance(s, str))
        except Exception:
            pass
    return str(texto_bruto) if texto_bruto is not None else ""

def _log_len(etapa: str, s: str) -> None:
    logging.info(f"{etapa}: {len(s)} caracteres")

def formatar_texto_para_tts(texto_bruto: Any) -> str:
    texto_in = _coagir_para_string(texto_bruto)
    if not texto_in:
        logging.warning("Texto de entrada vazio após coerção para string.")
        return ""

    _log_len("Entrada", texto_in)

    # 1) Normalização inicial
    texto = _normalizar_unicode(texto_in)
    _log_len("Após normalização unicode", texto)

    # 2) Remoção segura de marcas/rodapés
    texto = _remover_marcas_dagua_e_rodapes(texto)
    _log_len("Após remoção de marcas/rodapés", texto)

    # 3) Remoção de hifenização antes de unir linhas
    texto = _remover_hifenizacao_fim_de_linha(texto)
    _log_len("Após juntar hifenização de fim de linha", texto)

    # 4) Mescla quebras simples em espaço (preservando parágrafos)
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    _log_len("Após mesclar quebras simples", texto)

    # 5) Expansões abreviadas (controladas)
    texto = _aplicar_expansoes(texto)
    _log_len("Após expansões", texto)

    # 6) Normalização de capítulos
    texto = _normalizar_capitulos(texto)
    _log_len("Após normalização de capítulos", texto)

    # 7) (Opcional) Expansão de números para palavras com cautela
    def expandir_numeros(seg: str) -> str:
        if num2words is None:
            return seg

        # Palavras que desabilitam expansão quando aparecem imediatamente antes do número
        NAO_EXPANDIR_ANTES = ("capítulo ", "capitulo ", "página ", "pagina ", "número ", "numero ")

        def _cardinal(m: re.Match) -> str:
            num = m.group(0)
            ini = m.start()
            # Janela de 20 caracteres antes do número para checagem de contexto
            prefixo = seg[max(0, ini - 20):ini].lower()
            if any(prefixo.endswith(w) for w in NAO_EXPANDIR_ANTES):
                return num
            try:
                val = int(num)
                # Evita expandir ANOS (1900–2100) e números com >4 dígitos
                if 1900 <= val <= 2100 or len(num) > 4:
                    return num
                return num2words(val, lang='pt_BR')  # type: ignore
            except Exception:
                return num

        # Casa números "isolados", evitando decimais e milhares (1,5 / 1.000)
        padrao = re.compile(r'(?<!\d[.,])\b\d+\b(?![.,]\d)')
        return padrao.sub(_cardinal, seg)

    texto = expandir_numeros(texto)
    _log_len("Após expansão (opcional) de números", texto)

    # 8) Limpeza fina de pontuação/espaços
    texto = _limpar_pontuacao_e_espacos(texto)
    _log_len("Final", texto)

    return texto


# ================== CLI ==================

def main():
    parser = argparse.ArgumentParser(
        description="Extrai e formata texto (PDF, DOCX, EPUB, TXT) para uso com TTS.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_file", help="Caminho do arquivo de entrada.")
    parser.add_argument("output_file", help="Caminho do .txt de saída.")
    args = parser.parse_args()

    input_path = args.input_file
    if not os.path.exists(input_path):
        logging.error(f"Arquivo de entrada não encontrado: '{input_path}'.")
        return

    _, ext = os.path.splitext(input_path.lower())
    extractors = {
        '.pdf': extract_from_pdf,
        '.docx': extract_from_docx,
        '.epub': extract_from_epub,
        '.txt': extract_from_txt
    }
    if ext not in extractors:
        logging.error(f"Formato '{ext}' não suportado. Use PDF, DOCX, EPUB ou TXT.")
        return

    logging.info(f"Processando: {input_path}")
    raw_text = extractors[ext](input_path)
    if not raw_text:
        logging.error("Nada foi extraído (arquivo vazio/corrompido/protegido?).")
        return

    formatted = formatar_texto_para_tts(raw_text)

    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(formatted)
        print(f"\nSucesso! Texto formatado salvo em: {args.output_file}")
    except IOError as e:
        logging.error(f"Erro ao salvar o arquivo de saída: {e}")


if __name__ == "__main__":
    main()
