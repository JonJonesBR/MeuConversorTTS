# -*- coding: utf-8 -*-
"""
Manipulação de arquivos: Leitura/gravação de texto, PDF via pdftotext (externo),
e extração de texto de EPUB via zipfile/html2text.
"""
from __future__ import annotations
import os
import re
import unicodedata
import subprocess
import shutil
import zipfile
from pathlib import Path
from typing import List

import chardet
from tqdm import tqdm
import html2text
from bs4 import BeautifulSoup

# ================== I/O BÁSICO ==================

def ler_arquivo_texto(caminho_arquivo: str) -> str:
    """Lê um arquivo de texto tentando detectar o encoding."""
    try:
        with open(caminho_arquivo, 'rb') as f:
            dados = f.read()
        enc = chardet.detect(dados).get('encoding') or 'utf-8'
        return dados.decode(enc, errors='replace')
    except Exception as e:
        print(f"❌ Erro ao ler arquivo '{caminho_arquivo}': {e}")
        return ""

def salvar_arquivo_texto(caminho_arquivo: str, conteudo: str):
    """Salva uma string em um arquivo de texto com encoding UTF-8."""
    try:
        Path(caminho_arquivo).parent.mkdir(parents=True, exist_ok=True)
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
    except Exception as e:
        print(f"Erro ao salvar arquivo '{caminho_arquivo}': {e}")

def limpar_nome_arquivo(nome: str) -> str:
    """Limpa e sanitiza um nome de arquivo, removendo caracteres especiais."""
    nome_sem_ext, ext = os.path.splitext(nome)
    nome_normalizado = unicodedata.normalize('NFKD', nome_sem_ext).encode('ascii', 'ignore').decode('ascii')
    nome_limpo = re.sub(r'[^\w\s-]', '', nome_normalizado).strip()
    nome_limpo = re.sub(r'[-\s]+', '_', nome_limpo)
    return nome_limpo + ext if ext else nome_limpo

# ================== CONVERSÃO DE PDF (VIA pdftotext) ==================

def converter_pdf_para_txt(caminho_pdf: str, caminho_txt: str) -> bool:
    """Converte um arquivo PDF para TXT usando a ferramenta externa pdftotext."""
    print(f"📖 Extraindo conteúdo de: {Path(caminho_pdf).name}")
    try:
        # No Windows, o subprocesso não herda o PATH modificado dinamicamente,
        # então é melhor não especificar flags que possam causar problemas.
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        comando = ["pdftotext", "-layout", "-enc", "UTF-8", caminho_pdf, caminho_txt]
        subprocess.run(comando, check=True, capture_output=True, creationflags=flags)
        return True
    except FileNotFoundError:
        print("❌ 'pdftotext' não encontrado. Instale o Poppler e garanta que esteja no PATH.")
        return False
    except subprocess.CalledProcessError as e:
        stderr_decoded = e.stderr.decode(errors='ignore') if e.stderr else str(e)
        print(f"❌ Erro ao converter PDF: {stderr_decoded}")
        return False

# ================== EPUB (VIA zipfile + html2text) ==================

def extrair_texto_de_epub(caminho_epub: str) -> str:
    """Extrai texto de um EPUB usando zipfile e html2text, inspirado no script antigo."""
    print(f"📖 Extraindo conteúdo de: {Path(caminho_epub).name}")
    texto_completo = ""
    try:
        with zipfile.ZipFile(caminho_epub, 'r') as epub_zip:
            # Encontrar a ordem dos arquivos a partir do 'spine' no arquivo .opf
            container_xml = epub_zip.read('META-INF/container.xml').decode('utf-8')
            opf_path_match = re.search(r'full-path="([^"]+)"', container_xml)
            if not opf_path_match:
                raise Exception("Caminho do arquivo OPF não encontrado no container.xml.")

            opf_path = opf_path_match.group(1)
            opf_content = epub_zip.read(opf_path).decode('utf-8')
            opf_dir = os.path.dirname(opf_path)

            spine_items = [m.group(1) for m in re.finditer(r'<itemref\s+idref="([^"]+)"', opf_content)]
            manifest_hrefs = {m.group(1): m.group(2) for m in re.finditer(r'<item\s+id="([^"]+)"\s+href="([^"]+)"', opf_content)}
            
            arquivos_xhtml_ordenados = []
            for idref in spine_items:
                if idref in manifest_hrefs:
                    # Constrói o caminho relativo ao diretório do OPF
                    xhtml_path_rel = manifest_hrefs[idref]
                    xhtml_path_in_zip = os.path.normpath(os.path.join(opf_dir, xhtml_path_rel)).replace('\\', '/')
                    arquivos_xhtml_ordenados.append(xhtml_path_in_zip)

            if not arquivos_xhtml_ordenados:
                 # Fallback se a leitura do spine falhar
                arquivos_xhtml_ordenados = sorted([
                    f.filename for f in epub_zip.infolist() 
                    if f.filename.lower().endswith(('.html', '.xhtml'))
                ])
            
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            h.ignore_emphasis = True
            
            for nome_arquivo in tqdm(arquivos_xhtml_ordenados, desc="Processando capítulos do EPUB"):
                html_bytes = epub_zip.read(nome_arquivo)
                html_texto = html_bytes.decode(chardet.detect(html_bytes)['encoding'] or 'utf-8', errors='replace')
                
                # Usa BeautifulSoup para remover tags indesejadas antes de converter
                soup = BeautifulSoup(html_texto, 'html.parser')
                for tag in soup(['nav', 'header', 'footer', 'style', 'script', 'figure', 'aside']):
                    tag.decompose()

                texto_limpo = h.handle(str(soup))
                texto_completo += texto_limpo + "\n\n"
        
        return texto_completo.strip()
    except Exception as e:
        print(f"❌ Erro ao processar EPUB: {e}")
        return ""

