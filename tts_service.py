# -*- coding: utf-8 -*-
"""
Módulo de serviço para a conversão de texto em fala (TTS).
Encapsula a lógica de divisão de texto e a comunicação com a
biblioteca edge_tts.
"""
import asyncio
import re
from pathlib import Path

import edge_tts

# Importa de nossos outros módulos
import config
import shared_state

def dividir_texto_para_tts(texto_processado: str) -> list[str]:
    """
    Divide o texto em partes menores para TTS, respeitando parágrafos e frases
    para manter um fluxo mais natural e evitar erros na API.
    """
    print(f"⚙️ Dividindo texto em chunks de até {config.LIMITE_CARACTERES_CHUNK_TTS} caracteres...")
    
    partes_iniciais = texto_processado.split('\n\n')
    partes_finais = []

    for p_inicial in partes_iniciais:
        p_strip = p_inicial.strip()
        if not p_strip:
            continue

        if len(p_strip) <= config.LIMITE_CARACTERES_CHUNK_TTS:
            partes_finais.append(p_strip)
            continue

        # Se o parágrafo é muito longo, quebra em frases
        frases = re.split(r'(?<=[.!?…])\s+', p_strip)
        segmento_atual = ""
        for frase in frases:
            if len(segmento_atual) + len(frase) + 1 > config.LIMITE_CARACTERES_CHUNK_TTS:
                if segmento_atual:
                    partes_finais.append(segmento_atual)
                segmento_atual = frase
            else:
                segmento_atual += (" " if segmento_atual else "") + frase
        
        if segmento_atual:
            partes_finais.append(segmento_atual)

    # Garante que nenhum chunk final seja maior que o limite (caso de frases muito longas)
    partes_super_finais = []
    for parte in partes_finais:
        if len(parte) > config.LIMITE_CARACTERES_CHUNK_TTS:
            for i in range(0, len(parte), config.LIMITE_CARACTERES_CHUNK_TTS):
                partes_super_finais.append(parte[i:i+config.LIMITE_CARACTERES_CHUNK_TTS])
        else:
            partes_super_finais.append(parte)

    print(f"✅ Texto dividido em {len(partes_super_finais)} parte(s).")
    return [p for p in partes_super_finais if p.strip()]


async def converter_chunk_tts(texto_chunk: str, voz: str, caminho_saida: str, indice: int, total: int) -> bool:
    """
    Converte um único chunk de texto para áudio. Gere tentativas e erros.
    Retorna True em sucesso, False em falha.
    """
    path_saida_obj = Path(caminho_saida)

    # Pula se o arquivo já existe e é válido (retomada de progresso)
    if path_saida_obj.exists() and path_saida_obj.stat().st_size > 200:
        return True

    tentativas = 0
    while tentativas < config.MAX_TTS_TENTATIVAS:
        if shared_state.CANCELAR_PROCESSAMENTO:
            return False
        
        # Garante que um arquivo inválido de uma tentativa anterior seja removido
        path_saida_obj.unlink(missing_ok=True)
        
        try:
            communicate = edge_tts.Communicate(texto_chunk, voz)
            await communicate.save(caminho_saida)

            if path_saida_obj.exists() and path_saida_obj.stat().st_size > 200:
                return True  # Sucesso!
            else:
                tamanho = path_saida_obj.stat().st_size if path_saida_obj.exists() else 0
                print(f"\n⚠️  Chunk {indice}/{total}: Arquivo de áudio gerado é inválido (tamanho: {tamanho} bytes).")

        except edge_tts.exceptions.NoAudioReceived:
            print(f"\n⚠️  Chunk {indice}/{total}: API não retornou áudio (NoAudioReceived).")
        except asyncio.TimeoutError:
            print(f"\n⚠️  Chunk {indice}/{total}: Timeout na comunicação com a API.")
        except Exception as e:
            print(f"\n❌ Erro INESPERADO no chunk {indice}/{total}: {type(e).__name__} - {e}")

        # Se chegou aqui, a tentativa falhou.
        tentativas += 1
        if tentativas < config.MAX_TTS_TENTATIVAS:
            tempo_espera = 2 * tentativas
            print(f"   Tentando novamente em {tempo_espera}s...")
            await asyncio.sleep(tempo_espera)
        else:
            print(f"❌ Falha definitiva no chunk {indice}/{total} após {config.MAX_TTS_TENTATIVAS} tentativas.")
            path_saida_obj.unlink(missing_ok=True)
            return False
            
    return False
