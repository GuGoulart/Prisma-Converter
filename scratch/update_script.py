import sys

content = open('static/script.js', 'r', encoding='utf-8').read()

# Find boundaries using simple markers
form_start = content.rfind('\n\n\n', 0, content.find('converterForm'))
keyboard_idx = content.find('Atalhos', content.find('converterForm'))
section_end = content.rfind('\n\n', content.find('converterForm'), keyboard_idx)

new_section = r"""


    // -- Form de conversao -- Async API com progresso em tempo real -----------
    // Fluxo:
    //  1. Intercepta submit do #converterForm
    //  2. POST /api/converter/async -> recebe job_id
    //  3. Polling /api/converter/status/<job_id> a cada 800ms
    //  4. Quando concluido=true -> redirect para /api/converter/download/<job_id>
    // Fallback: se fetch falhar completamente, o submit normal e acionado.

    const converterForm = document.getElementById("converterForm");
    const btnConverter  = document.getElementById("btnConverter");
    const btnOutro      = document.getElementById("btnOutro");
    const progressWrap  = document.getElementById("progressWrap");
    const progressBar   = document.getElementById("progressBar");
    const progressLabel = document.getElementById("progressLabel");

    converterForm?.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!btnConverter || btnConverter.disabled) return;

        // Sincroniza orientacao do radio (se disponivel)
        const oriRadio = converterForm.querySelector("input[name='_ori']:checked");
        if (oriRadio) {
            const oriHidden = document.getElementById("orientacaoHidden");
            if (oriHidden) oriHidden.value = oriRadio.value;
        }

        // Mostrar estado de loading
        btnConverter.disabled = true;
        btnConverter.innerHTML = '<span>Processando...</span><div class="spinner"></div>';
        if (progressWrap)  progressWrap.classList.add("ativo");
        if (progressBar)   { progressBar.style.width = "5%"; progressBar.style.background = ""; }
        if (progressLabel) progressLabel.textContent = "Iniciando...";

        let pollInterval = null;

        function encerrarErro(msg) {
            clearInterval(pollInterval);
            if (progressBar)  { progressBar.style.width = "100%"; progressBar.style.background = "#f87171"; }
            if (progressLabel) progressLabel.textContent = msg || "Erro na conversao.";
            setTimeout(() => {
                btnConverter.disabled = false;
                btnConverter.innerHTML = '<span>Converter e baixar</span><span class="botao-arr">\u2193</span>';
                if (progressWrap) progressWrap.classList.remove("ativo");
                if (progressBar)  { progressBar.style.width = "0%"; progressBar.style.background = ""; }
            }, 3000);
        }

        function encerrarOk() {
            clearInterval(pollInterval);
            if (progressBar)   progressBar.style.width = "100%";
            if (progressLabel) progressLabel.textContent = "Concluido!";
            setTimeout(() => {
                btnConverter.disabled = false;
                btnConverter.innerHTML = '<span>Converter e baixar</span><span class="botao-arr">\u2193</span>';
                if (progressWrap) progressWrap.classList.remove("ativo");
                if (progressBar)  progressBar.style.width = "0%";
                if (btnOutro) btnOutro.style.display = "flex";
                mostrarToast("Download concluido!");
            }, 800);
        }

        try {
            // Etapa 1: Iniciar conversao assincrona
            const formData = new FormData(converterForm);
            const resp = await fetch("/api/converter/async", { method: "POST", body: formData });

            if (!resp.ok) {
                const errData = await resp.json().catch(() => ({}));
                encerrarErro(errData.erro || "Erro " + resp.status);
                return;
            }

            const data = await resp.json();
            if (data.erro || !data.job_id) {
                encerrarErro(data.erro || "Erro ao iniciar conversao.");
                return;
            }

            const jobId = data.job_id;
            if (progressLabel) progressLabel.textContent = "Aguardando processamento...";

            // Etapa 2: Polling do status
            let tentativas = 0;
            const MAX_TENTATIVAS = 180; // 180 x 800ms = 144s

            pollInterval = setInterval(async () => {
                tentativas++;
                if (tentativas > MAX_TENTATIVAS) {
                    encerrarErro("Tempo excedido. Tente com um arquivo menor.");
                    return;
                }

                try {
                    const sr = await fetch("/api/converter/status/" + jobId);
                    if (!sr.ok) return; // Ignora falhas transitorias

                    const status = await sr.json();
                    if (status.erro) { encerrarErro(status.erro); return; }

                    // Atualizar barra de progresso
                    const pct = Math.max(5, Math.min(99, status.percent || 5));
                    if (progressBar)   progressBar.style.width = pct + "%";
                    if (progressLabel) progressLabel.textContent = status.status || "Convertendo...";

                    // Conversao concluida!
                    if (status.concluido && status.download_url) {
                        encerrarOk();
                        window.location.href = status.download_url; // auto-download
                    }
                } catch (netErr) {
                    console.warn("[converter] Erro no poll de status:", netErr);
                }
            }, 800);

        } catch (fetchErr) {
            // Fallback sincrono caso o fetch falhe completamente
            console.warn("[converter] fetch falhou, usando submit sincrono:", fetchErr);
            clearInterval(pollInterval);
            btnConverter.disabled = false;
            btnConverter.innerHTML = '<span>Converter e baixar</span><span class="botao-arr">\u2193</span>';
            if (progressWrap) progressWrap.classList.remove("ativo");
            converterForm.submit();
        }
    });

"""

new_content = content[:form_start] + new_section + content[section_end:]
open('static/script.js', 'w', encoding='utf-8').write(new_content)
sys.stdout.buffer.write(b'OK: script.js updated with async polling\n')
sys.stdout.buffer.write(f'Total length: {len(new_content)}\n'.encode())
