"""
file_tools.py — Ferramentas de manipulação de arquivos.
Compressão, ZIP com senha, criptografia AES, hash, scrubber de metadados,
renomear em lote.
"""

import os
import io
import zipfile
import tarfile
import hashlib
import logging

log = logging.getLogger(__name__)


# ─── Comprimir Arquivos ───────────────────────────────────────

def comprimir_arquivos(caminhos: list, saida: str, formato: str = "zip"):
    """
    Comprime múltiplos arquivos em um ZIP ou TAR.GZ.

    Args:
        caminhos: Lista de caminhos de arquivos.
        saida: Caminho do arquivo comprimido de saída.
        formato: "zip" ou "tar.gz".
    """
    if not caminhos:
        raise ValueError("Nenhum arquivo fornecido para compressão.")

    if formato == "tar.gz":
        with tarfile.open(saida, "w:gz") as tar:
            for caminho in caminhos:
                if os.path.exists(caminho):
                    tar.add(caminho, arcname=os.path.basename(caminho))
    else:
        with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as zf:
            for caminho in caminhos:
                if os.path.exists(caminho):
                    zf.write(caminho, arcname=os.path.basename(caminho))

    if not os.path.exists(saida) or os.path.getsize(saida) == 0:
        raise RuntimeError("Erro ao gerar o arquivo comprimido.")

    log.info(f"Compressão OK: {len(caminhos)} arquivo(s) -> {formato}")


# ─── ZIP com Senha (AES-256) ─────────────────────────────────

def zip_com_senha(caminhos: list, saida: str, senha: str):
    """
    Cria um ZIP protegido com criptografia AES-256.

    Args:
        caminhos: Lista de caminhos de arquivos.
        saida: Caminho do arquivo ZIP de saída.
        senha: Senha para proteger o ZIP.
    """
    try:
        import pyzipper
    except ImportError:
        raise RuntimeError("pyzipper não instalado.")

    if not caminhos:
        raise ValueError("Nenhum arquivo fornecido.")
    if not senha or not senha.strip():
        raise ValueError("A senha não pode ser vazia.")

    with pyzipper.AESZipFile(
        saida, "w",
        compression=pyzipper.ZIP_LZMA,
        encryption=pyzipper.WZ_AES,
    ) as zf:
        zf.setpassword(senha.encode("utf-8"))
        for caminho in caminhos:
            if os.path.exists(caminho):
                zf.write(caminho, arcname=os.path.basename(caminho))

    if not os.path.exists(saida) or os.path.getsize(saida) == 0:
        raise RuntimeError("Erro ao gerar o ZIP protegido.")

    log.info(f"ZIP com senha OK: {len(caminhos)} arquivo(s)")


# ─── Criptografia AES-256-CBC ────────────────────────────────

