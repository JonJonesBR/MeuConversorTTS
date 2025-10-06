# -*- coding: utf-8 -*-
"""
Script definitivo de limpeza e formatação de texto para leitura TTS.

Este script foi aprimorado para processar textos, especialmente de e-books,
removendo formatação indesejada, corrigindo pontuação, expandindo abreviações,
siglas, números e símbolos para gerar um texto fluido e natural, ideal para
ser lido por um sintetizador de voz (Text-to-Speech).
"""
import re
import unicodedata
from num2words import num2words

# ================== CONFIGURAÇÕES E TEXTOS FIXOS ==================

# Textos comuns em rodapés ou cabeçalhos de e-books para serem removidos.
TEXTOS_REPETIDOS_PARA_REMOVER = [
    "Esse livro é protegido pelas leis internacionais de Copyright.",
    "A Detonando Home Page não se responsabiliza por qualquer dano que esse material possa causar.",
    "Seu uso deve ser exclusivamente pessoal.",
    "Distribuído gratuitamente pela Detonando Home Page – www.",
    "portaldetonando.",
    "cjb.",
    "net - Sempre uma novidade para você!"
]

# Mapeamento para converter números de capítulo por extenso para numerais.
# Exemplo: "UM" -> "1"
CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM = {
    'UM': '1', 'DOIS': '2', 'TRÊS': '3', 'QUATRO': '4', 'CINCO': '5',
    'SEIS': '6', 'SETE': '7', 'OITO': '8', 'NOVE': '9', 'DEZ': '10',
    'ONZE': '11', 'DOZE': '12', 'TREZE': '13', 'CATORZE': '14', 'QUINZE': '15',
    'DEZESSEIS': '16', 'DEZESSETE': '17', 'DEZOITO': '18', 'DEZENOVE': '19', 'VINTE': '20',
}


# ================== FUNÇÕES DE LIMPEZA E NORMALIZAÇÃO ==================

def _remover_lixo_textual(texto: str) -> str:
    """Remove cabeçalhos, rodapés e outros textos repetitivos."""
    print("   -> Removendo cabeçalhos e rodapés...")
    # Tenta encontrar o primeiro capítulo para remover qualquer texto introdutório
    padrao_primeiro_cap = re.compile(r'(cap[íi]tulo)', re.IGNORECASE)
    match = padrao_primeiro_cap.search(texto)
    if match:
        texto = texto[match.start():]

    # Remove frases comuns de e-books não oficiais
    for frase in TEXTOS_REPETIDOS_PARA_REMOVER:
        texto = texto.replace(frase, "")
    return texto


def _normalizar_pontuacao(texto: str) -> str:
    """Normaliza aspas, travessões e outros sinais para evitar leitura errada."""
    print("   -> Normalizando pontuação e aspas...")
    substituicoes = {
        '“': '"', '”': '"', '«': '"', '»': '"', '‘': "'", '’': "'",
        '–': '—', '--': '—', '―': '—',
        '…': '...',
    }
    for k, v in substituicoes.items():
        texto = texto.replace(k, v)

    # Remove aspas duplas ou simples mal posicionadas
    texto = re.sub(r'"{2,}', '"', texto)
    texto = re.sub(r"'{2,}", "'", texto)

    # Garante espaçamento consistente ao redor de travessões
    texto = re.sub(r'\s*—\s*', ' — ', texto)
    texto = re.sub(r'\s{2,}', ' ', texto) # Remove espaços múltiplos
    return texto.strip()


def _substituir_simbolos_especiais(texto: str) -> str:
    """Substitui símbolos que podem ser mal interpretados pelo TTS."""
    print("   -> Substituindo símbolos especiais...")
    substituicoes = {
        '&': ' e ',
        '@': ' arroba ',
        '#': ' ',  # Remove hashtags, que são ruído no texto de um livro
        '$': ' dólares ', # R$ já é tratado, isto é para o $ avulso
        '/': ' ou ', # "ou" soa mais natural que "barra" na maioria dos contextos
        '\\': ' ', # Barras invertidas são geralmente artefatos de formatação
        '_': ' ', # Remove underscores avulsos
        '+': ' mais ',
        '=': ' igual a ',
        '<': ' menor que ',
        '>': ' maior que ',
    }
    for simbolo, substituicao in substituicoes.items():
        texto = texto.replace(simbolo, substituicao)
    return texto


