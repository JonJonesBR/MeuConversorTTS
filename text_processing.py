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
    re.compile(r'\bNº\b', re.IGNORECASE): 'número',
    re.compile(r'\bkm\b', re.IGNORECASE): 'quilômetro',

    # --- Unidades e Medidas ---
    re.compile(r'\bN[º°o]\b', re.IGNORECASE): 'número',
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
    re.compile(r'\bg\b', re.IGNORECASE): 'grama',

    # --- Siglas Institucionais ---
    re.compile(r'\bIBGE\b'): 'Instituto Brasileiro de Geografia e Estatística',
    re.compile(r'\bFMI\b'): 'Fundo Monetário Internacional',
    re.compile(r'\bONU\b'): 'Organização das Nações Unidas',
    re.compile(r'\bOMS\b'): 'Organização Mundial da Saúde',
    re.compile(r'\bUNESCO\b'): 'Organização das Nações Unidas para a Educação, a Ciência e a Cultura',
    re.compile(r'\bFIFA\b'): 'Federação Internacional de Futebol Associado',
    re.compile(r'\bUEFA\b'): 'União das Associações Europeias de Futebol',
    re.compile(r'\bCPI\b'): 'Corte Penal Internacional',
    re.compile(r'\bSTF\b'): 'Supremo Tribunal Federal',
    re.compile(r'\bSTJ\b'): 'Superior Tribunal de Justiça',
    re.compile(r'\bTSE\b'): 'Tribunal Superior Eleitoral',
    re.compile(r'\bTST\b'): 'Tribunal Superior do Trabalho',
    re.compile(r'\bMP\b'): 'Ministério Público',
    re.compile(r'\bPCdoB\b'): 'Partido Comunista do Brasil',
    re.compile(r'\bPSB\b'): 'Partido Socialista Brasileiro',
    re.compile(r'\bPT\b'): 'Partido dos Trabalhadores',
    re.compile(r'\bPSDB\b'): 'Partido da Social Democracia Brasileira',
    re.compile(r'\bMDB\b'): 'Movimento Democrático Brasileiro',
    re.compile(r'\bPCB\b'): 'Partido Comunista Brasileiro',
    re.compile(r'\bPMDB\b'): 'Partido do Movimento Democrático Brasileiro',
    re.compile(r'\bPSOL\b'): 'Partido Socialismo e Liberdade',
    re.compile(r'\bPSD\b'): 'Partido Social Democrático',
    re.compile(r'\bPSL\b'): 'Partido Social Liberal',
    re.compile(r'\bPTB\b'): 'Partido Trabalhista Brasileiro',
    re.compile(r'\bPDT\b'): 'Partido Democrático Trabalhista',
    re.compile(r'\bPV\b'): 'Partido Verde',
    re.compile(r'\bRede\b'): 'Rede Sustentabilidade',
    re.compile(r'\bCID\b'): 'Classificação Internacional de Doenças',
    re.compile(r'\bCF\b'): 'Constituição Federal',
    re.compile(r'\bCLT\b'): 'Consolidação das Leis do Trabalho',
    re.compile(r'\bCNPJ\b'): 'Cadastro Nacional da Pessoa Jurídica',
    re.compile(r'\bCPF\b'): 'Cadastro de Pessoa Física',
    re.compile(r'\bPIS\b'): 'Programa de Integração Social',
    re.compile(r'\bCOFINS\b'): 'Contribuição para o Financiamento da Seguridade Social',
    re.compile(r'\bICMS\b'): 'Imposto sobre Circulação de Mercadorias e Serviços',
    re.compile(r'\bIPI\b'): 'Imposto sobre Produtos Industrializados',
    re.compile(r'\bIR\b', re.IGNORECASE): 'Imposto de Renda',
    re.compile(r'\bIRPF\b'): 'Imposto de Renda da Pessoa Física',
    re.compile(r'\bIRPJ\b'): 'Imposto de Renda da Pessoa Jurídica',
    re.compile(r'\bINSS\b'): 'Instituto Nacional do Seguro Social',
    re.compile(r'\bIPCA\b'): 'Índice Nacional de Preços ao Consumidor Amplo',
    re.compile(r'\bIGP-M\b'): 'Índice Geral de Preços do Mercado',
    re.compile(r'\bFGTS\b'): 'Fundo de Garantia por Tempo de Serviço',
    re.compile(r'\bSUS\b'): 'Sistema Único de Saúde',
    re.compile(r'\bBNDES\b'): 'Banco Nacional de Desenvolvimento Econômico e Social',
    re.compile(r'\bCaixa\b'): 'Caixa Econômica Federal',
    re.compile(r'\bBB\b'): 'Banco do Brasil',
    re.compile(r'\bCEF\b'): 'Caixa Econômica Federal',
    re.compile(r'\bFies\b'): 'Fundo de Financiamento Estudantil',
    re.compile(r'\bENEM\b'): 'Exame Nacional do Ensino Médio',
    re.compile(r'\bINEP\b'): 'Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira',
    re.compile(r'\bANP\b'): 'Agência Nacional do Petróleo, Gás Natural e Biocombustíveis',
    re.compile(r'\bANAC\b'): 'Agência Nacional de Aviação Civil',
    re.compile(r'\bANS\b'): 'Agência Nacional de Saúde Suplementar',
    re.compile(r'\bANVISA\b'): 'Agência Nacional de Vigilância Sanitária',
    re.compile(r'\bANEEL\b'): 'Agência Nacional de Energia Elétrica',
    re.compile(r'\bFUNAI\b'): 'Fundação Nacional do Índio',
    re.compile(r'\bIBAMA\b'): 'Instituto Brasileiro do Meio Ambiente e dos Recursos Naturais Renováveis',
    re.compile(r'\bDNIT\b'): 'Departamento Nacional de Infraestrutura de Transportes',
    re.compile(r'\bCVM\b'): 'Comissão de Valores Mobiliários',
    re.compile(r'\bBC\b'): 'Banco Central',
    re.compile(r'\bBACEN\b'): 'Banco Central do Brasil',
    re.compile(r'\bANS\b'): 'Agência Nacional de Saúde Suplementar',
    re.compile(r'\bCVM\b'): 'Comissão de Valores Mobiliários',

    # --- Diversos ---
    re.compile(r'\bEtc\.?', re.IGNORECASE): 'et cetera',
    re.compile(r'\bObs\.?', re.IGNORECASE): 'observação',
    re.compile(r'\bvs\.', re.IGNORECASE): 'versus',
    re.compile(r'\bp\.\s*(\d+)', re.IGNORECASE): r'página \1', # Ex: p. 12
    re.compile(r'\bpágs?\.', re.IGNORECASE): 'páginas',
    re.compile(r'\bcf\.', re.IGNORECASE): 'conforme',
    re.compile(r'\bvide\b', re.IGNORECASE): 'veja',
    re.compile(r'\bex\.\s+gr\.', re.IGNORECASE): 'exemplo gráfico',
    re.compile(r'\bid\.', re.IGNORECASE): 'idem', # mesmo que
    re.compile(r'\bloc\.\scit\.', re.IGNORECASE): 'loco citato', # no lugar citado
    re.compile(r'\bop\.\scit\.', re.IGNORECASE): 'opere citato', # obra citada
    re.compile(r'\bapud\b', re.IGNORECASE): 'citado por',
    re.compile(r'\bgr\.?(\s+de\s+)?', re.IGNORECASE): 'gramas', # Unidade de medida
    re.compile(r'\bvol\.', re.IGNORECASE): 'volume',
    re.compile(r'\bed\.', re.IGNORECASE): 'edição',
    re.compile(r'\brev\.', re.IGNORECASE): 'revisado',
    re.compile(r'\bcorr\.', re.IGNORECASE): 'corrigido',
    re.compile(r'\bref\.', re.IGNORECASE): 'referência',
    re.compile(r'\bnasc\.', re.IGNORECASE): 'nascimento',
    re.compile(r'\bfalec\.', re.IGNORECASE): 'falecimento',
    re.compile(r'\bproc\.', re.IGNORECASE): 'processo',
    re.compile(r'\bproc\.\s+nº', re.IGNORECASE): 'processo número',
    re.compile(r'\breg\.', re.IGNORECASE): 'registro',
    re.compile(r'\breg\.\s+nº', re.IGNORECASE): 'registro número',
    re.compile(r'\bref\.\s+nº', re.IGNORECASE): 'referência número',
    re.compile(r'\bcod\.', re.IGNORECASE): 'código',
    re.compile(r'\bliv\.', re.IGNORECASE): 'livro',
    re.compile(r'\bart\.', re.IGNORECASE): 'artigo',
    re.compile(r'\bparág\.', re.IGNORECASE): 'parágrafo',
    re.compile(r'\binc\.', re.IGNORECASE): 'inciso',
    re.compile(r'\balínea\b', re.IGNORECASE): 'alínea',
    re.compile(r'\bitem\b', re.IGNORECASE): 'item',
    re.compile(r'\bitem\s+nº', re.IGNORECASE): 'item número',
    re.compile(r'\bitem\s+(\d+)', re.IGNORECASE): r'item \1',
    re.compile(r'\bitem\s+([IVXLCDM]+)', re.IGNORECASE): r'item \1', # algarismos romanos
    re.compile(r'\bitem\s+([ivxlcdm]+)', re.IGNORECASE): r'item \1', # algarismos romanos
    re.compile(r'\bnasc\.', re.IGNORECASE): 'nascimento',
    re.compile(r'\bfalec\.', re.IGNORECASE): 'falecimento',
    re.compile(r'\bmatr\.', re.IGNORECASE): 'matrícula',
    re.compile(r'\bcertid\.', re.IGNORECASE): 'certidão',
    re.compile(r'\bexp\.', re.IGNORECASE): 'experiência',
    re.compile(r'\brec\.', re.IGNORECASE): 'recomendação',
    re.compile(r'\brecom\.', re.IGNORECASE): 'recomendação',
    re.compile(r'\bexper\.', re.IGNORECASE): 'experiência',
    re.compile(r'\bhist\.', re.IGNORECASE): 'histórico',
    re.compile(r'\bhistórico\s+de\s+', re.IGNORECASE): 'histórico de',
    re.compile(r'\bcart\.', re.IGNORECASE): 'carteira',
    re.compile(r'\bdoc\.', re.IGNORECASE): 'documento',
    re.compile(r'\bform\.', re.IGNORECASE): 'formulário',
    re.compile(r'\breg\.', re.IGNORECASE): 'registro',
    re.compile(r'\brel\.', re.IGNORECASE): 'relação',
    re.compile(r'\bres\.', re.IGNORECASE): 'resumo',
    re.compile(r'\bresult\.', re.IGNORECASE): 'resultado',
    re.compile(r'\bresp\.', re.IGNORECASE): 'responsável',
    re.compile(r'\bresp\.\s+por', re.IGNORECASE): 'responsável por',
    re.compile(r'\bresp\.\s+téc\.', re.IGNORECASE): 'responsável técnico',
    re.compile(r'\bresp\.\s+adm\.', re.IGNORECASE): 'responsável administrativo',
    re.compile(r'\btel\.', re.IGNORECASE): 'telefone',
    re.compile(r'\bcel\.', re.IGNORECASE): 'celular',
    re.compile(r'\bfax\b', re.IGNORECASE): 'fax',
    re.compile(r'\bemail\b', re.IGNORECASE): 'email',
    re.compile(r'\bweb\b', re.IGNORECASE): 'web',
    re.compile(r'\bsite\b', re.IGNORECASE): 'site',
    re.compile(r'\bhtml\b', re.IGNORECASE): 'HTML',
    re.compile(r'\bcss\b', re.IGNORECASE): 'CSS',
    re.compile(r'\bxml\b', re.IGNORECASE): 'XML',
    re.compile(r'\bjson\b', re.IGNORECASE): 'JSON',
    re.compile(r'\bftp\b', re.IGNORECASE): 'FTP',
    re.compile(r'\bhttp\b', re.IGNORECASE): 'HTTP',
    re.compile(r'\bhttps\b', re.IGNORECASE): 'HTTPS',
    re.compile(r'\bssl\b', re.IGNORECASE): 'SSL',
    re.compile(r'\bsql\b', re.IGNORECASE): 'SQL',
    re.compile(r'\bapi\b', re.IGNORECASE): 'API',
    re.compile(r'\bi\.e\.', re.IGNORECASE): 'isto é',
    re.compile(r'\be\.g\.', re.IGNORECASE): 'por exemplo',
    re.compile(r'\bviz\.', re.IGNORECASE): 'a saber',
    re.compile(r'\betc\b', re.IGNORECASE): 'e outros',
    re.compile(r'\bca\.\s+', re.IGNORECASE): 'cerca de ',
    re.compile(r'\bcirca\s+', re.IGNORECASE): 'cerca de ',
    re.compile(r'\baprox\.', re.IGNORECASE): 'aproximadamente',
    re.compile(r'\bsto\s+', re.IGNORECASE): 'santo ',
    re.compile(r'\bsta\s+', re.IGNORECASE): 'santa ',

    # --- Siglas Comuns (Adicionar conforme necessidade) ---
    re.compile(r'\bEUA\b'): 'Estados Unidos da América',
    re.compile(r'\bRJ\b'): 'Rio de Janeiro',
    re.compile(r'\bSP\b'): 'São Paulo',
    re.compile(r'\bDF\b'): 'Distrito Federal',
    re.compile(r'\bMG\b'): 'Minas Gerais',
    re.compile(r'\bRS\b'): 'Rio Grande do Sul',
    re.compile(r'\bPR\b'): 'Paraná',
    re.compile(r'\bSC\b'): 'Santa Catarina',
    re.compile(r'\bAM\b'): 'Amazonas',
    re.compile(r'\bPA\b'): 'Pará',
    re.compile(r'\bBA\b'): 'Bahia',
    re.compile(r'\bPE\b'): 'Pernambuco',
    re.compile(r'\bCE\b'): 'Ceará',
    re.compile(r'\bMA\b'): 'Maranhão',
    re.compile(r'\bPI\b'): 'Piauí',
    re.compile(r'\bPB\b'): 'Paraíba',
    re.compile(r'\bRN\b'): 'Rio Grande do Norte',
    re.compile(r'\bAL\b'): 'Alagoas',
    re.compile(r'\bSE\b'): 'Sergipe',
    re.compile(r'\bES\b'): 'Espírito Santo',
    re.compile(r'\bGO\b'): 'Goiás',
    re.compile(r'\bMT\b'): 'Mato Grosso',
    re.compile(r'\bMS\b'): 'Mato Grosso do Sul',
    re.compile(r'\bTO\b'): 'Tocantins',
    re.compile(r'\bRO\b'): 'Rondônia',
    re.compile(r'\bAC\b'): 'Acre',
    re.compile(r'\bRR\b'): 'Roraima',
    re.compile(r'\bAP\b'): 'Amapá',
}

