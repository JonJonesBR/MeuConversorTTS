# -*- coding: utf-8 -*-
"""
Módulo de serviço para a conversão de texto em fala (TTS).
Encapsula a lógica de divisão de texto e a comunicação com a
biblioteca edge_tts.
"""
import asyncio
from pathlib import Path

import edge_tts

# Importa de nossos outros módulos
import config
import shared_state
import settings_manager  # <-- LINHA CORRIGIDA: Import que estava faltando

def dividir_texto_para_tts(texto_processado: str) -> list[str]:
    """
    Divide o texto completo em blocos (chunks) otimizados para a API TTS.

    Esta função foi reescrita para agrupar parágrafos de forma inteligente,
    garantindo que cada bloco tenha um tamanho próximo ao limite máximo
    permitido, mas sem quebrar frases ou palavras no meio. Isso resulta
    em menos requisições e um áudio com fluxo mais natural.
    """
    print(f"Dividindo texto em chunks de ate {config.LIMITE_CARACTERES_CHUNK_TTS} caracteres...")
    
    paragrafos = texto_processado.split('\n\n')
    
    if not paragrafos:
        return []

    chunks_finais = []
    chunk_atual = ""

    for paragrafo in paragrafos:
        paragrafo = paragrafo.strip()
        if not paragrafo:
            continue

        if len(paragrafo) > config.LIMITE_CARACTERES_CHUNK_TTS:
            if chunk_atual:
                chunks_finais.append(chunk_atual)
            chunks_finais.append(paragrafo)
            chunk_atual = ""
            continue

        if len(chunk_atual) + len(paragrafo) + 2 > config.LIMITE_CARACTERES_CHUNK_TTS:
            if chunk_atual:
                chunks_finais.append(chunk_atual)
            chunk_atual = paragrafo
        else:
            if chunk_atual:
                chunk_atual += "\n\n" + paragrafo
            else:
                chunk_atual = paragrafo
    
    if chunk_atual:
        chunks_finais.append(chunk_atual)
    
    print(f"Texto dividido em {len(chunks_finais)} parte(s).")
    return [p for p in chunks_finais if p.strip()]


async def converter_texto_para_audio(texto: str, voz: str, caminho_saida: str, velocidade: str = "x1.0") -> tuple[bool, str]:
    """
    Converte um texto para áudio e salva-o diretamente. Ideal para testes.
    Retorna (True, caminho_saida) em sucesso, (False, "mensagem de erro") em falha.
    """
    path_saida_obj = Path(caminho_saida)
    path_saida_obj.unlink(missing_ok=True)

    try:
        multiplicador = float(velocidade.replace('x', ''))
        rate_str = f"{int((multiplicador - 1.0) * 100):+d}%"
    except ValueError:
        rate_str = "+0%"

    try:
        communicate = edge_tts.Communicate(text=texto, voice=voz, rate=rate_str)
        await communicate.save(caminho_saida)

        if path_saida_obj.exists() and path_saida_obj.stat().st_size > 200:
            return True, str(caminho_saida)
        else:
            tamanho = path_saida_obj.stat().st_size if path_saida_obj.exists() else 0
            return False, f"Ficheiro de áudio gerado é inválido (tamanho: {tamanho} bytes)."

    except edge_tts.exceptions.NoAudioReceived:
        return False, "API não retornou áudio (NoAudioReceived)."
    except asyncio.TimeoutError:
        return False, "Timeout na comunicação com a API."
    except Exception as e:
        return False, f"Erro inesperado: {type(e).__name__} - {e}"


async def converter_chunk_tts(texto: str, voz: str, caminho_saida: str, indice: int = 1, total: int = 1) -> bool:
    """
    Converte um único chunk de texto para áudio TTS com tentativas múltiplas.
    Retorna True em caso de sucesso, False em caso de falha.
    """
    path_saida_obj = Path(caminho_saida)
    path_saida_obj.unlink(missing_ok=True)
    
    # Obtém a configuração de velocidade usando o settings_manager importado
    velocidade_str = settings_manager.obter_configuracao('velocidade_padrao')
    try:
        multiplicador = float(velocidade_str.replace('x', ''))
        rate_param = f"{int((multiplicador - 1.0) * 100):+d}%"
    except ValueError:
        rate_param = "+0%"

    for tentativa in range(config.MAX_TTS_TENTATIVAS):
        if shared_state.CANCELAR_PROCESSAMENTO:
            return False
            
        try:
            communicate = edge_tts.Communicate(text=texto, voice=voz, rate=rate_param)
            await communicate.save(caminho_saida)

            if path_saida_obj.exists() and path_saida_obj.stat().st_size > 200:
                return True
            else:
                path_saida_obj.unlink(missing_ok=True)
        except Exception as e:
            if tentativa > 0:
                print(f"⚠️ Tentativa {tentativa+1} falhou para chunk {indice}/{total}: {type(e).__name__}")
            
            path_saida_obj.unlink(missing_ok=True)
            if tentativa == config.MAX_TTS_TENTATIVAS - 1:
                print(f"❌ Falha definitiva no chunk {indice}/{total} após {config.MAX_TTS_TENTATIVAS} tentativas.")
                return False
            await asyncio.sleep(2 * (tentativa + 1))
    
    return False

