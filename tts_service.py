# -*- coding: utf-8 -*-
"""
Módulo de serviço para a conversão de texto em fala (TTS).
Encapsula a lógica de divisão de texto e a comunicação com a
biblioteca edge_tts.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import re
import edge_tts

# Importa de nossos outros módulos
import config
import shared_state
import settings_manager  # <-- Import necessário para obter velocidade padrão

def dividir_texto_para_tts(texto_processado: str) -> list[str]:
    """
    Divide o texto em partes menores para TTS, respeitando parágrafos e frases,
    buscando um equilíbrio para performance.
    """
    print(f"Dividindo texto em chunks de ate {config.LIMITE_CARACTERES_CHUNK_TTS} caracteres...")
    
    partes_iniciais = texto_processado.split('\n\n') # Primeiro por parágrafos
    partes_finais = []

    for p_inicial in partes_iniciais:
        p_strip = p_inicial.strip()
        if not p_strip:
            continue

        # Se o parágrafo inteiro já é menor que o limite, adiciona-o
        if len(p_strip) < config.LIMITE_CARACTERES_CHUNK_TTS:
            partes_finais.append(p_strip)
            continue

        # Se o parágrafo é maior, tenta dividir por frases, agrupando-as.
        # Usar regex para dividir por frases, mantendo os delimitadores.
        frases_com_delimitadores = re.split(r'([.!?…]+)', p_strip)
        segmento_atual = ""

        idx_frase = 0
        while idx_frase < len(frases_com_delimitadores):
            frase_atual = frases_com_delimitadores[idx_frase].strip()
            delimitador = ""
            if idx_frase + 1 < len(frases_com_delimitadores):
                delimitador = frases_com_delimitadores[idx_frase + 1].strip()
            
            trecho_completo = frase_atual
            if delimitador: # Adiciona o delimitador se existir
                trecho_completo += delimitador
            trecho_completo = trecho_completo.strip()

            if not trecho_completo: # Pula se a frase/delimitador for vazio
                idx_frase += 2 if delimitador else 1
                continue

            # Se adicionar o trecho atual não excede o limite do chunk
            if len(segmento_atual) + len(trecho_completo) + (1 if segmento_atual else 0) <= config.LIMITE_CARACTERES_CHUNK_TTS:
                segmento_atual += (" " if segmento_atual else "") + trecho_completo
            else:
                # O trecho atual faria o segmento exceder. Finaliza o segmento atual.
                if segmento_atual: # Adiciona o segmento anterior se não estiver vazio
                    partes_finais.append(segmento_atual)
                
                # O trecho atual se torna o novo segmento.
                # Se o próprio trecho já for maior que o limite, precisa ser quebrado (caso raro para uma frase)
                if len(trecho_completo) > config.LIMITE_CARACTERES_CHUNK_TTS:
                    # Quebra o trecho grande em pedaços menores que o limite
                    for i in range(0, len(trecho_completo), config.LIMITE_CARACTERES_CHUNK_TTS):
                        partes_finais.append(trecho_completo[i:i+config.LIMITE_CARACTERES_CHUNK_TTS])
                    segmento_atual = "" # Reseta, pois o trecho grande foi totalmente processado
                else:
                    segmento_atual = trecho_completo # Inicia novo segmento com o trecho atual

            idx_frase += 2 if delimitador else 1 # Avança para a próxima frase e seu delimitador

        # Adiciona o último segmento que pode ter sobrado
        if segmento_atual:
            partes_finais.append(segmento_atual)

    print(f"Texto dividido em {len(partes_finais)} parte(s).")
    return [p for p in partes_finais if p.strip()] # Garante que não há chunks vazios


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
    velocidade_str = settings_manager.obter_configuracao('velocidade_padrao') or "1.0"
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
