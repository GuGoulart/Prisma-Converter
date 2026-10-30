"""errors.py — Exceções do domínio."""


class ErroUsuario(ValueError):
    """Erro cuja mensagem foi escrita para ser mostrada ao usuário."""


class JobCancelado(Exception):
    """O usuário cancelou a tarefa."""
