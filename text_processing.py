# -*- coding: utf-8 -*-
"""
Módulo responsável por toda a limpeza, formatação e preparação
do texto para a conversão em áudio (TTS). Esta é uma versão
aprimorada com lógica de limpeza e reconstrução de texto mais robusta.
"""
import re
import unicodedata
from num2words import num2words

# Importa as configurações do nosso arquivo config.py
# Supõe-se que config.py contém CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM
import config

# ================== CONSTANTES DE LIMPEZA ==================

# Textos de rodapé/cabeçalho repetidos que devem ser removidos
TEXTOS_REPETIDOS_PARA_REMOVER = [
    "Esse livro é protegido pelas leis internacionais de Copyright.",
    "A Detonando Home Page não se responsabiliza por qualquer dano que esse material possa causar.",
    "Seu uso deve ser exclusivamente pessoal.",
    "Distribuído gratuitamente pela Detonando Home Page – www.",
    "portaldetonando.",
    "cjb.",
    "net - Sempre uma novidade para você!"
]

# ================== FUNÇÕES AUXILIARES DE LIMPEZA E FORMATAÇÃO ==================

def _remover_lixo_textual(texto: str) -> str:
    """Remove cabeçalho inicial e textos de rodapé repetidos."""
    print("   -> Removendo cabeçalhos e rodapés...")
    # Remove tudo antes do primeiro capítulo
    padrao_primeiro_cap = re.compile(r'(cap[íi]tulo)', re.IGNORECASE)
    match = padrao_primeiro_cap.search(texto)
    if match:
        texto = texto[match.start():]
    
    # Remove os textos repetitivos de copyright/distribuição
    for frase in TEXTOS_REPETIDOS_PARA_REMOVER:
        texto = texto.replace(frase, "")
        
    return texto

def _remontar_paragrafos(texto: str) -> str:
    """A função mais crucial: junta linhas quebradas incorretamente."""
    print("   -> Remontando parágrafos quebrados...")
    
    # Usa um placeholder para quebras de parágrafo genuínas (linhas em branco)
    placeholder_paragrafo = "|||NEW_PARAGRAPH|||"
    texto_com_placeholders = re.sub(r'\n\s*\n', placeholder_paragrafo, texto)
    
    # Remove todas as quebras de linha restantes, que estão no meio das frases
    texto_sem_quebras = texto_com_placeholders.replace('\n', ' ')
    
    # Restaura as quebras de parágrafo
    texto_corrigido = texto_sem_quebras.replace(placeholder_paragrafo, '\n\n')
    
    # Junta palavras que foram separadas por hífen no final da linha
    texto_corrigido = re.sub(r'(\w+)-\s+', r'\1', texto_corrigido)
    
    return texto_corrigido
    
def _formatar_capitulos_e_titulos(texto: str) -> str:
    """Localiza e formata os títulos dos capítulos de forma mais robusta."""
    print("   -> Formatando títulos de capítulos...")

    def substituir_capitulo(match):
        numero = match.group(1).strip().upper()
        titulo = match.group(2).strip().title()
        
        numero_final = config.CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(numero, numero)
        
        if not re.search(r'[.!?]$', titulo):
            titulo += "."
            
        return f"\n\nCAPÍTULO {numero_final}.\n\n{titulo}\n\n"

    padrao = re.compile(
        r'CAP[ÍI]TULO\s+([\w\s]+?)\.\s*\n\n([^\n]+)',
        re.IGNORECASE
    )
    return padrao.sub(substituir_capitulo, texto)

