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
# import pdfplumber  <-- REMOVIDO
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

# Bloco da função extract_from_pdf REMOVIDO

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
    (re.compile(r'\bDra\.\s*', re.IGNORECASE),  'Doutora '),
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
    # Remove asteriscos que podem ter vindo de conversão HTML
    t = t.replace('*', '')
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
    # Evita adicionar caracteres de escape indevidos
    return re.sub(r'(\w+)-\s*\n(\w+)', r'\1\2', texto)

def _formatar_numeracao_capitulos(texto: str) -> str:
    """
    Localiza títulos como 'Capítulo 1 Mesmo em pleno verão...' ou 'CAPÍTULO UM ...'
    e converte para: '\n\nCAPÍTULO 1.\n\nMesmo em pleno verão...'
    Também padroniza números por extenso para arábicos.
    """
    def substituir_cap(match):
        tipo_cap = match.group(1).upper() # CAPÍTULO ou CAP.
        numero_rom_arab = match.group(2)
        numero_extenso = match.group(3)
        titulo_opcional = match.group(4).strip() if match.group(4) else ""

        numero_final = ""
        if numero_rom_arab:
            numero_final = numero_rom_arab.upper()
        elif numero_extenso:
            num_ext_upper = numero_extenso.strip().upper()
            numero_final = CAPITULOS_EXTENSO.get(num_ext_upper, num_ext_upper)

        cabecalho = f"{tipo_cap} {numero_final}."
        if titulo_opcional: # Se houver título após o número
             # Capitaliza o título do capítulo, mas preserva siglas
            palavras_titulo = []
            for p in titulo_opcional.split():
                if p.isupper() and len(p) > 1: # sigla
                    palavras_titulo.append(p)
                else:
                    palavras_titulo.append(p.capitalize())
            titulo_formatado = " ".join(palavras_titulo)
            return f"\n\n{cabecalho}\n\n{titulo_formatado}"
        return f"\n\n{cabecalho}\n\n" # Se o título já está na próxima linha

    padrao = re.compile(
        r'(?i)(cap[íi]tulo|cap\.?)\s+'
        r'(?:(\d+|[IVXLCDM]+)|([A-ZÇÉÊÓÃÕa-zçéêóãõ]+))'
        r'\s*[:\-.]?\s*'
        r'(?=\S)([^\n]*)?',
        re.IGNORECASE
    )
    texto = padrao.sub(substituir_cap, texto)

    def substituir_extenso_com_titulo(match):
        num_ext = match.group(1).strip().upper()
        titulo = match.group(2).strip().title()
        numero = CAPITULOS_EXTENSO.get(num_ext, num_ext)
        return f"CAPÍTULO {numero}: {titulo}"

    padrao_extenso_titulo = re.compile(r'CAP[IÍ]TULO\s+([A-ZÇÉÊÓÃÕ]+)\s*[:\-]\s*(.+)', re.IGNORECASE)
    texto = padrao_extenso_titulo.sub(substituir_extenso_com_titulo, texto)
    
    # Adiciona detecção de capítulos em formato romano
    def substituir_capitulo_romano(match):
        tipo_cap = match.group(1).upper()
        cap_romano = match.group(2).upper()
        titulo = match.group(3).strip() if match.group(3) else ""
        
        # Converter número romano para arábico
        romano_para_arabico = {
            'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
            'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10',
            'XI': '11', 'XII': '12', 'XIII': '13', 'XIV': '14', 'XV': '15',
            'XVI': '16', 'XVII': '17', 'XVIII': '18', 'XIX': '19', 'XX': '20'
        }
        numero_arabico = romano_para_arabico.get(cap_romano, cap_romano)
        
        cabecalho = f"{tipo_cap} {numero_arabico}."
        if titulo:
            palavras_titulo = []
            for p in titulo.split():
                if p.isupper() and len(p) > 1:
                    palavras_titulo.append(p)
                else:
                    palavras_titulo.append(p.capitalize())
            titulo_formatado = " ".join(palavras_titulo)
            return f"\n\n{cabecalho}\n\n{titulo_formatado}"
        return f"\n\n{cabecalho}\n\n"

    padrao_romano = re.compile(
        r'(?i)(cap[íi]tulo|cap\.?)\s+([IVXLCDM]+)\s*[:\-.]?\s*([^\n]*)?',
        re.IGNORECASE
    )
    texto = padrao_romano.sub(substituir_capitulo_romano, texto)
    
    return texto


