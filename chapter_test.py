#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para entender o problema com títulos de capítulo.
"""

import re

def test_chapter_regex():
    """Testa as expressões regulares para títulos de capítulo."""
    
    # Texto de exemplo que causa problema
    test_lines = [
        "Capítulo 1 - Introdução",
        "=======================",
        "Capítulo 2: O Menino que Sobreviveu",
        "capítulo 3 O vidro sumiu",
        "CAPITULO 4 A carta",
        "Capítulo Cinco - A fuga",
        "Capítulo Seis",
        "Capítulo VII - Algo em Romanos",
        "Capitulo oito, uma variação",
        "Capítulo 9—Travessão mal colado",
        "Capítulo 10— Travessão correto",
        "Outro texto aleatório sem capítulo",
        "CAPÍTULO ONZE O título em maiúsculas",
        "Capítulo doze: Em minúsculas",
        "Capitulo TREZE TÍTULO",
        "capítulo quatorze: título testado",
        "capítulo quinze título sem pontuação",
        "Capítulo dezesseis - título com hífen",
        "Capítulo DEZESSETE: outro título",
    ]
    
    # Padrões de detecção diferentes
    chapter_pattern1 = r'^\s*Cap[ií]tulo\s+(\d+|[IVXLCDM]+)\s*[—:-]?\s*(.*)$'
    chapter_pattern2 = r'^\s*CAP[IÍ]TULO\s+([A-ZÇÃÕÉÍÁÚÂÊÔ]+|\d+)\s*(.*)$'
    chapter_pattern3 = r'^\s*cap[ií]tulo\s+([a-zçãõéíáúâêô]+|\d+)\s*[:—-]?\s*(.*)$'
    
    print("Testando linhas:")
    for line in test_lines:
        print(f"-> {line}")
        
        # Testa padrão 1
        match1 = re.search(chapter_pattern1, line, re.MULTILINE | re.IGNORECASE)
        if match1:
            print(f"  Padrão 1 match: grupo1={repr(match1.group(1))}, grupo2={repr(match1.group(2))}")
        else:
            print(f"  Padrão 1: Nenhum match")
            
        # Testa padrão 2
        match2 = re.search(chapter_pattern2, line, re.MULTILINE | re.IGNORECASE)
        if match2:
            print(f"  Padrão 2 match: grupo1={repr(match2.group(1))}, grupo2={repr(match2.group(2))}")
        else:
            print(f"  Padrão 2: Nenhum match")
            
        # Testa padrão 3
        match3 = re.search(chapter_pattern3, line, re.MULTILINE | re.IGNORECASE)
        if match3:
            print(f"  Padrão 3 match: grupo1={repr(match3.group(1))}, grupo2={repr(match3.group(2))}")
        else:
            print(f"  Padrão 3: Nenhum match")
        print()

if __name__ == "__main__":
    test_chapter_regex()
