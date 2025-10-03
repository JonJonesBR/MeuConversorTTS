# -*- coding: utf-8 -*-
"""
Módulo responsável por toda a limpeza, formatação e preparação
do texto para a conversão em áudio (TTS).
"""
import re
import unicodedata
from num2words import num2words

# Importa as configurações do nosso arquivo config.py
import config

# ================== CONSTANTES E PRÉ-PROCESSAMENTO DO MÓDULO ==================

# Pré-processa o dicionário de abreviações para busca rápida e case-insensitive
ABREVIACOES_MAP_LOWER = {k.lower(): v for k, v in config.ABREVIACOES_MAP.items()}

# Casos especiais de abreviações que precisam de tratamento com regex
CASOS_ESPECIAIS_RE = {
     r'\bV\.Exa\.(?=\s)': 'Vossa Excelência',
     r'\bV\.Sa\.(?=\s)': 'Vossa Senhoria',
     r'\bEngª\.(?=\s)': 'Engenheira'
}

# Regex pré-compilada para encontrar siglas com pontos (ex: U.S.A.)
SIGLA_COM_PONTOS_RE = re.compile(r'\b([A-Z]\.\s*)+$')


# ================== FUNÇÕES AUXILIARES DE PROCESSAMENTO DE TEXTO ==================

def _formatar_numeracao_capitulos(texto):
    """
    Localiza títulos como 'Capítulo 1 Mesmo em pleno verão...' ou 'CAPÍTULO UM ...'
    e converte para: '\n\nCAPÍTULO 1.\n\nMesmo em pleno verão...'
    Também padroniza números por extenso para arábicos.
    """
    def substituir_cap(match):
        tipo_cap = match.group(1).upper()
        numero_rom_arab = match.group(2)
        numero_extenso = match.group(3)
        titulo_opcional = match.group(4).strip() if match.group(4) else ""

        numero_final = ""
        if numero_rom_arab:
            numero_final = numero_rom_arab.upper()
        elif numero_extenso:
            num_ext_upper = numero_extenso.strip().upper()
            numero_final = config.CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(num_ext_upper, num_ext_upper)

        cabecalho = f"{tipo_cap} {numero_final}."
        if titulo_opcional:
            palavras_titulo = []
            for p in titulo_opcional.split():
                if p.isupper() and len(p) > 1:
                    palavras_titulo.append(p)
                else:
                    palavras_titulo.append(p.capitalize())
            titulo_formatado = " ".join(palavras_titulo)
            return f"\n\n{cabecalho}\n\n{titulo_formatado}"
        return f"\n\n{cabecalho}\n\n"

    padrao = re.compile(
        r'(?i)(cap[íi]tulo|cap\.?)\s+'
        r'(?:(\d+|[IVXLCDM]+)|([A-ZÇÉÊÓÃÕa-zçéêóãõ]+))'
        r'\s*[:\-.]?\s*'
        r'(?=\S)([^\n]*)?',
        re.IGNORECASE
    )
    texto = padrao.sub(substituir_cap, texto)

    def substituir_extenso_com_titulo(match):
        num_ext = match.group(1).strip().upper()
        titulo = match.group(2).strip().title()
        numero = config.CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(num_ext, num_ext)
        return f"CAPÍTULO {numero}: {titulo}"

    padrao_extenso_titulo = re.compile(r'CAP[IÍ]TULO\s+([A-ZÇÉÊÓÃÕ]+)\s*[:\-]\s*(.+)', re.IGNORECASE)
    texto = padrao_extenso_titulo.sub(substituir_extenso_com_titulo, texto)
    return texto

def _remover_numeros_pagina_isolados(texto):
    linhas = texto.splitlines()
    novas_linhas = []
    for linha in linhas:
        if re.match(r'^\s*\d+\s*$', linha):
            continue
        linha = re.sub(r'\s{3,}\d+\s*$', '', linha)
        novas_linhas.append(linha)
    return '\n'.join(novas_linhas)

def _normalizar_caixa_alta_linhas(texto):
    linhas = texto.splitlines()
    texto_final = []
    for linha in linhas:
        if not re.match(r'^\s*CAP[ÍI]TULO\s+[\w\d]+\.?\s*$', linha, re.IGNORECASE):
            if linha.isupper() and len(linha.strip()) > 3 and any(c.isalpha() for c in linha):
                palavras = []
                for p in linha.split():
                    if len(p) > 1 and p.isupper() and p.isalpha() and p not in ['I', 'A', 'E', 'O', 'U']:
                        if not (sum(1 for char in p if char in "AEIOU") > 0 and \
                                sum(1 for char in p if char not in "AEIOU") > 0 and len(p) <=4) :
                            palavras.append(p)
                            continue
                    palavras.append(p.capitalize())
                texto_final.append(" ".join(palavras))
            else:
                texto_final.append(linha)
        else:
            texto_final.append(linha)
    return "\n".join(texto_final)

