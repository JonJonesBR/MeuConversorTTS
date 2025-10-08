# -*- coding: utf-8 -*-
"""
Módulo para gerir a verificação de atualizações do projeto usando Git.
Implementação robusta baseada em 'git rev-list', independente do idioma.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Tuple

# URL do repositório remoto para referência (não é estritamente necessário)
REPO_URL = "https://github.com/JonJonesBR/MeuConversorTTS.git"


def _run_git(args: list[str]) -> Tuple[int, str, str]:
    """Executa um comando git no diretório atual e retorna (rc, stdout, stderr)."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=False
        )
        return proc.returncode, proc.stdout.strip(), (proc.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", "git não encontrado no PATH"


def is_git_repository() -> bool:
    """Verifica se o diretório atual é um repositório Git válido."""
    rc, out, _ = _run_git(["rev-parse", "--is-inside-work-tree"])
    return rc == 0 and out.lower() == "true"


def _descobrir_branch_remoto_padrao() -> str:
    """
    Tenta descobrir o branch padrão do remoto 'origin' (ex.: 'main' ou 'master').
    Fallback: 'main'.
    """
    # ex.: 'origin/main'
    rc, out, _ = _run_git(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"])
    if rc == 0 and out.startswith("origin/"):
        return out.split("/", 1)[1]
    return "main"


def _estado_relativo(remote_branch: str) -> Tuple[int, int]:
    """
    Retorna (ahead, behind) comparando HEAD com origin/<remote_branch>,
    após garantir fetch.
    """
    _run_git(["remote", "update"])
    _run_git(["fetch", "origin", "--prune"])
    rc, out, err = _run_git(["rev-list", "--left-right", "--count", f"HEAD...origin/{remote_branch}"])
    if rc != 0 or not out:
        # Pode ocorrer se o repositório local não aponta para origin/<branch>.
        # Fallback para tentar diretamente 'origin/main'.
        rc2, out2, _ = _run_git(["rev-list", "--left-right", "--count", "HEAD...origin/main"])
        if rc2 != 0 or not out2:
            # Sem referência confiável
            return (0, 0)
        out = out2
    # Ex.: "A B" -> A commits à esquerda (local à frente), B commits à direita (local atrás)
    try:
        left_str, right_str = out.split()
        ahead = int(left_str)
        behind = int(right_str)
        return (ahead, behind)
    except Exception:
        return (0, 0)


def check_for_updates_git() -> tuple[str, str]:
    """
    Verifica o estado do repositório em relação ao remoto.
    Retorna (status, mensagem), onde status ∈ {'atualizado','atualizacao_disponivel','divergente','erro'}.
    """
    if not is_git_repository():
        return "erro", "❌ Esta não parece ser uma instalação via 'git clone'. A atualização automática não é possível."

    # Verifica se o git está acessível
    rc_git, _, err_git = _run_git(["--version"])
    if rc_git != 0:
        return "erro", "❌ O comando 'git' não foi encontrado. Certifique-se de que o Git está instalado."

    print("🔎 A verificar o estado do repositório local...")
    branch_remoto = _descobrir_branch_remoto_padrao()

    ahead, behind = _estado_relativo(branch_remoto)

    if ahead == 0 and behind == 0:
        # Pode significar "em dia" OU que não conseguimos determinar (e.g., remoto ausente).
        # Tentar identificar alterações locais não commitadas apenas para orientar.
        rc_st, out_st, _ = _run_git(["status", "--porcelain"])
        if rc_st == 0 and not out_st:
            return "atualizado", "✅ O seu script já está na versão mais recente."
        else:
            # Há modificações locais, mas sem commits à frente/atrás
            return "divergente", "⚠️ Foram detectadas alterações locais. A atualização irá substituí-las pela versão oficial."
    elif ahead == 0 and behind > 0:
        return "atualizacao_disponivel", "🆕 Uma nova versão está disponível!"
    elif ahead > 0 and behind == 0:
        return "divergente", "⚠️ O seu branch local está à frente do remoto (commits locais). A atualização forçará a versão do GitHub."
    else:  # ahead > 0 and behind > 0
        return "divergente", "⚠️ O seu branch local e o remoto divergem. A atualização forçará a versão do GitHub."


async def verificar_e_atualizar() -> None:
    """
    Verifica por atualizações e aplica, forçando a atualização para evitar conflitos locais.
    """
    status, message = check_for_updates_git()
    print(message)

    if status in ("atualizacao_disponivel", "divergente"):
        print("\n🔄 A aplicar atualização... Isto irá substituir quaisquer alterações locais.")
        branch_remoto = _descobrir_branch_remoto_padrao()
        # Busca e reseta para a referência do remoto
        rc1, _, err1 = _run_git(["fetch", "origin"])
        if rc1 != 0:
            print(f"❌ Erro ao buscar atualizações: {err1}")
            return
        rc2, _, err2 = _run_git(["reset", "--hard", f"origin/{branch_remoto}"])
        if rc2 != 0:
            print(f"❌ Erro ao aplicar atualização: {err2}")
            return

        print("\n✅ Atualização aplicada com sucesso!")
        print("   É recomendado reiniciar o script para que as alterações tenham efeito.")