# ================== FUNÇÕES DE LIMPEZA E NORMALIZAÇÃO ==================

def _remover_lixo_textual(texto: str) -> str:
    """Remove cabeçalhos, rodapés e outros textos repetitivos de e-books."""
    try:
        logger.info("Removendo lixo textual e artefatos de digitalização...")
        if not texto:
            return texto
            
        # Tenta encontrar o primeiro capítulo para remover qualquer texto introdutório
        # A expressão `(?s)` permite que `.` corresponda a quebras de linha
        match = re.search(r'(?s)(cap[íi]tulo\s+[\w\d]+|sum[áa]rio|pr[óo]logo|pref[áa]cio)', texto, re.IGNORECASE)
        if match:
            texto = texto[match.start():]

        # Remove textos repetitivos comuns (ex: notas de copyright de versões não oficiais)
        textos_a_remover = [
            r"Esse livro é protegido.*",
            r"A Detonando Home Page.*",
            r"Distribuído gratuitamente.*",
            r"www\.\s*portaldetonando\.\s*cjb\.\s*net.*",
            r"\bCopyright\b.*",
            r"\bTodos os direitos reservados\b.*",
            r"\bDireitos autorais\b.*",
            r"\bReservados todos os direitos\b.*",
            r"\bNenhuma parte deste livro\b.*",
            r"\bproibida a reprodução\b.*",
            r"\bproibida a cópia\b.*",
            r"\bvedado o armazenamento\b.*",
            r"\bsem a devida permissão\b.*"
        ]
        for padrao in textos_a_remover:
            texto = re.sub(padrao, "", texto, flags=re.IGNORECASE | re.MULTILINE)

        return texto
    except Exception as e:
        logger.error(f"Erro ao remover lixo textual: {e}")
        return texto

