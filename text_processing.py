# -*- coding: utf-8 -*-
"""
Script aprimorado de limpeza e formatação de texto para leitura TTS.

Este script processa textos brutos, especialmente de e-books, para gerar uma
saída otimizada para sintetizadores de voz (Text-to-Speech). O objetivo é
criar uma narração o mais natural e fluida possível, tratando desde a
limpeza de artefatos de digitalização até a expansão de abreviações e
números para uma pronúncia correta.
"""
import re
import unicodedata
from num2words import num2words
from typing import Dict, List, Pattern

# ================== CONFIGURAÇÕES GLOBAIS ==================

# Mapeamento de números por extenso para numerais, usado na formatação de capítulos.
# Flexibilizado para aceitar variações (ex: "CATORZE" e "QUATORZE").
CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM: Dict[str, str] = {
    'UM': '1', 'DOIS': '2', 'TRÊS': '3', 'QUATRO': '4', 'CINCO': '5',
    'SEIS': '6', 'SETE': '7', 'OITO': '8', 'NOVE': '9', 'DEZ': '10',
    'ONZE': '11', 'DOZE': '12', 'TREZE': '13', 'CATORZE': '14', 'QUATORZE': '14',
    'QUINZE': '15', 'DEZESSEIS': '16', 'DEZESSETE': '17', 'DEZOITO': '18',
    'DEZENOVE': '19', 'VINTE': '20',
}

# Mapeamento de abreviações e siglas para sua forma extensa.
# Organizado por categorias para melhor manutenção.
# A chave é uma expressão regular para garantir a substituição correta.
EXPANSOES_TEXTUAIS: Dict[Pattern, str] = {
    # --- Títulos e Pessoas ---
    re.compile(r'\bSr\.', re.IGNORECASE): 'Senhor',
    re.compile(r'\bSra\.', re.IGNORECASE): 'Senhora',
    re.compile(r'\bSrta\.', re.IGNORECASE): 'Senhorita',
    re.compile(r'\bDr\.', re.IGNORECASE): 'Doutor',
    re.compile(r'\bDra\.', re.IGNORECASE): 'Doutora',
    re.compile(r'\bProf\.', re.IGNORECASE): 'Professor',
    re.compile(r'\bProfa\.', re.IGNORECASE): 'Professora',
    re.compile(r'\bV\.Exa\.', re.IGNORECASE): 'Vossa Excelência',

    # --- Endereços ---
    re.compile(r'\bAv\.', re.IGNORECASE): 'Avenida',
    re.compile(r'\bR\.', re.IGNORECASE): 'Rua',
    re.compile(r'\bRod\.', re.IGNORECASE): 'Rodovia',
    re.compile(r'\bPça\.', re.IGNORECASE): 'Praça',
    re.compile(r'\bEst\.', re.IGNORECASE): 'Estrada',
    re.compile(r'\bS/N\b', re.IGNORECASE): 'sem número',

    # --- Unidades e Medidas ---
    re.compile(r'\bN[º°o]\b', re.IGNORECASE): 'número',
    re.compile(r'\bKg\b', re.IGNORECASE): 'quilogramas', # Plural soa mais natural
    re.compile(r'\bKm\b', re.IGNORECASE): 'quilômetros',
    re.compile(r'\bcm\b', re.IGNORECASE): 'centímetros',
    re.compile(r'\bmm\b', re.IGNORECASE): 'milímetros',
    re.compile(r'\bml\b', re.IGNORECASE): 'mililitros',
    re.compile(r'\bL\b'): 'litros', # "L" maiúsculo para evitar substituir "l" em palavras
    re.compile(r'\b°C\b', re.IGNORECASE): 'graus Celsius',
    re.compile(r'\bm²\b', re.IGNORECASE): 'metros quadrados',
    re.compile(r'\bm³\b', re.IGNORECASE): 'metros cúbicos',
    re.compile(r'\bKm/h\b', re.IGNORECASE): 'quilômetros por hora',

    # --- Diversos ---
    re.compile(r'\bEtc\.?', re.IGNORECASE): 'et cetera',
    re.compile(r'\bObs\.?', re.IGNORECASE): 'observação',
    re.compile(r'\bvs\.', re.IGNORECASE): 'versus',
    re.compile(r'\bp\.', re.IGNORECASE): 'página', # Ex: p. 12

    # --- Siglas Comuns (Adicionar conforme necessidade) ---
    re.compile(r'\bEUA\b'): 'Estados Unidos da América',
    re.compile(r'\bONU\b'): 'Organização das Nações Unidas',
    re.compile(r'\bRJ\b'): 'Rio de Janeiro',
    re.compile(r'\bSP\b'): 'São Paulo',
    re.compile(r'\bDF\b'): 'Distrito Federal',
}

