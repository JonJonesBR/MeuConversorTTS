#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples para verificar se a função de unificação de áudio está funcionando corretamente.
"""

import os
import tempfile
from pathlib import Path

# Importar a função de unificação de áudio
from file_handlers import unificar_arquivos_audio


def testar_unificacao():
    """
    Testa a função de unificação de áudio com arquivos de teste.
    """
    print("🧪 Iniciando teste de unificação de áudio...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Simular arquivos MP3 reais criando arquivos com extensão .mp3 mas conteúdo fake
        # Na prática real, os arquivos seriam arquivos MP3 reais
        arquivos_teste = [
            str(temp_path / "teste_001.mp3"),
            str(temp_path / "teste_002.mp3"),
            str(temp_path / "teste_003.mp3")
        ]
        
        print("📝 Criando arquivos de áudio de teste...")
        for arquivo in arquivos_teste:
            # Criar arquivos MP3 com conteúdo fake (mas com cabeçalhos MP3 válidos)
            # Usando conteúdo que simula um pequeno arquivo MP3
            fake_mp3_content = b'\xFF\xFB\x90\xC4' + b'teste_audio_data' * 100 # Cabeçalho MP3 + dados
            with open(arquivo, 'wb') as f:
                f.write(fake_mp3_content)
        
        # Caminho para o arquivo de saída
        arquivo_saida = str(temp_path / "saida_unificada.mp3")
        
        print("🔄 Testando função de unificação de áudio...")
        sucesso = unificar_arquivos_audio(arquivos_teste, arquivo_saida)
        
        if sucesso:
            print("✅ Função de unificação de áudio funcionou corretamente!")
            
            # Verificar se o arquivo de saída existe e tem tamanho razoável
            saida_path = Path(arquivo_saida)
            if saida_path.exists() and saida_path.stat().st_size > 100:  # Mais de 100 bytes
                print(f"✅ Arquivo unificado criado com sucesso: {saida_path.name}")
                print(f"   Tamanho: {saida_path.stat().st_size} bytes")
                return True
            else:
                print(f"❌ Arquivo unificado não parece válido: {saida_path.name}")
                print(f"   Tamanho: {saida_path.stat().st_size} bytes")
                return False
        else:
            print("❌ Função de unificação de áudio falhou!")
            return False


if __name__ == "__main__":
    print("🚀 Teste Simples de Unificação de Áudio")
    print("=" * 50)
    
    sucesso = testar_unificacao()
    
    print("=" * 50)
    if sucesso:
        print("🎉 Teste concluído com sucesso!")
        print("✅ A função de unificação de áudio está funcionando corretamente!")
    else:
        print("💥 Teste falhou!")
        print("❌ Verifique se o pydub está instalado corretamente.")
    
    print("🏁 Fim do teste.")