def _remover_formatacao_markdown(texto: str) -> str:
    """Remove formatação de ênfase como negrito e itálico."""
    print("   -> Removendo formatação Markdown (* e _)...")
    # Remove negrito (**) e itálico (_)
    texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)
    texto = re.sub(r'_(.*?)_', r'\1', texto)
    texto = re.sub(r'\*([^*]+)\*', r'\1', texto)
    return texto


def _remontar_paragrafos(texto: str) -> str:
    """Corrige quebras de linha indevidas no meio dos parágrafos."""
    print("   -> Remontando parágrafos...")
    # Marca o final de parágrafos reais
    texto = re.sub(r'\n\s*\n', '|||NEW_PAR|||', texto)
    # Remove quebras de linha simples e junta as palavras
    texto = texto.replace('\n', ' ')
    texto = re.sub(r'(\w+)-\s+', r'\1', texto) # Une palavras separadas por hífen
    # Restaura os parágrafos marcados
    texto = texto.replace('|||NEW_PAR|||', '\n\n')
    return texto.strip()


# ================== FUNÇÕES DE FORMATAÇÃO E EXPANSÃO ==================

def _formatar_capitulos_e_titulos(texto: str) -> str:
    """Padroniza a formatação de títulos de capítulos."""
    print("   -> Formatando capítulos e títulos...")

    def substituir_capitulo(match):
        numero_extenso = match.group(1).strip().upper()
        titulo = match.group(2).strip().title()
        # Converte número por extenso para numeral (Ex: "UM" -> "1")
        numero_final = CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(numero_extenso, numero_extenso)
        # Garante que o título termine com pontuação para uma pausa na leitura
        if not re.search(r'[.!?]$', titulo):
            titulo += "."
        return f"\n\nCAPÍTULO {numero_final}.\n\n{titulo}\n\n"

    padrao = re.compile(r'CAP[ÍI]TULO\s+([\w\s]+?)\.\s*\n\n([^\n]+)', re.IGNORECASE)
    return padrao.sub(substituir_capitulo, texto)


def _expandir_abreviacoes_comuns(texto: str) -> str:
    """Expande abreviações, siglas e unidades para uma leitura natural."""
    print("   -> Expandindo abreviações e siglas...")
    substituicoes = {
        # Pessoas e títulos
        r'\bSr\.': 'Senhor', r'\bSra\.': 'Senhora', r'\bSrta\.': 'Senhorita',
        r'\bDr\.': 'Doutor', r'\bDra\.': 'Doutora',
        r'\bProf\.': 'Professor', r'\bProfa\.': 'Professora',
        # Endereços
        r'\bAv\.': 'Avenida', r'\bR\.': 'Rua', r'\bRod\.': 'Rodovia', r'\bPça\.': 'Praça',
        # Unidades e diversos
        r'\bN[º°o]\b': 'número', r'\bn[º°o]\b': 'número',
        r'\bKg\b': 'quilograma', r'\bkm\b': 'quilômetro', r'\bcm\b': 'centímetro',
        r'\bmm\b': 'milímetro', r'\bml\b': 'mililitro', r'\bL\b': 'litro',
        r'\b°C\b': 'graus Celsius',
        r'\bm²\b': 'metros quadrados', r'\bm³\b': 'metros cúbicos',
        r'\bEtc\.?': 'et cetera', r'\bObs\.?': 'observação',
        # Siglas comuns
        r'\bEUA\b': 'Estados Unidos da América', r'\bONU\b': 'Organização das Nações Unidas',
        r'\bRJ\b': 'Rio de Janeiro', r'\bSP\b': 'São Paulo', r'\bDF\b': 'Distrito Federal',
        r'\bS/N\b': 'sem número',
    }
    for padrao, subst in substituicoes.items():
        texto = re.sub(padrao, subst, texto, flags=re.IGNORECASE)
    return texto


def _corrigir_apostrofos_estrangeiros(texto: str) -> str:
    """Corrige apóstrofos de possessivo em inglês (Ex: Dursley’s → Dursleys)."""
    texto = re.sub(r"([A-Za-z])’s\b", r"\1s", texto)
    texto = re.sub(r"([A-Za-z])'s\b", r"\1s", texto)
    return texto


