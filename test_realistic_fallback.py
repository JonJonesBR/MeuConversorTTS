#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste realista para verificar se a função de fallback de unificação de áudio 
funciona corretamente com arquivos de áudio reais ou simulados.
"""
import os
import tempfile
from pathlib import Path

def testar_fallback_realistico():
    """Testa a função de fallback com arquivos de áudio simulados."""
    print("Testando funcao de fallback com arquivos realistas...")
    
    # Importar a função de fallback
    from file_handlers import _unificar_arquivos_audio_fallback
    
    # Criar arquivos temporários com conteúdo de áudio realista (headers MP3)
    print("\n1. Criando arquivos de áudio simulados...")
    
    # Criar conteúdo MP3 realista com headers válidos
    # Um header MP3 típico para começar o arquivo
    mp3_header = b'\xFF\xFB\x90\x00'  # Cabeçalho MP3 básico
    audio_content_1 = mp3_header + b"This is the first part of the audio content. " * 100  # Mais conteúdo
    audio_content_2 = mp3_header + b"This is the second part of the audio content. " * 100  # Mais conteúdo
    audio_content_3 = mp3_header + b"This is the third part of the audio content. " * 100  # Mais conteúdo
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file1:
        temp_file1.write(audio_content_1)
        temp_file_path1 = temp_file1.name
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file2:
        temp_file2.write(audio_content_2)
        temp_file_path2 = temp_file2.name
    
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file3:
        temp_file3.write(audio_content_3)
        temp_file_path3 = temp_file3.name
    
    lista_arquivos = [temp_file_path1, temp_file_path2, temp_file_path3]
    
    try:
        print(f"2. Testando com {len(lista_arquivos)} arquivos de áudio...")
        print(f"   Tamanhos: {[Path(f).stat().st_size for f in lista_arquivos]} bytes")
        
        resultado = _unificar_arquivos_audio_fallback(lista_arquivos, "saida_unificada.mp3")
        print(f"   Resultado: {resultado}")
        
        # Verificar se o arquivo de saída foi criado
        if Path("saida_unificada.mp3").exists():
            tamanho_saida = Path("saida_unificada.mp3").stat().st_size
            print(f"   Arquivo de saida criado com sucesso! Tamanho: {tamanho_saida} bytes")
            
            # Verificar se o tamanho é razoável (deve ser maior que cada arquivo individual)
            tamanho_1 = Path(lista_arquivos[0]).stat().st_size
            tamanho_2 = Path(lista_arquivos[1]).stat().st_size
            tamanho_3 = Path(lista_arquivos[2]).stat().st_size
            print(f"   Tamanhos originais: {tamanho_1}, {tamanho_2}, {tamanho_3} bytes")
            
            if tamanho_saida >= (tamanho_1 + tamanho_2 + tamanho_3) / 2:  # Aproximadamente
                print("   Aparentemente os arquivos foram concatenados corretamente")
            else:
                print("   O arquivo de saida parece muito pequeno em relacao aos originais")
        else:
            print("   ❌ Arquivo de saida NAO foi criado")
            
    finally:
        # Limpar os arquivos temporários
        for path in lista_arquivos:
            if Path(path).exists():
                Path(path).unlink()
        
        # Limpar o arquivo de saída se existir
        if Path("saida_unificada.mp3").exists():
            Path("saida_unificada.mp3").unlink()
    
    print("\nTeste realista concluido!")

if __name__ == "__main__":
    testar_fallback_realistico()