# ================== FUNÇÕES DE LIMPEZA E NORMALIZAÇÃO ==================

def _remover_lixo_textual(texto: str) -> str:
    """Remove cabeçalhos, rodapés e outros textos repetitivos de e-books."""
    print("   -> Removendo lixo textual e artefatos de digitalização...")
    # Tenta encontrar o primeiro capítulo para remover qualquer texto introdutório
    # A expressão `(?s)` permite que `.` corresponda a quebras de linha
    match = re.search(r'(?s)(cap[íi]tulo\s+[\w\d]+|sum[áa]rio|pr[óo]logo)', texto, re.IGNORECASE)
    if match:
        texto = texto[match.start():]

    # Remove textos repetitivos comuns (ex: notas de copyright de versões não oficiais)
    textos_a_remover = [
        r"Esse livro é protegido.*",
        r"A Detonando Home Page.*",
        r"Distribuído gratuitamente.*",
        r"www\.\s*portaldetonando\.\s*cjb\.\s*net.*"
    ]
    for padrao in textos_a_remover:
        texto = re.sub(padrao, "", texto, flags=re.IGNORECASE)

    return texto

def _normalizar_caracteres_e_pontuacao(texto: str) -> str:
    """Normaliza caracteres Unicode, aspas, travessões e outros símbolos."""
    print("   -> Normalizando caracteres e pontuação...")
    # Normalização Unicode para consistência (ex: 'é' e 'e´' viram a mesma coisa)
    texto = unicodedata.normalize('NFKC', texto)

    substituicoes = {
        '[“”«»]': '"',  # Aspas curvas/francesas para aspas retas
        "[‘’]": "'",    # Apóstrofos curvos para retos
        '[–―]': '—',    # Hífens e barras para travessão padrão
        '…': '...',    # Reticências
    }
    for padrao, sub in substituicoes.items():
        texto = re.sub(padrao, sub, texto)

    # Garante espaçamento consistente ao redor de travessões para diálogos
    texto = re.sub(r'\s*—\s*', ' — ', texto)
    return texto

def _substituir_simbolos_por_extenso(texto: str) -> str:
    """Substitui símbolos que podem ser mal interpretados pelo TTS."""
    print("   -> Substituindo símbolos por extenso...")
    
    # Mapeamento de símbolos para sua forma por extenso.
    # As chaves são strings literais, não regex.
    substituicoes = {
        '&': ' e ',
        '@': ' arroba ',
        '#': ' ',
        '$': ' dólares ', # R$ é tratado em _expandir_numeros
        '/': ' ou ',
        '\\': ' ', # Barra invertida literal
        '_': ' ',
        '+': ' mais ',
        '=': ' igual a ',
        '<': ' menor que ',
        '>': ' maior que ',
        # '%' é melhor tratado na expansão de números, mas pode ficar aqui como fallback
    }

    # Cria uma única expressão regular compilada.
    # re.escape() garante que caracteres especiais (como $, +, \) sejam tratados literalmente.
    # As chaves são ordenadas pela mais longa primeiro para evitar substituições parciais (ex: tratar '--' antes de '-').
    padrao_compilado = re.compile("|".join(
        re.escape(k) for k in sorted(substituicoes.keys(), key=len, reverse=True)
    ))

    # A função de substituição (lambda) busca o valor correspondente no dicionário
    # para cada símbolo encontrado pelo padrão compilado.
    return padrao_compilado.sub(lambda m: substituicoes[m.group(0)], texto)


