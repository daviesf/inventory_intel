/**
 * Inventory Intelligence - SPA Logic
 */

const { createApp, ref, reactive, computed, onMounted, onUnmounted, onActivated, watch, nextTick } = Vue;
const { createRouter, createWebHistory } = VueRouter;

// Icons
const IconDashboard = { template: `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"></path></svg>` };
const IconStock = { template: `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>` };

// ========== ANALYSIS MODAL COMPONENT ==========
const AnalysisModal = {
    props: ['item', 'dayContext', 'isOpen'],
    emits: ['close'],
    setup(props) {
        const factorLabels = {
            'DOW': 'Dia da Semana',
            'Month': 'Sazonalidade Mensal',
            'Event': 'Evento no Calendário',
            'Bridge': 'Emenda de Feriado',
            'Payday': 'Dia de Pagamento'
        };
        const translateFactor = (label) => factorLabels[label] || label;

        const reliabilityLabel = computed(() => {
            const r = props.item?.meta?.temporal_confidence || 'MEDIUM';
            return r === 'HIGH' ? 'Alta' : r === 'LOW' ? 'Baixa' : 'Média';
        });

        return { translateFactor, reliabilityLabel };
    },
    template: `
        <teleport to="body">
            <div v-if="isOpen" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
                <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" @click="$emit('close')"></div>
                <div class="relative w-full max-w-lg bg-white dark:bg-slate-800 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden border border-slate-200 dark:border-slate-700 animate-in fade-in zoom-in-95 duration-200">
                    
                    <!-- Header -->
                    <div class="p-5 border-b border-slate-100 dark:border-slate-700/50 flex justify-between items-start bg-slate-50/50 dark:bg-slate-900/20">
                        <div>
                            <h3 class="text-lg font-bold text-slate-900 dark:text-white leading-tight mb-1">{{ item.title_business || item.title }}</h3>
                            <p class="text-xs font-mono text-slate-400 dark:text-slate-500">{{ item.title_technical || item.title }}</p>
                        </div>
                        <button @click="$emit('close')" class="p-1 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-400 transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                        </button>
                    </div>

                    <!-- Content -->
                    <div class="p-6 overflow-y-auto space-y-6">
                        
                        <!-- 1. Resumo da Decisão -->
                        <div>
                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2 flex items-center gap-2">
                                <span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span>Resumo da Decisão
                            </h4>
                            <div class="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border border-blue-100 dark:border-blue-800/30">
                                <p class="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{{ item.description }}</p>
                            </div>
                        </div>

                        <!-- ESTIMATED FINANCIAL IMPACT -->
                <div v-if="item.financial_impact" class="bg-slate-50 dark:bg-slate-700/30 border border-slate-200 dark:border-slate-700/50 rounded-lg p-4">
                     <!-- Case 1: Missing Data (Neutral Message) -->
                    <div v-if="item.financial_impact.type === 'missing_data'" class="flex items-start gap-3">
                         <div class="p-2 bg-slate-100 dark:bg-slate-600 rounded-lg">
                            <svg class="text-slate-400 dark:text-slate-300 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        </div>
                        <div>
                            <h4 class="text-sm font-medium text-slate-700 dark:text-slate-200">Impacto financeiro não exibido</h4>
                            <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
                                Preço ou custo não cadastrado para este item.
                            </p>
                        </div>
                    </div>

                    <!-- Case 2: Valid Impact (Show Value) -->
                    <div v-else class="flex items-start gap-3">
                        <div class="p-2 bg-slate-100 dark:bg-slate-600 rounded-lg">
                            <svg class="text-slate-600 dark:text-slate-300 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                        </div>
                        <div>
                            <h4 class="text-sm font-medium text-slate-900 dark:text-white">Impacto Financeiro Estimado</h4>
                            <div class="mt-1 flex items-baseline gap-2">
                                <span class="text-2xl font-bold text-slate-900 dark:text-white">
                                    {{ item.financial_impact.amount.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) }}
                                </span>
                            </div>
                            <p class="text-sm text-slate-600 dark:text-slate-300 mt-2">
                                {{ item.financial_impact.description }}
                            </p>
                            <p class="text-xs text-slate-400 dark:text-slate-500 mt-2 border-t border-slate-200 dark:border-slate-700 pt-2 italic">
                                Estimativa baseada em dados históricos e preços cadastrados.
                            </p>
                        </div>
                    </div>
                </div>
                        <!-- 2. Contexto do Dia -->
                        <div v-if="dayContext">
                            <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2 flex items-center gap-2">
                                 <span class="w-1.5 h-1.5 rounded-full bg-purple-500"></span>Contexto do Dia
                            </h4>
                            <div class="flex flex-wrap gap-2">
                                <span class="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-lg text-xs font-bold shadow-sm">
                                    📅 {{ dayContext.summary }}
                                </span>
                            </div>
                        </div>

                        <!-- 3. Fatores de Ajuste -->
                        <div v-if="item.meta && item.meta.temporal_breakdown">
                             <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2 flex items-center gap-2">
                                 <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>Fatores de Ajuste
                             </h4>
                             <div class="space-y-2">
                                 <div v-for="comp in item.meta.temporal_breakdown" :key="comp.label" 
                                      class="flex justify-between items-center p-2.5 bg-slate-50 dark:bg-slate-700/30 rounded-lg border border-slate-100 dark:border-slate-700/50">
                                     <span class="text-sm font-medium text-slate-700 dark:text-slate-300">{{ translateFactor(comp.label) }}</span>
                                     <div class="flex items-center gap-3">
                                         <div class="h-1.5 w-16 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden">
                                             <div class="h-full bg-slate-400" :style="{ width: (comp.factor * 50) + '%' }"></div>
                                         </div>
                                         <span class="font-mono text-sm font-bold w-12 text-right" 
                                            :class="comp.factor > 1.05 ? 'text-emerald-600' : comp.factor < 0.95 ? 'text-red-500' : 'text-slate-600'">
                                            {{ comp.factor }}x
                                         </span>
                                     </div>
                                 </div>
                             </div>
                             <p class="mt-2 text-xs text-slate-400 dark:text-slate-500 italic">"{{ item.meta.temporal_explanation }}"</p>
                        </div>

                        <!-- 4. Confiabilidade -->
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                 <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2">Confiabilidade</h4>
                                 <div class="p-3 bg-slate-50 dark:bg-slate-700/30 rounded-lg border border-slate-100 dark:border-slate-700/50">
                                     <div class="flex items-center gap-2 mb-1">
                                         <span class="w-2 h-2 rounded-full" :class="item.meta?.temporal_confidence === 'HIGH' ? 'bg-emerald-500' : 'bg-amber-500'"></span>
                                         <span class="text-sm font-bold text-slate-700 dark:text-slate-200">{{ reliabilityLabel }}</span>
                                     </div>
                                     <p class="text-[10px] text-slate-500 leading-tight">Baseado na estabilidade histórica do item.</p>
                                 </div>
                            </div>
                            
                            <!-- 5. Perecibilidade (se aplicável) -->
                            <div v-if="item.sphere === 'PERISHABLE'">
                                 <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-2">Perecibilidade</h4>
                                 <div class="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-100 dark:border-red-800/30">
                                     <p class="text-xs font-bold text-red-700 dark:text-red-300">Risco Iminente</p>
                                     <p class="text-[10px] text-red-600/80 mt-1">Lotes vencendo em breve.</p>
                                 </div>
                            </div>
                        </div>
                    </div>

                    <!-- Footer -->
                    <div class="p-4 bg-slate-50 dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700 text-center">
                        <button @click="$emit('close')" class="w-full px-4 py-2 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 shadow-sm rounded-lg text-sm font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-600 transition-colors">
                            Fechar Análise
                        </button>
                    </div>
                </div>
            </div>
        </teleport>
    `
};

