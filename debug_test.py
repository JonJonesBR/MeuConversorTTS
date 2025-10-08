#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug para identificar problemas no texto processado.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from text_processing import formatar_texto_para_tts
import re

def debug_chapter_formatting():
    """Debuga especificamente o problema com os títulos de capítulo."""
    
    # Texto de exemplo
    test_text = """
    CAPÍTULO UM O MENINO QUE SOBREVIVEU
    Capítulo 2: O vidro sumiu
    Capítulo Três - As cartas de ninguém
    Outro conteúdo irrelevante
    """
    
    # Padrões que estavam sendo usados (para comparar)
    chapter_pattern1 = r'^\s*Cap[ií]tulo\s+(\d+|[IVXLCDM]+)\s*[—:-]?\s*(.*)$'
    chapter_pattern2 = r'^\s*CAP[IÍ]TULO\s+([A-ZÇÃÕÉÍÁÚÂÊÔ]+|\d+)\s*(.*)$'
    chapter_pattern3 = r'^\s*cap[ií]tulo\s+([a-zçãõéíáúâêô]+|\d+)\s*[:—-]?\s*(.*)$'
    
    print("=== DEBUG CAPÍTULOS ===")
    print("Texto original:")
    print(test_text)
    
    print("\nTestando regex anteriores...")
    for pattern in [chapter_pattern1, chapter_pattern2, chapter_pattern3]:
        print(f"\nUsando padrão: {pattern}")
        for line in test_text.splitlines():
            m = re.search(pattern, line, re.MULTILINE | re.IGNORECASE)
            if m:
                print(f"Match: linha='{line}' -> grupos: {m.groups()}")
    
    # Aplicar o pipeline de formatação para TTS
    formatted_text = formatar_texto_para_tts(test_text)
    
    print("\nTexto formatado:")
    print("-" * 50)
    print(repr(formatted_text))  # Mostra os caracteres especiais
    print("-" * 50)
    
    print("\nTexto formatado legível:")
    print("-" * 50)
    print(formatted_text)
    print("-" * 50)

if __name__ == "__main__":
    debug_chapter_formatting()
