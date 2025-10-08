#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se a funcao de fallback de unificacao de audio esta funcionando corretamente.
"""

import os
import tempfile
from pathlib import Path

def testar_fallback():
    """Testa a funcao de fallback de unificacao de audio."""
    print("Testando funcao de fallback de unificacao de audio...")
    
    # Importar a funcao de fallback
    from file_handlers import _unificar_arquivos_audio_fallback
    
    # Testar com lista vazia
    print("\n1. Testando com lista vazia:")
    resultado = _unificar_arquivos_audio_fallback([], "saida_teste.mp3")
    print(f"   Resultado: {resultado} (esperado: False)")
    
    # Testar com um unico arquivo (que nao existe)
    print("\n2. Testando com um arquivo inexistente:")
    resultado = _unificar_arquivos_audio_fallback(["arquivo_inexistente.mp3"], "saida_teste.mp3")
    print(f"   Resultado: {resultado} (esperado: False)")
    
    # Testar com um unico arquivo (usando um arquivo temporario real)
    print("\n3. Testando com um arquivo temporario real:")
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        temp_file.write(b"fake mp3 content")
        temp_file_path = temp_file.name
    
    try:
        resultado = _unificar_arquivos_audio_fallback([temp_file_path], "saida_teste.mp3")
        print(f"   Resultado: {resultado} (esperado: True)")
        
        # Verificar se o arquivo de saida foi criado
        if Path("saida_teste.mp3").exists():
            print("   Arquivo de saida criado com sucesso")
            Path("saida_teste.mp3").unlink()  # Limpar
        else:
            print("   Arquivo de saida NAO foi criado")
    finally:
        # Limpar o arquivo temporario
        if Path(temp_file_path).exists():
            Path(temp_file_path).unlink()
    
    # Testar com multiplos arquivos (deve falhar no fallback)
    print("\n4. Testando com multiplos arquivos:")
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file1:
        temp_file1.write(b"fake mp3 content 1")
        temp_file_path1 = temp_file1.name
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file2:
        temp_file2.write(b"fake mp3 content 2")
        temp_file_path2 = temp_file2.name
    
    try:
        resultado = _unificar_arquivos_audio_fallback([temp_file_path1, temp_file_path2], "saida_teste2.mp3")
        print(f"   Resultado: {resultado} (esperado: False)")
    finally:
        # Limpar os arquivos temporarios
        for path in [temp_file_path1, temp_file_path2]:
            if Path(path).exists():
                Path(path).unlink()
    
    print("\nTeste de fallback concluido!")

if __name__ == "__main__":
    testar_fallback()