# ================== UNIFICAÇÃO DE ÁUDIO ==================

def unificar_arquivos_audio(lista_arquivos: List[str], caminho_saida: str) -> bool:
    """
    Concatena múltiplos arquivos de áudio em um único arquivo.
    Primeiro tenta usar pydub, depois tenta usar FFmpeg, e finalmente tenta um fallback simples.
    """
    # Tenta primeiro com pydub
    try:
        # pylint: disable=import-outside-toplevel
        # O pydub é uma dependência opcional que é instalada via requirements.txt
        from pydub import AudioSegment  # type: ignore
        # Testa se o módulo pode ser usado corretamente
        # Criar um segmento de áudio vazio para verificar se todas as dependências estão presentes
        test_segment = AudioSegment.silent(duration=100)  # 100ms de silêncio
    except ImportError as e:
        print("Modulo 'pydub' nao encontrado. Instalando automaticamente...")
        try:
            import subprocess
            import sys
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pydub"])
            print("pydub instalado com sucesso!")
            # Após instalar, tenta importar novamente
            from pydub import AudioSegment  # type: ignore
            # Testa novamente se o módulo pode ser usado corretamente
            test_segment = AudioSegment.silent(duration=100)  # 100ms de silêncio
        except Exception as install_e:
            print(f"Erro ao instalar ou usar pydub: {install_e}")
            print("AVISO: pydub nao esta funcionando corretamente devido a incompatibilidade com esta versao do Python.")
            print("   Isto ocorre em versoes mais recentes do Python (ex: 3.13) devido a mudancas na biblioteca 'audioop'.")
            print("   Tentando método alternativo...")
            # Chama o fallback que não depende de pydub
            return _unificar_arquivos_audio_fallback(lista_arquivos, caminho_saida)
    except Exception as e:
        # Ocorreu um erro ao tentar usar o pydub (possivelmente falta de dependências como audioop)
        print(f"pydub encontrado mas nao pode ser usado: {e}")
        print("AVISO: pydub nao esta funcionando corretamente devido a incompatibilidade com esta versao do Python.")
        print("   Isto ocorre em versoes mais recentes do Python (ex: 3.13) devido a mudancas na biblioteca 'audioop'.")
        print("   Tentando método alternativo...")
        # Chama o fallback que não depende de pydub
        return _unificar_arquivos_audio_fallback(lista_arquivos, caminho_saida)
    
    if not lista_arquivos:
        print("Lista de arquivos vazia.")
        return False
    
    print(f"Unificando {len(lista_arquivos)} arquivos de audio...")
    
    try:
        # Carrega o primeiro arquivo
        primeiro_arquivo = AudioSegment.from_file(lista_arquivos[0])
        audio_final = primeiro_arquivo
        
        # Adiciona os demais arquivos sequencialmente
        for caminho_arq in tqdm(lista_arquivos[1:], desc="Unificando audios", unit=" arq", ncols=80):
            try:
                parte_audio = AudioSegment.from_file(caminho_arq)
                audio_final += parte_audio  # Concatena
            except Exception as e:
                print(f"\nErro ao processar '{caminho_arq}': {e}")
                continue # Continua com o proximo arquivo
        
        # Exporta o áudio final
        audio_final.export(caminho_saida, format="mp3")
        print(f"Audio unificado salvo em: {caminho_saida}")
        return True
        
    except Exception as e:
        print(f"Erro ao unificar audios: {e}")
        import traceback
        traceback.print_exc()
        return False