def _expandir_numeros_e_abreviacoes(texto: str) -> str:
    """Converte números para texto por extenso (cardinais, ordinais, monetários)."""
    print("   -> Expandindo números e abreviações...")

    # Função interna para converter ordinais, com a correção do 'ordinal_female'
    def substituir_ordinal(match):
        try:
            numero = int(match.group(1))
            terminacao = match.group(2).lower()
            
            if terminacao in ('o', 'º'):
                return num2words(numero, lang='pt_BR', to='ordinal')
            elif terminacao in ('a', 'ª'):
                # **INÍCIO DA CORREÇÃO**
                # Pega a forma masculina e a adapta para a feminina.
                ordinal_masc = num2words(numero, lang='pt_BR', to='ordinal')
                if ordinal_masc.endswith('o'):
                    return ordinal_masc[:-1] + 'a'
                return ordinal_masc  # Fallback para casos como 'terceira' que a lib pode já retornar certo
                # **FIM DA CORREÇÃO**
            return match.group(0)
        except (ValueError, NotImplementedError):
             return match.group(0) # Retorna o original se houver erro
             
    texto = re.sub(r'\b(\d+)([oOaAºª])\b', substituir_ordinal, texto)

    # Converte valores monetários (ex: R$ 50,00)
    def substituir_monetario(match):
        valor = match.group(1).replace('.', '')
        return f"{num2words(int(valor), lang='pt_BR')} reais"
    texto = re.sub(r'R\$\s*(\d[\d.]*)', substituir_monetario, texto)
    
    # Converte números cardinais, ignorando anos e números muito grandes
    def substituir_cardinal(match):
        num_str = match.group(0)
        try:
            num_int = int(num_str)
            if 1900 <= num_int <= 2100:
                return num_str
            if len(num_str) > 6:
                return num_str
            return num2words(num_int, lang='pt_BR')
        except ValueError:
            return num_str
    texto = re.sub(r'\b\d+\b', substituir_cardinal, texto)

    return texto

def _limpeza_final(texto: str) -> str:
    """Aplica as limpezas finais de pontuação, espaçamento e diálogos."""
    print("   -> Realizando limpezas finais...")

    # Remove números de página que possam ter sobrado
    texto = re.sub(r'^\s*\d+\s*$', '', texto, flags=re.MULTILINE)
    
    # Garante que diálogos com travessão comecem em um novo parágrafo
    texto = re.sub(r'([.!?])\s*([—―-–])', r'\1\n\n\2', texto)
    
    # Remove espaços antes de pontuação
    texto = re.sub(r'\s+([,.!?;:])', r'\1', texto)
    
    # Garante um espaço após a pontuação
    texto = re.sub(r'([,.!?;:])(\w)', r'\1 \2', texto)

    # Remove espaços duplos ou mais
    texto = re.sub(r' {2,}', ' ', texto)

    # Remove quebras de linha múltiplas, deixando no máximo duas
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    # Garante que cada parágrafo termine com uma pontuação final
    paragrafos_finais = []
    for p in texto.split('\n\n'):
        p_strip = p.strip()
        if p_strip:
            if not re.search(r'[.!?]$', p_strip) and not p_strip.startswith("CAPÍTULO"):
                p_strip += '.'
            paragrafos_finais.append(p_strip)
            
    return '\n\n'.join(paragrafos_finais)

# ================== FUNÇÃO PRINCIPAL DE FORMATAÇÃO ==================

def formatar_texto_para_tts(texto_bruto: str) -> str:
    """
    Orquestra todas as etapas de limpeza e formatação para criar um
    texto perfeito para a conversão em áudio (TTS).
    """
    print("Aplicando formatacoes avancadas ao texto...")
    
    # Etapa 1: Normalização básica e remoção de lixo grosso
    texto = unicodedata.normalize('NFKC', texto_bruto)
    texto = _remover_lixo_textual(texto)
    
    # Etapa 2: A etapa mais crítica, reconstruir os parágrafos corretamente
    texto = _remontar_paragrafos(texto)

    # Etapa 3: Formatação de elementos estruturais
    texto = _formatar_capitulos_e_titulos(texto)

    # Etapa 4: Expansão de números para leitura natural
    texto = _expandir_numeros_e_abreviacoes(texto)
    
    # Etapa 5: Limpeza final de pontuação, espaçamento e diálogos
    texto = _limpeza_final(texto)
    
    print("✅ Formatação de texto concluída.")
    return texto.strip()

