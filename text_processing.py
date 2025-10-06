# -*- coding: utf-8 -*-
"""
Script aprimorado de limpeza e formatação de texto para leitura TTS.

Este script processa textos brutos, especialmente de e-books, para gerar uma
saída otimizada para sintetizadores de voz (Text-to-Speech). O objetivo é
criar uma narração o mais natural e fluida possível, tratando desde a
limpeza de artefatos de digitalização até a expansão de abreviações e
números para uma pronúncia correta.
"""
import re
import unicodedata
from num2words import num2words
from typing import Dict, List, Pattern
import logging

# Importa as configurações do nosso arquivo config.py
import config

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================== FUNÇÕES DE LIMPEZA E NORMALIZAÇÃO ==================

def _remover_lixo_textual_intrusivo(texto: str) -> str:
    """Remove avisos de copyright e outras anotações que interrompem o texto."""
    logger.info("Removendo lixo textual intrusivo (avisos de copyright, etc.)...")
    padroes_lixo = [
        r"Esse livro é protegido por direitos autorais.*?(?=em Duda mas não conseguiu)", # Específico para o corte problemático
        r"www\.\s*portaldetonando\.\s*cjb\.\s*net.*",
        r"\bCopyright\b.*",
        r"Distribuído gratuitamente.*",
        r"Detonando Home Page",
        r"\[\d+\]" # Remove citações como [1], [2], etc.
    ]
    for padrao in padroes_lixo:
        texto = re.sub(padrao, "", texto, flags=re.IGNORECASE | re.MULTILINE)
    return texto

def _corrigir_artefatos_especificos(texto: str) -> str:
    """Corrige erros de extração de texto específicos e conhecidos."""
    logger.info("Corrigindo artefatos de texto específicos...")
    for erro, correcao in config.CORRECOES_ESPECIFICAS.items():
        texto = texto.replace(erro, correcao)
    return texto

def _normalizar_caracteres_e_pontuacao(texto: str) -> str:
    """Normaliza caracteres Unicode, aspas, travessões e pontuação."""
    logger.info("Normalizando caracteres e pontuação...")
    texto = unicodedata.normalize('NFKC', texto)
    substituicoes = {
        '[“”«»]': '"',
        "[‘’]": "'",
        '[–—―‐‑]': '—',
        '…': '...',
        ';': ',',
    }
    for padrao, sub in substituicoes.items():
        texto = re.sub(padrao, sub, texto)
    texto = re.sub(r'\s*—\s*', ' — ', texto)
    return texto

def _remontar_paragrafos(texto: str) -> str:
    """Corrige quebras de linha indevidas no meio dos parágrafos."""
    logger.info("Remontando parágrafos...")
    # Remove hifenização no final da linha
    texto = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)
    linhas = texto.split('\n')
    paragrafos_remontados = []
    paragrafo_atual = ""
    for linha in linhas:
        linha = linha.strip()
        # Se a linha estiver vazia, encerra o parágrafo atual.
        if not linha:
            if paragrafo_atual:
                paragrafos_remontados.append(paragrafo_atual)
                paragrafo_atual = ""
        # Se a linha não começar com maiúscula, provavelmente é continuação.
        elif paragrafo_atual and not linha[0].isupper():
            paragrafo_atual += " " + linha
        # Se a linha anterior termina sem pontuação final, une.
        elif paragrafo_atual and paragrafo_atual[-1] not in ".!?\"'":
            paragrafo_atual += " " + linha
        # Caso contrário, começa um novo parágrafo
        else:
            if paragrafo_atual:
                paragrafos_remontados.append(paragrafo_atual)
            paragrafo_atual = linha

    if paragrafo_atual:
        paragrafos_remontados.append(paragrafo_atual)
    return "\n\n".join(paragrafos_remontados)

def _remover_resquicios_paginacao(texto: str) -> str:
    """Remove números de página que ficaram no meio do texto."""
    logger.info("Removendo resquícios de paginação...")
    # Remove números sozinhos que podem ser páginas, especialmente após pontuação.
    texto = re.sub(r'(?<=[.!?])\s*\b(\d+)\b\s*(?=[A-Z])', ' ', texto)
    # Remove números por extenso que ficaram no texto
    numeros_extenso = '|'.join(config.CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.keys())
    texto = re.sub(rf'\b({numeros_extenso})\b\s*\.', '', texto, flags=re.IGNORECASE)
    return texto

# ================== FUNÇÕES DE EXPANSÃO PARA TTS ==================

