# -*- coding: utf-8 -*-
"""
Módulo para gerir o arquivo de configurações (settings.ini).
Lida com a leitura e escrita das preferências do utilizador.
"""
import configparser
from pathlib import Path

# Nome do arquivo de configuração
SETTINGS_FILE = "settings.ini"

# Estrutura das configurações
CONFIG = {
    'Geral': {
        'voz_padrao': 'pt-BR-ThalitaMultilingualNeural',
        'velocidade_padrao': '1.0'
    }
}

def carregar_configuracoes():
    """
    Carrega as configurações do arquivo settings.ini.
    Se o arquivo não existir, cria com os valores padrão.
    """
    config_parser = configparser.ConfigParser()
    if not Path(SETTINGS_FILE).exists():
        print(f"Arquivo '{SETTINGS_FILE}' não encontrado. Criando com valores padrão.")
        salvar_configuracoes(CONFIG['Geral']['voz_padrao'], CONFIG['Geral']['velocidade_padrao'])
    
    config_parser.read(SETTINGS_FILE)
    
    # Atualiza o dicionário global com as configurações carregadas
    try:
        CONFIG['Geral']['voz_padrao'] = config_parser.get('Geral', 'voz_padrao')
        CONFIG['Geral']['velocidade_padrao'] = config_parser.get('Geral', 'velocidade_padrao')
    except (configparser.NoSectionError, configparser.NoOptionError):
        print("⚠️ Arquivo de configuração inválido. Recriando com valores padrão.")
        salvar_configuracoes(CONFIG['Geral']['voz_padrao'], CONFIG['Geral']['velocidade_padrao'])
        config_parser.read(SETTINGS_FILE)
        CONFIG['Geral']['voz_padrao'] = config_parser.get('Geral', 'voz_padrao')
        CONFIG['Geral']['velocidade_padrao'] = config_parser.get('Geral', 'velocidade_padrao')


def salvar_configuracoes(voz, velocidade):
    """Salva as configurações no arquivo settings.ini."""
    config_parser = configparser.ConfigParser()
    config_parser['Geral'] = {
        'voz_padrao': voz,
        'velocidade_padrao': str(velocidade)
    }
    with open(SETTINGS_FILE, 'w') as configfile:
        config_parser.write(configfile)
    
    # Atualiza o dicionário global em memória
    CONFIG['Geral']['voz_padrao'] = voz
    CONFIG['Geral']['velocidade_padrao'] = str(velocidade)
    print("Configuracoes salvas com sucesso!")

def obter_configuracao(chave):
    """Retorna o valor de uma chave de configuração."""
    return CONFIG['Geral'].get(chave)