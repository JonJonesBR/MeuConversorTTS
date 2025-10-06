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
from typing import Dict, List, Pattern, Optional
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================== CONFIGURAÇÕES GLOBAIS ==================

# Mapeamento de números por extenso para numerais, usado na formatação de capítulos.
# Flexibilizado para aceitar variações (ex: "CATORZE" e "QUATORZE").
CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM: Dict[str, str] = {
    'UM': '1', 'DOIS': '2', 'TRÊS': '3', 'QUATRO': '4', 'CINCO': '5',
    'SEIS': '6', 'SETE': '7', 'OITO': '8', 'NOVE': '9', 'DEZ': '10',
    'ONZE': '11', 'DOZE': '12', 'TREZE': '13', 'CATORZE': '14', 'QUATORZE': '14',
    'QUINZE': '15', 'DEZESSEIS': '16', 'DEZESSETE': '17', 'DEZOITO': '18',
    'DEZENOVE': '19', 'VINTE': '20', 'VINTE E UM': '21', 'VINTE E DOIS': '22',
    'VINTE E TRÊS': '23', 'VINTE E QUATRO': '24', 'VINTE E CINCO': '25',
    'VINTE E SEIS': '26', 'VINTE E SETE': '27', 'VINTE E OITO': '28',
    'VINTE E NOVE': '29', 'TRINTA': '30'
}

# Correções para artefatos específicos de OCR ou extração.
CORRECOES_ESPECIFICAS: Dict[str, str] = {
    'observaçãoervadores': 'observadores',
    'observaçãoervando': 'observando',
    'observaçãoervava': 'observava',
    'gramasunnings': 'Grunnings',
    'Sr:;': 'Sr.'
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
    re.compile(r'\bV\.Sa\.', re.IGNORECASE): 'Vossa Senhoria',
    re.compile(r'\bExmo\.', re.IGNORECASE): 'Excelentíssimo',
    re.compile(r'\bExma\.', re.IGNORECASE): 'Excelentíssima',
    re.compile(r'\bEng\.', re.IGNORECASE): 'Engenheiro',
    re.compile(r'\bArq\.', re.IGNORECASE): 'Arquiteto',
    re.compile(r'\bAdv\.', re.IGNORECASE): 'Advogado',
    re.compile(r'\bPe\.', re.IGNORECASE): 'Padre',
    re.compile(r'\bFrei\b', re.IGNORECASE): 'Frei',
    re.compile(r'\bIr\.', re.IGNORECASE): 'Irmã',
    re.compile(r'\bIrma\b', re.IGNORECASE): 'Irmã',

    # --- Datas e Tempo ---
    re.compile(r'\bjan\.', re.IGNORECASE): 'janeiro',
    re.compile(r'\bfev\.', re.IGNORECASE): 'fevereiro',
    re.compile(r'\bmar\.', re.IGNORECASE): 'março',
    re.compile(r'\babr\.', re.IGNORECASE): 'abril',
    re.compile(r'\bmai\.', re.IGNORECASE): 'maio',
    re.compile(r'\bjun\.', re.IGNORECASE): 'junho',
    re.compile(r'\bjul\.', re.IGNORECASE): 'julho',
    re.compile(r'\bag\.', re.IGNORECASE): 'agosto',
    re.compile(r'\bset\.', re.IGNORECASE): 'setembro',
    re.compile(r'\bout\.', re.IGNORECASE): 'outubro',
    re.compile(r'\bnov\.', re.IGNORECASE): 'novembro',
    re.compile(r'\bdez\.', re.IGNORECASE): 'dezembro',
    re.compile(r'\bs\.sec\.', re.IGNORECASE): 'século',
    re.compile(r'\bsec\.', re.IGNORECASE): 'século',
    re.compile(r'\bano\s+sec\.', re.IGNORECASE): 'ano século',

    # --- Endereços ---
    re.compile(r'\bAv\.', re.IGNORECASE): 'Avenida',
    re.compile(r'\bR\.', re.IGNORECASE): 'Rua',
    re.compile(r'\bRod\.', re.IGNORECASE): 'Rodovia',
    re.compile(r'\bPça\.', re.IGNORECASE): 'Praça',
    re.compile(r'\bEst\.', re.IGNORECASE): 'Estrada',
    re.compile(r'\bS/N\b', re.IGNORECASE): 'sem número',
    re.compile(r'\bn\.\s*o\.', re.IGNORECASE): 'número', # AJUSTE: Captura "n. o."
    re.compile(r'\bN[º°]\b', re.IGNORECASE): 'número', # AJUSTE: Não captura mais a palavra "no"

    # --- Unidades e Medidas ---
    re.compile(r'\bKg\b', re.IGNORECASE): 'quilogramas', # Plural soa mais natural
    re.compile(r'\bKm\b', re.IGNORECASE): 'quilômetros',
    re.compile(r'\bcm\b', re.IGNORECASE): 'centímetros',
    re.compile(r'\bmm\b', re.IGNORECASE): 'milímetros',
    re.compile(r'\bml\b', re.IGNORECASE): 'mililitros',
    re.compile(r'\bL\b'): 'litros', # "L" maiúsculo para evitar substituir "l" em palavras
    re.compile(r'°C\b', re.IGNORECASE): 'graus Celsius',
    re.compile(r'\bm²\b', re.IGNORECASE): 'metros quadrados',
    re.compile(r'\bm³\b', re.IGNORECASE): 'metros cúbicos',
    re.compile(r'\bKm/h\b', re.IGNORECASE): 'quilômetros por hora',
    re.compile(r'\bh\b', re.IGNORECASE): 'hora',
    re.compile(r'\bmin\b', re.IGNORECASE): 'minuto',
    re.compile(r'\bsg\b', re.IGNORECASE): 'segundo',
    re.compile(r'\bmg\b', re.IGNORECASE): 'miligrama',
    re.compile(r'\bgr\.?\b', re.IGNORECASE): 'gramas', # AJUSTE: Não captura "gr" no início de palavras como "grande"

    # --- Siglas Institucionais (Exemplos) ---
    re.compile(r'\bONU\b'): 'Organização das Nações Unidas',
    re.compile(r'\bOMS\b'): 'Organização Mundial da Saúde',
    re.compile(r'\bSTF\b'): 'Supremo Tribunal Federal',

    # --- Diversos ---
    re.compile(r'\bEtc\.?', re.IGNORECASE): 'et cetera',
    re.compile(r'\bObs\.?', re.IGNORECASE): 'observação',
    re.compile(r'\bvs\.', re.IGNORECASE): 'versus',
    re.compile(r'\bp\.\s*(\d+)', re.IGNORECASE): r'página \1', # Ex: p. 12
    re.compile(r'\bpágs?\.', re.IGNORECASE): 'páginas',
    re.compile(r'\bcf\.', re.IGNORECASE): 'conforme',
    re.compile(r'\bi\.e\.', re.IGNORECASE): 'isto é',
    re.compile(r'\be\.g\.', re.IGNORECASE): 'por exemplo',
}

