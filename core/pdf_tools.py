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
            if not intervalos:
                # CONV-004: avisa o usuário em vez de fallback silencioso
                raise ValueError(
                    "Nenhum intervalo válido encontrado. Use o formato '1-3, 5, 7-10'."
                )
                
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


def comprimir_pdf(arquivo_entrada: str, caminho_saida: str, nivel: str = "media"):
    """
    Comprime o PDF reduzindo objetos redundantes e recomprimindo imagens.
    Níveis suportados: 'baixa', 'media', 'alta'.
    """
    import io
    try:
        from PIL import Image
    except ImportError:
        Image = None

    doc = fitz.open(arquivo_entrada)

    if nivel in ("media", "alta") and Image is not None:
        quality = 40 if nivel == "alta" else 75
        max_dim = 1200 if nivel == "alta" else 2000

        xrefs_processados = set()
        
        for i in range(len(doc)):
            for img in doc.get_page_images(i):
                xref = img[0]
                if xref in xrefs_processados:
                    continue
                xrefs_processados.add(xref)
                
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n >= 4:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    
                    img_bytes = pix.tobytes("png")
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    
                    if pil_img.mode in ("RGBA", "P", "CMYK"):
                        pil_img = pil_img.convert("RGB")
                    
                    w, h = pil_img.size
                    if w > max_dim or h > max_dim:
                        ratio = min(max_dim/w, max_dim/h)
                        novo_w, novo_h = int(w * ratio), int(h * ratio)
                        pil_img = pil_img.resize((novo_w, novo_h), Image.Resampling.LANCZOS)
                        
                    img_io = io.BytesIO()
                    pil_img.save(img_io, format="JPEG", quality=quality, optimize=True)
                    new_bytes = img_io.getvalue()
                    
                    doc.update_stream(xref, new_bytes)
                    new_w, new_h = pil_img.size
                    doc.update_object(xref, f"<< /Type /XObject /Subtype /Image /Width {new_w} /Height {new_h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode >>")
                except Exception:
                    pass

    doc.save(caminho_saida, garbage=4, deflate=True, clean=True, linear=True)
    doc.close()

    # CONV-002: se o arquivo comprimido for maior ou igual ao original, retornar o original
    tamanho_original = os.path.getsize(arquivo_entrada)
    tamanho_comprimido = os.path.getsize(caminho_saida)
    if tamanho_comprimido >= tamanho_original:
        import shutil
        shutil.copy2(arquivo_entrada, caminho_saida)


def adicionar_marca_dagua(arquivo_entrada: str, texto: str, caminho_saida: str):
    """
    Adiciona uma marca d'água de texto semi-transparente no centro de todas as páginas.
    """
    doc = fitz.open(arquivo_entrada)
    for pagina in doc:
        retangulo = pagina.rect
        p = fitz.Point(retangulo.width / 4, retangulo.height / 2)
        
        tamanho_fonte = min(retangulo.width, retangulo.height) / (len(texto) * 0.5)
        if tamanho_fonte > 72: tamanho_fonte = 72
        
        pagina.insert_text(
            p,
            texto,
            fontsize=tamanho_fonte,
            color=(0.5, 0.5, 0.5), # cinza
            fill_opacity=0.3       # semi-transparente
        )
    doc.save(caminho_saida)
    doc.close()


def extrair_imagens_pdf(arquivo_entrada: str, caminho_saida_zip: str):
    """
    Extrai todas as imagens do PDF e compacta em um ZIP.
    """
    doc = fitz.open(arquivo_entrada)
    pasta_temp = caminho_saida_zip + "_temp"
    os.makedirs(pasta_temp, exist_ok=True)
    
    caminhos_gerados = []
    img_index = 1
    
    for page_num in range(len(doc)):
        pagina = doc[page_num]
        lista_imagens = pagina.get_images(full=True)
        
        for img in lista_imagens:
            xref = img[0]
            imagem_bytes = doc.extract_image(xref)
            ext = imagem_bytes["ext"]
            conteudo = imagem_bytes["image"]
            
            caminho_img = os.path.join(pasta_temp, f"imagem_{img_index}.{ext}")
            with open(caminho_img, "wb") as img_file:
                img_file.write(conteudo)
                
            caminhos_gerados.append(caminho_img)
            img_index += 1
            
    doc.close()
    
    with zipfile.ZipFile(caminho_saida_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for caminho in caminhos_gerados:
            nome_arquivo = os.path.basename(caminho)
            zipf.write(caminho, arcname=nome_arquivo)
            
    for caminho in caminhos_gerados:
        try: os.remove(caminho)
        except: pass
    try: os.rmdir(pasta_temp)
    except: pass


def manipular_paginas_pdf(arquivo_entrada: str, caminho_saida: str, remover: str = "", rotacionar: str = ""):
    """
    Remove e/ou rotaciona páginas específicas.
    remover: ex. "1, 3-5"
    rotacionar: ex. "2:90, 4:180"
    """
    doc = fitz.open(arquivo_entrada)
    total_paginas = doc.page_count
    
    # 1. Parse rotacoes (formato: "pagina:graus, pagina:graus")
    rotacoes_dict = {}
    if rotacionar:
        partes = [p.strip() for p in rotacionar.split(",")]
        for parte in partes:
            if ":" in parte:
                try:
                    pg_str, grau_str = parte.split(":")
                    pg = int(pg_str) - 1
                    grau = int(grau_str)
                    grau = round(grau / 90.0) * 90 # Arredondar para múltiplo de 90
                    if 0 <= pg < total_paginas:
                        rotacoes_dict[pg] = grau
                except: pass
                
    # 2. Parse exclusões (formato: "1, 3-5")
    paginas_manter = []
    exclusoes = set()
    if remover:
        partes = [p.strip() for p in remover.split(",")]
        for parte in partes:
            if "-" in parte:
                try:
                    inicio, fim = parte.split("-")
                    inicio = max(0, int(inicio) - 1)
                    fim = min(total_paginas - 1, int(fim) - 1)
                    for i in range(inicio, fim + 1):
                        exclusoes.add(i)
                except: pass
            else:
                try:
                    pg = int(parte) - 1
                    if 0 <= pg < total_paginas:
                        exclusoes.add(pg)
                except: pass

    for i in range(total_paginas):
        if i not in exclusoes:
            paginas_manter.append(i)
            
    if not paginas_manter:
        doc.close()
        raise ValueError("Operação resultaria em um PDF sem páginas.")
        
    doc.select(paginas_manter)
    
    # 3. Aplicar rotacoes nas páginas que ficaram
    # A numeração mudou, precisamos achar o index novo.
    # Mas é mais fácil aplicar a rotação antes de deletar ou manter um mapeamento.
    # doc.select() já reorganizou as páginas em doc[i]. 
    # O paginas_manter[i] guarda o número original da página.
    for i, original_idx in enumerate(paginas_manter):
        if original_idx in rotacoes_dict:
            pagina = doc[i]
            nova_rotacao = (pagina.rotation + rotacoes_dict[original_idx]) % 360
            pagina.set_rotation(nova_rotacao)
            
    doc.save(caminho_saida)
    doc.close()
