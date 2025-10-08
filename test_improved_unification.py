#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se a função de unificação de áudio melhorada está funcionando corretamente.
"""
import os
import tempfile
from pathlib import Path

# Importar a função de unificação de áudio
from ffmpeg_utils import unificar_arquivos_audio_ffmpeg


def criar_arquivo_audio_teste(caminho, duracao=1):
    """
    Cria um arquivo de áudio de teste (silêncio) usando FFmpeg.
    """
    try:
        # Usar FFmpeg para criar um arquivo de áudio de silêncio
        import subprocess
        comando = [
            "ffmpeg",
            "-y",  # Sobrescrever arquivo se existir
            "-f", "lavfi",
            "-i", f"silence=d={duracao}",  # Gerar silêncio por 'duracao' segundos
            "-c:a", "mp3",
            "-b:a", "64k",
            caminho
        ]
        resultado = subprocess.run(comando, capture_output=True, text=True)
        return resultado.returncode == 0
    except Exception as e:
        print(f"Erro ao criar arquivo de teste com FFmpeg: {e}")
        return False


def testar_unificacao():
    """
    Testa a função de unificação de áudio com arquivos de teste.
    """
    print("[TEST] Iniciando teste de unificacao de audio melhorada...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Criar arquivos de áudio de teste
        arquivos_teste = [
            str(temp_path / "teste_001.mp3"),
            str(temp_path / "teste_002.mp3"),
            str(temp_path / "teste_003.mp3")
        ]
        
        print("[INFO] Criando arquivos de audio de teste...")
        for arquivo in arquivos_teste:
            sucesso = criar_arquivo_audio_teste(arquivo)
            if not sucesso:
                print(f"[WARN] Nao foi possivel criar arquivo de teste: {arquivo}")
                # Criar um arquivo vazio para testar a função de qualquer forma
                Path(arquivo).write_bytes(b"fake_audio_data")
        
        # Caminho para o arquivo de saída
        arquivo_saida = str(temp_path / "saida_unificada.mp3")
        
        print("[INFO] Testando funcao de unificacao de audio melhorada...")
        sucesso = unificar_arquivos_audio_ffmpeg(arquivos_teste, arquivo_saida)
        
        if sucesso:
            print("[SUCCESS] Funcao de unificacao de audio funcionou corretamente!")
            
            # Verificar se o arquivo de saída existe e tem tamanho razoável
            saida_path = Path(arquivo_saida)
            if saida_path.exists() and saida_path.stat().st_size > 100:  # Mais de 100 bytes
                print(f"[SUCCESS] Arquivo unificado criado com sucesso: {saida_path.name}")
                print(f"   Tamanho: {saida_path.stat().st_size} bytes")
                return True
            else:
                print(f"[ERROR] Arquivo unificado nao parece valido: {saida_path.name}")
                print(f"   Tamanho: {saida_path.stat().st_size} bytes")
                return False
        else:
            print("[ERROR] Funcao de unificacao de audio falhou!")
            return False


if __name__ == "__main__":
    print("Teste de Unificacao de Audio Melhorada")
    print("=" * 40)
    
    sucesso = testar_unificacao()
    
    print("=" * 40)
    if sucesso:
        print("Teste concluido com sucesso!")
    else:
        print("Teste falhou!")
    
    print("Fim do teste.")