def _remover_numeros_pagina_isolados(texto: str) -> str:
    linhas = texto.splitlines()
    novas_linhas = []
    for linha in linhas:
        if re.match(r'^\s*\d+\s*$', linha):
            continue
        linha = re.sub(r'\s{3,}\d+\s*$', '', linha)
        novas_linhas.append(linha)
    return '\n'.join(novas_linhas)


def _normalizar_caixa_alta_linhas(texto: str) -> str:
    """
    Converte linhas inteiramente em caixa alta para normal (capitalizado),
    mas preserva siglas e abreviações.
    """
    linhas = texto.splitlines()
    texto_final = []
    for linha in linhas:
        if not re.match(r'^\s*CAP[ÍI]TULO\s+[\w\d]+\.?\s*$', linha, re.IGNORECASE):
            if linha.isupper() and len(linha.strip()) > 3 and any(c.isalpha() for c in linha):
                palavras = []
                for p in linha.split():
                    # Verifica se é uma sigla comum (todas maiúsculas e com vogais)
                    if len(p) > 1 and p.isupper() and p.isalpha():
                        # Verifica se é uma sigla válida (contém vogais e consoantes)
                        vogais = sum(1 for char in p if char in "AEIOU")
                        consoantes = sum(1 for char in p if char not in "AEIOU")
                        
                        # Se for uma sigla válida (tem vogais e consoantes, e não é muito curta)
                        if vogais > 0 and consoantes > 0 and len(p) > 3:
                            palavras.append(p)
                        elif p in ['I', 'A', 'E', 'O', 'U', 'AI', 'AO', 'EI', 'EU', 'OI', 'OU', 'AE', 'OE']:
                            # Preserva certos monossílabos e ditongos
                            palavras.append(p)
                        else:
                            # Converte para capitalizado
                            palavras.append(p.capitalize())
                    else:
                        palavras.append(p.capitalize())
                texto_final.append(" ".join(palavras))
            else:
                texto_final.append(linha)
        else:
            texto_final.append(linha)
    return "\n".join(texto_final)


def _corrigir_hifenizacao_quebras(texto: str) -> str:
    return re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)


def _remover_metadados_pdf(texto: str) -> str:
    texto = re.sub(r'^\s*[\w\d_-]+\.indd\s+\d+\s+\d{2}/\d{2}/\d{2,4}\s+\d{1,2}:\d{2}(:\d{2})?\s*([AP]M)?\s*$', '', texto, flags=re.MULTILINE)
    return texto


def _normalizar_capitulos(texto: str) -> str:
    # Aplica a nova função de formatação de capítulos
    texto = _formatar_numeracao_capitulos(texto)
    return texto

