"""utils.py — Funções puras compartilhadas, sem dependências pesadas."""
import os


def formatar_tamanho(b: float) -> str:
    for unidade in ("B", "KB", "MB", "GB"):
        if b < 1024 or unidade == "GB":
            return f"{int(b)} B" if unidade == "B" else f"{b:.1f} {unidade}"
        b /= 1024
    return ""


def nomes_unicos(nomes: list[str]) -> list[str]:
    """Numera repetições ("a.pdf", "a (2).pdf") sem diferenciar maiúsculas."""
    vistos: dict[str, int] = {}
    resultado = []
    for nome in nomes:
        chave = nome.lower()
        vistos[chave] = vistos.get(chave, 0) + 1
        if vistos[chave] == 1:
            resultado.append(nome)
        else:
            base, ext = os.path.splitext(nome)
            resultado.append(f"{base} ({vistos[chave]}){ext}")
    return resultado