def _remontar_paragrafos(texto: str) -> str:
    """Corrige quebras de linha indevidas no meio dos parágrafos."""
    print("   -> Remontando parágrafos...")
    # Une palavras hifenizadas no final da linha (ex: "rapida-\nmente" -> "rapidamente")
    texto = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)

    # Substitui quebras de linha únicas por espaço, preservando parágrafos (quebras duplas)
    linhas = texto.split('\n')
    paragrafos_remontados = []
    paragrafo_atual = ""
    for linha in linhas:
        linha = linha.strip()
        if not linha: # Linha vazia indica fim de parágrafo
            if paragrafo_atual:
                paragrafos_remontados.append(paragrafo_atual)
                paragrafo_atual = ""
        else:
            paragrafo_atual += " " + linha
    if paragrafo_atual: # Adiciona o último parágrafo
        paragrafos_remontados.append(paragrafo_atual)

    return "\n\n".join(p.strip() for p in paragrafos_remontados)

# ================== FUNÇÕES DE EXPANSÃO PARA TTS ==================

def _formatar_capitulos(texto: str) -> str:
    """Padroniza a formatação de títulos de capítulos para uma leitura clara."""
    print("   -> Formatando títulos de capítulos...")

    def substituir_capitulo(match: re.Match) -> str:
        prefixo = match.group(1).strip()
        numero_str = match.group(2).strip().upper()
        titulo = match.group(3).strip().title() if match.group(3) else ""

        # Converte número por extenso para numeral (Ex: "UM" -> "1")
        numero_final = CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(numero_str, numero_str)

        # Garante que o título termine com pontuação para uma pausa na leitura
        if titulo and not re.search(r'[.!?]$', titulo):
            titulo += "."

        return f"\n\n{prefixo.upper()} {numero_final}.\n\n{titulo}\n\n"

    # Padrão mais flexível para capturar "CAPÍTULO 1", "CAPÍTULO UM", "PRÓLOGO", etc.
    # com ou sem título na linha seguinte.
    padrao = re.compile(
        r'^\s*(cap[íi]tulo|pr[óo]logo|ep[íi]logo)\s+([\d\w]+)\s*\.?\s*\n\n([^\n]+)',
        re.IGNORECASE | re.MULTILINE
    )
    return padrao.sub(substituir_capitulo, texto)

def _expandir_abreviacoes(texto: str) -> str:
    """Expande abreviações, siglas e unidades para uma leitura natural."""
    print("   -> Expandindo abreviações e siglas...")
    for padrao, substituicao in EXPANSOES_TEXTUAIS.items():
        texto = padrao.sub(substituicao, texto)
    return texto

def _expandir_numeros(texto: str) -> str:
    """Converte números em texto por extenso, tratando casos especiais."""
    print("   -> Expandindo números para leitura...")

    # Converte números ordinais: 2º -> segundo, 3ª -> terceira
    def ordinal(match: re.Match) -> str:
        try:
            n = int(match.group(1))
            sufixo = match.group(2).lower()
            if sufixo in ('o', 'º'):
                return num2words(n, lang='pt_BR', to='ordinal')
            elif sufixo in ('a', 'ª'):
                ordinal_masc = num2words(n, lang='pt_BR', to='ordinal')
                return re.sub(r'o$', 'a', ordinal_masc)
        except (ValueError, IndexError):
            return match.group(0)
        return match.group(0)
    texto = re.sub(r'\b(\d+)([oOaAºª])\b', ordinal, texto)

    # Converte valores monetários: R$ 10,50 -> dez reais e cinquenta centavos
    def monetario(match: re.Match) -> str:
        try:
            partes = match.group(1).replace('.', '').replace(',', '.').split('.')
            reais = int(partes[0])
            centavos = int(partes[1]) if len(partes) > 1 else 0

            str_reais = num2words(reais, lang='pt_BR') + (' real' if reais == 1 else ' reais')
            if centavos > 0:
                str_centavos = num2words(centavos, lang='pt_BR') + (' centavo' if centavos == 1 else ' centavos')
                return f"{str_reais} e {str_centavos}"
            return str_reais
        except ValueError:
            return match.group(0)
    texto = re.sub(r'R\$\s*([\d.,]+)', monetario, texto)

    # Converte números cardinais, ignorando anos e números muito longos
    def cardinal(match: re.Match) -> str:
        num_str = match.group(0)
        # Não converte números que parecem anos ou códigos/identificadores longos
        if 1900 <= int(num_str) <= 2100 or len(num_str) > 6:
            return num_str
        return num2words(int(num_str), lang='pt_BR')
    texto = re.sub(r'\b\d+\b', cardinal, texto)
    return texto