def _formatar_capitulos(texto: str) -> str:
    """Padroniza a formatação de títulos de capítulos para uma leitura clara."""
    logger.info("Formatando títulos de capítulos...")

    def substituir_capitulo(match: re.Match) -> str:
        prefixo = "CAPÍTULO"
        numero_str = match.group(2).strip().upper() if match.group(2) else ""
        titulo_opcional = match.group(3) if len(match.groups()) > 2 else None
        
        titulo = titulo_opcional.strip().rstrip(' ._*-') if titulo_opcional else ""
        numero_final = config.CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(numero_str, numero_str)

        if titulo:
            return f"\n\n{prefixo} {numero_final}. {titulo}.\n\n"
        return f"\n\n{prefixo} {numero_final}.\n\n"

    # Padrão mais flexível para capturar diferentes formatações de título
    padrao = re.compile(
        r'^\s*[-_]*\s*(cap[íi]tulo)\s+([\d\w\s]+)\s*[-–—._]*\s*(?:\n\s*\n?\s*_*([^*_].*?)\*?_*)?',
        re.IGNORECASE | re.MULTILINE
    )
    return padrao.sub(substituir_capitulo, texto)


def _expandir_abreviacoes(texto: str) -> str:
    """Expande abreviações e siglas para uma leitura natural."""
    logger.info("Expandindo abreviações...")
    for padrao, substituicao in config.EXPANSOES_TEXTUAIS.items():
        texto = padrao.sub(substituicao, texto)
    return texto

def _expandir_numeros(texto: str) -> str:
    """Converte números em texto por extenso, tratando casos especiais."""
    logger.info("Expandindo números...")

    def ordinal(match: re.Match) -> str:
        try:
            n = int(match.group(1))
            sufixo = match.group(2).lower()
            if sufixo in ('o', 'º'):
                return num2words(n, lang='pt_BR', to='ordinal')
            elif sufixo in ('a', 'ª'):
                ordinal_masc = num2words(n, lang='pt_BR', to='ordinal')
                return ordinal_masc[:-1] + 'a' if ordinal_masc.endswith('o') else ordinal_masc
        except (ValueError, IndexError):
            return match.group(0)
        return match.group(0)
    texto = re.sub(r'\b(\d+)([oOaAºª])\b', ordinal, texto)
    
    def cardinal(match: re.Match) -> str:
        num_str = match.group(0)
        try:
            num_int = int(num_str)
            # Não expande anos ou números muito grandes
            if 1900 <= num_int <= 2100 or len(num_str) > 6:
                return num_str
            return num2words(num_int, lang='pt_BR')
        except ValueError:
            return num_str
    texto = re.sub(r'\b\d+\b', cardinal, texto)
    return texto

def _limpeza_final(texto: str) -> str:
    """Aplica ajustes finais de espaçamento e pontuação para fluidez."""
    logger.info("Realizando limpeza final e ajustes de ritmo...")
    if not texto:
        return texto
        
    # Garante espaço após pontuação final e remove espaços antes.
    texto = re.sub(r'\s+([,.!?;:])', r'\1', texto)
    texto = re.sub(r'([,.!?;:])(?=\w)', r'\1 ', texto)
    # Remove espaços múltiplos
    texto = re.sub(r' {2,}', ' ', texto)
    # Normaliza quebras de parágrafo
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    # Remove letras maiúsculas sozinhas com um ponto. Ex: "O."
    texto = re.sub(r'\b([A-Z])\.\s', r'\1 ', texto)

    return texto.strip()

# ================== FUNÇÃO PRINCIPAL ==================

def formatar_texto_para_tts(texto_bruto: str) -> str:
    """
    Executa um pipeline completo de limpeza e formatação para preparar o texto para TTS.
    """
    logger.info("Iniciando pipeline completo de formatação para TTS...")
    
    if not texto_bruto or not isinstance(texto_bruto, str):
        logger.warning("Texto de entrada inválido ou vazio. Retornando string vazia.")
        return ""

    try:
        # Ordem de execução otimizada
        texto = _remover_lixo_textual_intrusivo(texto_bruto)
        texto = _corrigir_artefatos_especificos(texto)
        texto = _remontar_paragrafos(texto)
        texto = _normalizar_caracteres_e_pontuacao(texto)
        texto = _remover_resquicios_paginacao(texto)
        texto = _expandir_abreviacoes(texto)
        texto = _expandir_numeros(texto)      
        texto = _formatar_capitulos(texto)
        texto = _limpeza_final(texto)

        logger.info("Processamento para TTS concluído.")
        return texto
    except Exception as e:
        logger.error(f"Erro no pipeline de formatação: {e}")
        return texto_bruto

