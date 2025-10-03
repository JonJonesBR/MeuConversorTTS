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
    try:
<<<<<<< HEAD
        print("A verificar o estado do repositorio local...")
        # Garante que o estado local está limpo antes de verificar
=======
        print("🔎 A verificar o estado do repositório local...")
>>>>>>> bb19449059105991693c172edf8db34073a419fe
        subprocess.run(
            ["git", "status"],
            capture_output=True, check=True, text=True, cwd=Path.cwd()
        )

<<<<<<< HEAD
        print("A contactar o GitHub para procurar atualizacoes...")
        # Busca as últimas alterações do repositório remoto sem as aplicar
=======
        print("📡 A contactar o GitHub para procurar atualizações...")
>>>>>>> bb19449059105991693c172edf8db34073a419fe
        subprocess.run(
            ["git", "fetch"],
            capture_output=True, check=True, text=True, cwd=Path.cwd()
        )

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
            return "divergente", "⚠️ A sua versão local e a remota divergem. Recomenda-se uma reinstalação."
        else:
            return "erro", "🤔 Não foi possível determinar o estado da atualização."

    except FileNotFoundError:
        return "erro", "❌ O comando 'git' não foi encontrado. Certifique-se de que o Git está instalado."
    except subprocess.CalledProcessError as e:
        error_message = e.stderr or e.stdout
        if "not a git repository" in error_message.lower():
             return "erro", "❌ Esta não parece ser uma instalação via 'git clone'."
        return "erro", f"❌ Ocorreu um erro ao comunicar com o Git:\n{error_message}"