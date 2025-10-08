# Dependências Externas

Este projeto depende de alguns programas externos que não são instalados automaticamente via `pip`. Estas dependências devem ser instaladas separadamente no seu sistema.

## FFmpeg

O FFmpeg é necessário para as seguintes funcionalidades:

- Redução de ruído em arquivos de áudio
- Normalização de volume
- Geração de vídeos MP4 a partir de arquivos de áudio
- Unificação de arquivos de áudio

### Instalação do FFmpeg

#### Windows

1. Baixe o FFmpeg em <https://www.gyan.dev/ffmpeg/builds/>
2. Extraia o conteúdo em uma pasta (ex: C:\\ffmpeg)
3. Adicione o caminho 'C:\\ffmpeg\\bin' ao PATH do sistema:
   - Abra o Painel de Controle > Sistema > Configurações Avançadas do Sistema
   - Clique em 'Variáveis de Ambiente'
   - Na seção 'Variáveis do Sistema', encontre e selecione 'Path', clique em 'Editar'
   - Clique em 'Novo' e adicione o caminho 'C:\\ffmpeg\\bin'
   - Clique em 'OK' para fechar todas as janelas
4. Reinicie o terminal ou o computador para aplicar as alterações

#### Linux (Ubuntu/Debian)

```bash
sudo apt update && sudo apt install ffmpeg
```

#### macOS

Primeiro instale o Homebrew (caso ainda não tenha):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Depois instale o FFmpeg:

```bash
brew install ffmpeg
```

#### Termux (Android)

```bash
pkg install ffmpeg
```

## Poppler

O Poppler é necessário para converter arquivos PDF em texto. O executável `pdftotext` é usado para esta função.

### Instalação do Poppler

#### Windows (Poppler)

O programa tentará instalar automaticamente o Poppler no diretório de dados do usuário.

#### Linux (Ubuntu/Debian) (Poppler)

```bash
sudo apt install poppler-utils
```

#### macOS (Poppler)

```bash
brew install poppler
```

#### Termux (Android) (Poppler)

```bash
pkg install poppler
```

## Verificação

O programa verifica automaticamente a presença destas dependências na inicialização e exibe mensagens informativas caso elas não estejam instaladas.