def _limpeza_final(texto: str) -> str:
    """Aplica ajustes finais de espaçamento e pontuação para fluidez."""
    print("   -> Realizando limpeza final e ajustes de ritmo...")
    # Adiciona quebra de parágrafo antes de um diálogo iniciado por travessão, se não houver
    texto = re.sub(r'([.!?"])\s*([—-])', r'\1\n\n\2', texto)

    # Remove espaços antes de pontuação e garante espaço depois
    texto = re.sub(r'\s+([,.!?;:])', r'\1', texto)
    texto = re.sub(r'([,.!?;:])(\w)', r'\1 \2', texto)

    # Remove espaços múltiplos e quebras de linha excessivas
    texto = re.sub(r' {2,}', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    # Garante que parágrafos que não são diálogos terminem com pontuação
    paragrafos = texto.split('\n\n')
    paragrafos_formatados = []
    for p in paragrafos:
        p_strip = p.strip()
        if p_strip and not p_strip.startswith('—') and not re.search(r'[.!?]$', p_strip):
            p += '.'
        paragrafos_formatados.append(p)

    return '\n\n'.join(paragrafos_formatados).strip()

# ================== FUNÇÃO PRINCIPAL ==================

def formatar_texto_para_tts(texto_bruto: str) -> str:
    """
    Executa um pipeline completo de limpeza e formatação para preparar o texto
    para uma leitura natural e agradável em um sistema TTS.
    """
    print("🧩 Iniciando processamento completo do texto para TTS...")

    # Pipeline de processamento
    texto = _remover_lixo_textual(texto_bruto)
    texto = _normalizar_caracteres_e_pontuacao(texto)
    texto = _substituir_simbolos_por_extenso(texto)
    texto = _remontar_paragrafos(texto)
    texto = _formatar_capitulos(texto)
    texto = _expandir_abreviacoes(texto)
    texto = _expandir_numeros(texto)
    texto = _limpeza_final(texto)

    print("✅ Texto pronto para TTS.")
    return texto

# ================== EXEMPLO DE USO ==================

if __name__ == '__main__':
    texto_de_exemplo = """
    Esse livro é protegido pelas leis internacionais de Copyright.
    www.portaldetonando.cjb.net

    CAPÍTULO UM.

    O Sr. & a Sra. Dursley, da rua dos Alfeneiros, nº 4, orgulhavam-se de
    dizer que eram perfeitamente normais, muito obrigado. O preço é R$ 50,50.
    O carro andava a 80Km/h.

    "Isso é 50% verdade!", disse o Dr. João.
    — Cuidado! — alertou a Profa. Ana.
    O evento será na Av. Brasil, S/N.
    """
    texto_processado = formatar_texto_para_tts(texto_de_exemplo)
    print("\n--- TEXTO PROCESSADO ---\n")
    print(texto_processado)

    # Saída esperada:
    #
    # CAPÍTULO 1.
    #
    # O Senhor e a Senhora Dursley, da rua dos Alfeneiros, número quatro, orgulhavam-se de dizer que eram perfeitamente normais, muito obrigado. O preço é cinquenta reais e cinquenta centavos. O carro andava a oitenta quilômetros por hora.
    #
    # "Isso é cinquenta por cento verdade!", disse o Doutor João.
    #
    # — Cuidado! — alertou a Professora Ana.
    #
    # O evento será na Avenida Brasil, sem número.