def _normalizar_caracteres_e_pontuacao(texto: str) -> str:
    """Normaliza caracteres Unicode, aspas, travessões e outros símbolos."""
    try:
        logger.info("Normalizando caracteres e pontuação...")
        if not texto:
            return texto
            
        # Normalização Unicode para consistência (ex: 'é' e 'e´' viram a mesma coisa)
        texto = unicodedata.normalize('NFKC', texto)

        substituicoes = {
            '[“”«»]': '"',  # Aspas curvas/francesas para aspas retas
            "[‘’]": "'",    # Apóstrofos curvos para retos
            '[–—―‐‑]': '—',    # Hífens e barras para travessão padrão
            '…': '...',    # Reticências
        }
        for padrao, sub in substituicoes.items():
            texto = re.sub(padrao, sub, texto)

        # Garante espaçamento consistente ao redor de travessões para diálogos
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
            
        # Primeiro, remover formatação markdown e outros símbolos de formatação
        # Substituir **texto** por texto (deixar espaços para não juntar palavras)
        texto = re.sub(r'\*\*(.*?)\*\*', r' \1 ', texto)
        # Substituir *texto* por texto (deixar espaços para não juntar palavras)
        texto = re.sub(r'\*(.*?)\*', r' \1 ', texto)
        # Substituir __texto__ por texto (deixar espaços para não juntar palavras)
        texto = re.sub(r'__(.*?)__', r' \1 ', texto)
        # Substituir _texto_ por texto (deixar espaços para não juntar palavras)
        texto = re.sub(r'_(.*?)_', r' \1 ', texto)
        
        # Mapeamento de símbolos para sua forma por extenso.
        # As chaves são strings literais, não regex.
        # Importante: Excluir o símbolo $ pois R$ é tratado separadamente em _expandir_numeros
        substituicoes = {
            '&': ' e ',
            '@': ' arroba ',
            '#': ' cerquilha ',  # Melhor que deixar em branco
            '%': ' por cento ', # Melhor tratamento aqui
            '/': ' barra ', # 'ou' pode causar confusão em algumas situações
            '\\': ' ', # Barra invertida literal
            '+': ' mais ',
            '=': ' igual a ',
            '<': ' menor que ',
            '>': ' maior que ',
            '≤': ' menor ou igual a ',
            '≥': ' maior ou igual a ',
            '≠': ' diferente de ',
            '≈': ' aproximadamente ',
            '→': ' para ',
            '←': ' de ',
            '↑': ' acima de ',
            '↓': ' abaixo de ',
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
    except Exception as e:
        logger.error(f"Erro ao substituir símbolos por extenso: {e}")
        return texto


def _remontar_paragrafos(texto: str) -> str:
    """Corrige quebras de linha indevidas no meio dos parágrafos."""
    try:
        logger.info("Remontando parágrafos...")
        if not texto:
            return texto
            
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
            titulo = match.group(3).strip() if match.group(3) else ""

            # Converte número por extenso para numeral (Ex: "UM" -> "1")
            numero_final = CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM.get(numero_str, numero_str)

            # Garante que o título termine com pontuação para uma pausa na leitura
            if titulo and not re.search(r'[.!?]$', titulo):
                titulo += "."

            return f"\n\n{prefixo.upper()} {numero_final}.\n\n{titulo}\n\n"

        # Padrão mais flexível para capturar "CAPÍTULO 1", "CAPÍTULO UM", "PRÓLOGO", etc.
        # com ou sem título na linha seguinte.
        padrao = re.compile(
            r'^\s*(cap[íi]tulo|pr[óo]logo|ep[íi]logo|pref[áa]cio)\s+([\d\w\s]+)\s*\.?\s*\n\n([^\n]+)',
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

        # Converte números ordinais: 2º -> segundo, 3ª -> terceira
        def ordinal(match: re.Match) -> str:
            try:
                n = int(match.group(1))
                sufixo = match.group(2).lower()
                if sufixo in ('o', 'º'):
                    return num2words(n, lang='pt_BR', to='ordinal')
                elif sufixo in ('a', 'ª'):
                    ordinal_masc = num2words(n, lang='pt_BR', to='ordinal')
                    # Converte ordinal masculino para feminino
                    if ordinal_masc.endswith('o'):
                        return ordinal_masc[:-1] + 'a'
                    elif ordinal_masc.endswith('os'):
                        return ordinal_masc[:-2] + 'as'
                    else:
                        return ordinal_masc
            except (ValueError, IndexError):
                return match.group(0)
            return match.group(0)
        texto = re.sub(r'\b(\d+)([oOaAºª])\b', ordinal, texto)

        # Converte valores monetários: R$ 10,50 -> dez reais e cinquenta centavos
        def monetario(match: re.Match) -> str:
            try:
                valor_str = match.group(1).replace('.', '').replace(',', '.')
                partes = valor_str.split('.')
                
                if len(partes) == 1:
                    reais = int(partes[0])
                    centavos = 0
                elif len(partes) == 2:
                    reais = int(partes[0])
                    # Garantir que temos exatamente 2 dígitos para centavos
                    centavos_parte = partes[1]
                    if len(centavos_parte) == 1:
                        centavos = int(centavos_parte) * 10
                    else:
                        centavos = int(centavos_parte[:2])
                else:
                    return match.group(0)
                
                str_reais = num2words(reais, lang='pt_BR') + (' real' if reais == 1 else ' reais')
                if centavos > 0:
                    str_centavos = num2words(centavos, lang='pt_BR') + (' centavo' if centavos == 1 else ' centavos')
                    return f"{str_reais} e {str_centavos}"
                return str_reais
            except (ValueError, IndexError):
                return match.group(0)
        texto = re.sub(r'R\$\s*([\d.,]+)', monetario, texto)

        # Converte números cardinais, ignorando anos e números muito longos
        def cardinal(match: re.Match) -> str:
            try:
                num_str = match.group(0)
                num_int = int(num_str)
                
                # Não converte números que parecem anos ou códigos/identificadores longos
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
            
        # Adiciona quebra de parágrafo antes de um diálogo iniciado por travessão, se não houver
        texto = re.sub(r'([.!?\"])\\s*([—-])', r'\1\n\n\2', texto)

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
    except Exception as e:
        logger.error(f"Erro na limpeza final: {e}")
        return texto

# ================== FUNÇÃO PRINCIPAL ==================

def formatar_texto_para_tts(texto_bruto: str, log_progresso: bool = True) -> str:
    """
    Executa um pipeline completo de limpeza e formatação para preparar o texto
    para uma leitura natural e agradável em um sistema TTS.
    
    Args:
        texto_bruto: Texto de entrada a ser processado
        log_progresso: Se True, imprime mensagens de progresso
        
    Returns:
        Texto processado e otimizado para TTS
    """
    if log_progresso:
        logger.info("Iniciando processamento completo do texto para TTS...")
    
    if not texto_bruto or not isinstance(texto_bruto, str):
        logger.warning("Texto de entrada inválido ou vazio")
        return ""

    try:
        # Pipeline de processamento - ordem correta
        texto = _remover_lixo_textual(texto_bruto)
        texto = _normalizar_caracteres_e_pontuacao(texto)
        texto = _remontar_paragrafos(texto)
        # Primeiro, remover símbolos de formatação markdown, mas manter símbolos monetários intactos
        texto = _substituir_simbolos_por_extenso(texto)  
        texto = _expandir_abreviacoes(texto)  # Expandir abreviações antes de números
        # Processar números e moedas antes de qualquer outra substituição de símbolos
        texto = _expandir_numeros(texto)      
        texto = _formatar_capitulos(texto)    # Formatar capítulos após outras expansões
        texto = _limpeza_final(texto)

        if log_progresso:
            logger.info("Texto pronto para TTS.")
        return texto
    except Exception as e:
        logger.error(f"Erro no processamento completo do texto: {e}")
        return texto_bruto  # Retorna o texto original em caso de erro

# ================== FUNÇÕES ADICIONAIS ==================

def validar_texto_para_tts(texto: str) -> tuple[bool, List[str]]:
    """
    Valida o texto para garantir que está adequado para processamento TTS
    
    Args:
        texto: Texto a ser validado
        
    Returns:
        Tupla contendo (é_válido, lista_de_erros)
    """
    erros = []
    
    if not texto:
        erros.append("Texto está vazio")
    
    if not isinstance(texto, str):
        erros.append("Texto não é uma string")
    
    # Verificar se o texto é muito pequeno
    if len(texto.strip()) < 10:
        erros.append("Texto é muito curto para processamento")
    
    # Verificar se o texto é muito longo (poderia causar problemas de performance)
    if len(texto) > 1000000:  # 1 milhão de caracteres
        erros.append("Texto é muito longo (maior que 1MB), pode afetar a performance")
    
    return len(erros) == 0, erros

def preprocessar_texto(texto: str) -> str:
    """
    Função auxiliar que faz um pré-processamento básico do texto
    
    Args:
        texto: Texto de entrada
        
    Returns:
        Texto pré-processado
    """
    if not texto:
        return texto
        
    # Remover espaços em branco excessivos no início e final
    texto = texto.strip()
    
    # Normalizar quebras de linha
    texto = re.sub(r'\r\n', '\n', texto)  # Windows
    texto = re.sub(r'\r', '\n', texto)    # Mac
    texto = re.sub(r'\n\s*\n', '\n\n', texto)  # Normalizar quebras de parágrafo múltiplas
    
    return texto

# ================== EXEMPLO DE USO ==================

if __name__ == '__main__':
    texto_de_exemplo = """
    Esse livro é protegido pelas leis internacionais de Copyright.
    www.portaldetonando.cjb.net

    CAPÍTULO VINTE E UM.

    O Sr. & a Sra. Dursley, da rua dos Alfeneiros, nº 4, orgulhavam-se de
    dizer que eram perfeitamente normais, muito obrigado. O preço é R$ 50,50.
    O carro andava a 80Km/h. A temperatura estava em 25°C.
    O evento será em jan. de 2023.

    "Isso é 50% verdade!", disse o Dr. João.
    — Cuidado! — alertou a Profa. Ana.
    O evento será na Av. Brasil, S/N.
    """
    
    # Validar o texto antes do processamento
    valido, erros = validar_texto_para_tts(texto_de_exemplo)
    if not valido:
        print("Erros de validação:", erros)
    else:
        # Pré-processar o texto
        texto_de_exemplo = preprocessar_texto(texto_de_exemplo)
        
        # Processar o texto
        texto_processado = formatar_texto_para_tts(texto_de_exemplo)
        print("\n--- TEXTO PROCESSADO ---\n")
        print(texto_processado)

    # Saída esperada:
    #
    # CAPÍTULO VINTE E UM.
    #
    # O Senhor e a Senhora Dursley, da rua dos Alfeneiros, número quatro, orgulhavam-se de dizer que eram perfeitamente normais, muito obrigado. O preço é cinquenta reais e cinquenta centavos. O carro andava a oitenta quilômetros por hora. A temperatura estava em vinte e cinco graus celsius.
    # O evento será em janeiro de dois mil e vinte e três.
    #
    # "Isso é cinquenta por cento verdade!", disse o Doutor João.
    #
    # — Cuidado! — alertou a Professora Ana.
    #
    # O evento será na Avenida Brasil, sem número.