def _expandir_numeros(texto: str) -> str:
    """Converte números em texto por extenso."""
    print("   -> Expandindo números...")

    # Função para tratar porcentagens: 25% -> vinte e cinco por cento
    def porcentagem(match):
        try:
            num_str = match.group(1).replace('.', '').replace(',', '')
            num_extenso = num2words(int(num_str), lang='pt_BR')
            return f"{num_extenso} por cento"
        except ValueError:
            return f"{match.group(1)} por cento"
    texto = re.sub(r'(\d[\d.,]*)\s*%', porcentagem, texto)

    # Função para tratar números ordinais: 2º -> segundo, 3ª -> terceira
    def ordinal(match):
        try:
            n = int(match.group(1))
            sufixo = match.group(2).lower()
            if sufixo in ('o', 'º'):
                return num2words(n, lang='pt_BR', to='ordinal')
            elif sufixo in ('a', 'ª'):
                s = num2words(n, lang='pt_BR', to='ordinal')
                return s[:-1] + 'a' if s.endswith('o') else s
        except (ValueError, IndexError):
            return match.group(0)
        return match.group(0)
    texto = re.sub(r'\b(\d+)([oOaAºª])\b', ordinal, texto)

    # Função para tratar valores monetários: R$ 10 -> dez reais
    def monetario(match):
        valor = match.group(1).replace('.', '').replace(',', '')
        try:
            return f"{num2words(int(valor), lang='pt_BR')} reais"
        except ValueError:
            return match.group(0)
    texto = re.sub(r'R\$\s*(\d[\d.,]*)', monetario, texto)

    # Função para converter números cardinais, ignorando anos e números longos
    def cardinal(match):
        num_str = match.group(0)
        try:
            valor = int(num_str)
            # Evita converter anos ou números muito grandes (códigos, etc.)
            if 1900 <= valor <= 2100 or len(num_str) > 6:
                return num_str
            return num2words(valor, lang='pt_BR')
        except ValueError:
            return num_str
    texto = re.sub(r'\b\d+\b', cardinal, texto)
    return texto


def _limpeza_final(texto: str) -> str:
    """Aplica ajustes finais de espaçamento e pontuação."""
    print("   -> Limpando e ajustando espaçamento final...")
    # Adiciona quebra de parágrafo antes de um diálogo iniciado por travessão
    texto = re.sub(r'([.!?])\s*([—-])', r'\1\n\n\2', texto)

    # Remove espaços antes de pontuação
    texto = re.sub(r'\s+([,.!?;:])', r'\1', texto)
    # Garante espaço depois de pontuação
    texto = re.sub(r'([,.!?;:])(\w)', r'\1 \2', texto)
    # Remove espaços múltiplos
    texto = re.sub(r' {2,}', ' ', texto)
    # Remove quebras de linha múltiplas
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    # Garante que todo parágrafo termine com uma pontuação para dar ritmo à leitura
    paragrafos = []
    for p in texto.split('\n\n'):
        p = p.strip()
        if p and not p.startswith("CAPÍTULO") and not re.search(r'[.!?]$', p):
            p += '.'
        if p:
            paragrafos.append(p)
    return '\n\n'.join(paragrafos).strip()


# ================== FUNÇÃO PRINCIPAL ==================

def formatar_texto_para_tts(texto_bruto: str) -> str:
    """
    Executa todas as etapas de limpeza e formatação para preparar o texto
    para uma leitura natural e agradável em um sistema TTS.
    """
    print("🧩 Iniciando processamento completo do texto...")

    texto = unicodedata.normalize('NFKC', texto_bruto)
    texto = _remover_lixo_textual(texto)
    texto = _normalizar_pontuacao(texto)
    texto = _substituir_simbolos_especiais(texto)
    texto = _remover_formatacao_markdown(texto)
    texto = _remontar_paragrafos(texto)
    texto = _corrigir_apostrofos_estrangeiros(texto)
    texto = _formatar_capitulos_e_titulos(texto)
    texto = _expandir_abreviacoes_comuns(texto)
    texto = _expandir_numeros(texto)
    texto = _limpeza_final(texto)

    print("✅ Texto pronto para TTS.")
    return texto

# Exemplo de como usar a função:
#
# if __name__ == '__main__':
#     texto_de_exemplo = """
#     CAPÍTULO UM.
#
#     O Sr. & a Sra. Dursley, da rua dos Alfeneiros, nº 4, orgulhavam-se de dizer que eram perfeitamente normais, muito obrigado. Custava a crer que alguém se metesse em coisas estranhas ou misteriosas, porque não pactuavam com disparates. _Isso é 50% verdade!_
#     O preço é R$ 50,00 e o frete é $3.
#     Contato: email@exemplo.com / site.com
#     """
#     texto_processado = formatar_texto_para_tts(texto_de_exemplo)
#     print("\n--- TEXTO PROCESSADO ---\n")
#     print(texto_processado)
