#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se a função de fallback de unificação de áudio aprimorada está funcionando corretamente.
"""
import os
import tempfile
from pathlib import Path

def testar_fallback_aprimorado():
    """Testa a função de fallback aprimorado de unificação de audio."""
    print("Testando funcao de fallback aprimorado de unificacao de audio...")
    
    # Importar a função de fallback
    from file_handlers import _unificar_arquivos_audio_fallback
    
    # Testar com lista vazia
    print("\n1. Testando com lista vazia:")
    resultado = _unificar_arquivos_audio_fallback([], "saida_teste.mp3")
    print(f"   Resultado: {resultado} (esperado: False)")
    
    # Testar com um único arquivo (que não existe)
    print("\n2. Testando com um arquivo inexistente:")
    resultado = _unificar_arquivos_audio_fallback(["arquivo_inexistente.mp3"], "saida_teste.mp3")
    print(f"   Resultado: {resultado} (esperado: False)")
    
    # Testar com um único arquivo (usando um arquivo temporário real)
    print("\n3. Testando com um arquivo temporário real:")
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        temp_file.write(b"fake mp3 content")
        temp_file_path = temp_file.name
    
    try:
        resultado = _unificar_arquivos_audio_fallback([temp_file_path], "saida_teste.mp3")
        print(f"   Resultado: {resultado} (esperado: True)")
        
        # Verificar se o arquivo de saída foi criado
        if Path("saida_teste.mp3").exists():
            print("   Arquivo de saida criado com sucesso")
            Path("saida_teste.mp3").unlink()  # Limpar
        else:
            print("   Arquivo de saida NAO foi criado")
    finally:
        # Limpar o arquivo temporário
        if Path(temp_file_path).exists():
            Path(temp_file_path).unlink()
    
    # Testar com múltiplos arquivos (deve tentar concatenar)
    print("\n4. Testando com múltiplos arquivos:")
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file1:
        temp_file1.write(b"fake mp3 content 1")
        temp_file_path1 = temp_file1.name
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file2:
        temp_file2.write(b"fake mp3 content 2")
        temp_file_path2 = temp_file2.name
    
    try:
        resultado = _unificar_arquivos_audio_fallback([temp_file_path1, temp_file_path2], "saida_teste2.mp3")
        print(f"   Resultado: {resultado} (esperado: True ou False dependendo do ambiente)")
        
        # Verificar se o arquivo de saída foi criado
        if Path("saida_teste2.mp3").exists():
            print("   Arquivo de saida concatenado criado com sucesso")
            print(f"   Tamanho: {Path('saida_teste2.mp3').stat().st_size} bytes")
            Path("saida_teste2.mp3").unlink()  # Limpar
        else:
            print("   Arquivo de saida NAO foi criado")
    finally:
        # Limpar os arquivos temporários
        for path in [temp_file_path1, temp_file_path2]:
            if Path(path).exists():
                Path(path).unlink()
    
    print("\nTeste de fallback aprimorado concluido!")

if __name__ == "__main__":
    testar_fallback_aprimorado()