# Mapeia a forma base (sem ponto, case-insensitive) para a expansão
ABREVIACOES_MAP = {
    'dr': 'Doutor', 'd': 'Dona', 'dra': 'Doutora',
    'sr': 'Senhor', 'sra': 'Senhora', 'srta': 'Senhorita',
    'prof': 'Professor', 'profa': 'Professora',
    'eng': 'Engenheiro', 'engª': 'Engenheira', # 'engª' é um caso especial
    'adm': 'Administrador', 'adv': 'Advogado',
    'exmo': 'Excelentíssimo', 'exma': 'Excelentíssima',
    'v.exa': 'Vossa Excelência', 'v.sa': 'Vossa Senhoria', # Casos com ponto interno
    'av': 'Avenida', 'r': 'Rua', 'km': 'Quilômetro',
    'etc': 'etcétera', 'ref': 'Referência',
    'pag': 'Página', 'pags': 'Páginas',
    'fl': 'Folha', 'fls': 'Folhas',
    'pe': 'Padre',
    'dept': 'Departamento', 'depto': 'Departamento',
    'univ': 'Universidade', 'inst': 'Instituição',
    'est': 'Estado', 'tel': 'Telefone',
    # CEP, CNPJ, CPF não terminam em ponto geralmente
    'eua': 'Estados Unidos da América', # Sigla comum
    'ed': 'Edição', 'ltda': 'Limitada',
    # Adicione mais conforme necessário
    # Abreviações adicionais baseadas no script monolítico
    'p.ex': 'Por exemplo', 'ex': 'Exemplo',
    'i.e': 'Isto é', 'e.g': 'Exempli gratia', # Em latim, significa "por exemplo"
    'vs': 'Versus', 'cf': 'Conferir', # Comparar
    'op.cit': 'Opere citato', # Na obra citada
    'loc.cit': 'Loco citato', # No lugar citado
    'cfr': 'Conferir', # Versão em português de "cf"
    'jr': 'Júnior', 'sr': 'Sênior',
    'ph.d': 'Doutorado', 'ms': 'Mestre', 'msc': 'Mestre', # MSc = Master of Science
    'esp': 'Especialista', 'psic': 'Psicólogo', 'psico': 'Psicólogo',
    'pç': 'Praça', 'esq': 'Esquina', 'trav': 'Travessa', 'jd': 'Jardim',
    'pq': 'Parque', 'rod': 'Rodovia', 'apt': 'Apartamento', 'ap': 'Apartamento',
    'bl': 'Bloco', 'cj': 'Conjunto', 'cs': 'Casa', 'ed': 'Edifício',
    'nº': 'Número', 'no': 'Número', 'uf': 'Unidade Federativa',
    'dist': 'Distrito', 'zon': 'Zona', 'reg': 'Região',
    'kg': 'Quilograma', 'cm': 'Centímetro', 'mm': 'Milímetro',
    'lt': 'Litro', 'ml': 'Mililitro', 'mg': 'Miligrama',
    'seg': 'Segundo', 'min': 'Minuto', 'hr': 'Hora',
    'ltda': 'Limitada', 's.a': 'Sociedade Anônima', 's/a': 'Sociedade por Ações',
    'cnpj': 'Cadastro Nacional da Pessoa Jurídica',
    'cpf': 'Cadastro de Pessoas Físicas',
    'rg': 'Registro Geral', 'proc': 'Processo',
    'cod': 'Código', 'tel': 'Telefone',
    'obs': 'Observação', 'att': 'Atenciosamente', # Atenciosamente
    'resp': 'Responsável', 'publ': 'Publicação',
    'dout': 'Doutor', 'propr': 'Proprietário',
    'gen': 'General', 'cel': 'Coronel', 'maj': 'Major', 'cap': 'Capitão',
    'ten': 'Tenente', 'sgt': 'Sargento', 'cb': 'Cabo', 'sd': 'Soldado',
    'me': 'Microempresa', # Termo legal no Brasil
    'mei': 'Microempreendedor Individual',
    'suz': 'Sujeito', 'obj': 'Objeto', 'pred': 'Predicado',
    'adj': 'Adjetivo', 'sub': 'Substantivo', 'verb': 'Verbo',
    'adv': 'Advérbio', 'pron': 'Pronome', 'prep': 'Preposição',
    'conj': 'Conjunção', 'interj': 'Interjeição', 'num': 'Numeral',
    'art': 'Artigo', 'nom': 'Nome', 'fem': 'Feminino', 'masc': 'Masculino',
    'sg': 'Singular', 'pl': 'Plural', 'inf': 'Infinitivo', 'part': 'Particípio',
    'ger': 'Gerúndio', 'pres': 'Presente', 'pret': 'Pretérito', 'fut': 'Futuro',
    'ind': 'Indicativo', 'subj': 'Subjuntivo', 'imp': 'Imperativo',
    '1ª': 'Primeira', '2ª': 'Segunda', '3ª': 'Terceira', '4ª': 'Quarta',
    '5ª': 'Quinta', '6ª': 'Sexta', 'dom': 'Domingo', 'seg': 'Segunda',
    'ter': 'Terça', 'qua': 'Quarta', 'qui': 'Quinta', 'sex': 'Sexta',
    'sab': 'Sábado', 'jan': 'Janeiro', 'fev': 'Fevereiro', 'mar': 'Março',
    'abr': 'Abril', 'mai': 'Maio', 'jun': 'Junho', 'jul': 'Julho',
    'ago': 'Agosto', 'set': 'Setembro', 'out': 'Outubro', 'nov': 'Novembro',
    'dez': 'Dezembro', 'mat': 'Matutino', 'vesp': 'Vespertino', 'not': 'Noturno',
    'am': 'Ante meridiem', 'pm': 'Post meridiem',
    'a.c': 'Antes de Cristo', 'd.c': 'Depois de Cristo',
    'séc': 'Século', 'vol': 'Volume', 'n': 'Número', # Em referências bibliográficas
    'p': 'Página', 'pp': 'Páginas', # Em referências bibliográficas
    'cit': 'Citar', 'citado': 'Citado'
}

