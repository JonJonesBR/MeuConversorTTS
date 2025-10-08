#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples para verificar se a funcao de unificacao de audio esta funcionando corretamente.
"""

import os
import tempfile
from pathlib import Path

# Importar a funcao de unificacao de audio
from file_handlers import unificar_arquivos_audio


def testar_unificacao():
    """
    Testa a funcao de unificacao de audio com arquivos de teste.
    """
    print("Iniciando teste de unificacao de audio...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Simular arquivos MP3 reais criando arquivos com extensao .mp3 mas conteudo fake
        # Na pratica real, os arquivos seriam arquivos MP3 reais
        arquivos_teste = [
            str(temp_path / "teste_001.mp3"),
            str(temp_path / "teste_002.mp3"),
            str(temp_path / "teste_003.mp3")
        ]
        
        print("Criando arquivos de audio de teste...")
        for arquivo in arquivos_teste:
            # Criar arquivos MP3 com conteudo fake (mas com cabecalhos MP3 validos)
            # Usando conteudo que simula um pequeno arquivo MP3
            fake_mp3_content = b'\xFF\xFB\x90\xC4' + b'teste_audio_data' * 100 # Cabecalho MP3 + dados
            with open(arquivo, 'wb') as f:
                f.write(fake_mp3_content)
        
        # Caminho para o arquivo de saida
        arquivo_saida = str(temp_path / "saida_unificada.mp3")
        
        print("Testando funcao de unificacao de audio...")
        sucesso = unificar_arquivos_audio(arquivos_teste, arquivo_saida)
        
        if sucesso:
            print("Funcao de unificacao de audio funcionou corretamente!")
            
            # Verificar se o arquivo de saida existe e tem tamanho razoavel
            saida_path = Path(arquivo_saida)
            if saida_path.exists() and saida_path.stat().st_size > 100:  # Mais de 100 bytes
                print(f"Arquivo unificado criado com sucesso: {saida_path.name}")
                print(f"   Tamanho: {saida_path.stat().st_size} bytes")
                return True
            else:
                print(f"Arquivo unificado nao parece valido: {saida_path.name}")
                print(f"   Tamanho: {saida_path.stat().st_size} bytes")
                return False
        else:
            print("Funcao de unificacao de audio falhou!")
            return False


if __name__ == "__main__":
    print("Teste Simples de Unificacao de Audio")
    print("=" * 50)
    
    sucesso = testar_unificacao()
    
    print("=" * 50)
    if sucesso:
        print("Teste concluido com sucesso!")
        print("A funcao de unificacao de audio esta funcionando corretamente!")
    else:
        print("Teste falhou!")
        print("Verifique se o pydub esta instalado corretamente.")
    
    print("Fim do teste.")