def _unificar_arquivos_audio_fallback(lista_arquivos: List[str], caminho_saida: str) -> bool:
    """
    Método de fallback para unificar arquivos de áudio.
    Este método tenta usar o módulo wave do Python para concatenar arquivos de áudio MP3,
    ou simplesmente copia o primeiro arquivo se houver apenas um.
    """
    if not lista_arquivos:
        print("Lista de arquivos vazia.")
        return False
    
    print(f"Usando metodo de fallback para unificar {len(lista_arquivos)} arquivos de audio...")
    
    if len(lista_arquivos) == 1:
        # Se há apenas um arquivo, simplesmente copia para o destino
        try:
            shutil.copy2(lista_arquivos[0], caminho_saida)
            print(f"Arquivo unico copiado para: {caminho_saida}")
            return True
        except Exception as e:
            print(f"Erro ao copiar arquivo: {e}")
            return False
    else:
        # Tenta usar uma abordagem alternativa para concatenar arquivos MP3
        # Vamos chamar diretamente a função que faz a concatenação binária
        sucesso = _concatenar_mp3_com_wave(lista_arquivos, caminho_saida)
        if not sucesso:
            print(f"Não é possível unificar {len(lista_arquivos)} arquivos de audio sem FFmpeg ou pydub funcionando.")
            print(f"Os arquivos individuais permanecem disponiveis para uso individual.")
            print(f"   Pasta com arquivos individuais: {Path(lista_arquivos[0]).parent}")
        return sucesso

def _concatenar_mp3_com_wave(lista_arquivos: List[str], caminho_saida: str) -> bool:
    """
    Tenta concatenar arquivos MP3 usando o módulo wave.
    Esta função tenta lidar com arquivos MP3 diretamente ou convertendo-os temporariamente.
    """
    import tempfile
    import subprocess
    from pathlib import Path
    
    # Primeiro, vamos tentar verificar se os arquivos são realmente MP3 válidos
    arquivos_validos = []
    for arquivo in lista_arquivos:
        if Path(arquivo).exists():
            # Aceita arquivos mesmo que sejam pequenos, pois o tamanho pode ser pequeno
            # devido a headers de MP3 ou outros fatores
            arquivos_validos.append(arquivo)
        else:
            print(f"Arquivo invalido ou inexistente ignorado: {arquivo}")
    
    if len(arquivos_validos) == 0:
        print("Nenhum arquivo de audio valido encontrado para concatenacao.")
        return False
    
    # Para arquivos MP3, vamos usar uma abordagem baseada em bytes
    # já que o módulo wave não lida diretamente com MP3
    try:
        # Vamos tentar uma abordagem mais robusta para concatenar MP3s
        with open(caminho_saida, 'wb') as saida:
            for i, arquivo in enumerate(arquivos_validos):
                print(f"Adicionando parte {i+1}/{len(arquivos_validos)}...")
                with open(arquivo, 'rb') as entrada:
                    # Pular o cabeçalho ID3 se existir
                    data = entrada.read()
                    # Encontrar o início real do áudio MP3 (procurar pelo frame sync)
                    # O frame MP3 começa com 0xFFE, então vamos procurar por este padrão
                    start_pos = 0
                    # Procurar por padrão de sincronização de frame MP3 (0xFFE)
                    for j in range(len(data) - 1):
                        if (data[j] & 0xFF) == 0xFF and (data[j+1] & 0xE0) == 0xE0:
                            start_pos = j
                            break
                    
                    # Escrever o conteúdo do arquivo, começando do frame MP3
                    if start_pos > 0:
                        saida.write(data[start_pos:])
                    else:
                        # Se não encontrar sincronização, escrever todo o conteúdo
                        saida.write(data)
        
        print(f"Audio concatenado salvo em: {caminho_saida}")
        return True
    except Exception as e:
        print(f"Erro ao concatenar arquivos MP3 diretamente: {e}")
        # Se a abordagem direta falhar, tentar usar o FFmpeg via subprocess como ultimo recurso
        return _tentar_concatenacao_ffmpeg_simples(lista_arquivos, caminho_saida)

def _tentar_concatenacao_ffmpeg_simples(lista_arquivos: List[str], caminho_saida: str) -> bool:
    """
    Tenta usar FFmpeg diretamente via subprocess para concatenar arquivos.
    Esta e uma tentativa final se outros metodos falharem.
    """
    try:
        # Criar um arquivo de lista temporário para o FFmpeg
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f_lista:
            for arquivo in lista_arquivos:
                # Usar caminho absoluto escapar caracteres especiais
                caminho_absoluto = Path(arquivo).resolve()
                f_lista.write(f"file '{caminho_absoluto}'\n")
            caminho_lista = f_lista.name
        
        # Comando FFmpeg para concatenar arquivos usando o arquivo de lista
        comando = [
            "ffmpeg",
            "-y",  # Sobrescrever arquivo de saída se existir
            "-f", "concat",
            "-safe", "0",  # Permitir caminhos não seguros
            "-i", caminho_lista,  # Arquivo com lista de inputs
            "-c", "copy",  # Copiar streams sem re-encoder
            caminho_saida
        ]
        
        # Executar o comando FFmpeg
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Limpar o arquivo temporário
        Path(caminho_lista).unlink()
        
        if resultado.returncode == 0:
            print(f"Audio concatenado com FFmpeg salvo em: {caminho_saida}")
            return True
        else:
            print(f"❌ FFmpeg falhou ao concatenar arquivos: {resultado.stderr}")
            return False
            
    except FileNotFoundError:
        print("FFmpeg nao encontrado no sistema para concatenacao de audio.")
        return False
    except Exception as e:
        print(f"Erro ao tentar usar FFmpeg para concatenacao: {e}")
        return False