# ================== FUNÇÕES DE LIMPEZA E NORMALIZAÇÃO ==================

def _remover_lixo_textual(texto: str) -> str:
    """Remove cabeçalhos, rodapés e outros textos repetitivos de e-books."""
    try:
        logger.info("Removendo lixo textual e artefatos de digitalização...")
        if not texto:
            return texto
            
        # Tenta encontrar o primeiro capítulo para remover qualquer texto introdutório
        match = re.search(r'(cap[íi]tulo\s+[\w\d]+|sum[áa]rio|pr[óo]logo|pref[áa]cio)', texto, re.IGNORECASE)
        if match:
            texto = texto[match.start():]

        # Remove textos repetitivos comuns
        textos_a_remover = [
            r"Esse livro é protegido.*",
            r"www\.\s*portaldetonando\.\s*cjb\.\s*net.*",
            r"\bCopyright\b.*",
            r"Distribuído gratuitamente.*",
        ]
        for padrao in textos_a_remover:
            texto = re.sub(padrao, "", texto, flags=re.IGNORECASE | re.MULTILINE)

        return texto
    except Exception as e:
        logger.error(f"Erro ao remover lixo textual: {e}")
        return texto

def _remover_artefatos_visuais(texto: str) -> str:
    """Remove elementos visuais como separadores de cena e números de página."""
    try:
        logger.info("Removendo artefatos visuais...")
        if not texto:
            return texto
        
        # Remove separadores de cena (ex: "_. " em uma linha)
        texto = re.sub(r'^\s*_\.\s*$', '', texto, flags=re.MULTILINE)

        # Remove números de página que aparecem no meio do texto, geralmente no final de uma linha
        # Cria uma lista de números por extenso para busca
        numeros_extenso = list(CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.keys())
        numeros_extenso.extend(['cem', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos']) # Adicionar mais se necessário
        padrao_palavras = r'\b(' + '|'.join(numeros_extenso) + r')\b\s*\.'
        
        # Remove números (dígitos ou por extenso) que quebram parágrafos
        texto = re.sub(rf'({padrao_palavras})\s*\n', '\n', texto, flags=re.IGNORECASE)
        texto = re.sub(r'(\b\d+\b\s*\.)\s*\n', '\n', texto, flags=re.IGNORECASE)

        # Remove os mesmos padrões quando seguidos por um espaço e uma letra maiúscula (início de frase)
        texto = re.sub(rf'\s+{padrao_palavras}\s+(?=[A-Z])', ' ', texto, flags=re.IGNORECASE)
        texto = re.sub(r'\s+\b\d+\b\s*\.\s+(?=[A-Z])', ' ', texto, flags=re.IGNORECASE)

        return texto
    except Exception as e:
        logger.error(f"Erro ao remover artefatos visuais: {e}")
        return texto

def _corrigir_artefatos_especificos(texto: str) -> str:
    """Corrige erros de extração de texto específicos e conhecidos."""
    try:
        logger.info("Corrigindo artefatos de texto específicos...")
        if not texto:
            return texto
            
        for erro, correcao in CORRECOES_ESPECIFICAS.items():
            texto = texto.replace(erro, correcao)
        return texto
    except Exception as e:
        logger.error(f"Erro ao corrigir artefatos específicos: {e}")
        return texto


def _normalizar_caracteres_e_pontuacao(texto: str) -> str:
    """Normaliza caracteres Unicode, aspas, travessões e outros símbolos."""
    try:
        logger.info("Normalizando caracteres e pontuação...")
        if not texto:
            return texto
            
        texto = unicodedata.normalize('NFKC', texto)

        substituicoes = {
            '[“”«»]': '"',
            "[‘’]": "'",
            '[–—―‐‑]': '—',
            '…': '...',
            '; ': ', ', # AJUSTE: Converte ponto e vírgula em vírgula
            ';': ',',   # AJUSTE: Converte ponto e vírgula em vírgula
        }
        for padrao, sub in substituicoes.items():
            texto = re.sub(padrao, sub, texto)

        texto = re.sub(r'\s*—\s*', ' — ', texto)
        return texto
    except Exception as e:
        logger.error(f"Erro ao normalizar caracteres e pontuação: {e}")
        return texto

def _substituir_simbolos_por_extenso(texto: str) -> str:
    """Substitui símbolos que podem ser mal interpretados pelo TTS."""
    try:
        logger.info("Substituindo símbolos por extenso...")
        if not texto:
            return texto
            
        texto = re.sub(r'\*\*(.*?)\*\*', r' \1 ', texto)
        texto = re.sub(r'\*(.*?)\*', r' \1 ', texto)
        texto = re.sub(r'__(.*?)__', r' \1 ', texto)
        texto = re.sub(r'_(.*?)_', r' \1 ', texto)
        
        substituicoes = {
            '&': ' e ',
            '@': ' arroba ',
            '#': ' cerquilha ',
            '%': ' por cento', # Removido espaço inicial para casos como "50%"
            '/': ' barra ',
            '\\': ' ',
            '+': ' mais ',
            '=': ' igual a ',
        }
        padrao_compilado = re.compile("|".join(
            re.escape(k) for k in sorted(substituicoes.keys(), key=len, reverse=True)
        ))

        return padrao_compilado.sub(lambda m: substituicoes[m.group(0)], texto)
    except Exception as e:
        logger.error(f"Erro ao substituir símbolos por extenso: {e}")
        return texto


def _remontar_paragrafos(texto: str) -> str:
    """Corrige quebras de linha indevidas no meio dos parágrafos."""
    try:
        logger.info("Remontando parágrafos...")
        if not texto:
            return texto
            
        # Une sentenças quebradas por uma nova linha
        texto = re.sub(r'([.!?])\n(\w)', r'\1 \2', texto)
        texto = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)

        linhas = texto.split('\n')
        paragrafos_remontados = []
        paragrafo_atual = ""
        for linha in linhas:
            linha = linha.strip()
            if not linha:
                if paragrafo_atual:
                    paragrafos_remontados.append(paragrafo_atual)
                    paragrafo_atual = ""
            else:
                if paragrafo_atual:
                    paragrafo_atual += " " + linha
                else:
                    paragrafo_atual = linha
        if paragrafo_atual:
            paragrafos_remontados.append(paragrafo_atual)

        return "\n\n".join(p.strip() for p in paragrafos_remontados)
    except Exception as e:
        logger.error(f"Erro ao remontar parágrafos: {e}")
        return texto

# ================== FUNÇÕES DE EXPANSÃO PARA TTS ==================

def _formatar_capitulos(texto: str) -> str:
    """Padroniza a formatação de títulos de capítulos para uma leitura clara."""
    try:
        logger.info("Formatando títulos de capítulos...")
        if not texto:
            return texto

        def substituir_capitulo(match: re.Match) -> str:
            prefixo = match.group(1).strip()
            numero_str = match.group(2).strip().upper()
            titulo_opcional = match.group(3)
            
            titulo = titulo_opcional.strip().rstrip(' .') if titulo_opcional else ""
            numero_final = CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(numero_str, numero_str)

            if titulo:
                return f"\n\n{prefixo.upper()} {numero_final}. {titulo}.\n\n"
            else:
                return f"\n\n{prefixo.upper()} {numero_final}.\n\n"

        # AJUSTE: Padrão mais robusto para capturar títulos de capítulo com ou sem título de texto
        padrao = re.compile(
            r'^\s*(cap[íi]tulo)\s+([\d\w\s]+)\s*[-–—.]*\s*(?:\n\s*\n\s*(.*?)\s*\.?)?',
            re.IGNORECASE | re.MULTILINE
        )
        return padrao.sub(substituir_capitulo, texto)
    except Exception as e:
        logger.error(f"Erro ao formatar capítulos: {e}")
        return texto

def _expandir_abreviacoes(texto: str) -> str:
    """Expande abreviações, siglas e unidades para uma leitura natural."""
    try:
        logger.info("Expandindo abreviações e siglas...")
        if not texto:
            return texto
            
        for padrao, substituicao in EXPANSOES_TEXTUAIS.items():
            texto = padrao.sub(substituicao, texto)
        return texto
    except Exception as e:
        logger.error(f"Erro ao expandir abreviações: {e}")
        return texto

def _expandir_numeros(texto: str) -> str:
    """Converte números em texto por extenso, tratando casos especiais."""
    try:
        logger.info("Expandindo números para leitura...")
        if not texto:
            return texto

        def ordinal(match: re.Match) -> str:
            try:
                n = int(match.group(1))
                sufixo = match.group(2).lower()
                if sufixo in ('o', 'º'):
                    return num2words(n, lang='pt_BR', to='ordinal')
                elif sufixo in ('a', 'ª'):
                    ordinal_masc = num2words(n, lang='pt_BR', to='ordinal')
                    return ordinal_masc[:-1] + 'a' if ordinal_masc.endswith('o') else ordinal_masc
            except (ValueError, IndexError):
                return match.group(0)
            return match.group(0)
        texto = re.sub(r'\b(\d+)([oOaAºª])\b', ordinal, texto)

        def monetario(match: re.Match) -> str:
            try:
                valor_str = match.group(1).replace('.', '').replace(',', '.')
                reais_str, centavos_str = (valor_str.split('.') + ['0'])[:2]
                reais = int(reais_str)
                centavos_str = centavos_str.ljust(2, '0')[:2]
                centavos = int(centavos_str)
                
                str_reais = num2words(reais, lang='pt_BR') + (' real' if reais == 1 else ' reais')
                if centavos > 0:
                    str_centavos = num2words(centavos, lang='pt_BR') + (' centavo' if centavos == 1 else ' centavos')
                    return f"{str_reais} e {str_centavos}"
                return str_reais
            except (ValueError, IndexError):
                return match.group(0)
        texto = re.sub(r'R\$\s*([\d.,]+)', monetario, texto)

        def cardinal(match: re.Match) -> str:
            try:
                num_str = match.group(0)
                num_int = int(num_str)
                
                if 1900 <= num_int <= 2100 or len(num_str) > 6:
                    return num_str
                    
                return num2words(num_int, lang='pt_BR')
            except ValueError:
                return match.group(0)
        texto = re.sub(r'\b\d+\b', cardinal, texto)
        
        return texto
    except Exception as e:
        logger.error(f"Erro ao expandir números: {e}")
        return texto

def _limpeza_final(texto: str) -> str:
    """Aplica ajustes finais de espaçamento e pontuação para fluidez."""
    try:
        logger.info("Realizando limpeza final e ajustes de ritmo...")
        if not texto:
            return texto
            
        texto = re.sub(r'([.!?"])\s*([—-])', r'\1\n\n\2', texto)
        texto = re.sub(r'\s+([,.!?;:])', r'\1', texto)
        texto = re.sub(r'([,.!?;:])(?=\w)', r'\1 ', texto) # AJUSTE: Garante espaço após pontuação
        texto = re.sub(r' {2,}', ' ', texto)
        texto = re.sub(r'\n{3,}', '\n\n', texto)

        paragrafos = texto.split('\n\n')
        paragrafos_formatados = []
        for p in paragrafos:
            p_strip = p.strip()
            if p_strip and not p_strip.startswith('—') and not re.search(r'[.!?"]$', p_strip):
                p += '.'
            paragrafos_formatados.append(p)

        return '\n\n'.join(paragrafos_formatados).strip()
    except Exception as e:
        logger.error(f"Erro na limpeza final: {e}")
        return texto

# ================== FUNÇÃO PRINCIPAL ==================

def formatar_texto_para_tts(texto_bruto: str, log_progresso: bool = True) -> str:
    """
    Executa um pipeline completo de limpeza e formatação para preparar o texto
    para uma leitura natural e agradável em um sistema TTS.
    """
    if log_progresso:
        logger.info("Iniciando processamento completo do texto para TTS...")
    
    if not texto_bruto or not isinstance(texto_bruto, str):
        logger.warning("Texto de entrada inválido ou vazio")
        return ""

    try:
        # Pipeline de processamento com ordem ajustada
        texto = preprocessar_texto(texto_bruto)
        texto = _remover_lixo_textual(texto)
        texto = _corrigir_artefatos_especificos(texto)
        texto = _remover_artefatos_visuais(texto)
        texto = _remontar_paragrafos(texto)
        texto = _normalizar_caracteres_e_pontuacao(texto)
        texto = _substituir_simbolos_por_extenso(texto)  
        texto = _expandir_abreviacoes(texto)
        texto = _expandir_numeros(texto)      
        texto = _formatar_capitulos(texto)
        texto = _limpeza_final(texto)

        if log_progresso:
            logger.info("Texto pronto para TTS.")
        return texto
    except Exception as e:
        logger.error(f"Erro no processamento completo do texto: {e}")
        return texto_bruto

# ================== FUNÇÕES ADICIONAIS ==================

def validar_texto_para_tts(texto: str) -> tuple[bool, List[str]]:
    """Valida o texto para garantir que está adequado para processamento TTS."""
    erros = []
    if not texto or not isinstance(texto, str) or len(texto.strip()) < 10:
        erros.append("Texto de entrada inválido, vazio ou muito curto")
    return len(erros) == 0, erros

def preprocessar_texto(texto: str) -> str:
    """Função auxiliar que faz um pré-processamento básico do texto."""
    if not texto:
        return ""
    texto = texto.strip()
    texto = re.sub(r'\r\n?', '\n', texto)
    texto = re.sub(r'\n\s*\n', '\n\n', texto)
    return texto

# ================== EXEMPLO DE USO ==================

if __name__ == '__main__':
    # Tenta ler o arquivo de texto fornecido pelo usuário
    try:
        with open('Harry_Potter_e_a_Pedra_Filosofal_formatado.txt', 'r', encoding='utf-8') as f:
            texto_de_exemplo = f.read()
        logger.info("Arquivo 'Harry_Potter_e_a_Pedra_Filosofal_formatado.txt' lido com sucesso.")
    except FileNotFoundError:
        logger.error("Arquivo de exemplo não encontrado. Usando texto interno.")
        texto_de_exemplo = """
        Capítulo Um -. O menino que sobreviveu . O Sr. Dursley; da rua dos Alfeneiros, n. o. quatro, se orgulhava de dizer que eram normais. Eram as últimas pessoas número mundo...
        ... uma nova três. moda idiota. O St Dursley ficou pregado número chão.
        """
    
    valido, erros = validar_texto_para_tts(texto_de_exemplo)
    if not valido:
        print("Erros de validação:", erros)
    else:
        texto_processado = formatar_texto_para_tts(texto_de_exemplo)
        
        # Salva o resultado em um novo arquivo
        try:
            with open('Harry_Potter_corrigido.txt', 'w', encoding='utf-8') as f_out:
                f_out.write(texto_processado)
            logger.info("Texto processado salvo em 'Harry_Potter_corrigido.txt'.")
            print("\n--- TEXTO PROCESSADO E SALVO COM SUCESSO ---\n")
            print("Amostra do resultado:")
            print(texto_processado[:1000] + "...")
        except IOError as e:
            logger.error(f"Não foi possível salvar o arquivo: {e}")
            print("\n--- TEXTO PROCESSADO (não foi possível salvar) ---\n")
            print(texto_processado)