// ========== STOCK ADJUSTMENT MODAL ==========
const StockAdjustmentModal = {
    props: ['item', 'isOpen'],
    emits: ['close', 'submit'],
    template: `
        <teleport to="body">
            <div v-if="isOpen" class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
                <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" @click="$emit('close')"></div>
                <div class="relative w-full max-w-md bg-white dark:bg-slate-800 rounded-2xl shadow-2xl p-6 border border-slate-200 dark:border-slate-700 animate-in fade-in zoom-in-95 duration-200">
                    
                    <h3 class="text-lg font-bold text-slate-900 dark:text-white mb-4">Ajustar Estoque <br><span class="text-sm font-normal text-slate-500">{{ item.title }}</span></h3>
                    
                    <!-- Mode Switch -->
                    <div class="flex p-1 bg-slate-100 dark:bg-slate-700/50 rounded-lg mb-4">
                        <button @click="mode = 'add'" :class="mode === 'add' ? 'bg-white dark:bg-slate-600 shadow text-blue-600 dark:text-blue-300' : 'text-slate-500'"
                                class="flex-1 py-1.5 text-sm font-bold rounded-md transition-all">Lote / Seguro</button>
                        <button @click="mode = 'set'" :class="mode === 'set' ? 'bg-white dark:bg-slate-600 shadow text-red-600 dark:text-red-300' : 'text-slate-500'"
                                class="flex-1 py-1.5 text-sm font-bold rounded-md transition-all">Contagem Total</button>
                    </div>

                    <div class="space-y-4">
                        <!-- Qty -->
                        <div>
                            <label class="block text-xs font-bold uppercase text-slate-500 mb-1">Quantidade</label>
                            <input v-model.number="quantity" type="number" step="0.01" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg p-2.5 text-slate-900 dark:text-white font-mono focus:ring-2 focus:ring-blue-500 outline-none">
                        </div>

                        <!-- Lot Details (Only for Add) -->
                        <div v-if="mode === 'add'" class="grid grid-cols-2 gap-3 animate-in fade-in slide-in-from-top-2">
                             <div>
                                <label class="block text-xs font-bold uppercase text-slate-500 mb-1">Lote (Opcional)</label>
                                <input v-model="lotId" type="text" placeholder="Ex: Lote_A" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg p-2.5 text-slate-900 dark:text-white text-sm outline-none">
                             </div>
                             <div>
                                <label class="block text-xs font-bold uppercase text-slate-500 mb-1">Validade</label>
                                <input v-model="expiresAt" type="date" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg p-2.5 text-slate-900 dark:text-white text-sm outline-none">
                             </div>
                        </div>

                        <!-- Warning for Set -->
                        <div v-else class="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-100 dark:border-red-800/30">
                            <p class="text-xs text-red-600 dark:text-red-300 font-bold flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                                Atenção: Reset de Dados
                            </p>
                            <p class="text-[10px] text-red-600/80 mt-1">Apaga histórico de lotes. Use para correção de contagem cega.</p>
                        </div>
                    </div>

                    <div class="mt-6 flex gap-3">
                         <button @click="$emit('close')" class="flex-1 px-4 py-2 border border-slate-200 dark:border-slate-600 rounded-lg text-slate-600 dark:text-slate-300 font-bold hover:bg-slate-50">Cancelar</button>
                         <button @click="confirm" class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-bold shadow-lg shadow-blue-500/30 hover:bg-blue-700 transition-colors">
                            {{ mode === 'set' ? 'Confirmar Reset' : 'Salvar Estoque' }}
                         </button>
                    </div>
                </div>
            </div>
        </teleport>
    `,
    setup(props, { emit }) {
        const mode = ref('add');
        const quantity = ref(0);
        const lotId = ref('');
        const expiresAt = ref('');
        function confirm() {
            emit('submit', {
                quantity: quantity.value,
                mode: mode.value,
                lot_id: lotId.value || null,
                expires_at: expiresAt.value || null
            });
        }
        return { mode, quantity, lotId, expiresAt, confirm };
    }
};

