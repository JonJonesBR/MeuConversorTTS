# -*- coding: utf-8 -*-
"""
Módulo de configurações centralizadas para o MeuConversorTTS.
"""
import re

# ================== CONFIGURAÇÕES GLOBAIS DE TTS E VOZES ==================
VOZES_PT_BR = [
    "pt-BR-ThalitaMultilingualNeural",
    "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural"
]
MAX_TTS_TENTATIVAS = 3
LIMITE_CARACTERES_CHUNK_TTS = 7500
LOTE_MAXIMO_TAREFAS_CONCORRENTES = 8

# ================== CONFIGURAÇÕES DE PROCESSAMENTO DE ARQUIVO ==================
ENCODINGS_TENTATIVAS = ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252']

# ================== CONFIGURAÇÕES DE VÍDEO E FFMPEG ==================
FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"
FFPLAY_BIN = "ffplay"
LIMITE_SEGUNDOS_DIVISAO = 43200
RESOLUCOES_VIDEO = {
    '1': ('640x360', '360p'),
    '2': ('854x480', '480p'),
    '3': ('1280x720', '720p (HD)')
}

# ================== REGRAS DE LIMPEZA E FORMATAÇÃO DE TEXTO ==================

# 1. Padrões para remover lixo textual repetitivo (avisos de copyright, etc.)
PADROES_LIXO_INTRUSIVO = [
    re.compile(r'.*detonando home page.*', re.IGNORECASE | re.MULTILINE),
    re.compile(r"Esse livro é protegido.*", re.IGNORECASE | re.MULTILINE),
    re.compile(r"www\.\s*portaldetonando\.\s*cjb\.\s*net.*", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\bCopyright\b.*", re.IGNORECASE | re.MULTILINE),
    re.compile(r"Distribuído gratuitamente.*", re.IGNORECASE | re.MULTILINE),
]

# 2. Correções para erros específicos de OCR ou conversão
CORRECOES_ESPECIFICAS = {
    'observaçãoervadores': 'observadores',
    'observaçãoervando': 'observando',
    'observaçãoervava': 'observava',
    'gramasunnings': 'Grunnings',
    'gramasande': 'grande',
    'gramasito': 'grito',
    'gramasitou': 'gritou',
    'gramasifinória': 'Grifinória',
    'gramasingotes': 'Gringotes',
    'Doutor Dursley': 'Senhor Dursley',
    'St Dursley': 'Senhor Dursley',
    'Sr:;': 'Sr.',
    # Adicione outras correções comuns aqui
}

# 3. Mapeamento de abreviações para sua forma extensa
EXPANSOES_TEXTUAIS = {
    # Títulos e Pessoas
    re.compile(r'\bSr\.', re.IGNORECASE): 'Senhor',
    re.compile(r'\bSra\.', re.IGNORECASE): 'Senhora',
    re.compile(r'\bSrta\.', re.IGNORECASE): 'Senhorita',
    re.compile(r'\bDr\.', re.IGNORECASE): 'Doutor',
    re.compile(r'\bDra\.', re.IGNORECASE): 'Doutora',
    re.compile(r'\bProf\.', re.IGNORECASE): 'Professor',
    re.compile(r'\bProfa\.', re.IGNORECASE): 'Professora',
    # Endereços
    re.compile(r'\bAv\.', re.IGNORECASE): 'Avenida',
    re.compile(r'\bR\.', re.IGNORECASE): 'Rua',
    re.compile(r'\bn\.\s*o\.', re.IGNORECASE): 'número',
    re.compile(r'\bN[º°]\b', re.IGNORECASE): 'número',
    # Unidades e Diversos
    re.compile(r'\bKm/h\b', re.IGNORECASE): 'quilômetros por hora',
    re.compile(r'\bEtc\.?', re.IGNORECASE): 'et cetera',
}

# 4. Mapeamento de capítulos por extenso para numeral
CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM = {
    'UM': '1', 'DOIS': '2', 'TRÊS': '3', 'QUATRO': '4', 'CINCO': '5',
    'SEIS': '6', 'SETE': '7', 'OITO': '8', 'NOVE': '9', 'DEZ': '10',
    'ONZE': '11', 'DOZE': '12', 'TREZE': '13', 'CATORZE': '14', 'QUATORZE': '14',
    'QUINZE': '15', 'DEZESSEIS': '16', 'DEZESSETE': '17'
}
