# -*- coding: utf-8 -*-
import re
from typing import Dict, Pattern

# ================== CONFIGURAÇÕES GLOBAIS DE TTS E VOZES ==================
VOZES_PT_BR = [
    "pt-BR-ThalitaMultilingualNeural",  # Voz padrão
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
LIMITE_SEGUNDOS_DIVISAO = 43200 # 12 horas
RESOLUCOES_VIDEO = {
    '1': ('640x360', '360p'),
    '2': ('854x480', '480p'),
    '3': ('1280x720', '720p (HD)')
}


# ================== CONFIGURAÇÕES DE PROCESSAMENTO DE TEXTO ==================

# Correções para artefatos específicos de OCR ou extração.
CORRECOES_ESPECIFICAS: Dict[str, str] = {
    'observaçãoervadores': 'observadores',
    'observaçãoervando': 'observando',
    'observaçãoervava': 'observava',
    'gramasunnings': 'Grunnings',
    'Sr:;': 'Sr.',
    'St Dursley': 'Sr. Dursley',
    'Doutor Dursley': 'Senhor Dursley', # Adicionado
    'gramasande': 'grande',
    'gramas': 'grande', # Para casos como "gramasupinho"
    'gramasito': 'grito',
    'gramasitou': 'gritou',
    'gramasitava': 'gritava',
    'gramasitando': 'gritando',
    'gramasafite': 'grafite',
    'gramasosseiros': 'grosseiros',
    'gramasave': 'grave',
    'gramasupinho': 'grupinho',
    'gramasupo': 'grupo',
    'gramasaça': 'graça',
    'gramasamado': 'gramado',
    'gramasudado': 'grudado',
    'gramasudadas': 'grudadas',
    'gramasunhido': 'grunhido',
    'número mundo': 'no mundo', # Correções de substituição "no" -> "número"
    'número rosto': 'no rosto',
    'número céu': 'no céu',
    'número volante': 'no volante',
    'número nono': 'no nono',
    'número futuro': 'no futuro',
    'número nosso': 'no nosso',
    'número meio': 'no meio',
    'número entanto': 'no entanto',
    'número seu': 'no seu',
    'número ar': 'no ar',
    'número dia': 'no dia',
    'número chão': 'no chão',
    'número Brasil': 'no Brasil',
    'número caso': 'no caso',
    'número fundo': 'no fundo',
    'número final': 'no final',
    'número alto': 'no alto',
    'número momento': 'no momento',
    'número armário': 'no armário',
    'número primeiro': 'no primeiro',
    'número carrossel': 'no carrossel',
    'número desastre': 'no desastre',
    'número telhado': 'no telhado',
    'número trabalho': 'no trabalho',
    'número carro': 'no carro',
    'número alojamento': 'no alojamento',
    'número seu passatempo': 'no seu passatempo',
    'número banco': 'no banco',
    'número bico': 'no bico',
    'número colo': 'no colo',
    'número que': 'no que',
    'número banheiro': 'no banheiro',
    'número dormitório': 'no dormitório',
    'número qual': 'no qual',
    'número quintal': 'no quintal',
    'número interior': 'no interior',
    'número meio da multidão': 'no meio da multidão',
    'número sábado': 'no sábado',
    'número alçapão': 'no alçapão',
}


# Mapeamento de abreviações e siglas para sua forma extensa.
EXPANSOES_TEXTUAIS: Dict[Pattern, str] = {
    re.compile(r'\bSr\.', re.IGNORECASE): 'Senhor',
    re.compile(r'\bSra\.', re.IGNORECASE): 'Senhora',
    re.compile(r'\bSrta\.', re.IGNORECASE): 'Senhorita',
    re.compile(r'\bDr\.', re.IGNORECASE): 'Doutor',
    re.compile(r'\bProf\.', re.IGNORECASE): 'Professor',
    re.compile(r'\bProfa\.', re.IGNORECASE): 'Professora',
    re.compile(r'\bAv\.', re.IGNORECASE): 'Avenida',
    re.compile(r'\bn\.\s*o\.', re.IGNORECASE): 'número',
    re.compile(r'\bN[º°]\b', re.IGNORECASE): 'número',
    re.compile(r'\bEtc\.?', re.IGNORECASE): 'et cetera',
}

# Mapeamento para conversão de capítulos de numeral por extenso para arábico.
CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM: Dict[str, str] = {
    'UM': '1', 'DOIS': '2', 'TRÊS': '3', 'QUATRO': '4', 'CINCO': '5',
    'SEIS': '6', 'SETE': '7', 'OITO': '8', 'NOVE': '9', 'DEZ': '10',
    'ONZE': '11', 'DOZE': '12', 'TREZE': '13', 'CATORZE': '14', 'QUINZE': '15',
    'DEZESSEIS': '16', 'DEZESSETE': '17', 'DEZOITO': '18', 'DEZENOVE': '19', 'VINTE': '20'
}


