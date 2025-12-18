/**
 * Inventory Intelligence - Dashboard Logic v5.6 (Final Fix - Missing Function Restored)
 */

const Dashboard = {
    config: {
        refreshInterval: 60000,
        endpoints: {
            metrics: '/metrics',
            todo: '/todo',
            suppress: (id) => `/alerts/${id}/suppress`,
            restore: (id) => `/alerts/${id}/suppress`, // DELETE method
            engineConfig: '/config/engine',
            engineProfile: '/config/engine/profile',
            stock: (id) => `/stock/${id}`
        }
    },

    state: {
        baseZero: false,
        includeSuppressed: false,
        isLoading: false,
        isSavingConfig: false,
        engineConfig: null,
        data: { purchasing: [], kitchen: [], management: [] },
        metrics: null,
        filters: { purchasingPriority: 'all', purchasingType: 'all' },
        activeMenuId: null
    },

    translations: {
        priority: { urgent: 'URGENTE', plan: 'PLANEJAR', info: 'INFO' }
    },

    icons: {
        kebab: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path></svg>',
        clock: '<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
        snooze: '<svg class="w-4 h-4 mr-2 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
        snooze_week: '<svg class="w-4 h-4 mr-2 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>',
        trash: '<svg class="w-4 h-4 mr-2 opacity-70 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>',
        restore: '<svg class="w-4 h-4 mr-2 opacity-70 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>',
        alert: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>',
        fire: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z"></path></svg>',
        chart: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>',
        ban: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path></svg>',
        empty: '<svg class="w-12 h-12 mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
        edit: '<svg class="w-4 h-4 mr-2 opacity-70 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>'
    },

    elements: {
        metricsBox: document.getElementById("metrics-container"),
        purchasingBox: document.getElementById("todo-purchasing"),
        kitchenBox: document.getElementById("todo-kitchen"),
        managementBox: document.getElementById("todo-management"),
        countPurchasing: document.getElementById("count-purchasing"),
        countKitchen: document.getElementById("count-kitchen"),
        countManagement: document.getElementById("count-management"),
        baseZeroToggle: document.getElementById("baseZeroToggle"),
        showIgnoredToggle: document.getElementById("showIgnoredToggle"),
        refreshBtn: document.getElementById("refresh-btn"),
        lastUpdatedLabel: document.getElementById("last-updated"),
        statusDot: document.getElementById("status-dot"),
        statusText: document.getElementById("status-text"),
        filterPrioBtns: document.querySelectorAll('.filter-btn-prio'),
        filterTypeSelect: document.getElementById('filter-type-select'),
        themeToggle: document.getElementById('theme-toggle'),
        themeIconLight: document.getElementById('theme-toggle-light-icon'),
        themeIconDark: document.getElementById('theme-toggle-dark-icon'),
        toastContainer: document.getElementById('toast-container'),

        // Engine Config Elements
        engineProfileSelect: document.getElementById('engine-profile-select'),
        btnOpenConfig: document.getElementById('btn-open-advanced-config'),
        btnCloseConfig: document.getElementById('btn-close-config'),
        btnCancelConfig: document.getElementById('btn-cancel-config'),
        configModal: document.getElementById('engine-config-modal'),
        configForm: document.getElementById('engine-config-form')
    },

    init() {
        this.bindEvents();
        this.initTheme();
        this.loadEngineConfig();
        this.loadAll(false);
        setInterval(() => this.loadAll(true), this.config.refreshInterval);
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.menu-container')) this.closeAllMenus();
        });
    },

    initTheme() {
        const setDark = (isDark) => {
            if (isDark) {
                document.documentElement.classList.add('dark');
                this.elements.themeIconDark.classList.add('hidden');
                this.elements.themeIconLight.classList.remove('hidden');
                localStorage.theme = 'dark';
            } else {
                document.documentElement.classList.remove('dark');
                this.elements.themeIconDark.classList.remove('hidden');
                this.elements.themeIconLight.classList.add('hidden');
                localStorage.theme = 'light';
            }
        };
        const isDark = localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches);
        setDark(isDark);
        this.elements.themeToggle.addEventListener('click', () => {
            setDark(!document.documentElement.classList.contains('dark'));
        });
    },

    bindEvents() {
        // Base Zero
        this.elements.baseZeroToggle.addEventListener("change", (e) => {
            this.state.baseZero = e.target.checked;
            this.loadAll(false);
        });

        // Show Ignored
        if (this.elements.showIgnoredToggle) {
            this.elements.showIgnoredToggle.addEventListener("change", (e) => {
                this.state.includeSuppressed = e.target.checked;
                if (this.state.includeSuppressed) document.body.classList.add('filtering-ignored');
                else document.body.classList.remove('filtering-ignored');
                this.loadAll(false);
            });
        }

        // Refresh
        this.elements.refreshBtn.addEventListener("click", () => {
            this.elements.refreshBtn.classList.add('animate-spin');
            setTimeout(() => this.elements.refreshBtn.classList.remove('animate-spin'), 1000);
            this.loadAll(true);
        });

        // Filtros
        this.elements.filterPrioBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.elements.filterPrioBtns.forEach(b => {
                    b.classList.remove('bg-blue-100', 'text-blue-700', 'ring-2', 'ring-blue-200', 'dark:bg-blue-900', 'dark:text-blue-300', 'dark:ring-blue-800');
                    b.classList.add('bg-slate-100', 'text-slate-600', 'dark:bg-slate-700', 'dark:text-slate-300');
                });
                e.target.classList.remove('bg-slate-100', 'text-slate-600', 'dark:bg-slate-700', 'dark:text-slate-300');
                e.target.classList.add('bg-blue-100', 'text-blue-700', 'ring-2', 'ring-blue-200', 'dark:bg-blue-900', 'dark:text-blue-300', 'dark:ring-blue-800');
                this.state.filters.purchasingPriority = e.target.dataset.filterPriority;
                this.renderTodos(true);
            });
        });

        this.elements.filterTypeSelect.addEventListener('change', (e) => {
            this.state.filters.purchasingType = e.target.value;
            this.renderTodos(true);
        });

        // Engine Config
        this.elements.engineProfileSelect.addEventListener('change', (e) => {
            this.setEngineProfile(e.target.value);
        });
        this.elements.btnOpenConfig.addEventListener('click', () => this.openConfigModal());
        this.elements.btnCloseConfig.addEventListener('click', () => this.closeConfigModal());
        this.elements.btnCancelConfig.addEventListener('click', () => this.closeConfigModal());
        this.elements.configModal.addEventListener('click', (e) => {
            if (e.target === this.elements.configModal) this.closeConfigModal();
        });
        this.elements.configForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveAdvancedConfig();
        });
        this.elements.configForm.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn-adjust');
            if (!btn) return;
            const targetName = btn.dataset.target;
            const step = parseFloat(btn.dataset.step);
            const input = this.elements.configForm.elements[targetName];
            if (input) {
                let val = parseFloat(input.value) || 0;
                val += step;
                if (Math.abs(step) < 1) val = Math.round(val * 10) / 10;
                if (val < 0) val = 0;
                input.value = val;
            }
        });

        // Event Delegation para Actions
        const handleContainerClick = async (e) => {
            // Menu
            const menuBtn = e.target.closest('.menu-trigger');
            if (menuBtn) {
                const menuId = menuBtn.dataset.target;
                const menuEl = document.getElementById(menuId);
                if (!menuEl.classList.contains('hidden')) {
                    menuEl.classList.add('hidden');
                    this.state.activeMenuId = null;
                } else {
                    this.closeAllMenus();
                    menuEl.classList.remove('hidden');
                    this.state.activeMenuId = menuId;
                }
                e.stopPropagation();
                return;
            }

            // Actions
            const actionBtn = e.target.closest('.menu-action-btn');
            if (actionBtn) {
                const alertId = actionBtn.dataset.id; // Pode ser item_id no caso do estoque
                const action = actionBtn.dataset.action;
                const card = actionBtn.closest('.alert-card');

                this.closeAllMenus();

                if (!alertId || !action) return;

                // --- FEATURE: AJUSTE DE ESTOQUE ---
                if (action === 'adjust_stock') {
                    const itemId = alertId;
                    const newQty = prompt("Digite a quantidade real em estoque agora:");
                    if (newQty !== null && !isNaN(parseFloat(newQty))) {
                        try {
                            await fetch(this.config.endpoints.stock(itemId), {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ quantity: parseFloat(newQty) })
                            });
                            this.showToast("Estoque atualizado.", null);
                            this.loadAll(true); // Reload para recalcular alertas
                        } catch (e) {
                            alert("Erro ao atualizar estoque.");
                        }
                    }
                    return; // Fim do fluxo para estoque
                }

                // --- FEATURE: SUPRESSÃO / SNOOZE ---
                // Feedback Visual
                if (card) {
                    if (action === 'restore') {
                        card.classList.remove('opacity-60', 'grayscale', 'hover:grayscale-0', 'hover:opacity-100', 'border-dashed', 'bg-slate-50', 'dark:bg-slate-800/50');
                        card.classList.add('bg-white', 'dark:bg-slate-800');
                    } else {
                        if (this.state.includeSuppressed) {
                            card.classList.add('opacity-60', 'grayscale', 'hover:grayscale-0', 'hover:opacity-100', 'border-dashed');
                            card.classList.remove('bg-white', 'dark:bg-slate-800');
                            card.classList.add('bg-slate-50', 'dark:bg-slate-800/50');
                        } else {
                            card.style.transition = 'all 0.3s ease';
                            card.style.opacity = '0';
                            card.style.transform = 'translateX(20px)';
                            card.style.pointerEvents = 'none';
                        }
                    }
                }

                try {
                    let url, method;
                    if (action === 'restore') {
                        url = this.config.endpoints.restore(alertId);
                        method = 'DELETE';
                    } else {
                        url = this.config.endpoints.suppress(alertId);
                        method = 'POST';
                    }

                    const res = await fetch(url, {
                        method: method,
                        headers: { 'Content-Type': 'application/json' },
                        body: action !== 'restore' ? JSON.stringify({ action: action }) : null
                    });

                    if (!res.ok) throw new Error('Falha na ação');

                    if (action !== 'restore' && !this.state.includeSuppressed && card) {
                        card.remove();
                    }

                    if (action !== 'restore') {
                        this.showToast("Alerta ocultado.", async () => {
                            await fetch(this.config.endpoints.restore(alertId), { method: 'DELETE' });
                            this.loadAll(true);
                        });
                    } else {
                        this.showToast("Alerta restaurado.", null);
                        setTimeout(() => this.loadAll(true), 500);
                    }

                } catch (err) {
                    console.error("Action error:", err);
                    if (card) {
                        card.style.opacity = '1';
                        card.style.transform = 'none';
                        card.style.pointerEvents = 'auto';
                        card.classList.remove('opacity-60', 'grayscale', 'border-dashed');
                    }
                    this.showToast("Erro ao executar ação.", null);
                }
            }
        };

        this.elements.purchasingBox.addEventListener('click', handleContainerClick);
        this.elements.kitchenBox.addEventListener('click', handleContainerClick);
        this.elements.managementBox.addEventListener('click', handleContainerClick);
    },

    closeAllMenus() {
        document.querySelectorAll('.menu-dropdown').forEach(el => el.classList.add('hidden'));
        this.state.activeMenuId = null;
    },

    updateStatus(isOnline, message = "") {
        const { statusDot, statusText } = this.elements;
        if (isOnline) {
            statusDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse";
            statusText.textContent = "Online";
            statusText.className = "text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wide";
        } else {
            statusDot.className = "w-2.5 h-2.5 rounded-full bg-red-500";
            statusText.textContent = message || "Offline";
            statusText.className = "text-xs font-bold text-red-600 dark:text-red-400 uppercase tracking-wide";
        }
    },

    getQuery() {
        const params = new URLSearchParams();
        if (this.state.baseZero) params.append('ignore_stock_balance', 'true');
        if (this.state.includeSuppressed) params.append('status', 'suppressed');
        const q = params.toString();
        return q ? `?${q}` : "";
    },

    async loadAll(isBackground = false) {
        if (!isBackground) this.state.isLoading = true;
        try {
            await Promise.all([this.loadMetrics(isBackground), this.loadTodos(isBackground)]);
            this.state.error = null;
            const now = new Date();
            this.elements.lastUpdatedLabel.textContent = now.toLocaleTimeString('pt-BR');
            this.updateStatus(true);
        } catch (err) {
            console.error(err);
            this.state.error = err;
            this.updateStatus(false, "Erro API");
        } finally {
            this.state.isLoading = false;
        }
    },

    async loadMetrics(isBackground) {
        const res = await fetch(`${this.config.endpoints.metrics}${this.getQuery()}`);
        if (!res.ok) throw new Error("Metrics error");
        const newData = await res.json();
        if (isBackground && JSON.stringify(newData) === JSON.stringify(this.state.metrics)) return;
        this.state.metrics = newData;
        this.renderMetrics(newData);
    },

    async loadTodos(isBackground) {
        const res = await fetch(`${this.config.endpoints.todo}${this.getQuery()}`);
        if (!res.ok) throw new Error("Todo error");
        const newData = await res.json();
        const prevData = { purchasing: this.state.data.purchasing, kitchen: this.state.data.kitchen, management: this.state.data.management };
        if (isBackground && JSON.stringify(newData) === JSON.stringify(prevData)) return;

        this.state.data.purchasing = newData.purchasing || [];
        this.state.data.kitchen = newData.kitchen || [];
        this.state.data.management = newData.management || [];
        this.renderTodos();
    },

    async loadEngineConfig() {
        try {
            const res = await fetch(this.config.endpoints.engineConfig);
            if (!res.ok) throw new Error("Falha config");
            const data = await res.json();
            this.state.engineConfig = data;
            if (this.elements.engineProfileSelect && data.profile) {
                this.elements.engineProfileSelect.value = data.profile;
            }
        } catch (err) {
            console.error("Erro config:", err);
        }
    },

    async setEngineProfile(profile) {
        if (this.state.isSavingConfig) return;
        this.state.isSavingConfig = true;
        this.elements.engineProfileSelect.disabled = true;
        this.elements.engineProfileSelect.classList.add('opacity-50');

        try {
            const res = await fetch(this.config.endpoints.engineProfile, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile })
            });
            if (!res.ok) throw new Error("Falha PUT profile");
            const newData = await res.json();
            this.state.engineConfig = newData;
            this.showToast(`Modo de operação atualizado.`, null);
            this.loadAll(false);
        } catch (err) {
            console.error(err);
            this.showToast("Não foi possível alterar o modo.", null);
            if(this.state.engineConfig) this.elements.engineProfileSelect.value = this.state.engineConfig.profile;
        } finally {
            this.state.isSavingConfig = false;
            this.elements.engineProfileSelect.disabled = false;
            this.elements.engineProfileSelect.classList.remove('opacity-50');
        }
    },

    openConfigModal() {
        if (!this.state.engineConfig) return;
        const cfg = this.state.engineConfig;
        const form = this.elements.configForm;
        form.elements['coverage_days_target_A'].value = cfg.coverage_days_target_A;
        form.elements['coverage_days_target_B'].value = cfg.coverage_days_target_B;
        form.elements['coverage_days_target_C'].value = cfg.coverage_days_target_C;
        form.elements['forecast_window_days'].value = cfg.forecast_window_days;
        form.elements['supplier_variability_finished'].value = cfg.supplier_variability_finished;
        form.elements['supplier_variability_ingredient'].value = cfg.supplier_variability_ingredient;
        form.elements['perishable_risk_threshold_days'].value = cfg.perishable_risk_threshold_days;
        this.elements.configModal.classList.remove('hidden');
    },

    closeConfigModal() {
        this.elements.configModal.classList.add('hidden');
    },

    async saveAdvancedConfig() {
        if (this.state.isSavingConfig) return;
        this.state.isSavingConfig = true;

        const form = this.elements.configForm;
        const payload = {
            coverage_days_target_A: parseFloat(form.elements['coverage_days_target_A'].value),
            coverage_days_target_B: parseFloat(form.elements['coverage_days_target_B'].value),
            coverage_days_target_C: parseFloat(form.elements['coverage_days_target_C'].value),
            forecast_window_days: parseInt(form.elements['forecast_window_days'].value),
            supplier_variability_finished: parseFloat(form.elements['supplier_variability_finished'].value),
            supplier_variability_ingredient: parseFloat(form.elements['supplier_variability_ingredient'].value),
            perishable_risk_threshold_days: parseFloat(form.elements['perishable_risk_threshold_days'].value)
        };

        try {
            const res = await fetch(this.config.endpoints.engineConfig, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error("Falha PATCH config");
            const newData = await res.json();
            this.state.engineConfig = newData;
            if (newData.profile) this.elements.engineProfileSelect.value = newData.profile;
            this.showToast("Configurações salvas com sucesso.", null);
            this.closeConfigModal();
            this.loadAll(false);
        } catch (err) {
            console.error(err);
            this.showToast("Erro ao salvar configurações.", null);
        } finally {
            this.state.isSavingConfig = false;
        }
    },

    renderMetrics(data) {
        const contextTitle = this.state.includeSuppressed ? "(COM OCULTOS)" : "";
        const cards = [
            { title: `TOTAL DE ALERTAS ${contextTitle}`, value: data.totals.alerts, icon: this.icons.alert, color: "text-blue-600 dark:text-blue-200", bg: "bg-blue-50 dark:bg-blue-900/50", gradient: "from-blue-50 to-white dark:from-slate-800 dark:to-slate-800" },
            { title: "PRIORIDADE URGENTE", value: data.by_priority.urgent || 0, icon: this.icons.fire, color: "text-red-600 dark:text-red-200", bg: "bg-red-50 dark:bg-red-900/50", gradient: "from-red-50 to-white dark:from-slate-800 dark:to-slate-800", isAlert: (data.by_priority.urgent > 0) },
            { title: "ESTOQUE NEGATIVO", value: data.data_quality.negative_stock, icon: this.icons.ban, color: "text-orange-600 dark:text-orange-200", bg: "bg-orange-50 dark:bg-orange-900/50", gradient: "from-orange-50 to-white dark:from-slate-800 dark:to-slate-800", isAlert: (data.data_quality.negative_stock > 0) },
            { title: "SEM HISTÓRICO", value: data.data_quality.no_demand_items, icon: this.icons.chart, color: "text-slate-500 dark:text-slate-300", bg: "bg-slate-100 dark:bg-slate-700", gradient: "from-slate-50 to-white dark:from-slate-800 dark:to-slate-800" }
        ];
        this.elements.metricsBox.innerHTML = cards.map(c => this.createMetricCard(c)).join("");
    },

    createMetricCard({ title, value, icon, color, bg, gradient, isAlert }) {
        const alertClass = isAlert ? "ring-2 ring-red-100 dark:ring-red-900 border-red-200 dark:border-red-900" : "border-slate-200 dark:border-slate-700";
        return `
            <div class="bg-gradient-to-br ${gradient} rounded-xl p-5 shadow-sm border ${alertClass} flex items-center justify-between transition hover:shadow-md fade-in">
                <div>
                    <p class="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">${title}</p>
                    <p class="text-3xl font-bold text-slate-800 dark:text-slate-100 tracking-tight">${value}</p>
                </div>
                <div class="w-10 h-10 rounded-full ${bg} ${color} flex items-center justify-center shadow-inner dark:shadow-none">${icon}</div>
            </div>`;
    },

    renderTodos() {
        const updateList = (container, html, countEl, count) => {
            const scrollTop = container.scrollTop;
            container.innerHTML = html;
            countEl.textContent = count;
            if (container.scrollHeight > container.clientHeight) {
                container.scrollTop = scrollTop;
            }
        };

        // Purchasing Logic
        let pList = this.state.data.purchasing;
        if (this.state.filters.purchasingPriority !== 'all') {
            pList = pList.filter(i => i.priority === this.state.filters.purchasingPriority);
        }
        if (this.state.filters.purchasingType !== 'all') {
            pList = pList.filter(i => {
                if (this.state.filters.purchasingType === 'product') return i.sphere === 'product';
                if (this.state.filters.purchasingType === 'ingredient') return i.sphere === 'ingredient';
                return true;
            });
        }
        updateList(this.elements.purchasingBox, this.createListHTML(pList, "purchasing"), this.elements.countPurchasing, pList.length);

        // Kitchen Logic
        updateList(this.elements.kitchenBox, this.createListHTML(this.state.data.kitchen, "kitchen"), this.elements.countKitchen, this.state.data.kitchen.length);

        // Management Logic
        updateList(this.elements.managementBox, this.createListHTML(this.state.data.management, "management"), this.elements.countManagement, this.state.data.management.length);
    },

    createListHTML(list, context) {
        if (!list || list.length === 0) {
            const msg = this.state.includeSuppressed ? "Lixeira vazia" : "Nenhum alerta pendente";
            return `<div class="flex flex-col items-center justify-center h-32 bg-slate-50/50 dark:bg-slate-800/50 rounded-lg border border-dashed border-slate-300 dark:border-slate-700 text-slate-400 dark:text-slate-500">
                    ${this.icons.empty}<span class="text-xs font-semibold">${msg}</span></div>`;
        }
        return list.map(item => this.createTaskCard(item, context)).join("");
    },

    createTaskCard(item, context) {
        const styles = {
            urgent: { border: 'border-l-red-500', badge: 'bg-red-50 text-red-700 border-red-100 dark:bg-red-900/30 dark:text-red-300 dark:border-red-900' },
            plan:   { border: 'border-l-amber-500', badge: 'bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-900' },
            info:   { border: 'border-l-blue-500', badge: 'bg-blue-50 text-blue-700 border-blue-100 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-900' }
        };
        const style = styles[item.priority] || styles.info;
        const meta = item.meta || {};
        const timeStr = new Date(item.created_at || Date.now()).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
        const priorityLabel = this.translations.priority[item.priority] || item.priority.toUpperCase();

        let reliabilityBadge = '';
        if (item.is_suppressed) {
            reliabilityBadge = `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border bg-slate-200 text-slate-500 border-slate-300 dark:bg-slate-700 dark:text-slate-400 dark:border-slate-600">OCULTO</span>`;
        } else if (item.reliability === 'low') {
            reliabilityBadge = `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-500 border border-gray-200 dark:bg-slate-700 dark:text-slate-400 dark:border-slate-600 uppercase tracking-wide">⚠️ Dados Antigos</span>`;
        }

        const opacityClass = item.is_suppressed ? "opacity-60 grayscale hover:grayscale-0 hover:opacity-100 border-dashed" : "";
        const bgClass = item.is_suppressed ? "bg-slate-50 dark:bg-slate-800/50" : "bg-white dark:bg-slate-800";

        const menuId = `menu-${item.alert_id}`;
        let menuItemsHTML = '';

        if (item.is_suppressed) {
            menuItemsHTML = `
                <li class="border-t border-slate-100 dark:border-slate-700">
                    <button class="menu-action-btn w-full text-left px-4 py-2 text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 flex items-center" data-id="${item.alert_id}" data-action="restore">
                        ${this.icons.restore} Restaurar Alerta
                    </button>
                </li>
            `;
        } else {
            // Feature: Ajuste de Estoque (se item_id presente)
            if (meta.item_id && (item.sphere === 'product' || item.sphere === 'ingredient')) {
                 menuItemsHTML += `
                    <li>
                        <button class="menu-action-btn w-full text-left px-4 py-2 text-xs font-medium text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20 flex items-center" data-id="${meta.item_id}" data-action="adjust_stock">
                            ${this.icons.edit} Ajustar Estoque
                        </button>
                    </li>
                    <hr class="border-slate-100 dark:border-slate-700 my-1">
                 `;
            }

            menuItemsHTML += `
                <li>
                    <button class="menu-action-btn w-full text-left px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 flex items-center" data-id="${item.alert_id}" data-action="tomorrow">
                        ${this.icons.snooze} Adiar Amanhã
                    </button>
                </li>
                <li>
                    <button class="menu-action-btn w-full text-left px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 flex items-center" data-id="${item.alert_id}" data-action="week">
                        ${this.icons.snooze_week} Adiar 7 Dias
                    </button>
                </li>
                <li class="border-t border-slate-100 dark:border-slate-700">
                    <button class="menu-action-btn w-full text-left px-4 py-2 text-xs font-bold text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center" data-id="${item.alert_id}" data-action="forever">
                        ${this.icons.trash} Ignorar Sempre
                    </button>
                </li>
            `;
        }

        const menuHTML = `
            <div class="relative menu-container">
                <button class="menu-trigger p-1 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors" data-target="${menuId}">
                    ${this.icons.kebab}
                </button>
                <div id="${menuId}" class="menu-dropdown hidden absolute right-0 top-8 w-40 bg-white dark:bg-slate-800 shadow-xl rounded-lg border border-slate-100 dark:border-slate-700 z-50 overflow-hidden fade-in">
                    <ul class="py-1">${menuItemsHTML}</ul>
                </div>
            </div>
        `;

        let detailsHTML = '';

        if (context === 'purchasing' && (item.sphere === 'product' || item.sphere === 'ingredient')) {
            const current = parseFloat(meta.current_stock || 0).toFixed(0);
            const rop = parseFloat(meta.reorder_point || 0).toFixed(0);
            const days = parseFloat(meta.days_of_cover || 0).toFixed(1);
            const toBuy = Math.max(0, (meta.target_stock || 0) - current);
            let buyHTML = toBuy > 0
                ? `<div class="mt-2 pt-2 border-t border-slate-100 dark:border-slate-700 flex items-center justify-start gap-2">
                     <span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase">Sugestão:</span>
                     <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 px-2 py-0.5 rounded-full border border-emerald-100 dark:border-emerald-900">+${toBuy.toFixed(0)} un</span>
                   </div>`
                : '';

            detailsHTML = `
                <div class="mt-3 grid grid-cols-3 gap-2 text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-700/30 p-2 rounded border border-slate-100 dark:border-slate-700/50">
                    <div class="flex flex-col">
                        <span class="uppercase text-slate-400 dark:text-slate-500 text-[10px] font-bold">Estoque</span>
                        <span class="font-mono font-semibold text-slate-700 dark:text-slate-200">${current}</span>
                    </div>
                    <div class="flex flex-col">
                        <span class="uppercase text-slate-400 dark:text-slate-500 text-[10px] font-bold">Mínimo</span>
                        <span class="font-mono font-semibold text-slate-700 dark:text-slate-200">${rop}</span>
                    </div>
                    <div class="flex flex-col">
                        <span class="uppercase text-slate-400 dark:text-slate-500 text-[10px] font-bold">Cobertura</span>
                        <span class="font-mono font-semibold text-slate-700 dark:text-slate-200">${days}d</span>
                    </div>
                </div>
                ${buyHTML}`;
        }

        if (context === 'kitchen' && item.sphere === 'production') {
            detailsHTML = `
                <div class="mt-3 grid grid-cols-3 gap-2 bg-orange-50 dark:bg-amber-900/20 p-2 rounded border border-orange-100 dark:border-amber-800/40">
                    <div class="flex flex-col items-center">
                        <span class="text-orange-400 dark:text-amber-500/80 font-bold uppercase text-[9px] mb-0.5">Necessário</span>
                        <span class="font-mono font-bold text-lg text-orange-800 dark:text-amber-400 leading-none">${parseFloat(meta.required||0).toFixed(2)}</span>
                    </div>
                    <div class="flex flex-col items-center border-l border-orange-200 dark:border-amber-800/50">
                        <span class="text-orange-400 dark:text-amber-500/80 font-bold uppercase text-[9px] mb-0.5">Atual</span>
                        <span class="font-mono font-bold text-lg text-orange-800 dark:text-amber-400 leading-none">${parseFloat(meta.current_stock||0).toFixed(2)}</span>
                    </div>
                    <div class="flex flex-col items-center border-l border-orange-200 dark:border-amber-800/50">
                        <span class="text-orange-400 dark:text-amber-500/80 font-bold uppercase text-[9px] mb-0.5">Produzir</span>
                        <span class="font-mono font-bold text-lg text-orange-800 dark:text-amber-400 leading-none">${parseFloat(meta.to_produce||0).toFixed(2)}</span>
                    </div>
                </div>`;
        }

        if (context === 'management' && item.data_error) {
             detailsHTML = `<div class="mt-2 pt-2 border-t border-slate-100 dark:border-slate-700"><span class="text-xs text-red-500 dark:text-red-400 font-bold flex items-center gap-1">${this.icons.ban} Estoque registrado: ${meta.current_stock}</span></div>`;
        }

        return `
            <div class="alert-card ${bgClass} ${opacityClass} border border-slate-200 dark:border-slate-700 border-l-4 ${style.border} rounded-lg shadow-sm p-3 transition-all hover:shadow-md fade-in relative group">
                <div class="flex justify-between items-start mb-2">
                    <div class="flex items-center gap-2">
                        <span class="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${style.badge}">${priorityLabel}</span>
                        ${reliabilityBadge}
                    </div>
                    <div class="flex items-center gap-2">
                        <div class="flex items-center text-slate-400 dark:text-slate-500 text-[10px] font-medium gap-1">
                            ${this.icons.clock}<span>${timeStr}</span>
                        </div>
                        ${menuHTML}
                    </div>
                </div>
                <h3 class="text-sm font-bold text-slate-800 dark:text-slate-100 leading-snug mb-1.5 pr-2">${item.title}</h3>
                <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-1">${item.description}</p>
                ${detailsHTML}
            </div>`;
    },

    showToast(message, undoCallback) {
        const container = this.elements.toastContainer;
        if (!container) return;
        const toast = document.createElement('div');
        toast.className = "flex items-center gap-3 bg-slate-900 dark:bg-slate-700 text-white px-4 py-3 rounded-lg shadow-xl text-sm font-medium transform translate-y-10 opacity-0 transition-all duration-300 pointer-events-auto border border-slate-700 dark:border-slate-600 z-[100]";
        let undoHTML = '';
        if (undoCallback) {
            undoHTML = `<button class="text-amber-400 hover:text-amber-300 font-bold uppercase text-xs tracking-wide ml-2 border-l border-slate-600 pl-3 underline decoration-amber-400/50 hover:decoration-amber-300 cursor-pointer pointer-events-auto" id="toast-undo">DESFAZER</button>`;
        }
        toast.innerHTML = `<span>${message}</span>${undoHTML}`;
        container.appendChild(toast);
        requestAnimationFrame(() => { toast.classList.remove('translate-y-10', 'opacity-0'); });

        if (undoCallback) {
            const undoBtn = toast.querySelector('#toast-undo');
            if(undoBtn) {
                undoBtn.onclick = (e) => { e.stopPropagation(); undoCallback(); removeToast(); };
            }
        }
        let timeout = setTimeout(removeToast, 5000);
        function removeToast() {
            clearTimeout(timeout);
            toast.classList.add('opacity-0', 'translate-y-2');
            setTimeout(() => toast.remove(), 300);
        }
    }
};

document.addEventListener("DOMContentLoaded", () => { Dashboard.init(); });