#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar a remoção de caracteres de escape indesejados (\\- e \\.) do texto TTS
"""

import text_processing

def test_escape_chars():
    """Testa a remoção de caracteres de escape indesejados"""
    
    # Teste com texto contendo caracteres problemáticos
    texto_teste = "Este é um texto de teste com \\-. Este é outro \\.. E aqui temos \\- novamente."
    
    print("Texto original:")
    print(repr(texto_teste))
    print("\nTexto original (formatado):")
    print(texto_teste)
    
    # Processa o texto
    texto_formatado = text_processing.formatar_texto_para_tts(texto_teste)
    
    print("\nTexto após formatação:")
    print(repr(texto_formatado))
    print("\nTexto após formatação (formatado):")
    print(texto_formatado)
    
    # Verifica se os caracteres problemáticos ainda estão presentes
    if '\\-' in texto_formatado:
        print("\n[WARNING] AINDA EXISTEM caracteres '\\-' no texto após formatação!")
    else:
        print("\n[SUCCESS] Caracteres '\\-' foram removidos com sucesso!")
        
    if '\\.' in texto_formatado:
        print("[WARNING] AINDA EXISTEM caracteres '\\.' no texto após formatação!")
    else:
        print("[SUCCESS] Caracteres '\\.' foram removidos com sucesso!")

def test_normal_text():
    """Testa com texto normal para garantir que não quebramos nada"""
    
    texto_normal = "Este é um texto normal com hífens verdadeiros como este - e pontos normais."
    
    print("\n" + "="*60)
    print("TESTE COM TEXTO NORMAL:")
    print("Texto original:")
    print(repr(texto_normal))
    
    texto_formatado = text_processing.formatar_texto_para_tts(texto_normal)
    
    print("\nTexto após formatação:")
    print(repr(texto_formatado))
    
    print("\nTexto formatado (legível):")
    print(texto_formatado)

if __name__ == "__main__":
    print("Testando remoção de caracteres de escape indesejados...")
    test_escape_chars()
    test_normal_text()
    print("\nTeste concluído!")