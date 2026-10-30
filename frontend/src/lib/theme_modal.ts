export const MODAL_HTML = `
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
                    <div class="theme-section">
                        <div class="theme-section-head-bar">
                            <label class="theme-section-label" data-i18n="customizer.lang.title">Idioma do Sistema</label>
                        </div>
                        <div class="theme-lang-grid">
                            <button type="button" class="btn-lang-opt theme-lang-btn" data-lang="pt">
                                <span class="lang-flag-symbol" aria-hidden="true">
                                    <svg width="22" height="15" viewBox="0 0 24 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="flag-icon-svg">
                                        <rect x="1" y="1" width="22" height="14" rx="1"/>
                                        <polygon points="12,3.5 20.5,8 12,12.5 3.5,8"/>
                                        <circle cx="12" cy="8" r="2.5"/>
                                    </svg>
                                </span>
                                <span data-i18n="customizer.lang.pt">Português (Brasil)</span>
                            </button>
                            <button type="button" class="btn-lang-opt theme-lang-btn" data-lang="en">
                                <span class="lang-flag-symbol" aria-hidden="true">
                                    <svg width="22" height="15" viewBox="0 0 24 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="flag-icon-svg">
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
                                    <svg width="22" height="15" viewBox="0 0 24 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" class="flag-icon-svg">
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
                    <div class="theme-section">
                        <div class="theme-section-head-bar">
                            <label class="theme-section-label" data-i18n="customizer.accent.title">Cor Principal do Site</label>
                            <span id="themeAccentSub" class="theme-section-sub" data-i18n="customizer.accent.darkSub">Cores otimizadas para o modo escuro</span>
                        </div>
                        <div id="themeSwatchesContainer" class="theme-swatches-grid">
                        </div>
                    </div>
                </div>

                <div class="theme-modal-footer">
                    <button type="button" class="btn-theme-modal-done" id="doneCustomizerBtn" data-i18n="customizer.done">Concluído</button>
                </div>
            </div>
        </div>
`;
