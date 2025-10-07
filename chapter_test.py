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
        "=================================="
    ]
    
    print("Testando expressões regulares para títulos de capítulo:")
    print("=" * 60)
    
    # Teste com a regex atual
    chapter_pattern1 = r'^\s*-+\s*CAPÍTULO\s+(.+?)\s*-+\s*$'
    chapter_pattern2 = r'^\s*CAPÍTULO\s*(\w+)\s*[-:]\s*(.+)$'
    chapter_pattern3 = r'^\s*CAPÍTULO\s*(\w+)\s+(.+)$'
    
    for i, line in enumerate(test_lines):
        print(f"Linha {i+1}: {repr(line)}")
        
        # Testa padrão 1
        match1 = re.search(chapter_pattern1, line, re.MULTILINE | re.IGNORECASE)
        if match1:
            print(f"  Padrão 1 match: {repr(match1.group(1))}")
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