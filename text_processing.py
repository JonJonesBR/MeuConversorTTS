# -*- coding: utf-8 -*-
"""
Processador de texto completo para TTS.

Este script combina a extração de texto de múltiplos formatos de arquivo
(PDF, DOCX, EPUB, TXT) com um pipeline avançado de limpeza e formatação,
otimizando o conteúdo para sintetizadores de voz (Text-to-Speech).
"""
import os
import argparse
import re
import logging
import unicodedata

# Tente importar as bibliotecas necessárias e forneça instruções claras se faltarem.
try:
    import fitz  # PyMuPDF
    import docx
    from bs4 import BeautifulSoup
    from ebooklib import epub, ITEM_DOCUMENT
    from num2words import num2words
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Uma ou mais bibliotecas necessárias não estão instaladas.")
    print("Por favor, instale todas com o comando: pip install PyMuPDF python-docx ebooklib BeautifulSoup4 num2words")
    exit()

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ================== CONFIGURAÇÕES DE FORMATAÇÃO ==================

# Mapeamento de abreviações e siglas para sua forma extensa.
EXPANSOES_TEXTUAIS = {
    re.compile(r'\bSr\.', re.IGNORECASE): 'Senhor',
    re.compile(r'\bSra\.', re.IGNORECASE): 'Senhora',
    re.compile(r'\bDr\.', re.IGNORECASE): 'Doutor',
    re.compile(r'\bAv\.', re.IGNORECASE): 'Avenida',
    re.compile(r'\bR\.', re.IGNORECASE): 'Rua',
    re.compile(r'\bEtc\.?', re.IGNORECASE): 'et cetera',
    re.compile(r'\bvs\.', re.IGNORECASE): 'versus',
    re.compile(r'\bp\.\s*(\d+)', re.IGNORECASE): r'página \1',
    # Adicione outras expansões do script original aqui se necessário...
}

# ================== FUNÇÕES DE EXTRAÇÃO DE TEXTO ==================

def extract_from_pdf(filepath: str) -> str:
    """Extrai texto de um arquivo .pdf."""
    try:
        doc = fitz.open(filepath)
        text = "".join(page.get_text() for page in doc.pages())
        doc.close()
        return text
    except Exception as e:
        logging.error(f"Erro ao processar o PDF '{filepath}': {e}")
        return ""

def extract_from_docx(filepath: str) -> str:
    """Extrai texto de um arquivo .docx."""
    try:
        doc = docx.Document(filepath)
        return "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        logging.error(f"Erro ao processar o DOCX '{filepath}': {e}")
        return ""

