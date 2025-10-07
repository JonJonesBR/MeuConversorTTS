#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples para verificar os problemas reais.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from text_processing import formatar_texto_para_tts

# Teste com um trecho mais simples que mostra os problemas
test_text = "Capítulo 1 - Introdução\n\nQuatro gatos estavam na casa."

print("Texto original:")
print(repr(test_text))
print()

formatted = formatar_texto_para_tts(test_text)

print("Texto formatado:")
print(repr(formatted))
print()

print("Texto formatado legível:")
print(formatted)