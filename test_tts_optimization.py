#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para validar as otimizações do text_processing.py
para melhorar a qualidade do texto para TTS.
"""

import sys
import os
import io

# Redefinir stdout para lidar com codificação UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from text_processing import formatar_texto_para_tts

def test_tts_optimizations():
    """Testa as otimizações implementadas no pipeline TTS."""
    
    # Teste com texto de exemplo que contém elementos comuns em livros
    test_text = """
    Este é um exemplo de texto para teste. Ele contém vários elementos
    que precisam ser otimizados para leitura por TTS.
    
    Capítulo 1 - Introdução
    =======================
    
    Neste capítulo vamos discutir os conceitos básicos.
    Por exemplo, o número 42 é importante. Também temos números como 100, 200 e 300.
    
    A seguir, apresentamos alguns dados: 123, 456, 789.
    E também alguns valores como 1.000, 2.500, 3.750.
    
    Sr. João e Sra. Maria foram ao mercado. Eles compraram algo.
    
    "Isso é um exemplo de citação", disse ele.
    
    O texto precisa ser formatado para que o TTS consiga ler de forma natural.
    Pode haver problemas com pontuação, espaçamento e numeração.
    
    Capítulo 2: O Menino que Sobreviveu
    ===================================
    
    Este é o segundo capítulo do livro.
    """

    print("Texto original:")
    print("-" * 50)
    print(test_text)
    print("-" * 50)
    
    # Aplicar o pipeline de formatação para TTS
    formatted_text = formatar_texto_para_tts(test_text)
    
    print("\nTexto formatado para TTS:")
    print("-" * 50)
    print(formatted_text)
    print("-" * 50)
    
    # Verifica se as otimizações estão funcionando
    print("\nAnálise das otimizações:")
    print("-" * 30)
    
    # Verificar se houve expansão de números
    if "quarenta e dois" in formatted_text.lower():
        print("[OK] Números foram expandidos corretamente")
    else:
        print("[ERRO] Números não foram expandidos")
        
    # Verificar se houve expansão de abreviações
    if "Senhor" in formatted_text:
        print("[OK] Abreviações foram expandidas corretamente")
    else:
        print("[ERRO] Abreviações não foram expandidas")
        
    # Verificar se há pausas apropriadas
    if ".\n\n" in formatted_text:
        print("[OK] Pausas foram adicionadas após pontos")
    else:
        print("[ERRO] Pausas não foram adicionadas após pontos")
        
    print("\nTeste concluído!")

if __name__ == "__main__":
    test_tts_optimizations()