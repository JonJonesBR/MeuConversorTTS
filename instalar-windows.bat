@echo off
:: Script para automatizar a instalação do MeuConversorTTS no Windows

:: --- INÍCIO DO SCRIPT ---

:: Define o título da janela
TITLE Instalador MeuConversorTTS para Windows

ECHO.
ECHO    ######################################################
ECHO    #                                                    #
ECHO    #    Instalador do MeuConversorTTS para Windows      #
ECHO    #                                                    #
ECHO    ######################################################
ECHO.

:: Passo 1: Verificar pré-requisitos (Python e Git)
ECHO.
ECHO >>> (1/5) Verificando pre-requisitos (Python e Git)...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    ECHO [ERRO] Python nao encontrado. Por favor, instale o Python 3 a partir de https://python.org
    ECHO Marque a opcao "Add Python to PATH" durante a instalacao.
    pause
    exit /b
)

git --version >nul 2>nul
if %errorlevel% neq 0 (
    ECHO [ERRO] Git nao encontrado. Por favor, instale o Git a partir de https://git-scm.com/
    pause
    exit /b
)
ECHO Python e Git foram encontrados.

:: Aviso sobre FFmpeg e Poppler
ECHO.
ECHO !!! ATENCAO: Este script nao instala o FFmpeg e o Poppler. !!!
ECHO Voce precisa instala-los manualmente e adiciona-los ao PATH do sistema.
ECHO Links para download:
ECHO   - FFmpeg: https://ffmpeg.org/download.html
ECHO   - Poppler: procure por "poppler for windows"
ECHO Pressione qualquer tecla para continuar a instalacao...
pause >nul

:: Passo 2: Baixar o projeto do GitHub
:: Navega para o diretório do usuário (ex: C:\Users\SeuNome)
cd %USERPROFILE%
ECHO.
ECHO >>> (2/5) Baixando o projeto do GitHub...
if exist "MeuConversorTTS" (
    ECHO A pasta 'MeuConversorTTS' ja existe. Pulando o download.
) else (
    git clone https://github.com/JonJonesBR/MeuConversorTTS.git
)

:: Entra na pasta do projeto
cd MeuConversorTTS

:: Passo 3: Configurar o ambiente virtual Python
ECHO.
ECHO >>> (3/5) Criando o ambiente virtual...
python -m venv venv

ECHO.
ECHO >>> (4/5) Ativando o ambiente virtual e instalando dependencias...
:: Ativa o venv e instala os pacotes
call venv\Scripts\activate.bat
pip install -r requirements.txt

ECHO.
ECHO >>> (5/5) Finalizando...

:: Mensagem final
ECHO.
ECHO --- INSTALACAO CONCLUIDA! ---
ECHO.
ECHO Para comecar a usar, siga os proximos passos:
ECHO 1. Abra um novo Prompt de Comando (CMD).
ECHO 2. Navegue ate a pasta do projeto com: cd %USERPROFILE%\MeuConversorTTS
ECHO 3. Ative o ambiente virtual com o comando:
ECHO    venv\Scripts\activate.bat
ECHO 4. Execute o programa principal com:
ECHO    python main.py
ECHO.
pause
exit

:: --- FIM DO SCRIPT ---
