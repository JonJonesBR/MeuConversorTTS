# -*- coding: utf-8 -*-
"""
Configurações do Conversor TTS.
Atenção: correções específicas perigosas foram desativadas por padrão.
"""

from __future__ import annotations

import re
from typing import Dict, Pattern

# ================== CONFIGURAÇÕES GLOBAIS DE TTS E VOZES ==================
VOZES_PT_BR = [
    "pt-BR-ThalitaMultilingualNeural",  # Voz padrão
    "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural",
]
MAX_TTS_TENTATIVAS = 3
LIMITE_CARACTERES_CHUNK_TTS = 7500
LOTE_MAXIMO_TAREFAS_CONCORRENTES = 8

# ================== CORREÇÕES ESPECÍFICAS (DESATIVADAS) ==================
HABILITAR_CORRECOES_ESPECIFICAS = False  # ⚠️ Ative apenas para casos pontuais
CORRECOES_ESPECIFICAS: Dict[str, str] = {}
if HABILITAR_CORRECOES_ESPECIFICAS:
    CORRECOES_ESPECIFICAS.update({
        # Exemplo:
        # 'gramasunnings': 'Grunnings',
    })

# ================== EXPANSÕES TEXTUAIS (USO CONTROLADO) ==================
# Mantidas apenas entradas inofensivas. Expansões como 'nº'→'número' devem ser feitas
# no pipeline dedicado (text_processing), com lookahead para dígitos, e não aqui.
EXPANSOES_TEXTUAIS: Dict[Pattern[str], str] = {
    re.compile(r'\bEtc\.?', re.IGNORECASE): 'et cetera',
}
# ================== MAPA DE CAPÍTULOS POR EXTENSO → ALGARISMOS ==================
CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM: Dict[str, str] = {
    'UM': '1', 'DOIS': '2', 'TRÊS': '3', 'TRES': '3', 'QUATRO': '4', 'CINCO': '5',
    'SEIS': '6', 'SETE': '7', 'OITO': '8', 'NOVE': '9', 'DEZ': '10',
    'ONZE': '11', 'DOZE': '12', 'TREZE': '13', 'CATORZE': '14', 'QUINZE': '15',
    'DEZESSEIS': '16', 'DEZESSETE': '17', 'DEZOITO': '18', 'DEZENOVE': '19', 'VINTE': '20',
}
