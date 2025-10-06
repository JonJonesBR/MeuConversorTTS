# -*- coding: utf-8 -*-
"""
Script definitivo de limpeza e formatação de texto para leitura TTS.
Aprimorado para EPUBs: remove formatação, corrige pontuação, expande
abreviações, siglas e unidades, e deixa o texto fluido e natural.
"""
import re
import unicodedata
from num2words import num2words
import config

# ================== TEXTOS FIXOS ==================

TEXTOS_REPETIDOS_PARA_REMOVER = [
    "Esse livro é protegido pelas leis internacionais de Copyright.",
    "A Detonando Home Page não se responsabiliza por qualquer dano que esse material possa causar.",
    "Seu uso deve ser exclusivamente pessoal.",
    "Distribuído gratuitamente pela Detonando Home Page – www.",
    "portaldetonando.",
    "cjb.",
    "net - Sempre uma novidade para você!"
]

# ================== LIMPEZAS ==================

def _remover_lixo_textual(texto: str) -> str:
    print("   -> Removendo cabeçalhos e rodapés...")
    padrao_primeiro_cap = re.compile(r'(cap[íi]tulo)', re.IGNORECASE)
    match = padrao_primeiro_cap.search(texto)
    if match:
        texto = texto[match.start():]
    for frase in TEXTOS_REPETIDOS_PARA_REMOVER:
        texto = texto.replace(frase, "")
    return texto


def _normalizar_pontuacao(texto: str) -> str:
    """Normaliza aspas, travessões e sinais para evitar leitura errada."""
    print("   -> Normalizando pontuação e aspas...")

    substituicoes = {
        '“': '"', '”': '"', '«': '"', '»': '"', '‘': "'", '’': "'",
        '–': '—', '--': '—', '―': '—',
        '…': '...',
    }
    for k, v in substituicoes.items():
        texto = texto.replace(k, v)

    # Remove duplas aspas mal posicionadas
    texto = re.sub(r'"{2,}', '"', texto)
    texto = re.sub(r"'{2,}", "'", texto)

    # Normaliza espaços antes e depois de travessões
    texto = re.sub(r'\s*—\s*', ' — ', texto)
    texto = re.sub(r'\s{2,}', ' ', texto)
    return texto.strip()


def _remover_formatacao_markdown(texto: str) -> str:
    print("   -> Removendo formatação Markdown (_ e **)...")
    texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
    texto = re.sub(r'_(.*?)_', r'\1', texto)
    texto = re.sub(r'\*([^*]+)\*', r'\1', texto)
    return texto


def _remontar_paragrafos(texto: str) -> str:
    print("   -> Remontando parágrafos...")
    texto = re.sub(r'\n\s*\n', '|||NEW_PAR|||', texto)
    texto = texto.replace('\n', ' ')
    texto = texto.replace('|||NEW_PAR|||', '\n\n')
    texto = re.sub(r'(\w+)-\s+', r'\1', texto)
    return texto.strip()


# ================== FORMATADORES ==================

def _formatar_capitulos_e_titulos(texto: str) -> str:
    print("   -> Formatando capítulos e títulos...")

    def substituir_capitulo(match):
        numero = match.group(1).strip().upper()
        titulo = match.group(2).strip().title()
        numero_final = config.CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(numero, numero)
        if not re.search(r'[.!?]$', titulo):
            titulo += "."
        return f"\n\nCAPÍTULO {numero_final}.\n\n{titulo}\n\n"

    padrao = re.compile(r'CAP[ÍI]TULO\s+([\w\s]+?)\.\s*\n\n([^\n]+)', re.IGNORECASE)
    return padrao.sub(substituir_capitulo, texto)


