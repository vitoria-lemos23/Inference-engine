"""Ponto de entrada:  python -m sbc [base] [--modo frente|tras|misto] [--meta variavel] [--script arquivo]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .dialogo import MODOS, PASTA_BASES, Dialogo, listar_bases
from .parser import carregar


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m sbc",
                                 description="Shell genérico de sistemas baseados em conhecimento (terminal).")
    ap.add_argument("base", nargs="?", help="arquivo .kb/.json ou nome de uma base de exemplo (ex.: animais)")
    ap.add_argument("--modo", choices=list(MODOS), default="misto", help="encadeamento inicial (padrão: misto)")
    ap.add_argument("--meta", help="se informado, já inicia uma consulta para essa variável")
    ap.add_argument("--script", help="arquivo com as respostas/comandos (uma por linha); eco na tela")
    ap.add_argument("--listar-bases", action="store_true", help="lista as bases de exemplo e sai")
    a = ap.parse_args(argv)

    if a.listar_bases:
        for nome, _, titulo, desc in listar_bases():
            print(f"{nome:<12} {titulo}\n{'':<12} {desc}")
        return 0

    base, caminho = None, None
    if a.base:
        cand = Path(a.base)
        if not cand.exists():
            cand = PASTA_BASES / (a.base if a.base.endswith((".kb", ".json")) else a.base + ".kb")
        if not cand.exists():
            print(f"Base não encontrada: {a.base}", file=sys.stderr)
            return 2
        base, caminho = carregar(cand), str(cand)

    entrada, eco = None, False
    if a.script:
        linhas = iter(Path(a.script).read_text(encoding="utf-8").splitlines())

        def entrada(prompt=""):
            try:
                return next(linhas)
            except StopIteration:
                raise EOFError from None
        eco = True

    d = Dialogo(None, entrada=entrada, modo=a.modo, eco=eco)
    if base is not None:
        d.carregar_base(base, caminho)
    d._banner()
    if a.meta and base is not None:
        d.processar(f"consultar {a.meta}")
    d.executar(banner=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
