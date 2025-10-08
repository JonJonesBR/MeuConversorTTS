#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste final para verificar a correção do problema com 'ª' indevido.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from text_processing import formatar_texto_para_tts

# Teste com o caso específico mencionado pelo usuário
test_text = "A rua tem 10 a. de comprimento e a janela tem 12 a. de altura."

print("Teste final:")
print(f"Entrada: {repr(test_text)}")
formatted = formatar_texto_para_tts(test_text)
print(f"Saída:   {repr(formatted)}")
print(f"Legível: {formatted}")

# Teste com palavras que não deveriam ter 'ª'
test_text2 = "Rua 10 a. e janela 12 a. e a porta."
print("\nTeste 2:")
print(f"Entrada: {repr(test_text2)}")
formatted2 = formatar_texto_para_tts(test_text2)
print(f"Saída:   {repr(formatted2)}")
print(f"Legível: {formatted2}")