// ========== TASK CARD COMPONENT ==========
const TaskCard = {
    props: ['item', 'context'],
    emits: ['action'],
    template: `
        <div @click="$emit('action', { action: 'analyze', item: item })" 
             class="relative bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-700/50 p-4 hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-lg dark:hover:shadow-none transition-all cursor-pointer group border-l-4 shadow-sm"
             :class="[borderColor, item.is_suppressed ? 'opacity-60 grayscale' : '']">
            
            <!-- 1. Topo: Badges e Botão Ações -->
            <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-2">
                    <span v-if="item.priority === 'urgent'" class="px-2 py-0.5 rounded bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-400 text-[10px] font-bold uppercase tracking-wide">Urgente</span>
                    <span v-if="item.reliability === 'low'" class="px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 text-[10px] font-bold uppercase">Dados Antigos</span>
                </div>
                <button @click.stop="menuOpen = !menuOpen" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded transition-colors -mt-1 -mr-1">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path></svg>
                </button>
            </div>

            <!-- 2. Corpo: Título e Descrição -->
            <div class="mb-4">
                 <h3 class="font-bold text-base text-slate-900 dark:text-white leading-tight mb-1">
                     {{ item.title_business || item.title }}
                 </h3>
                 <p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-1 leading-snug">{{ item.description }}</p>
            </div>

            <!-- 3. Métricas Principais -->
            <div v-if="item.meta && (context === 'purchasing' || context === 'kitchen')" class="flex items-center gap-4 text-xs text-slate-600 dark:text-slate-400 mb-4 bg-slate-50 dark:bg-slate-700/20 p-2 rounded-lg border border-slate-100 dark:border-slate-700/30">
                 <div class="text-center">
                     <span class="block text-[10px] uppercase font-bold text-slate-400">Estoque</span>
                     <span class="font-mono font-bold text-sm text-slate-700 dark:text-slate-200">{{ formatNum(item.meta.current_stock) }}</span>
                 </div>
                 <div class="w-px h-6 bg-slate-200 dark:bg-slate-700"></div>
                 <div class="text-center">
                     <span class="block text-[10px] uppercase font-bold text-slate-400">Mínimo</span>
                     <span class="font-mono font-bold text-sm text-slate-700 dark:text-slate-200">{{ formatNum(item.meta.reorder_point || item.meta.required) }}</span>
                 </div>
                 <!-- Sugestão (Botão Principal) -->
                 <div class="ml-auto">
                     <div v-if="toBuy > 0" class="flex items-center gap-2 bg-emerald-100 dark:bg-emerald-900/30 px-3 py-1.5 rounded-full border border-emerald-200 dark:border-emerald-800/50">
                        <span class="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 uppercase">Sugestão</span>
                        <span class="font-bold text-sm text-emerald-700 dark:text-emerald-400">{{ toBuy }} un</span>
                     </div>
                 </div>
            </div>

            <!-- Actions Menu (Absolute) -->
            <div v-show="menuOpen" @click.stop class="absolute right-2 top-10 w-48 bg-white dark:bg-slate-800 shadow-xl rounded-lg border border-slate-200 dark:border-slate-700 z-50 overflow-hidden py-1">
                 <a href="#" @click.prevent.stop="doAction('adjust_stock')" class="block px-4 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700">Ajustar Estoque</a>
                 <a href="#" @click.prevent.stop="doAction('tomorrow')" class="block px-4 py-2 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700">Adiar 24h</a>
                 <div class="border-t border-slate-100 dark:border-slate-700 my-1"></div>
                 <a href="#" @click.prevent.stop="doAction('forever')" class="block px-4 py-2 text-xs font-bold text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20">Ignorar Sempre</a>
            </div>
        </div>
    `,
    data() {
        return { menuOpen: false };
    },
    computed: {
        borderColor() {
            const p = this.item.priority;
            if (p === 'urgent') return 'border-l-red-500';
            if (p === 'plan') return 'border-l-amber-500';
            return 'border-l-blue-500';
        },
        timeStr() {
            return new Date(this.item.created_at || Date.now()).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        },
        toBuy() {
            if (!this.item.meta) return 0;
            return Math.max(0, Math.round((this.item.meta.target_stock || 0) - (this.item.meta.current_stock || 0)));
        }
    },
    methods: {
        formatNum(v) { return parseFloat(v || 0).toFixed(0); },
        doAction(action) {
            this.menuOpen = false;
            this.$emit('action', {
                action,
                alertId: this.item.alert_id,
                itemId: this.item.meta?.item_id,
                itemTitle: this.item.title_business || this.item.title,
                context: this.context
            });
        }
    },
    mounted() { document.addEventListener('click', () => { this.menuOpen = false; }); }
};

