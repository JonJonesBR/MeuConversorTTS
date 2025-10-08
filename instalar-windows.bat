@echo off
REM Instalação do MeuConversorTTS no Windows
REM Requisitos: Python 3.10+ instalado, FFmpeg opcional (para algumas funções),
REM Poppler (pdftotext) para conversão PDF→TXT se desejar essa funcionalidade.

setlocal

echo === (1/5) Verificando Python ===
where python >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python nao encontrado no PATH.
  echo Instale o Python 3.x e marque a opcao "Add python.exe to PATH".
  pause
  exit /b 1
)

echo === (2/5) Criando ambiente virtual ===
python -m venv venv
if errorlevel 1 (
  echo [ERRO] Falha ao criar o ambiente virtual.
  pause
  exit /b 1
)

echo === (3/5) Ativando o ambiente virtual ===
call venv\Scripts\activate.bat

echo === (4/5) Instalando dependencias Python ===
pip install --upgrade pip
pip install -r requirements.txt

echo === (5/5) Observacoes importantes ===
echo - Para PDF->TXT, instale o Poppler para Windows e adicione a pasta 'bin' ao PATH.
echo   Download: https://github.com/oschwartz10612/poppler-windows/releases
echo - Para funcoes de audio/video, instale FFmpeg e adicione ao PATH.
echo   Download: https://www.gyan.dev/ffmpeg/builds/
echo.
echo Ambiente pronto. Para executar:
echo   call venv\Scripts\activate.bat
echo   python main.py
echo.
pause
endlocal