def _corrigir_hifenizacao_quebras(texto):
    return re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)

def _remover_metadados_pdf(texto):
    return re.sub(r'^\s*[\w\d_-]+\.[indd]\s+\d+\s+\d{2}/\d{2}/\d{2,4}\s+\d{1,2}:\d{2}(?:\d{2})?\s*(?:[AP]M)?\s*$', '', texto, flags=re.MULTILINE)

def _expandir_abreviacoes_numeros(texto: str) -> str:
    """Expande abreviações comuns e converte números cardinais e monetários."""
    for abrev_re, expansao in CASOS_ESPECIAIS_RE.items():
         texto = re.sub(abrev_re, expansao, texto, flags=re.IGNORECASE)

    def replace_abrev_com_ponto(match):
        abrev_encontrada = match.group(1)
        expansao = ABREVIACOES_MAP_LOWER.get(abrev_encontrada.lower())
        return expansao if expansao else match.group(0)

    chaves_escapadas = [re.escape(k) for k in ABREVIACOES_MAP_LOWER.keys() if '.' not in k and 'ª' not in k]
    if chaves_escapadas:
        padrao_abrev_simples = r'\b(' + '|'.join(chaves_escapadas) + r')\.'
        texto = re.sub(padrao_abrev_simples, replace_abrev_com_ponto, texto, flags=re.IGNORECASE)

    def _converter_numero_match(match):
        num_str = match.group(0)
        try:
            if re.match(r'^\d{4}$', num_str) and (1900 <= int(num_str) <= 2100): return num_str
            if len(num_str) > 7 : return num_str
            return num2words(int(num_str), lang='pt_BR')
        except Exception: return num_str
    texto = re.sub(r'\b\d+\b', _converter_numero_match, texto)

    def _converter_valor_monetario_match(match):
        valor_inteiro = match.group(1).replace('.', '')
        try: return f"{num2words(int(valor_inteiro), lang='pt_BR')} reais"
        except Exception: return match.group(0)
    texto = re.sub(r'R\$\s*(\d{1,3}(?:\.\d{3})*),(\d{2})', _converter_valor_monetario_match, texto)
    texto = re.sub(r'R\$\s*(\d+)(?:,00)?', lambda m: f"{num2words(int(m.group(1)), lang='pt_BR')} reais" if m.group(1) else m.group(0) , texto)
    texto = re.sub(r'\b(\d+)\s*-\s*(\d+)\b', lambda m: f"{num2words(int(m.group(1)), lang='pt_BR')} a {num2words(int(m.group(2)), lang='pt_BR')}", texto)
    return texto

def _converter_ordinais_para_extenso(texto: str) -> str:
    """Converte números ordinais como 1º, 2a, 3ª para extenso."""
    def substituir_ordinal(match):
        numero = match.group(1)
        terminacao = match.group(2).lower()
        try:
            num_int = int(numero)
            if terminacao in ('o', 'º'):
                return num2words(num_int, lang='pt_BR', to='ordinal')
            elif terminacao in ('a', 'ª'):
                ordinal_masc = num2words(num_int, lang='pt_BR', to='ordinal')
                return ordinal_masc[:-1] + 'a' if ordinal_masc.endswith('o') else ordinal_masc
            else:
                return match.group(0)
        except ValueError:
            return match.group(0)

    padrao_ordinal = re.compile(r'\b(\d+)\s*([oaºª])(?!\w)', re.IGNORECASE)
    texto = padrao_ordinal.sub(substituir_ordinal, texto)
    return texto


# ================== FUNÇÃO PRINCIPAL DE FORMATAÇÃO DE TEXTO ==================

