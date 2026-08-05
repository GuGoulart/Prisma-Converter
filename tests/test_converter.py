import unittest
import sys
import os
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.converter import (csv_para_docx, csv_para_json, json_para_csv)
from core.file_tools import calcular_hashes, criptografar_arquivo, descriptografar_arquivo

class TestConverter(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_csv_para_json_e_reverso(self):
        csv_file = os.path.join(self.temp_dir, "test.csv")
        json_file = os.path.join(self.temp_dir, "test.json")
        csv_out = os.path.join(self.temp_dir, "out.csv")

        with open(csv_file, "w", encoding="utf-8") as f:
            f.write("nome,idade\nAlice,30\nBob,25\n")

        csv_para_json(csv_file, json_file)
        self.assertTrue(os.path.exists(json_file))
        self.assertGreater(os.path.getsize(json_file), 0)

        json_para_csv(json_file, csv_out)
        self.assertTrue(os.path.exists(csv_out))

    def test_csv_para_docx_direto(self):
        csv_file = os.path.join(self.temp_dir, "dados.csv")
        docx_file = os.path.join(self.temp_dir, "dados.docx")

        with open(csv_file, "w", encoding="utf-8") as f:
            f.write("id,produto,preco\n1,Notebook,3500\n2,Mouse,150\n")

        csv_para_docx(csv_file, docx_file)
        self.assertTrue(os.path.exists(docx_file))
        self.assertGreater(os.path.getsize(docx_file), 0)

    def test_criptografia_descriptografia_aes(self):
        orig_file = os.path.join(self.temp_dir, "segreto.txt")
        enc_file = os.path.join(self.temp_dir, "segreto.enc")
        dec_file = os.path.join(self.temp_dir, "restaurado.txt")
        senha = "ChaveSuperSegura123!"

        with open(orig_file, "wb") as f:
            f.write(b"Dados confidenciais do sistema Prisma 2026")

        criptografar_arquivo(orig_file, enc_file, senha)
        self.assertTrue(os.path.exists(enc_file))

        descriptografar_arquivo(enc_file, dec_file, senha)
        self.assertTrue(os.path.exists(dec_file))

        with open(dec_file, "rb") as f:
            conteudo = f.read()
        self.assertEqual(conteudo, b"Dados confidenciais do sistema Prisma 2026")

    def test_calcular_hashes(self):
        sample = os.path.join(self.temp_dir, "hash_test.txt")
        with open(sample, "wb") as f:
            f.write(b"Hello World")
        hashes = calcular_hashes(sample)
        self.assertIn("md5", hashes)
        self.assertIn("sha1", hashes)
        self.assertIn("sha256", hashes)
        self.assertEqual(hashes["md5"], "b10a8db164e0754105b7a99be72e3fe5")

if __name__ == "__main__":
    unittest.main()
