# -*- coding: utf-8 -*-
"""
Módulo de limpeza e formatação de texto para leitura TTS.
Contém o pipeline principal para transformar texto bruto em texto limpo.
"""
import re
import unicodedata
from num2words import num2words
import logging

# Importa as configurações centralizadas
import config

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ================== FUNÇÕES DE LIMPEZA E NORMALIZAÇÃO ==================

def _remover_avisos_intrusivos(texto: str) -> str:
    """Remove padrões de lixo textual definidos em config.py."""
    logger.info("Removendo avisos intrusivos e lixo textual...")
    for padrao in config.PADROES_LIXO_INTRUSIVO:
        texto = padrao.sub("", texto)
    return texto

def _corrigir_artefatos_especificos(texto: str) -> str:
    """Corrige erros de OCR/conversão com base no dicionário em config.py."""
    logger.info("Corrigindo artefatos de texto específicos...")
    for erro, correcao in config.CORRECOES_ESPECIFICAS.items():
        texto = texto.replace(erro, correcao)
    return texto

def _remover_resquicios_paginacao(texto: str) -> str:
    """Remove palavras de número de página que ficaram no meio do texto."""
    logger.info("Removendo resquícios de paginação...")
    # Cria um padrão regex com todos os números por extenso do dicionário de capítulos
    numeros_por_extenso = '|'.join(config.CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.keys())
    # Padrão para encontrar um número (dígito ou por extenso) no final de uma linha, seguido de ponto
    padrao = re.compile(rf'(\b(?:{numeros_por_extenso})\b|[0-9]+)\s*\.\s*$', re.IGNORECASE | re.MULTILINE)
    texto = padrao.sub('', texto)
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
    # Remove marcações de formatação como *, _
    texto = re.sub(r'[_*]', '', texto)
    return texto

def _remontar_paragrafos(texto: str) -> str:
    """Corrige quebras de linha indevidas no meio dos parágrafos."""
    logger.info("Remontando parágrafos...")
    # Une palavras separadas por hífen e quebra de linha
    texto = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)
    
    linhas = texto.split('\n')
    paragrafos_remontados = []
    paragrafo_atual = ""
    for linha in linhas:
        linha_strip = linha.strip()
        if not linha_strip:
            if paragrafo_atual:
                paragrafos_remontados.append(paragrafo_atual)
                paragrafo_atual = ""
        else:
            # Concatena com espaço se o parágrafo atual não terminar com pontuação final
            if paragrafo_atual and not paragrafo_atual.endswith(('.', '!', '?', '"')):
                 paragrafo_atual += " " + linha_strip
            else:
                 paragrafo_atual += linha_strip # Inicia ou continua após pontuação
    if paragrafo_atual:
        paragrafos_remontados.append(paragrafo_atual)
        
    return "\n\n".join(paragrafos_remontados)

# ================== FUNÇÕES DE EXPANSÃO PARA TTS ==================

def _formatar_capitulos(texto: str) -> str:
    """Padroniza a formatação de títulos de capítulos."""
    logger.info("Formatando títulos de capítulos...")

    def substituir_capitulo(match: re.Match) -> str:
        prefixo = "CAPÍTULO" # Padrão
        numero_str = match.group(1).strip().upper()
        titulo_opcional = match.group(2)
        
        titulo = titulo_opcional.strip().rstrip(' .') if titulo_opcional else ""
        numero_final = config.CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(numero_str, numero_str)

        if titulo:
            return f"\n\n{prefixo} {numero_final}. {titulo}.\n\n"
        return f"\n\n{prefixo} {numero_final}.\n\n"

    padrao = re.compile(
        r'^\s*(?:cap[íi]tulo)\s+([\d\w\s]+)\s*[-–—.]*\s*(?:\n\s*(.*?)\s*\.?)?',
        re.IGNORECASE | re.MULTILINE
    )
    return padrao.sub(substituir_capitulo, texto)

def _expandir_abreviacoes(texto: str) -> str:
    """Expande abreviações para uma leitura natural."""
    logger.info("Expandindo abreviações...")
    for padrao, substituicao in config.EXPANSOES_TEXTUAIS.items():
        texto = padrao.sub(substituicao, texto)
    return texto

def _expandir_numeros(texto: str) -> str:
    """Converte números em texto por extenso."""
    logger.info("Expandindo números...")

    def cardinal(match: re.Match) -> str:
        num_str = match.group(0)
        try:
            num_int = int(num_str)
            if 1900 <= num_int <= 2100 or len(num_str) > 4:
                return num_str
            return num2words(num_int, lang='pt_BR')
        except ValueError:
            return num_str
    texto = re.sub(r'\b\d+\b', cardinal, texto)
    return texto

def _limpeza_final(texto: str) -> str:
    """Aplica ajustes finais de espaçamento e pontuação."""
    logger.info("Realizando limpeza final...")
    # Remove espaço antes de pontuação
    texto = re.sub(r'\s+([,.!?;:])', r'\1', texto)
    # Garante espaço depois de pontuação
    texto = re.sub(r'([,.!?;:])(?=\w)', r'\1 ', texto)
    # Remove espaços duplos
    texto = re.sub(r' {2,}', ' ', texto)
    # Normaliza quebras de linha
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()

# ================== FUNÇÃO PRINCIPAL ==================

def formatar_texto_para_tts(texto_bruto: str) -> str:
    """
    Executa o pipeline completo de limpeza e formatação para preparar o texto para TTS.
    A ordem das funções é crucial para o resultado final.
    """
    logger.info("Iniciando pipeline completo de formatação para TTS...")
    
    if not texto_bruto or not isinstance(texto_bruto, str):
        logger.warning("Texto de entrada inválido ou vazio. Retornando string vazia.")
        return ""

    # Pipeline de processamento
    texto = _remover_avisos_intrusivos(texto_bruto)
    texto = _remover_resquicios_paginacao(texto)
    texto = _corrigir_artefatos_especificos(texto)
    texto = _normalizar_caracteres_e_pontuacao(texto)
    texto = _remontar_paragrafos(texto)
    texto = _expandir_abreviacoes(texto)
    texto = _expandir_numeros(texto)      
    texto = _formatar_capitulos(texto)
    texto = _limpeza_final(texto)

    logger.info("Processamento para TTS concluído.")
    return texto
