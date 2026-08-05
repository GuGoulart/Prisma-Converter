import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.security import (validar_nome, verificar_assinatura_maliciosa)

class TestSecurity(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sanitizacao_nome_arquivo(self):
        # validar_nome retorna True se extensao e valida, False se proibidav (ex: .exe, .bat, .dll)
        self.assertFalse(validar_nome("../malicious.exe"))
        self.assertFalse(validar_nome("script.sh"))
        self.assertTrue(validar_nome("normal_file.pdf"))
        self.assertTrue(validar_nome("imagem.png"))

    def test_verificar_assinatura_maliciosa(self):
        # Cria arquivo binario executavel MZ
        exe_file = os.path.join(self.temp_dir, "test.exe")
        with open(exe_file, "wb") as f:
            f.write(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00")

        # Cria arquivo PNG legitimo
        png_file = os.path.join(self.temp_dir, "test.png")
        with open(png_file, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

        self.assertTrue(verificar_assinatura_maliciosa(exe_file))
        self.assertFalse(verificar_assinatura_maliciosa(png_file))

if __name__ == "__main__":
    unittest.main()