def criptografar_arquivo(entrada: str, saida: str, senha: str):
    """
    Criptografa um arquivo com AES-256-CBC.
    O formato do arquivo .enc:
        [16 bytes salt][16 bytes IV][dados criptografados]

    Args:
        entrada: Caminho do arquivo original.
        saida: Caminho do arquivo .enc de saída.
        senha: Senha para criptografia.
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes

    if not os.path.exists(entrada):
        raise FileNotFoundError(f"Arquivo não encontrado: {entrada}")
    if not senha or not senha.strip():
        raise ValueError("A senha não pode ser vazia.")

    # Gerar salt e derivar chave
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    chave = kdf.derive(senha.encode("utf-8"))

    # IV aleatório
    iv = os.urandom(16)

    # Ler e paddar dados
    with open(entrada, "rb") as f:
        dados = f.read()

    padder = padding.PKCS7(128).padder()
    dados_padded = padder.update(dados) + padder.finalize()

    # Criptografar
    cipher = Cipher(algorithms.AES(chave), modes.CBC(iv))
    encryptor = cipher.encryptor()
    dados_cripto = encryptor.update(dados_padded) + encryptor.finalize()

    # Salvar: salt + IV + dados criptografados
    with open(saida, "wb") as f:
        f.write(salt)
        f.write(iv)
        f.write(dados_cripto)

    log.info(f"Criptografia OK: {os.path.basename(entrada)}")


def descriptografar_arquivo(entrada: str, saida: str, senha: str):
    """
    Descriptografa um arquivo .enc criado por criptografar_arquivo().

    Args:
        entrada: Caminho do arquivo .enc.
        saida: Caminho do arquivo descriptografado.
        senha: Senha usada na criptografia.
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes

    if not os.path.exists(entrada):
        raise FileNotFoundError(f"Arquivo não encontrado: {entrada}")
    if not senha or not senha.strip():
        raise ValueError("A senha não pode ser vazia.")

    with open(entrada, "rb") as f:
        conteudo = f.read()

    if len(conteudo) < 48:  # 16 salt + 16 IV + pelo menos 16 dados
        raise ValueError("Arquivo criptografado inválido ou corrompido.")

    salt = conteudo[:16]
    iv = conteudo[16:32]
    dados_cripto = conteudo[32:]

    # Derivar chave com o mesmo salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    chave = kdf.derive(senha.encode("utf-8"))

    # Descriptografar
    cipher = Cipher(algorithms.AES(chave), modes.CBC(iv))
    decryptor = cipher.decryptor()

    try:
        dados_padded = decryptor.update(dados_cripto) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        dados = unpadder.update(dados_padded) + unpadder.finalize()
    except Exception:
        raise ValueError("Senha incorreta ou arquivo corrompido.")

    with open(saida, "wb") as f:
        f.write(dados)

    log.info(f"Descriptografia OK: {os.path.basename(entrada)}")





# ─── Calculadora de Hash ─────────────────────────────────────

def calcular_hashes(caminho: str) -> dict:
    """
    Calcula hashes MD5, SHA-1 e SHA-256 de um arquivo.

    Args:
        caminho: Caminho do arquivo.

    Returns:
        Dict com {md5, sha1, sha256, tamanho_bytes, tamanho_formatado}.
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()

    tamanho = 0
    with open(caminho, "rb") as f:
        while True:
            bloco = f.read(8192)
            if not bloco:
                break
            md5.update(bloco)
            sha1.update(bloco)
            sha256.update(bloco)
            tamanho += len(bloco)

    return {
        "md5": md5.hexdigest(),
        "sha1": sha1.hexdigest(),
        "sha256": sha256.hexdigest(),
        "tamanho_bytes": tamanho,
        "tamanho_formatado": _formatar_tamanho(tamanho),
    }


def _formatar_tamanho(bytes_val: int) -> str:
    """Formata bytes em formato legível."""
    for unidade in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unidade}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


# ─── Renomear em Lote ────────────────────────────────────────

def renomear_em_lote(caminhos: list, padrao: str, saida_zip: str):
    """
    Renomeia múltiplos arquivos com um padrão e empacota em ZIP.
    O padrão pode conter {n} para numeração sequencial.

    Args:
        caminhos: Lista de caminhos dos arquivos.
        padrao: Padrão de nome (ex: "foto_{n}", "documento_{n}").
        saida_zip: Caminho do ZIP de saída.

    Exemplo:
        padrao="relatorio_{n}" → "relatorio_001.pdf", "relatorio_002.pdf", ...
    """
    if not caminhos:
        raise ValueError("Nenhum arquivo fornecido.")
    if not padrao or not padrao.strip():
        raise ValueError("O padrão de nome não pode ser vazio.")

    padrao = padrao.strip()

    with zipfile.ZipFile(saida_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, caminho in enumerate(caminhos, start=1):
            if not os.path.exists(caminho):
                continue

            ext = os.path.splitext(caminho)[1]  # Mantém a extensão original
            num = str(i).zfill(3)

            if "{n}" in padrao:
                novo_nome = padrao.replace("{n}", num) + ext
            else:
                novo_nome = f"{padrao}_{num}{ext}"

            zf.write(caminho, arcname=novo_nome)

    if not os.path.exists(saida_zip) or os.path.getsize(saida_zip) == 0:
        raise RuntimeError("Erro ao gerar o ZIP com arquivos renomeados.")

    log.info(f"Renomear em lote OK: {len(caminhos)} arquivo(s)")