def extract_from_epub(filepath: str) -> str:
    """Extrai texto de um arquivo .epub."""
    try:
        book = epub.read_epub(filepath)
        content = []
        for item in book.get_items_of_type(ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            content.append(soup.get_text(separator='\n', strip=True))
        return "\n\n".join(content)
    except Exception as e:
        logging.error(f"Erro ao processar o EPUB '{filepath}': {e}")
        return ""

def extract_from_txt(filepath: str) -> str:
    """Extrai texto de um arquivo .txt."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo TXT '{filepath}': {e}")
        return ""

# ================== PIPELINE DE LIMPEZA E FORMATAÇÃO PARA TTS ==================

def formatar_texto_para_tts(texto_bruto: str) -> str:
    """
    Executa um pipeline completo de limpeza e formatação para preparar o texto para TTS.
    """
    if not texto_bruto or not isinstance(texto_bruto, str):
        logging.warning("Texto de entrada inválido ou vazio.")
        return ""

    logging.info("Iniciando pipeline de formatação para TTS...")

    # 1. Remover copyright e numeração de páginas
    texto = re.sub(r'_Distribuído gratuitamente.*?você!_', '', texto_bruto, flags=re.DOTALL)
    texto = re.sub(r'^\s*-+\s*\d+\s*-+$', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'^[ ]*\d+[ ]*$', '', texto, flags=re.MULTILINE)
    texto = re.sub(r'^\s*Esse livro é protegido pelas leis internacionais de Copyright\..*?Seu uso deve ser exclusivamente pessoal\.\s*$', '', texto, flags=re.MULTILINE | re.DOTALL)

    # 2. Padronizar cabeçalhos de capítulo
    # Trata diferentes formatos de cabeçalhos de capítulo
    # Primeiro, trata o caso com traço e padrões de separação
    texto = re.sub(r'^\s*-+\s*CAPÍTULO\s+(.+?)\s*-+\s*$', r'Capítulo \1', texto, flags=re.MULTILINE | re.IGNORECASE)
    # Trata o caso com dois pontos ou traço (mais robusto)
    texto = re.sub(r'^\s*CAPÍTULO\s*(\w+)\s*[-:]\s*(.+)$', r'Capítulo \1: \2', texto, flags=re.MULTILINE | re.IGNORECASE)
    # Trata o caso mais genérico de capítulo com qualquer caractere após o número
    # Correção: Remove traços extras antes de aplicar este padrão
    texto = re.sub(r'^\s*CAPÍTULO\s*(\w+)\s*-\s*(.+)$', r'Capítulo \1: \2', texto, flags=re.MULTILINE | re.IGNORECASE)
    # Trata casos especiais de formatação de títulos (como **texto**)
    texto = re.sub(r'\*\*(.+?)\*\*', r'\1', texto)
    # Remove caracteres de formatação extras que podem causar problemas
    texto = re.sub(r'\s*[-*]+\s*', ' ', texto)
    # Corrige problemas de codificação e caracteres especiais
    texto = texto.replace('', '')  # Remove caracteres de codificação inválida
    # Remove barras invertidas extras
    texto = texto.replace('\\', '')

    # 3. Normalizar quebras de linha e hifenização
    texto = re.sub(r'-\s*\n', ' ', texto)  # Remove hífens no final da linha e substitui por espaço
    texto = re.sub(r'(?<!\n)\n(?!\n)', ' ', texto)  # Junta parágrafos quebrados
    texto = re.sub(r'\n{2,}', '\n\n', texto)  # Garante parágrafos com linha dupla

    # 4. Normalizar caracteres e pontuação
    texto = unicodedata.normalize('NFKC', texto)
    texto = re.sub(r'[“”«»]', '"', texto)
    texto = re.sub(r"[‘’]", "'", texto)
    texto = re.sub(r'[–—―‐‑]', ' — ', texto)  # Usa travessão com espaços
    texto = re.sub(r'…', '...', texto)
    # Corrige ordinais antes da expansão de números para evitar conflitos
    texto = re.sub(r'(\d)o\.', r'\1º', texto)  # Corrige ordinal masculino
    texto = re.sub(r'(\d)a\.', r'\1ª', texto)  # Corrige ordinal feminino
    # Correção adicional para caracteres especiais problemáticos
    texto = texto.encode('utf-8', 'ignore').decode('utf-8')
    # Garantir codificação correta no final
    texto = texto.encode('latin1', 'ignore').decode('latin1')

    # 5. Remover underscores
    texto = re.sub(r'_', '', texto)

    # 6. Expandir abreviações
    for padrao, substituicao in EXPANSOES_TEXTUAIS.items():
        texto = padrao.sub(substituicao, texto)

    # 7. Expandir números (exemplo simplificado, pode ser expandido)
    # Otimização: Criar uma única função para lidar com todos os números
    def expandir_numeros(texto: str) -> str:
        def expandir_cardinal(match: re.Match) -> str:
            num_str = match.group(0)
            try:
                num_int = int(num_str)
                # Evita converter anos ou números muito grandes
                if 1900 <= num_int <= 2100 or len(num_str) > 6:
                    return num_str
                return num2words(num_int, lang='pt_BR')
            except ValueError:
                return num_str
        return re.sub(r'\b\d+\b', expandir_cardinal, texto)
    
    texto = expandir_numeros(texto)
            
    # 8. Limpeza final - otimização para melhorar a qualidade do TTS
    # Adiciona pausas após pontos e vírgulas para melhor pronunciação
    # Melhoria: Adicionar pausas mais inteligentes para TTS
    texto = re.sub(r'\.(\s*)([A-Z])', r'.\n\n\2', texto)  # Pausa após ponto e letra maiúscula
    texto = re.sub(r';(\s*)([A-Z])', r';\n\n\2', texto)   # Pausa após ponto-e-vírgula e letra maiúscula
    texto = re.sub(r',(\s*)([A-Z])', r',\n\n\2', texto)   # Pausa após vírgula e letra maiúscula
    texto = re.sub(r'\s+([,.!?;:])', r'\1', texto)  # Remove espaço antes da pontuação
    texto = re.sub(r' {2,}', ' ', texto)  # Remove espaços múltiplos
    texto = texto.strip()
    
    # 9. Otimização adicional para TTS: Adicionar pausas entre frases
    # Substituir múltiplos pontos por um único ponto seguido de pausa
    texto = re.sub(r'\.{3,}', '...', texto)
    
    logging.info("Processamento para TTS concluído.")
    return texto

# ================== FUNÇÃO PRINCIPAL E EXECUÇÃO ==================

def main():
    """Função principal para orquestrar a extração e formatação."""
    parser = argparse.ArgumentParser(
        description="Extrai e formata texto de múltiplos formatos de arquivo para uso com TTS.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_file", help="Caminho para o arquivo de entrada (pdf, docx, epub, txt).")
    parser.add_argument("output_file", help="Caminho para o arquivo de saída .txt.")
    args = parser.parse_args()

    input_path = args.input_file
    
    if not os.path.exists(input_path):
        logging.error(f"O arquivo de entrada '{input_path}' não foi encontrado.")
        return

    _, ext = os.path.splitext(input_path.lower())
    
    extractors = {
        '.pdf': extract_from_pdf,
        '.docx': extract_from_docx,
        '.epub': extract_from_epub,
        '.txt': extract_from_txt
    }

    if ext not in extractors:
        if ext == '.doc':
            logging.error("Arquivos .doc não são suportados. Por favor, converta para .docx primeiro.")
        else:
            logging.error(f"Formato de arquivo '{ext}' não suportado.")
        return

    logging.info(f"Processando arquivo: {input_path}")
    extractor_func = extractors[ext]
    raw_text = extractor_func(input_path)

    if not raw_text:
        logging.error("Nenhum texto foi extraído. O arquivo pode estar vazio ou corrompido.")
        return
        
    formatted_text = formatar_texto_para_tts(raw_text)

    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        print(f"\nSucesso! Texto formatado e salvo em: {args.output_file}")
    except IOError as e:
        logging.error(f"Erro ao salvar o arquivo de saída: {e}")

if __name__ == "__main__":
    main()