// ========== DASHBOARD VIEW ==========
const DashboardView = {
    props: ['baseZero', 'showIgnored', 'isLoading'],
    emits: ['refresh', 'toast'],
    template: `
        <div class="space-y-6 relative">
            
            <!-- Analysis Modal -->
            <analysis-modal 
                v-if="selectedItem" 
                :isOpen="!!selectedItem" 
                :item="selectedItem" 
                :dayContext="dayContext"
                @close="selectedItem = null" 
            />

            <!-- Stock Adjustment Modal -->
            <stock-adjustment-modal
                v-if="adjustItem"
                :isOpen="!!adjustItem"
                :item="adjustItem"
                @close="adjustItem = null"
                @submit="handleStockSubmit"
            />
            
            <!-- Day Context Banner -->
            <transition name="fade">
                <div v-if="dayContext" class="bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 dark:from-indigo-500/20 dark:via-purple-500/20 dark:to-pink-500/20 rounded-xl p-3 border border-indigo-200/50 dark:border-indigo-700/30 flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                        <svg class="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    </div>
                    <div class="flex-1">
                        <p class="text-xs font-bold text-indigo-700 dark:text-indigo-300 uppercase tracking-wide">Contexto do Dia</p>
                        <p class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ dayContext.summary }}</p>
                    </div>
                    <div class="flex flex-wrap gap-1">
                        <span v-for="flag in visibleFlags" :key="flag" class="px-2 py-0.5 text-[10px] font-bold uppercase rounded-full bg-indigo-500/20 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30">
                            {{ formatFlag(flag) }}
                        </span>
                    </div>
                </div>
            </transition>

            <!-- Planning Preview Section (NEW) -->
            <transition name="fade">
                <div v-if="planningData && planningData.events.length > 0" class="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700/50">
                    <h3 class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
                        Planejamento Próximo ({{ planningData.window_days }} dias)
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        <div v-for="event in planningData.events" :key="event.date + event.label" 
                             class="bg-white dark:bg-slate-900/50 p-3 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-700 transition-colors group">
                             
                             <div class="flex items-start gap-3">
                                 <div class="p-2 rounded-lg shrink-0 transition-colors" :class="getEventIconClass(event.type)">
                                    <span v-html="getEventIcon(event.type)"></span>
                                 </div>
                                 <div class="flex-1 min-w-0">
                                    <div class="flex items-center justify-between">
                                        <p class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">{{ formatDate(event.date) }} <span class="ml-1 font-normal opacity-75">({{ event.days_away === 0 ? 'Hoje' : event.days_away + 'd' }})</span></p>
                                    </div>
                                    <p class="text-sm font-bold text-slate-800 dark:text-slate-200 leading-tight mt-0.5 truncate">{{ event.label }}</p>
                                    <p class="text-xs font-medium text-slate-600 dark:text-slate-400 mt-1.5 leading-snug">{{ event.impact_summary }}</p>
                                    
                                    <button v-if="event.impacted_items && event.impacted_items.length > 0" 
                                            @click="toggleEvent(event.date + event.label)"
                                            class="mt-2 text-[10px] font-bold uppercase tracking-wide text-blue-600 dark:text-blue-400 hover:underline focus:outline-none flex items-center gap-1">
                                        {{ isExpanded(event) ? 'Ocultar Detalhes' : 'Ver Impacto nos Itens' }}
                                        <svg class="w-3 h-3 transition-transform duration-200" :class="isExpanded(event) ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                                    </button>
                                 </div>
                             </div>

                             <!-- Details Expansion -->
                             <div v-if="isExpanded(event)" class="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/50 space-y-2">
                                <div v-for="imp in event.impacted_items" :key="imp.item_name" class="text-xs flex flex-col gap-0.5">
                                    <div class="flex items-center justify-between">
                                        <span class="font-semibold text-slate-700 dark:text-slate-300">{{ imp.item_name }}</span>
                                        <span class="font-bold whitespace-nowrap" :class="imp.delta_direction === 'increase' ? 'text-emerald-600 dark:text-emerald-400' : 'text-orange-500 dark:text-orange-400'">
                                            {{ imp.delta_direction === 'increase' ? '+' : '' }}{{ imp.delta_quantity }} un
                                        </span>
                                    </div>
                                    <p class="text-[10px] text-slate-500 dark:text-slate-400 leading-tight">{{ imp.message }}</p>
                                </div>
                             </div>
                        </div>
                    </div>
                </div>
            </transition>

            <!-- Metrics -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div v-for="m in metrics" :key="m.label" class="bg-white dark:bg-slate-800/50 rounded-2xl p-5 border border-slate-200/80 dark:border-slate-700/50 shadow-sm dark:shadow-none" :class="m.alert ? 'ring-2 ring-red-500/40' : ''">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">{{ m.label }}</p>
                            <p class="text-4xl font-bold mt-2 tracking-tight" :class="m.color">{{ m.value }}</p>
                        </div>
                        <div class="w-10 h-10 rounded-lg flex items-center justify-center opacity-60" :class="m.bgColor" v-html="m.icon"></div>
                    </div>
                </div>
            </div>

            <!-- TODO Columns -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Compras -->
                <div class="flex flex-col gap-4">
                    <div class="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-700/50">
                        <h2 class="text-sm font-bold text-slate-700 dark:text-slate-200 uppercase flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-blue-500"></span>Compras & Reposição
                        </h2>
                        <span class="bg-blue-500/20 text-blue-600 dark:text-blue-400 text-xs font-bold px-2 py-0.5 rounded-full">{{ purchasingList.length }}</span>
                    </div>
                    <div class="bg-slate-50 dark:bg-slate-800/30 rounded-lg p-2 space-y-2 border border-slate-100 dark:border-transparent">
                        <div class="flex gap-1">
                            <button v-for="f in ['all', 'urgent', 'plan']" :key="f" @click="filterPriority = f"
                                class="flex-1 text-[10px] font-bold uppercase py-1.5 rounded transition-all"
                                :class="filterPriority === f ? 'bg-blue-600 text-white' : 'text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'">
                                {{ f === 'all' ? 'Todos' : f === 'urgent' ? 'Urgente' : 'Planejar' }}
                            </button>
                        </div>
                        <select v-model="filterType" class="w-full text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded py-1.5 px-2 text-slate-700 dark:text-slate-300 outline-none">
                            <option value="all">Todos os tipos</option>
                            <option value="product">Produtos</option>
                            <option value="ingredient">Ingredientes</option>
                        </select>
                    </div>
                    <div class="space-y-4 max-h-[600px] overflow-y-auto pr-1">
                        <div v-if="loading" class="space-y-3"><div class="h-24 skeleton rounded-lg"></div><div class="h-24 skeleton rounded-lg"></div></div>
                        <div v-else-if="purchasingList.length === 0" class="text-center py-8 text-slate-400 dark:text-slate-500"><p class="text-sm">Nenhum item pendente</p></div>
                        <task-card v-else v-for="item in purchasingList" :key="item.alert_id" :item="item" context="purchasing" @action="handleAction" />
                    </div>
                </div>

                <!-- Cozinha -->
                <div class="flex flex-col gap-4">
                    <div class="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-700/50">
                        <h2 class="text-sm font-bold text-slate-700 dark:text-slate-200 uppercase flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-orange-500"></span>Cozinha & Produção
                        </h2>
                        <span class="bg-orange-500/20 text-orange-600 dark:text-orange-400 text-xs font-bold px-2 py-0.5 rounded-full">{{ kitchenList.length }}</span>
                    </div>
                    <div class="space-y-4 max-h-[600px] overflow-y-auto pr-1">
                        <div v-if="loading" class="h-24 skeleton rounded-lg"></div>
                        <div v-else-if="kitchenList.length === 0" class="text-center py-8 text-slate-400 dark:text-slate-500"><p class="text-sm">Nenhum item pendente</p></div>
                        <task-card v-else v-for="item in kitchenList" :key="item.alert_id" :item="item" context="kitchen" @action="handleAction" />
                    </div>
                </div>

                <!-- Gestão -->
                <div class="flex flex-col gap-4">
                    <div class="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-700/50">
                        <h2 class="text-sm font-bold text-slate-700 dark:text-slate-200 uppercase flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-purple-500"></span>Gestão & Qualidade
                        </h2>
                        <span class="bg-purple-500/20 text-purple-600 dark:text-purple-400 text-xs font-bold px-2 py-0.5 rounded-full">{{ managementList.length }}</span>
                    </div>
                    <div class="space-y-4 max-h-[600px] overflow-y-auto pr-1">
                        <div v-if="loading" class="h-24 skeleton rounded-lg"></div>
                        <div v-else-if="managementList.length === 0" class="text-center py-8 text-slate-400 dark:text-slate-500"><p class="text-sm">Nenhum item pendente</p></div>
                        <task-card v-else v-for="item in managementList" :key="item.alert_id" :item="item" context="management" @action="handleAction" />
                    </div>
                </div>
            </div>
        </div>
    `,
    setup(props, { emit }) {
        const loading = ref(true);
        const todos = ref({ purchasing: [], kitchen: [], management: [] });
        const dayContext = ref(null);
        const planningData = ref(null); // NEW
        const selectedItem = ref(null);
        const adjustItem = ref(null);
        const metricsData = ref(null);
        const filterPriority = ref('all');
        const filterType = ref('all');
        const expandedEvents = ref(new Set()); // NEW: Track expanded events
        let refreshTimer = null;

        function toggleEvent(id) {
            if (expandedEvents.value.has(id)) {
                expandedEvents.value.delete(id);
            } else {
                expandedEvents.value.add(id);
            }
        }

        function isExpanded(event) {
            return expandedEvents.value.has(event.date + event.label);
        }

        const purchasingList = computed(() => {
            let list = todos.value.purchasing || [];
            if (filterPriority.value !== 'all') list = list.filter(i => i.priority === filterPriority.value);
            if (filterType.value !== 'all') list = list.filter(i => i.sphere === filterType.value);
            return list;
        });
        const kitchenList = computed(() => todos.value.kitchen || []);
        const managementList = computed(() => todos.value.management || []);

        const metrics = computed(() => {
            const m = metricsData.value || {};
            const totals = m.totals || {};
            const byPrio = m.by_priority || {};
            const dq = m.data_quality || {};
            return [
                { label: 'Total Alertas', value: totals.alerts || 0, color: 'text-blue-600 dark:text-blue-400', bgColor: 'bg-blue-100 dark:bg-blue-500/20', icon: '<svg class="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>' },
                { label: 'Urgente', value: byPrio.urgent || 0, color: 'text-red-600 dark:text-red-400', bgColor: 'bg-red-100 dark:bg-red-500/20', alert: (byPrio.urgent > 0), icon: '<svg class="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"></path></svg>' },
                { label: 'Estoque Negativo', value: dq.negative_stock || 0, color: 'text-orange-600 dark:text-orange-400', bgColor: 'bg-orange-100 dark:bg-orange-500/20', alert: (dq.negative_stock > 0), icon: '<svg class="w-6 h-6 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path></svg>' },
                { label: 'Sem Histórico', value: dq.no_demand_items || 0, color: 'text-slate-600 dark:text-slate-400', bgColor: 'bg-slate-200 dark:bg-slate-500/20', icon: '<svg class="w-6 h-6 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>' }
            ];
        });

        async function fetchData(isBackground = false) {
            if (!isBackground) {
                loading.value = true;
            }
            window.dispatchEvent(new CustomEvent('loading-start'));
            const startTime = Date.now();
            const MIN_LOADING_TIME = 700;
            try {
                const query = `?ignore_stock_balance=${props.baseZero}&${props.showIgnored ? 'status=suppressed' : ''}`;

                // ADDED planning preview request
                const [todosRes, metricsRes, planningRes] = await Promise.all([
                    fetch('/todo' + query).then(r => r.json()),
                    fetch('/metrics' + query).then(r => r.json()),
                    fetch('/planning/preview?window=7').then(r => r.json())
                ]);

                dayContext.value = todosRes.context || null;
                todos.value = {
                    purchasing: todosRes.purchasing || [],
                    kitchen: todosRes.kitchen || [],
                    management: todosRes.management || []
                };
                metricsData.value = metricsRes;
                planningData.value = planningRes; // Set planning data

            } catch (err) { console.error(err); }
            finally {
                if (!isBackground) {
                    const elapsed = Date.now() - startTime;
                    if (elapsed < MIN_LOADING_TIME) {
                        await new Promise(r => setTimeout(r, MIN_LOADING_TIME - elapsed));
                    }
                    loading.value = false;
                }
                window.dispatchEvent(new CustomEvent('loading-end'));
            }
        }

        async function handleStockSubmit(payload) {
            const itemId = adjustItem.value.id;
            try {
                await fetch(`/stock/${itemId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                emit('toast', { message: 'Estoque atualizado!', type: 'success' });
                adjustItem.value = null;
                fetchData();
            } catch (err) { emit('toast', { message: 'Erro ao atualizar estoque', type: 'error' }); }
        }

        async function handleAction({ action, alertId, itemId, itemTitle, item }) {
            try {
                if (action === 'analyze') {
                    selectedItem.value = item;
                    return;
                }
                if (action === 'adjust_stock') {
                    adjustItem.value = { title: itemTitle, id: itemId };
                    return;
                }
                if (action === 'restore') {
                    await fetch(`/alerts/${alertId}/suppress`, { method: 'DELETE' });
                    emit('toast', { message: 'Alerta restaurado!', type: 'success' });
                } else {
                    await fetch(`/alerts/${alertId}/suppress`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action }) });
                    emit('toast', { message: 'Alerta ocultado', type: 'info', undo: async () => { await fetch(`/alerts/${alertId}/suppress`, { method: 'DELETE' }); fetchData(); } });
                }
                await fetchData();
            } catch (err) { emit('toast', { message: 'Erro ao executar ação', type: 'error' }); }
        }

        watch(() => [props.baseZero, props.showIgnored], () => fetchData(false));

        const route = VueRouter.useRoute();
        watch(() => route.path, (newPath) => {
            if (newPath === '/dashboard') {
                fetchData(false);
            }
        });

        onMounted(() => {
            fetchData(false);
            refreshTimer = setInterval(() => fetchData(true), 60000);
            window.addEventListener('refresh-dashboard', () => fetchData(false));
        });
        onUnmounted(() => {
            if (refreshTimer) clearInterval(refreshTimer);
            window.removeEventListener('refresh-dashboard', () => fetchData(false));
        });

        const visibleFlags = computed(() => {
            if (!dayContext.value) return [];
            return dayContext.value.flags
                .filter(f => f !== 'EVENT')
                .slice(0, 4);
        });

        const flagMap = {
            'MONDAY': 'Segunda', 'TUESDAY': 'Terça', 'WEDNESDAY': 'Quarta', 'THURSDAY': 'Quinta', 'FRIDAY': 'Sexta', 'SATURDAY': 'Sábado', 'SUNDAY': 'Domingo',
            'PAYDAY': '$ Pagamento', 'BRIDGE_DAY': '>> Emenda'
        };

        function formatFlag(flag) {
            if (flagMap[flag]) return flagMap[flag];
            if (flag.startsWith('EVENT_')) {
                return flag.replace('EVENT_', '').replace(/_/g, ' ').toLowerCase().replace(/(^\w|\s\w)/g, m => m.toUpperCase());
            }
            return flag;
        }

        // Planning helpers
        function formatDate(isoDate) {
            if (!isoDate) return '';
            const d = new Date(isoDate);
            // Timezone fix: assume input is YYYY-MM-DD local
            // Better to split and construct date
            const [year, month, day] = isoDate.split('-');
            const dateObj = new Date(year, month - 1, day);
            return dateObj.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
        }

        function getEventIcon(type) {
            if (type === 'PAYDAY') return '<svg class="w-5 h-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
            if (type === 'EVENT') return '<svg class="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>';
            return '<svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path></svg>';
        }

        function getEventIconClass(type) {
            if (type === 'PAYDAY') return 'bg-emerald-100 dark:bg-emerald-500/20';
            if (type === 'EVENT') return 'bg-purple-100 dark:bg-purple-500/20';
            return 'bg-blue-100 dark:bg-blue-500/20';
        }

        function getImpactClass(impact) {
            if (impact.includes('acima')) return 'text-emerald-600 dark:text-emerald-400';
            if (impact.includes('abaixo')) return 'text-red-500 dark:text-red-400';
            return 'text-slate-500 dark:text-slate-400';
        }

        return { loading, dayContext, planningData, selectedItem, adjustItem, metrics, purchasingList, kitchenList, managementList, filterPriority, filterType, handleAction, handleStockSubmit, visibleFlags, formatFlag, formatDate, getEventIcon, getEventIconClass, getImpactClass, toggleEvent, isExpanded };
    }
};

// Export for use
window.SpaComponents = { IconDashboard, IconStock, TaskCard, DashboardView, AnalysisModal, StockAdjustmentModal };
