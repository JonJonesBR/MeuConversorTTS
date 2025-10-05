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

def _remover_cabecalho_inicial(texto: str) -> str:
    """
    Encontra a primeira menção a um capítulo e remove todo o texto anterior a ele.
    """
    # Padrão flexível para encontrar "capítulo", "cap.", etc., seguido de um número ou palavra
    padrao_primeiro_cap = re.compile(r'(cap[íi]tulo|cap\.?)\s+'
                                     r'(?:(\d+|[IVXLCDM]+)|([A-ZÇÉÊÓÃÕa-zçéêóãõ]+))', re.IGNORECASE)
    
    match = padrao_primeiro_cap.search(texto)
    
    if match:
        # Se encontrou um capítulo, retorna o texto a partir do início da correspondência
        print("   -> Cabeçalho/Preâmbulo identificado e removido.")
        return texto[match.start():]
    
    # Se não encontrou nenhum padrão de capítulo, retorna o texto original
    return texto


def _formatar_numeracao_capitulos(texto):
    """
    Localiza títulos e os formata corretamente, separando número e título.
    Ex: 'CAPÍTULO UM O Menino...' -> '\n\nCAPÍTULO 1.\n\nO Menino Que Sobreviveu.\n\n'
    """
    def substituir_cap(match):
        tipo_cap = match.group(1).upper()
        numero_rom_arab = match.group(2)
        numero_extenso = match.group(3)
        titulo_opcional = match.group(4).strip() if match.group(4) else ""

        numero_final = ""
        if numero_rom_arab:
            numero_final = numero_rom_arab.strip().upper()
        elif numero_extenso:
            num_ext_upper = numero_extenso.strip().upper()
            # Converte o número por extenso para um número arábico
            numero_final = config.CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(num_ext_upper, num_ext_upper)

        # Garante que o cabeçalho sempre termine com um ponto.
        cabecalho = f"{tipo_cap} {numero_final}."
        
        if titulo_opcional:
            # Capitaliza o título de forma inteligente (Title Case)
            titulo_formatado = titulo_opcional.title()
            # Garante que o título também termine com um ponto.
            if not titulo_formatado.endswith(('.', '!', '?')):
                 titulo_formatado += "."
            # Retorna o cabeçalho e o título em parágrafos separados
            return f"\n\n{cabecalho}\n\n{titulo_formatado}\n\n"
        
        return f"\n\n{cabecalho}\n\n"

    # Regex atualizada para ser mais flexível com quebras de linha e capturar o título
    padrao = re.compile(
        r'(?i)(cap[íi]tulo|cap\.?)\s+'  # Grupo 1: "Capítulo" ou "Cap."
        r'(?:(\d+|[IVXLCDM]+)|([A-ZÇÉÊÓÃÕa-zçéêóãõ]+))'  # Grupo 2 ou 3: Número arábico/romano OU por extenso
        r'\s*[:\-.]?\s*\n?\s*' # Separadores e quebra de linha opcional
        r'([^\n]+)', # Grupo 4: O título do capítulo (o resto da linha)
        re.IGNORECASE
    )
    texto = padrao.sub(substituir_cap, texto)
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
    
    # ETAPA 1: Normalizações básicas e remoção de caracteres indesejados
    texto = unicodedata.normalize('NFKC', texto_bruto)
    texto = texto.replace('\f', '\n\n')
    texto = re.sub(r'[*_#@(){}\[\]\\]', ' ', texto) # Remove mais caracteres de uma vez
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = "\n".join([linha.strip() for linha in texto.splitlines() if linha.strip()])
    
    # ETAPA 2 (NOVA): Remove todo o conteúdo antes do primeiro capítulo
    texto = _remover_cabecalho_inicial(texto)

    # ETAPA 3 (ATUALIZADA): Formata os cabeçalhos dos capítulos
    texto = _formatar_numeracao_capitulos(texto)

    # ETAPA 4: Lógicas de limpeza de parágrafos e junção de linhas
    texto = _remover_metadados_pdf(texto)
    texto = _remover_numeros_pagina_isolados(texto)
    texto = _corrigir_hifenizacao_quebras(texto)
    
    # Reagrupamento de parágrafos
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    # ETAPA 5: Separação de frases em parágrafos distintos para melhor ritmo
    segmentos = re.split(r'([.!?…])\s*', texto)
    texto_reconstruido = ""
    for i in range(0, len(segmentos) - 1, 2):
        frase = (segmentos[i] + segmentos[i+1]).strip()
        if frase:
            texto_reconstruido += frase + "\n\n"
    if len(segmentos) % 2 != 0 and segmentos[-1].strip():
        texto_reconstruido += segmentos[-1].strip() + ".\n\n"
    texto = texto_reconstruido.strip()

    # ETAPA 6: Expansão de números e abreviações
    texto = _normalizar_caixa_alta_linhas(texto)
    texto = _converter_ordinais_para_extenso(texto)
    texto = _expandir_abreviacoes_numeros(texto)

    # ETAPA 7: Limpezas finais e padronização
    texto = re.sub(r'[ \t]+', ' ', texto).strip()
    texto = re.sub(r'\n{2,}', '\n\n', texto)

    print("✅ Formatação de texto concluída.")
    return texto.strip()
