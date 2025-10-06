# -*- coding: utf-8 -*-
"""
Módulo para gerir a verificação de atualizações do projeto usando Git.
"""
import os
import subprocess
from pathlib import Path

# URL do repositório remoto para referência
REPO_URL = "https://github.com/JonJonesBR/MeuConversorTTS.git"

def is_git_repository():
    """Verifica se o diretório atual do script é um repositório Git válido."""
    project_path = Path.cwd()
    git_path = project_path / ".git"
    return git_path.is_dir()

def check_for_updates_git():
    """
    Usa comandos Git para verificar se há atualizações no repositório remoto.
    Retorna um status: 'atualizado', 'atualizacao_disponivel', 'erro' ou 'divergente'.
    """
    if not is_git_repository():
        return "erro", "❌ Esta não parece ser uma instalação via 'git clone'. A atualização automática não é possível."

    try:
        print("🔎 A verificar o estado do repositório local...")
        # Limpa o estado local para evitar falsos positivos
        subprocess.run(["git", "remote", "update"], capture_output=True, check=True, text=True, cwd=Path.cwd())

        print("📡 A contactar o GitHub para procurar atualizações...")
        status_result = subprocess.run(
            ["git", "status", "-uno"],
            capture_output=True, check=True, text=True, cwd=Path.cwd()
        )
        
        output = status_result.stdout.lower()

        if "your branch is up to date" in output:
            return "atualizado", "✅ O seu script já está na versão mais recente."
        elif "your branch is behind" in output:
            return "atualizacao_disponivel", "🆕 Uma nova versão está disponível!"
        elif "have diverged" in output:
            return "divergente", "⚠️ A sua versão local e a remota divergem. A atualização forçará a versão do GitHub."
        else:
            # Se houver modificações locais, mas o branch não estiver "behind", ainda oferece a atualização para resetar.
            if "changes not staged for commit" in output or "untracked files" in output:
                 return "divergente", "⚠️ Foram detetadas alterações locais. A atualização irá substituí-las pela versão oficial."
            return "erro", "🤔 Não foi possível determinar o estado da atualização."

    except FileNotFoundError:
        return "erro", "❌ O comando 'git' não foi encontrado. Certifique-se de que o Git está instalado."
    except subprocess.CalledProcessError as e:
        error_message = e.stderr or e.stdout
        return "erro", f"❌ Ocorreu um erro ao comunicar com o Git:\n{error_message}"

async def verificar_e_atualizar():
    """
    Verifica por atualizações e aplica se disponível, forçando a atualização
    para evitar conflitos locais.
    """
    status, message = check_for_updates_git()
    print(message)

    # Permite a atualização tanto se estiver desatualizado ("behind") quanto se tiver divergido
    if status in ["atualizacao_disponivel", "divergente"]:
        print("\n🔄 A aplicar atualização... Isto irá substituir quaisquer alterações locais.")
        try:
            # 1. Busca as últimas alterações do repositório remoto
            subprocess.run(["git", "fetch", "origin"], capture_output=True, check=True, text=True, cwd=Path.cwd())
            
            # 2. Força o reset do branch local para corresponder ao branch 'main' do repositório remoto
            subprocess.run(["git", "reset", "--hard", "origin/main"], capture_output=True, check=True, text=True, cwd=Path.cwd())
            
            print("\n✅ Atualização aplicada com sucesso!")
            print("   É recomendado reiniciar o script para que as alterações tenham efeito.")

        except subprocess.CalledProcessError as e:
            # Imprime o erro detalhado do Git para ajudar a diagnosticar
            error_details = e.stderr.strip() if e.stderr else e.stdout.strip()
            print(f"❌ Erro ao aplicar atualização: {e}")
            if error_details:
                print(f"   Detalhes do Git: {error_details}")