def _expandir_abreviacoes_comuns(texto: str) -> str:
    """Expande abreviações e siglas para leitura natural."""
    print("   -> Expandindo abreviações e siglas...")

    substituicoes = {
        # Pessoas e títulos
        r'\bSr\.': 'Senhor', r'\bSra\.': 'Senhora', r'\bSrta\.': 'Senhorita',
        r'\bDr\.': 'Doutor', r'\bDra\.': 'Doutora',
        r'\bProf\.': 'Professor', r'\bProfa\.': 'Professora',
        # Endereços
        r'\bAv\.': 'Avenida', r'\bR\.': 'Rua', r'\bRod\.': 'Rodovia', r'\bPça\.': 'Praça',
        # Diversos
        r'\bN[º°o]\b': 'número', r'\bn[º°o]\b': 'número',
        r'\bKg\b': 'quilograma', r'\bkm\b': 'quilômetro', r'\bcm\b': 'centímetro',
        r'\bmm\b': 'milímetro', r'\bml\b': 'mililitro', r'\bL\b': 'litro',
        r'\b°C\b': 'graus Celsius', r'\b%\b': 'por cento',
        r'\bm²\b': 'metros quadrados', r'\bm³\b': 'metros cúbicos',
        r'\bEtc\.?': 'et cetera', r'\bObs\.?': 'observação',
        # Siglas comuns
        r'\bEUA\b': 'Estados Unidos da América', r'\bONU\b': 'Organização das Nações Unidas',
        r'\bRJ\b': 'Rio de Janeiro', r'\bSP\b': 'São Paulo', r'\bDF\b': 'Distrito Federal',
        r'\bS/N\b': 'sem número',
    }

    for padrao, subst in substituicoes.items():
        texto = re.sub(padrao, subst, texto, flags=re.IGNORECASE)
    return texto


def _corrigir_apostrofos_estrangeiros(texto: str) -> str:
    """Corrige casos como Dursley’s → Dursleys."""
    texto = re.sub(r"([A-Za-z])’s", r"\1s", texto)
    texto = re.sub(r"([A-Za-z])'s", r"\1s", texto)
    return texto


def _expandir_numeros(texto: str) -> str:
    print("   -> Expandindo números...")

    def ordinal(match):
        try:
            n = int(match.group(1))
            suf = match.group(2)
            if suf.lower() in ('o', 'º'):
                return num2words(n, lang='pt_BR', to='ordinal')
            elif suf.lower() in ('a', 'ª'):
                s = num2words(n, lang='pt_BR', to='ordinal')
                return s[:-1] + 'a' if s.endswith('o') else s
        except Exception:
            return match.group(0)
        return match.group(0)

    texto = re.sub(r'\b(\d+)([oOaAºª])\b', ordinal, texto)

    def monetario(match):
        valor = match.group(1).replace('.', '')
        return f"{num2words(int(valor), lang='pt_BR')} reais"
    texto = re.sub(r'R\$\s*(\d[\d.]*)', monetario, texto)

    def cardinal(match):
        n = match.group(0)
        try:
            v = int(n)
            if 1900 <= v <= 2100 or len(n) > 6:
                return n
            return num2words(v, lang='pt_BR')
        except:
            return n
    texto = re.sub(r'\b\d+\b', cardinal, texto)
    return texto


def _limpeza_final(texto: str) -> str:
    print("   -> Limpando e ajustando espaçamento final...")
    texto = re.sub(r'([.!?])\s*([—-])', r'\1\n\n\2', texto)
    texto = re.sub(r'\s+([,.!?;:])', r'\1', texto)
    texto = re.sub(r'([,.!?;:])(\w)', r'\1 \2', texto)
    texto = re.sub(r' {2,}', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    paragrafos = []
    for p in texto.split('\n\n'):
        p = p.strip()
        if p:
            if not re.search(r'[.!?]$', p) and not p.startswith("CAPÍTULO"):
                p += '.'
            paragrafos.append(p)
    return '\n\n'.join(paragrafos).strip()


# ================== FUNÇÃO PRINCIPAL ==================

def formatar_texto_para_tts(texto_bruto: str) -> str:
    """
    Executa todas as etapas para preparar o texto
    ideal para leitura natural em TTS.
    """
    print("🧩 Iniciando processamento completo do texto...")

    texto = unicodedata.normalize('NFKC', texto_bruto)
    texto = _remover_lixo_textual(texto)
    texto = _normalizar_pontuacao(texto)
    texto = _remover_formatacao_markdown(texto)
    texto = _remontar_paragrafos(texto)
    texto = _corrigir_apostrofos_estrangeiros(texto)
    texto = _formatar_capitulos_e_titulos(texto)
    texto = _expandir_abreviacoes_comuns(texto)
    texto = _expandir_numeros(texto)
    texto = _limpeza_final(texto)

    print("✅ Texto pronto para TTS.")
    return texto.strip()
