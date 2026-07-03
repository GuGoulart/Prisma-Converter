import fitz
import os
import zipfile

def mesclar_pdfs(arquivos_entrada: list, caminho_saida: str):
    """
    Mescla uma lista de arquivos PDF em um único arquivo.
    """
    if not arquivos_entrada:
        raise ValueError("Nenhum arquivo fornecido para mesclagem.")
        
    resultado = fitz.open()
    for caminho in arquivos_entrada:
        with fitz.open(caminho) as doc:
            resultado.insert_pdf(doc)
    
    resultado.save(caminho_saida)
    resultado.close()


def dividir_pdf(arquivo_entrada: str, caminho_saida_zip: str, modo: str = "individual", parametro: str = ""):
    """
    Divide um PDF e salva em um arquivo ZIP.
    Modos:
    - "individual": 1 arquivo por página.
    - "fixo": Divide a cada N páginas (parametro = N).
    - "custom": Intervalos específicos (parametro = "1-2, 4-5").
    """
    with fitz.open(arquivo_entrada) as doc:
        total_paginas = doc.page_count
        
        pasta_temp = caminho_saida_zip + "_temp"
        os.makedirs(pasta_temp, exist_ok=True)
        
        caminhos_gerados = []
        
        # 1. Definir os intervalos
        intervalos = []
        if modo == "fixo":
            try:
                passo = int(parametro)
                if passo < 1: passo = 1
            except:
                passo = 1
            for i in range(0, total_paginas, passo):
                fim = min(i + passo - 1, total_paginas - 1)
                intervalos.append((i, fim))
                
        elif modo == "custom":
            partes = [p.strip() for p in parametro.split(",")]
            for parte in partes:
                if "-" in parte:
                    try:
                        inicio, fim = parte.split("-")
                        inicio = max(0, int(inicio) - 1)
                        fim = min(total_paginas - 1, int(fim) - 1)
                        if inicio <= fim:
                            intervalos.append((inicio, fim))
                    except: pass
                else:
                    try:
                        pg = int(parte) - 1
                        if 0 <= pg < total_paginas:
                            intervalos.append((pg, pg))
                    except: pass
            if not intervalos: # fallback
                intervalos = [(i, i) for i in range(total_paginas)]
                
        else: # individual
            intervalos = [(i, i) for i in range(total_paginas)]
            
        # 2. Gerar PDFs baseados nos intervalos
        for idx, (inicio, fim) in enumerate(intervalos):
            novo_doc = fitz.open()
            novo_doc.insert_pdf(doc, from_page=inicio, to_page=fim)
            caminho_pag = os.path.join(pasta_temp, f"parte_{idx+1}.pdf")
            novo_doc.save(caminho_pag)
            novo_doc.close()
            caminhos_gerados.append(caminho_pag)
            
        with zipfile.ZipFile(caminho_saida_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for caminho in caminhos_gerados:
                nome_arquivo = os.path.basename(caminho)
                zipf.write(caminho, arcname=nome_arquivo)
                
        for caminho in caminhos_gerados:
            try: os.remove(caminho)
            except: pass
        try: os.rmdir(pasta_temp)
        except: pass


def proteger_pdf(arquivo_entrada: str, senha: str, caminho_saida: str):
    """
    Adiciona uma senha (user_pw) para abrir o PDF.
    """
    with fitz.open(arquivo_entrada) as doc:
        perm = int(fitz.PDF_PERM_PRINT | fitz.PDF_PERM_COPY)
        doc.save(
            caminho_saida, 
            encryption=fitz.PDF_ENCRYPT_AES_256, 
            owner_pw=senha, 
            user_pw=senha,
            permissions=perm
        )


def desproteger_pdf(arquivo_entrada: str, senha: str, caminho_saida: str):
    """
    Remove a senha de um PDF criptografado.
    """
    doc = fitz.open(arquivo_entrada)
    if not doc.is_encrypted:
        doc.save(caminho_saida)
        doc.close()
        return

    sucesso = doc.authenticate(senha)
    if not sucesso:
        doc.close()
        raise ValueError("Senha incorreta.")
        
    doc.save(caminho_saida)
    doc.close()
