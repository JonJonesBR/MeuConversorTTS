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
    project_path = Path(__file__).parent
    git_path = project_path / ".git"
    return git_path.is_dir()

def check_for_updates_git():
    """
    Usa comandos Git para verificar se há atualizações no repositório remoto.
    Retorna um status: 'atualizado', 'atualizacao_disponivel', 'erro' ou 'divergente'.
    """
    try:
        print("🔎 A verificar o estado do repositório local...")
        # Garante que o estado local está limpo antes de verificar
        subprocess.run(
            ["git", "status"],
            capture_output=True, check=True, text=True
        )

        print("📡 A contactar o GitHub para procurar atualizações...")
        # Busca as últimas alterações do repositório remoto sem as aplicar
        subprocess.run(
            ["git", "fetch"],
            capture_output=True, check=True, text=True
        )

        # Compara o estado local com o remoto que acabámos de buscar
        status_result = subprocess.run(
            ["git", "status", "-uno"],
            capture_output=True, check=True, text=True
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
             # Este erro não deveria acontecer se is_git_repository for chamado primeiro
             return "erro", "❌ Esta não parece ser uma instalação via 'git clone'."
        return "erro", f"❌ Ocorreu um erro ao comunicar com o Git:\n{error_message}"
