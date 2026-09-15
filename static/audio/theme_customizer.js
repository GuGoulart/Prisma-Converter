/**
 * theme_customizer.js — Gerenciador de Tema e Personalização de Cores de Destaque
 * Prisma Audio — Design Studio Geométrico & Quadrado
 */

(function () {
    const ACCENT_PRESETS = {
        dark: {
            red:     { key: "red",     namePt: "Vermelho Prisma",  nameEn: "Prisma Red",       nameEs: "Rojo Prisma",       color: "#ff3b3b", hover: "#ff5252", text: "#ffffff", glow: "rgba(255, 59, 59, 0.35)" },
            emerald: { key: "emerald", namePt: "Verde Prisma",     nameEn: "Prisma Green",     nameEs: "Verde Prisma",      color: "#c8ff00", hover: "#d4ff1a", text: "#0a0a0a", glow: "rgba(200, 255, 0, 0.35)" },
            cyan:    { key: "cyan",    namePt: "Ciano Elétrico",   nameEn: "Electric Cyan",    nameEs: "Cian Eléctrico",    color: "#00f0ff", hover: "#33f3ff", text: "#0a0a0a", glow: "rgba(0, 240, 255, 0.35)" },
            purple:  { key: "purple",  namePt: "Roxo Neon",        nameEn: "Neon Purple",      nameEs: "Púrpura Neón",      color: "#a855f7", hover: "#b666ff", text: "#ffffff", glow: "rgba(168, 85, 247, 0.35)" },
            orange:  { key: "orange",  namePt: "Laranja Vibrante", nameEn: "Vibrant Orange",   nameEs: "Naranja Vibrante",  color: "#ff7700", hover: "#ff8c26", text: "#ffffff", glow: "rgba(255, 119, 0, 0.35)" },
            pink:    { key: "pink",    namePt: "Rosa Magenta",     nameEn: "Magenta Pink",     nameEs: "Rosa Magenta",      color: "#ff007f", hover: "#ff3399", text: "#ffffff", glow: "rgba(255, 0, 127, 0.35)" },
            blue:    { key: "blue",    namePt: "Azul Elétrico",    nameEn: "Electric Blue",    nameEs: "Azul Eléctrico",    color: "#3b82f6", hover: "#60a5fa", text: "#ffffff", glow: "rgba(59, 130, 246, 0.35)" },
            indigo:  { key: "indigo",  namePt: "Índigo Neon",      nameEn: "Neon Indigo",      nameEs: "Índigo Neón",       color: "#6366f1", hover: "#818cf8", text: "#ffffff", glow: "rgba(99, 102, 241, 0.35)" },
            mint:    { key: "mint",    namePt: "Verde Menta",      nameEn: "Mint Green",       nameEs: "Verde Menta",       color: "#10b981", hover: "#34d399", text: "#0a0a0a", glow: "rgba(16, 185, 129, 0.35)" },
            amber:   { key: "amber",   namePt: "Âmbar Dourado",    nameEn: "Golden Amber",     nameEs: "Ámbar Dorado",      color: "#ffb703", hover: "#ffc333", text: "#0a0a0a", glow: "rgba(255, 183, 3, 0.35)" }
        },
        light: {
            red:     { key: "red",     namePt: "Vermelho Prisma",  nameEn: "Prisma Red",       nameEs: "Rojo Prisma",       color: "#dc2626", hover: "#b91c1c", text: "#ffffff", glow: "rgba(220, 38, 38, 0.35)" },
            emerald: { key: "emerald", namePt: "Verde Esmeralda",  nameEn: "Emerald Green",    nameEs: "Verde Esmeralda",   color: "#059669", hover: "#047857", text: "#ffffff", glow: "rgba(5, 150, 105, 0.35)" },
            cyan:    { key: "cyan",    namePt: "Ciano Profundo",   nameEn: "Deep Cyan",        nameEs: "Cian Profundo",     color: "#0891b2", hover: "#0e7490", text: "#ffffff", glow: "rgba(8, 145, 178, 0.35)" },
            purple:  { key: "purple",  namePt: "Violeta Imperial", nameEn: "Imperial Purple",  nameEs: "Violeta Imperial",  color: "#7c3aed", hover: "#6d28d9", text: "#ffffff", glow: "rgba(124, 58, 237, 0.35)" },
            orange:  { key: "orange",  namePt: "Laranja Âmbar",    nameEn: "Amber Orange",     nameEs: "Naranja Ámbar",     color: "#ea580c", hover: "#c2410c", text: "#ffffff", glow: "rgba(234, 88, 12, 0.35)" },
            pink:    { key: "pink",    namePt: "Rosa Carmim",      nameEn: "Carmine Rose",     nameEs: "Rosa Carmín",       color: "#db2777", hover: "#be185d", text: "#ffffff", glow: "rgba(219, 39, 119, 0.35)" },
            blue:    { key: "blue",    namePt: "Azul Real",        nameEn: "Royal Blue",       nameEs: "Azul Real",         color: "#2563eb", hover: "#1d4ed8", text: "#ffffff", glow: "rgba(37, 99, 235, 0.35)" },
            indigo:  { key: "indigo",  namePt: "Índigo Elegante",  nameEn: "Elegant Indigo",   nameEs: "Índigo Elegante",   color: "#4f46e5", hover: "#4338ca", text: "#ffffff", glow: "rgba(79, 70, 229, 0.35)" },
            mint:    { key: "mint",    namePt: "Verde Menta",      nameEn: "Mint Green",       nameEs: "Verde Menta",       color: "#0d9488", hover: "#0f766e", text: "#ffffff", glow: "rgba(13, 148, 136, 0.35)" },
            amber:   { key: "amber",   namePt: "Âmbar Dourado",    nameEn: "Golden Amber",     nameEs: "Ámbar Dorado",      color: "#d97706", hover: "#b45309", text: "#ffffff", glow: "rgba(217, 119, 6, 0.35)" }
        }
    };

    function getSavedTheme() {
        return localStorage.getItem("theme") === "light" ? "light" : "dark";
    }

    function getSavedAccent(mode) {
        let saved = localStorage.getItem(mode === "light" ? "theme_accent_light" : "theme_accent_dark");
        if (saved === "rose") saved = "pink";
        if (saved === "amber") saved = "orange";
        if (saved && ACCENT_PRESETS[mode][saved]) {
            return saved;
        }
        return mode === "light" ? "purple" : "red";
    }

    function applyThemeAndAccent(mode, accentKey) {
        const root = document.documentElement;
        if (mode === "light") {
            root.setAttribute("data-theme", "light");
        } else {
            root.removeAttribute("data-theme");
        }

        const preset = ACCENT_PRESETS[mode][accentKey] || ACCENT_PRESETS[mode]["red"];

        root.style.setProperty("--accent", preset.color);
        root.style.setProperty("--accent-hover", preset.hover);
        root.style.setProperty("--accent-text", preset.text);
        root.style.setProperty("--accent-glow", preset.glow);

        localStorage.setItem("theme", mode);
        localStorage.setItem(mode === "light" ? "theme_accent_light" : "theme_accent_dark", preset.key);

        updateModalUI(mode, preset.key);
    }

    // Execução imediata no carregamento
    const currentMode = getSavedTheme();
    const currentAccent = getSavedAccent(currentMode);
    applyThemeAndAccent(currentMode, currentAccent);

    function injectModal() {
        if (document.getElementById("themeCustomizerModal")) return;

        const modalHTML = `
        <div id="themeCustomizerModal" class="theme-modal-overlay" aria-hidden="true">
            <div class="theme-modal-card" role="dialog" aria-labelledby="themeModalTitle">
                <div class="theme-modal-top-accent"></div>

                <div class="theme-modal-header">
                    <div class="theme-modal-header-left">
                        <h3 id="themeModalTitle" class="theme-modal-title" data-i18n="customizer.title">Personalizar Aparência</h3>
                        <p class="theme-modal-subtitle" data-i18n="customizer.subtitle">Escolha o idioma, modo de exibição e cor de destaque do sistema</p>
                    </div>
                    <button type="button" class="theme-modal-close" id="closeCustomizerBtn" aria-label="Fechar">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>

                <div class="theme-modal-body">
                    <!-- Seção Idioma -->
                    <div class="theme-section">
                        <div class="theme-section-head-bar">
                            <label class="theme-section-label" data-i18n="customizer.lang.title">Idioma do Sistema</label>
                        </div>
                        <div class="theme-lang-grid">
                            <button type="button" class="btn-lang-opt theme-lang-btn" data-lang="pt">
                                <span class="lang-flag-symbol" aria-hidden="true">
                                    <svg width="22" height="15" viewBox="0 0 24 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                        <rect x="1" y="1" width="22" height="14" rx="1"/>
                                        <polygon points="12,3.5 20.5,8 12,12.5 3.5,8"/>
                                        <circle cx="12" cy="8" r="2.5"/>
                                    </svg>
                                </span>
                                <span data-i18n="customizer.lang.pt">Português (Brasil)</span>
                            </button>
                            <button type="button" class="btn-lang-opt theme-lang-btn" data-lang="en">
                                <span class="lang-flag-symbol" aria-hidden="true">
                                    <svg width="22" height="15" viewBox="0 0 24 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                        <rect x="1" y="1" width="22" height="14" rx="1"/>
                                        <rect x="1" y="1" width="9" height="7"/>
                                        <line x1="10" y1="3.8" x2="23" y2="3.8"/>
                                        <line x1="1" y1="11" x2="23" y2="11"/>
                                        <line x1="10" y1="7.4" x2="23" y2="7.4"/>
                                    </svg>
                                </span>
                                <span data-i18n="customizer.lang.en">English</span>
                            </button>
                            <button type="button" class="btn-lang-opt theme-lang-btn" data-lang="es">
                                <span class="lang-flag-symbol" aria-hidden="true">
                                    <svg width="22" height="15" viewBox="0 0 24 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                                        <rect x="1" y="1" width="22" height="14" rx="1"/>
                                        <line x1="1" y1="4.8" x2="23" y2="4.8"/>
                                        <line x1="1" y1="11.2" x2="23" y2="11.2"/>
                                        <rect x="5.5" y="6.5" width="2.5" height="3" rx="0.5"/>
                                    </svg>
                                </span>
                                <span data-i18n="customizer.lang.es">Español</span>
                            </button>
                        </div>
                    </div>

                    <!-- Seção Modo de Exibição -->
                    <div class="theme-section">
                        <div class="theme-section-head-bar">
                            <label class="theme-section-label" data-i18n="customizer.mode.title">Modo de Exibição</label>
                        </div>
                        <div class="theme-mode-grid-square">
                            <button type="button" class="theme-mode-square-btn" data-mode="dark">
                                <div class="mode-icon-wrap">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                                    </svg>
                                </div>
                                <span data-i18n="customizer.mode.dark">Escuro</span>
                            </button>
                            <button type="button" class="theme-mode-square-btn" data-mode="light">
                                <div class="mode-icon-wrap">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <circle cx="12" cy="12" r="5"></circle>
                                        <line x1="12" y1="1" x2="12" y2="3"></line>
                                        <line x1="12" y1="21" x2="12" y2="23"></line>
                                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                                        <line x1="1" y1="12" x2="3" y2="12"></line>
                                        <line x1="21" y1="12" x2="23" y2="12"></line>
                                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                                    </svg>
                                </div>
                                <span data-i18n="customizer.mode.light">Claro</span>
                            </button>
                        </div>
                    </div>

                    <!-- Seção Cor Principal de Destaque -->
                    <div class="theme-section">
                        <div class="theme-section-head-bar">
                            <label class="theme-section-label" data-i18n="customizer.accent.title">Cor Principal do Site</label>
                            <span id="themeAccentSub" class="theme-section-sub" data-i18n="customizer.accent.darkSub">Cores otimizadas para o modo escuro</span>
                        </div>
                        <div id="themeSwatchesContainer" class="theme-swatches-grid"></div>
                    </div>
                </div>

                <div class="theme-modal-footer">
                    <button type="button" class="btn-theme-modal-done" id="doneCustomizerBtn" data-i18n="customizer.done">Concluído</button>
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML("beforeend", modalHTML);
    }

    function renderSwatches(mode, activeAccentKey) {
        const container = document.getElementById("themeSwatchesContainer");
        if (!container) return;

        const presets = ACCENT_PRESETS[mode];
        const currentLang = (window.i18n && window.i18n.currentLang) || "pt";

        container.innerHTML = "";
        Object.keys(presets).forEach((key) => {
            const item = presets[key];
            const name = currentLang === "en" ? item.nameEn : (currentLang === "es" ? item.nameEs : item.namePt);
            const isSelected = key === activeAccentKey;

            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = `theme-swatch-btn ${isSelected ? "active" : ""}`;
            btn.setAttribute("data-accent-key", key);
            btn.setAttribute("title", name);
            btn.style.setProperty("--swatch-color", item.color);
            btn.style.setProperty("--swatch-glow", item.glow);

            btn.innerHTML = `
                <div class="swatch-box-wrap">
                    <span class="swatch-box" style="background-color: ${item.color};"></span>
                </div>
                <span class="swatch-name">${name}</span>
                <span class="swatch-check">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                </span>
            `;

            btn.addEventListener("click", () => {
                applyThemeAndAccent(mode, key);
            });

            container.appendChild(btn);
        });
    }

    function updateModalUI(mode, activeAccentKey) {
        document.querySelectorAll(".theme-mode-square-btn, .theme-mode-pill-btn, .theme-mode-card").forEach((card) => {
            const cardMode = card.getAttribute("data-mode");
            if (cardMode === mode) {
                card.classList.add("active");
            } else {
                card.classList.remove("active");
            }
        });

        const currentLang = (window.i18n && window.i18n.currentLang) || "pt";
        document.querySelectorAll("#themeCustomizerModal .btn-lang-opt").forEach((btn) => {
            if (btn.getAttribute("data-lang") === currentLang) {
                btn.classList.add("ativo");
            } else {
                btn.classList.remove("ativo");
            }
        });

        const sub = document.getElementById("themeAccentSub");
        if (sub) {
            const isLight = mode === "light";
            sub.setAttribute("data-i18n", isLight ? "customizer.accent.lightSub" : "customizer.accent.darkSub");
            if (window.i18n && window.i18n.aplicarTraducoes) {
                window.i18n.aplicarTraducoes();
            }
        }

        renderSwatches(mode, activeAccentKey);
    }

    function openModal() {
        injectModal();
        const modal = document.getElementById("themeCustomizerModal");
        if (!modal) return;

        const mode = getSavedTheme();
        const accent = getSavedAccent(mode);
        updateModalUI(mode, accent);

        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";

        if (window.i18n && window.i18n.aplicarTraducoes) {
            window.i18n.aplicarTraducoes();
        }
    }

    function closeModal() {
        const modal = document.getElementById("themeCustomizerModal");
        if (!modal) return;
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
    }

    document.addEventListener("DOMContentLoaded", () => {
        injectModal();

        const toggleBtns = document.querySelectorAll("#themeToggle, .btn-open-customizer");
        toggleBtns.forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                openModal();
            });
        });

        window.addEventListener("languageChanged", () => {
            const mode = getSavedTheme();
            const accent = getSavedAccent(mode);
            updateModalUI(mode, accent);
        });

        document.addEventListener("click", (e) => {
            if (e.target.closest("#closeCustomizerBtn") || e.target.closest("#doneCustomizerBtn")) {
                closeModal();
            } else if (e.target.classList && e.target.classList.contains("theme-modal-overlay")) {
                closeModal();
            }

            const modeBtn = e.target.closest(".theme-mode-square-btn, .theme-mode-pill-btn, .theme-mode-card");
            if (modeBtn) {
                const targetMode = modeBtn.getAttribute("data-mode");
                const currentAccent = getSavedAccent(targetMode);
                applyThemeAndAccent(targetMode, currentAccent);
            }
        });

        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                closeModal();
            }
        });
    });

    window.ThemeCustomizer = {
        open: openModal,
        close: closeModal,
        apply: applyThemeAndAccent,
        getSavedTheme,
        getSavedAccent
    };
})();
