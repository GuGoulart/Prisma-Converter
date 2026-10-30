"""file_tools.py — Compressão, ZIP com senha, criptografia AES, hash e renomeação em lote.

Os arquivos chegam como pares [caminho, nome] para que o nome original seja
preservado dentro dos pacotes, sem depender do nome usado no disco.
"""
import hashlib
import logging
import os
import tarfile
import zipfile

from core.errors import ErroUsuario
from core.utils import formatar_tamanho, nomes_unicos

log = logging.getLogger(__name__)

_BLOCO = 1024 * 1024
_ITERACOES_PBKDF2 = 480000


def comprimir_arquivos(arquivos: list, saida: str, formato: str = "zip") -> None:
    if not arquivos:
        raise ErroUsuario("Nenhum arquivo fornecido para compressão.")
    pares = list(zip([a[0] for a in arquivos], nomes_unicos([a[1] for a in arquivos])))
    if formato == "tar.gz":
        with tarfile.open(saida, "w:gz") as tar:
            for caminho, nome in pares:
                tar.add(caminho, arcname=nome)
    else:
        with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as zf:
            for caminho, nome in pares:
                zf.write(caminho, arcname=nome)


def zip_com_senha(arquivos: list, saida: str, senha: str) -> None:
    import pyzipper

    if not arquivos:
        raise ErroUsuario("Nenhum arquivo fornecido.")
    if not senha.strip():
        raise ErroUsuario("A senha não pode ser vazia.")
    with pyzipper.AESZipFile(saida, "w", compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(senha.encode("utf-8"))
        for (caminho, _), nome in zip(arquivos, nomes_unicos([a[1] for a in arquivos])):
            zf.write(caminho, arcname=nome)


def _derivar_chave(senha: str, salt: bytes) -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=_ITERACOES_PBKDF2)
    return kdf.derive(senha.encode("utf-8"))


def criptografar_arquivo(entrada: str, saida: str, senha: str) -> None:
    """AES-256-CBC em streaming. Formato: [16 bytes salt][16 bytes IV][dados]."""
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    if not senha.strip():
        raise ErroUsuario("A senha não pode ser vazia.")
    salt, iv = os.urandom(16), os.urandom(16)
    encryptor = Cipher(algorithms.AES(_derivar_chave(senha, salt)), modes.CBC(iv)).encryptor()
    padder = padding.PKCS7(128).padder()
    with open(entrada, "rb") as src, open(saida, "wb") as dst:
        dst.write(salt + iv)
        while bloco := src.read(_BLOCO):
            dst.write(encryptor.update(padder.update(bloco)))
        dst.write(encryptor.update(padder.finalize()) + encryptor.finalize())


def descriptografar_arquivo(entrada: str, saida: str, senha: str) -> None:
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    if os.path.getsize(entrada) < 48:
        raise ErroUsuario("Arquivo criptografado inválido ou corrompido.")
    with open(entrada, "rb") as src, open(saida, "wb") as dst:
        salt, iv = src.read(16), src.read(16)
        decryptor = Cipher(algorithms.AES(_derivar_chave(senha, salt)), modes.CBC(iv)).decryptor()
        unpadder = padding.PKCS7(128).unpadder()
        try:
            while bloco := src.read(_BLOCO):
                dst.write(unpadder.update(decryptor.update(bloco)))
            dst.write(unpadder.update(decryptor.finalize()) + unpadder.finalize())
        except ValueError:
            raise ErroUsuario("Senha incorreta ou arquivo corrompido.") from None


def calcular_hashes(caminho: str) -> dict:
    md5, sha1, sha256 = hashlib.md5(), hashlib.sha1(), hashlib.sha256()
    tamanho = 0
    with open(caminho, "rb") as f:
        while bloco := f.read(_BLOCO):
            md5.update(bloco)
            sha1.update(bloco)
            sha256.update(bloco)
            tamanho += len(bloco)
    return {"md5": md5.hexdigest(), "sha1": sha1.hexdigest(), "sha256": sha256.hexdigest(),
            "tamanho_bytes": tamanho, "tamanho_formatado": formatar_tamanho(tamanho)}


def renomear_em_lote(arquivos: list, padrao: str, saida_zip: str) -> None:
    """Empacota os arquivos em ZIP com nomes do padrão; {n} vira a numeração sequencial."""
    if not arquivos:
        raise ErroUsuario("Nenhum arquivo fornecido.")
    padrao = padrao.strip()
    if not padrao:
        raise ErroUsuario("O padrão de nome não pode ser vazio.")
    with zipfile.ZipFile(saida_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, (caminho, nome) in enumerate(arquivos, start=1):
            num = str(i).zfill(3)
            base = padrao.replace("{n}", num) if "{n}" in padrao else f"{padrao}_{num}"
            zf.write(caminho, arcname=base + os.path.splitext(nome)[1])
