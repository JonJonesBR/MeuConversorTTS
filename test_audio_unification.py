#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se a função de unificação de áudio está funcionando corretamente.
"""

import os
import tempfile
from pathlib import Path

# Importar a função de unificação de áudio
from file_handlers import unificar_arquivos_audio


def criar_arquivo_audio_teste(caminho, duracao=1):
    """
    Cria um arquivo de áudio de teste (silêncio) usando pydub.
    """
    try:
        from pydub import AudioSegment
        import numpy as np
        
        # Cria um áudio de silêncio de 1 segundo (44.1kHz, 16-bit)
        sample_rate = 44100
        duration = duracao  # segundos
        samples = np.zeros(sample_rate * duration)
        
        # Cria um áudio com dados
        audio = AudioSegment(
            samples.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,  # 16-bit
            channels=1
        )
        
        audio.export(caminho, format="mp3")
        return True
    except ImportError:
        print("⚠️ pydub não está instalado. Tentando criar arquivo de teste de outra forma...")
        # Criar um arquivo vazio para testar a detecção de erro
        with open(caminho, 'w') as f:
            f.write("")
        return False
    except Exception as e:
        print(f"Erro ao criar arquivo de teste: {e}")
        return False


def testar_unificacao():
    """
    Testa a função de unificação de áudio com arquivos de teste.
    """
    print("🧪 Iniciando teste de unificação de áudio...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Criar arquivos de áudio de teste
        arquivos_teste = [
            str(temp_path / "teste_001.mp3"),
            str(temp_path / "teste_002.mp3"),
            str(temp_path / "teste_003.mp3")
        ]
        
        print("📝 Criando arquivos de áudio de teste...")
        for arquivo in arquivos_teste:
            sucesso = criar_arquivo_audio_teste(arquivo)
            if not sucesso:
                print("⚠️ Não foi possível criar arquivos de áudio de teste, mas testando mesmo assim...")
                # Criar arquivos vazios para testar a função
                Path(arquivo).write_bytes(b"fake_audio_data")
        
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
    print("🚀 Teste de Unificação de Áudio")
    print("=" * 40)
    
    sucesso = testar_unificacao()
    
    print("=" * 40)
    if sucesso:
        print("🎉 Teste concluído com sucesso!")
    else:
        print("💥 Teste falhou!")
    
    print("🏁 Fim do teste.")