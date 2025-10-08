#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para verificar a correção do problema com 'ª' indevido.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from text_processing import formatar_texto_para_tts

# Teste com casos que deveriam ter 'ª' e casos que não deveriam
test_cases = [
    "Capítulo 1 - Introdução\n\nA rua tem 10 a. de comprimento.",  # Deveria ter 'ª'
    "A rua tem 10 a. de comprimento.",  # Deveria ter 'ª'
    "A rua tem 10 a. de comprimento e a janela.",  # Deveria ter 'ª' mas não 'a' em 'janela'
    "Rua 10 a. e janela 12 a.",  # Deveria ter 'ª' em ambos
    "A rua tem 10 a. de comprimento e a janela tem 12 a.",  # Deveria ter 'ª' em ambos
]

for i, test_text in enumerate(test_cases):
    print(f"Teste {i+1}:")
    print(f"Entrada: {repr(test_text)}")
    formatted = formatar_texto_para_tts(test_text)
    print(f"Saída:   {repr(formatted)}")
    print(f"Legível: {formatted}")
    print("-" * 50)