# Pré-processar para busca case-insensitive mais rápida
ABREVIACOES_MAP_LOWER = {k.lower(): v for k, v in ABREVIACOES_MAP.items()}

# Casos especiais que precisam de tratamento diferente (ex: ponto interno)
# Estes podem ser deixados nos padrões originais se a nova abordagem não funcionar bem
CASOS_ESPECIAIS_RE = {
     r'\bV\.Exa\.(?=\s)': 'Vossa Excelência', # Mantém o padrão original
     r'\bV\.Sa\.(?=\s)': 'Vossa Senhoria',  # Mantém o padrão original
     r'\bEngª\.(?=\s)': 'Engenheira' # Trata 'ª' separadamente
     # Adicionar outros casos complexos aqui se necessário
}


def _expandir_abreviacoes_numeros(texto: str) -> str:
    """Expande abreviações comuns (removendo o ponto da abrev.) e converte números."""

    # Primeiro, trata casos especiais com regex mais complexas
    for abrev_re, expansao in CASOS_ESPECIAIS_RE.items():
         texto = re.sub(abrev_re, expansao, texto, flags=re.IGNORECASE)

    # Agora, trata as abreviações mais simples terminadas em ponto
    def replace_abrev_com_ponto(match):
        abrev_encontrada = match.group(1) # A parte da abreviação antes do ponto
        # Busca a expansão no dicionário (case-insensitive)
        expansao = ABREVIACOES_MAP_LOWER.get(abrev_encontrada.lower())
        if expansao:
            return expansao # Retorna APENAS a expansão, removendo o ponto original
        else:
            return match.group(0) # Se não encontrar (improvável), retorna o match original

    # Cria um padrão regex que busca por qualquer chave do dicionário seguida por um ponto.
    # Ex: \b(Dr|D|Dra|Sr|Sra|...)\.(?!\.)
    # Usamos lookahead negativo (?!\.) para NÃO remover o ponto se for seguido por outro (ex: fim de frase..)
    # Ou, mais simples: sempre remove o ponto da abreviação e deixa a lógica de pontuação final para depois.
    
    # Padrão: \b(chave1|chave2|...)\.
    # Captura a chave (grupo 1) e o ponto literal.
    chaves_escapadas = [re.escape(k) for k in ABREVIACOES_MAP_LOWER.keys() if '.' not in k and 'ª' not in k] # Ignora chaves já tratadas ou complexas
    if chaves_escapadas: # Só cria o padrão se houver chaves simples
        padrao_abrev_simples = r'\b(' + '|'.join(chaves_escapadas) + r')\.'
        texto = re.sub(padrao_abrev_simples, replace_abrev_com_ponto, texto, flags=re.IGNORECASE)

    # --- Conversão de números cardinais (lógica mantida) ---
    def _converter_numero_match(match):
        num_str = match.group(0)
        try:
            if re.match(r'^\d{4}$', num_str) and (1900 <= int(num_str) <= 2100): return num_str
            if len(num_str) > 7 : return num_str
            if num2words is None: return num_str
            return num2words(int(num_str), lang='pt_BR')
        except Exception: return num_str
    texto = re.sub(r'\b\d+\b', _converter_numero_match, texto)

    # --- Conversão de valores monetários (lógica mantida) ---
    def _converter_valor_monetario_match(match):
        valor_inteiro = match.group(1).replace('.', '')
        try:
            if num2words is None: return match.group(0)
            return f"{num2words(int(valor_inteiro), lang='pt_BR')} reais"
        except Exception: return match.group(0)
    texto = re.sub(r'R\$\s*(\d{1,3}(?:\.\d{3})*),(\d{2})', _converter_valor_monetario_match, texto)
    texto = re.sub(r'R\$\s*(\d+)(?:,00)?', lambda m: f"{num2words(int(m.group(1)), lang='pt_BR')} reais" if m.group(1) and num2words else m.group(0) , texto)
    
    # --- Conversão de intervalos numéricos (lógica mantida) ---
    if num2words:
        texto = re.sub(r'\b(\d+)\s*-\s*(\d+)\b', lambda m: f"{num2words(int(m.group(1)), lang='pt_BR')} a {num2words(int(m.group(2)), lang='pt_BR')}" if num2words else f"{m.group(1)} a {m.group(2)}", texto)
    
    return texto


