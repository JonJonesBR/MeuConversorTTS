# -*- coding: utf-8 -*-

# ================== CONFIGURAÇÕES GLOBAIS DE TTS E VOZES ==================
VOZES_PT_BR = [
    "pt-BR-ThalitaMultilingualNeural",  # Voz padrão
    "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural"
]
MAX_TTS_TENTATIVAS = 3
# Limite de caracteres para cada chamada à API TTS.
# Valores menores podem ser mais estáveis em conexões ruins.
# Valores maiores resultam em menos arquivos temporários.
LIMITE_CARACTERES_CHUNK_TTS = 7500

# Número de chamadas concorrentes à API TTS. Ajuste para sua conexão/sistema.
# Termux: 5-8. Desktop com boa conexão: 10-15.
LOTE_MAXIMO_TAREFAS_CONCORRENTES = 8


# ================== CONFIGURAÇÕES DE PROCESSAMENTO DE ARQUIVO ==================
ENCODINGS_TENTATIVAS = ['utf-8', 'utf-16', 'iso-8859-1', 'cp1252']


# ================== CONFIGURAÇÕES DE VÍDEO E FFMPEG ==================
FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"
FFPLAY_BIN = "ffplay"

# Limite em segundos para sugerir a divisão de arquivos de mídia longos.
# 43200 segundos = 12 horas
LIMITE_SEGUNDOS_DIVISAO = 43200

RESOLUCOES_VIDEO = {
    '1': ('640x360', '360p'),
    '2': ('854x480', '480p'),
    '3': ('1280x720', '720p (HD)')
}


# ================== CONFIGURAÇÕES DE PROCESSAMENTO DE TEXTO ==================

# Mapeamento para expandir abreviações.
ABREVIACOES_MAP = {
    'dr': 'Doutor', 'd': 'Dona', 'dra': 'Doutora',
    'sr': 'Senhor', 'sra': 'Senhora', 'srta': 'Senhorita',
    'prof': 'Professor', 'profa': 'Professora',
    'eng': 'Engenheiro', 'engª': 'Engenheira',
    'adm': 'Administrador', 'adv': 'Advogado',
    'exmo': 'Excelentíssimo', 'exma': 'Excelentíssima',
    'v.exa': 'Vossa Excelência', 'v.sa': 'Vossa Senhoria',
    'av': 'Avenida', 'r': 'Rua', 'km': 'Quilômetro',
    'etc': 'etcétera', 'ref': 'Referência',
    'pag': 'Página', 'pags': 'Páginas',
    'fl': 'Folha', 'fls': 'Folhas',
    'pe': 'Padre',
    'dept': 'Departamento', 'depto': 'Departamento',
    'univ': 'Universidade', 'inst': 'Instituição',
    'est': 'Estado', 'tel': 'Telefone',
    'eua': 'Estados Unidos da América',
    'ed': 'Edição', 'ltda': 'Limitada'
}

# Mapeamento para conversão de capítulos de numeral por extenso para arábico.
CONVERSAO_CAPITULOS_EXTENSO_PARA_NUM = {
    'UM': '1', 'DOIS': '2', 'TRÊS': '3', 'QUATRO': '4', 'CINCO': '5',
    'SEIS': '6', 'SETE': '7', 'OITO': '8', 'NOVE': '9', 'DEZ': '10',
    'ONZE': '11', 'DOZE': '12', 'TREZE': '13', 'CATORZE': '14', 'QUINZE': '15',
    'DEZESSEIS': '16', 'DEZESSETE': '17', 'DEZOITO': '18', 'DEZENOVE': '19', 'VINTE': '20'
}

# Lista de abreviações que, mesmo terminando com ponto, não indicam o fim de uma frase.
ABREVIACOES_QUE_NAO_TERMINAM_FRASE = {
    'sr.', 'sra.', 'srta.', 'dr.', 'dra.', 'prof.', 'profa.', 'eng.', 'exmo.', 'exma.',
    'pe.', 'rev.', 'ilmo.', 'ilma.', 'gen.', 'cel.', 'maj.', 'cap.', 'ten.', 'sgt.',
    'cb.', 'sd.', 'me.', 'ms.', 'msc.', 'esp.', 'av.', 'r.', 'pç.', 'esq.', 'trav.',
    'jd.', 'pq.', 'rod.', 'km.', 'apt.', 'ap.', 'bl.', 'cj.', 'cs.', 'ed.', 'nº',
    'no.', 'uf.', 'cep.', 'est.', 'mun.', 'dist.', 'zon.', 'reg.', 'kg.', 'cm.',
    'mm.', 'lt.', 'ml.', 'mg.', 'seg.', 'min.', 'hr.', 'ltda.', 's.a.', 's/a',
    'cnpj.', 'cpf.', 'rg.', 'proc.', 'ref.', 'cod.', 'tel.', 'etc.', 'p.ex.', 'ex.',
    'i.e.', 'e.g.', 'vs.', 'cf.', 'op.cit.', 'loc.cit.', 'fl.', 'fls.', 'pag.',
    'p.', 'pp.', 'u.s.', 'e.u.a.', 'o.n.u.', 'i.b.m.', 'h.p.', 'obs.', 'att.',
    'resp.', 'publ.', 'doutora', 'senhora', 'senhor', 'doutor', 'professor',
    'professora', 'general'
}
