# -*- coding: utf-8 -*-
"""
Módulo responsável por toda a limpeza, formatação e preparação
do texto para a conversão em áudio (TTS). Versão aprimorada
para remover formatação Markdown (_ e **) e ajustar títulos.
"""
import re
import unicodedata
from num2words import num2words

import config

# ================== CONSTANTES DE LIMPEZA ==================

TEXTOS_REPETIDOS_PARA_REMOVER = [
    "Esse livro é protegido pelas leis internacionais de Copyright.",
    "A Detonando Home Page não se responsabiliza por qualquer dano que esse material possa causar.",
    "Seu uso deve ser exclusivamente pessoal.",
    "Distribuído gratuitamente pela Detonando Home Page – www.",
    "portaldetonando.",
    "cjb.",
    "net - Sempre uma novidade para você!"
]

# ================== FUNÇÕES AUXILIARES ==================

def _remover_lixo_textual(texto: str) -> str:
    print("   -> Removendo cabeçalhos e rodapés...")
    padrao_primeiro_cap = re.compile(r'(cap[íi]tulo)', re.IGNORECASE)
    match = padrao_primeiro_cap.search(texto)
    if match:
        texto = texto[match.start():]
    for frase in TEXTOS_REPETIDOS_PARA_REMOVER:
        texto = texto.replace(frase, "")
    return texto

def _remover_formatacao_markdown(texto: str) -> str:
    """Remove formatações como _**texto**_ ou **texto**, _texto_ etc."""
    print("   -> Removendo formatação Markdown (_ e **)...")
    texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)  # remove negrito
    texto = re.sub(r'_(.*?)_', r'\1', texto)        # remove itálico
    texto = re.sub(r'\*([^*]+)\*', r'\1', texto)    # remove asteriscos soltos
    return texto

def _remontar_paragrafos(texto: str) -> str:
    print("   -> Remontando parágrafos quebrados...")
    placeholder = "|||NEW_PARAGRAPH|||"
    texto = re.sub(r'\n\s*\n', placeholder, texto)
    texto = texto.replace('\n', ' ')
    texto = texto.replace(placeholder, '\n\n')
    texto = re.sub(r'(\w+)-\s+', r'\1', texto)
    return texto

def _formatar_capitulos_e_titulos(texto: str) -> str:
    print("   -> Formatando títulos de capítulos...")

    def substituir_capitulo(match):
        numero = match.group(1).strip().upper()
        titulo = match.group(2).strip().title()
        numero_final = config.CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(numero, numero)
        if not re.search(r'[.!?]$', titulo):
            titulo += "."
        return f"\n\nCAPÍTULO {numero_final}.\n\n{titulo}\n\n"

    padrao = re.compile(
        r'CAP[ÍI]TULO\s+([\w\s]+?)\.\s*\n\n([^\n]+)',
        re.IGNORECASE
    )
    return padrao.sub(substituir_capitulo, texto)

def _expandir_numeros_e_abreviacoes(texto: str) -> str:
    print("   -> Expandindo números e abreviações...")

    def substituir_ordinal(match):
        try:
            numero = int(match.group(1))
            terminacao = match.group(2).lower()
            if terminacao in ('o', 'º'):
                return num2words(numero, lang='pt_BR', to='ordinal')
            elif terminacao in ('a', 'ª'):
                ordinal = num2words(numero, lang='pt_BR', to='ordinal')
                if ordinal.endswith('o'):
                    return ordinal[:-1] + 'a'
                return ordinal
            return match.group(0)
        except Exception:
            return match.group(0)

    texto = re.sub(r'\b(\d+)([oOaAºª])\b', substituir_ordinal, texto)

    def substituir_monetario(match):
        valor = match.group(1).replace('.', '')
        return f"{num2words(int(valor), lang='pt_BR')} reais"
    texto = re.sub(r'R\$\s*(\d[\d.]*)', substituir_monetario, texto)

    def substituir_cardinal(match):
        num_str = match.group(0)
        try:
            num_int = int(num_str)
            if 1900 <= num_int <= 2100: return num_str
            if len(num_str) > 6: return num_str
            return num2words(num_int, lang='pt_BR')
        except ValueError:
            return num_str
    texto = re.sub(r'\b\d+\b', substituir_cardinal, texto)
    return texto

def _limpeza_final(texto: str) -> str:
    print("   -> Realizando limpezas finais...")
    texto = re.sub(r'^\s*\d+\s*$', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'([.!?])\s*([—―–-])', r'\1\n\n\2', texto)
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
    return '\n\n'.join(paragrafos)

# ================== FUNÇÃO PRINCIPAL ==================

def formatar_texto_para_tts(texto_bruto: str) -> str:
    """
    Executa todas as etapas de limpeza e formatação para gerar
    texto perfeito para conversão TTS (sem símbolos como _ ou **).
    """
    print("Aplicando formatações avançadas ao texto...")

    texto = unicodedata.normalize('NFKC', texto_bruto)
    texto = _remover_lixo_textual(texto)
    texto = _remover_formatacao_markdown(texto)
    texto = _remontar_paragrafos(texto)
    texto = _formatar_capitulos_e_titulos(texto)
    texto = _expandir_numeros_e_abreviacoes(texto)
    texto = _limpeza_final(texto)

    print("✅ Formatação de texto concluída.")
    return texto.strip()