def _converter_ordinais_para_extenso(texto: str) -> str:
    """Converte números ordinais como 1º, 2a, 3ª para extenso."""

    def substituir_ordinal(match):
        numero = match.group(1)
        terminacao = match.group(2).lower() # 'o', 'a', 'os', 'as' (embora 'os'/'as' sejam menos comuns assim)

        try:
            num_int = int(numero)
            if num2words is None:
                return match.group(0)  # Retorna o original se num2words não estiver disponível
            if terminacao == 'o' or terminacao == 'º':
                return num2words(num_int, lang='pt_BR', to='ordinal')
            elif terminacao == 'a' or terminacao == 'ª':
                # num2words para ordinal feminino em pt_BR pode precisar de ajuste manual
                # para algumas bibliotecas ou versões.
                # A biblioteca num2words geralmente lida bem com isso se o idioma estiver correto.
                # Ex: num2words(1, lang='pt_BR', to='ordinal_num') -> 1 (mas queremos extenso)
                # Tentativa: converter para ordinal masculino e trocar terminação se necessário
                ordinal_masc = num2words(num_int, lang='pt_BR', to='ordinal')
                if ordinal_masc.endswith('o'):
                    return ordinal_masc[:-1] + 'a'
                else: # Casos como 'terceiro' -> 'terceira' já são cobertos
                    return ordinal_masc # Ou lógica mais específica se necessário
            else: # Caso não previsto, retorna o original
                return match.group(0)
        except ValueError:
            return match.group(0) # Se não for um número válido

    # Padrão para encontrar números seguidos por 'o', 'a', 'º', ou 'ª'
    # \b(\d+)\s*([oaºª])\b -> \b para garantir que é uma palavra/número isolado
    # Adicionamos (?!\w) para evitar pegar em palavras como "para" ou "caso"
    padrao_ordinal = re.compile(r'\b(\d+)\s*([oaºª])(?!\w)', re.IGNORECASE)
    texto = padrao_ordinal.sub(substituir_ordinal, texto)

    return texto


def _aplicar_expansoes(texto: str) -> str:
    # Aplica a nova função de expansão de abreviações e números
    texto = _expandir_abreviacoes_numeros(texto)
    # Depois aplica as expansões regulares
    for rx, subst in EXPANSOES_REGEX:
        texto = rx.sub(subst, texto)
    return texto

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

    # 6.5) Remoção de números de página isolados
    texto = _remover_numeros_pagina_isolados(texto)
    _log_len("Após remoção de números de página", texto)

    # 6.6) Correção de hifenização em quebras de linha
    texto = _corrigir_hifenizacao_quebras(texto)
    _log_len("Após correção de hifenização", texto)

    # 6.7) Remoção de metadados de PDF
    texto = _remover_metadados_pdf(texto)
    _log_len("Após remoção de metadados PDF", texto)

    # 6.8) Normalização de caixa alta em linhas
    texto = _normalizar_caixa_alta_linhas(texto)
    _log_len("Após normalização de caixa alta", texto)

    # 6.9) Conversão de ordinais para extenso
    texto = _converter_ordinais_para_extenso(texto)
    _log_len("Após conversão de ordinais", texto)

    # 7) (Opcional) Expansão de números para palavras com cautela
    # A expansão de números já é feita na função _expandir_abreviacoes_numeros
    # Esta seção agora se concentra em expansões específicas com contexto
    def expandir_numeros_com_contexto(seg: str) -> str:
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

    texto = expandir_numeros_com_contexto(texto)
    _log_len("Após expansão (opcional) de números", texto)

    # 8) Limpeza fina de pontuação/espaços
    texto = _limpar_pontuacao_e_espacos(texto)
    _log_len("Final", texto)

    # Remover caracteres de escape indesejados que possam ter sido introduzidos em algum ponto
    texto = texto.replace('\\-', '-')
    texto = texto.replace('\\.', '.')

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
        #'.pdf': extract_from_pdf, # REMOVIDO
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