def formatar_texto_para_tts(texto_bruto: str) -> str:
    """
    Orquestra todas as etapas de limpeza e formatação do texto.
    """
    print("Aplicando formatacoes avancadas ao texto...")
    texto = texto_bruto

    texto = unicodedata.normalize('NFKC', texto)
    texto = texto.replace('\f', '\n\n').replace('*', '')
    for char in ['_', '#', '@']: texto = texto.replace(char, ' ')
    for char in ['(', ')', '\\', '[', ']']: texto = texto.replace(char, '')
    texto = re.sub(r'\{.*?\}', '', texto)
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = "\n".join([linha.strip() for linha in texto.splitlines() if linha.strip()])

    paragrafos_originais = texto.split('\n\n')
    paragrafos_processados = []
    for paragrafo_bruto in paragrafos_originais:
        paragrafo_bruto = paragrafo_bruto.strip()
        if not paragrafo_bruto: continue
        linhas_do_paragrafo = paragrafo_bruto.split('\n')
        buffer_linha_atual = ""
        for i, linha in enumerate(linhas_do_paragrafo):
            linha_strip = linha.strip()
            if not linha_strip: continue
            juntar_com_anterior = False
            if buffer_linha_atual:
                ultima_palavra_buffer = buffer_linha_atual.split()[-1].lower() if buffer_linha_atual else ""
                termina_abreviacao = ultima_palavra_buffer in config.ABREVIACOES_QUE_NAO_TERMINAM_FRASE
                termina_sigla_ponto = re.search(r'\b[A-Z]\.$', buffer_linha_atual) is not None
                termina_pontuacao_forte = re.search(r'[.!?…]$', buffer_linha_atual)
                nao_juntar = False
                if termina_pontuacao_forte and not termina_abreviacao and not termina_sigla_ponto:
                     if linha_strip and linha_strip[0].isupper(): nao_juntar = True
                if termina_abreviacao or termina_sigla_ponto: juntar_com_anterior = True
                elif not nao_juntar and not termina_pontuacao_forte: juntar_com_anterior = True
                elif buffer_linha_atual.lower() in ['doutora', 'senhora', 'senhor', 'doutor']: juntar_com_anterior = True
            if juntar_com_anterior: buffer_linha_atual += " " + linha_strip
            else:
                if buffer_linha_atual: paragrafos_processados.append(buffer_linha_atual)
                buffer_linha_atual = linha_strip
        if buffer_linha_atual: paragrafos_processados.append(buffer_linha_atual)
    texto = '\n\n'.join(paragrafos_processados)

    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'(?<!\n)\n(?!\\n)', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    texto = _remover_metadados_pdf(texto)
    texto = _remover_numeros_pagina_isolados(texto)
    texto = _corrigir_hifenizacao_quebras(texto)
    texto = _formatar_numeracao_capitulos(texto)

    segmentos = re.split(r'([.!?…])\s*', texto)
    texto_reconstruido = ""
    buffer_segmento = ""
    for i in range(0, len(segmentos), 2):
        parte_texto = segmentos[i]
        pontuacao = segmentos[i+1] if i + 1 < len(segmentos) else ""
        segmento_completo = (parte_texto + pontuacao).strip()
        if not segmento_completo: continue
        ultima_palavra = segmento_completo.split()[-1].lower() if segmento_completo else ""
        ultima_palavra_sem_ponto = ultima_palavra.rstrip('.!?…') if pontuacao else ultima_palavra
        termina_abreviacao_conhecida = ultima_palavra in config.ABREVIACOES_QUE_NAO_TERMINAM_FRASE or \
                                        ultima_palavra_sem_ponto in config.ABREVIACOES_QUE_NAO_TERMINAM_FRASE
        termina_sigla_padrao = SIGLA_COM_PONTOS_RE.search(segmento_completo) is not None
        nao_quebrar = False
        if pontuacao == '.':
             if termina_abreviacao_conhecida or termina_sigla_padrao: nao_quebrar = True
        if buffer_segmento: buffer_segmento += " " + segmento_completo
        else: buffer_segmento = segmento_completo
        if not nao_quebrar: texto_reconstruido += buffer_segmento + "\n\n" ; buffer_segmento = ""
    if buffer_segmento:
         texto_reconstruido += buffer_segmento
         if not re.search(r'[.!?…)]$', buffer_segmento): texto_reconstruido += "."
         texto_reconstruido += "\n\n"
    texto = texto_reconstruido.strip()

    texto = _normalizar_caixa_alta_linhas(texto)
    texto = _converter_ordinais_para_extenso(texto)
    texto = _expandir_abreviacoes_numeros(texto)

    formas_expandidas_tratamento = ['Senhor', 'Senhora', 'Doutor', 'Doutora', 'Professor', 'Professora', 'Excelentíssimo', 'Excelentíssima']
    for forma in formas_expandidas_tratamento:
        padrao_limpeza = r'\b' + re.escape(forma) + r'\.\s+([A-Z])'
        texto = re.sub(padrao_limpeza, rf'{forma} \1', texto)
        padrao_limpeza_sem_espaco = r'\b' + re.escape(forma) + r'\.([A-Z])'
        texto = re.sub(padrao_limpeza_sem_espaco, rf'{forma} \1', texto)

    texto = re.sub(r'\b([A-Z])\.\s+([A-Z])', r'\1. \2', texto)
    texto = re.sub(r'\b([A-Z])\.\s+([A-Z][a-z])', r'\1. \2', texto)

    paragrafos_finais = texto.split('\n\n')
    paragrafos_formatados_final = []
    for p in paragrafos_finais:
        p_strip = p.strip()
        if not p_strip: continue
        if not re.search(r'[.!?…)]$', p_strip) and \
           not re.match(r'^\s*CAP[ÍI]TULO\s+[\w\d]+\.?\s*$', p_strip.split('\n')[0].strip(), re.IGNORECASE):
            p_strip += '.'
        paragrafos_formatados_final.append(p_strip)
    texto = '\n\n'.join(paragrafos_formatados_final)
    texto = re.sub(r'[ \t]+', ' ', texto).strip()
    texto = re.sub(r'\n{2,}', '\n\n', texto)

    print("✅ Formatação de texto concluída.")
    return texto.strip()
