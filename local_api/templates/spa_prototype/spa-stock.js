/**
 * Inventory Intelligence - SPA Stock View & Config Modal
 */

// ========== STOCK VIEW ==========
const StockView = {
    emits: ['toast'],
    template: `
        <div class="space-y-6">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div><h2 class="text-3xl font-bold text-slate-900 dark:text-white">Controle de Estoque</h2><p class="text-slate-500 dark:text-slate-400 mt-1">Clique nos valores para editar</p></div>
                <button @click="showEventsModal = true" class="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium text-white transition-all">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    Eventos Sazonais
                </button>
                <button @click="exportCSV" class="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded-lg text-sm font-medium text-white transition-all">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    Exportar CSV
                </button>
            </div>
            <div class="bg-white dark:bg-slate-800/50 rounded-2xl border border-slate-200/80 dark:border-slate-700/50 p-4 shadow dark:shadow-none">
                <div class="flex flex-col md:flex-row gap-4">
                    <div class="flex-1"><label class="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-2">Buscar</label>
                        <input v-model="search" type="text" placeholder="Nome do item..." class="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"></div>
                    <div class="w-full md:w-48"><label class="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-2">Categoria</label>
                        <select v-model="filterCategory" class="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-700 dark:text-slate-300 outline-none">
                            <option value="all">Todas</option><option value="Produto (Venda)">Produtos</option><option value="Ingrediente">Ingredientes</option><option value="Pré-Preparo">Pré-Preparo</option>
                        </select></div>
                </div>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div class="bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-700/50 p-4 shadow dark:shadow-none"><p class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">Total</p><p class="text-2xl font-bold text-slate-900 dark:text-white mt-1">{{ items.length }}</p></div>
                <div class="bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-700/50 p-4 shadow dark:shadow-none"><p class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">C/ Estoque</p><p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{{ items.filter(i => i.current_stock >= 10).length }}</p></div>
                <div class="bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-700/50 p-4 shadow dark:shadow-none"><p class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">Baixo</p><p class="text-2xl font-bold text-yellow-600 dark:text-yellow-400 mt-1">{{ items.filter(i => i.current_stock > 0 && i.current_stock < 10).length }}</p></div>
                <div class="bg-white dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-700/50 p-4 shadow dark:shadow-none"><p class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">Zerado</p><p class="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{{ items.filter(i => i.current_stock === 0).length }}</p></div>
            </div>
            <div class="bg-white dark:bg-slate-800/50 rounded-2xl border border-slate-200/80 dark:border-slate-700/50 overflow-hidden shadow dark:shadow-none">
                <table class="w-full">
                    <thead><tr class="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700/50">
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">Item</th>
                        <th class="px-6 py-4 text-left text-xs font-bold text-slate-500 dark:text-slate-400 uppercase hidden sm:table-cell">Categoria</th>
                        <th class="px-6 py-4 text-center text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">Estoque</th>
                        <th class="px-6 py-4 text-center text-xs font-bold text-slate-500 dark:text-slate-400 uppercase hidden md:table-cell">Última Contagem</th>
                    </tr></thead>
                    <tbody class="divide-y divide-slate-200 dark:divide-slate-700/50">
                        <tr v-if="loading"><td colspan="4" class="p-6"><div class="h-12 skeleton rounded-lg mb-3"></div><div class="h-12 skeleton rounded-lg"></div></td></tr>
                        <tr v-else v-for="item in filteredItems" :key="item.id" class="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors" :class="{ 'bg-blue-50 dark:bg-blue-500/10': pendingChanges[item.id] }">
                            <td class="px-6 py-4"><p class="font-semibold text-slate-900 dark:text-white">{{ item.name }}</p></td>
                            <td class="px-6 py-4 hidden sm:table-cell"><span class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-medium">{{ item.category }}</span></td>
                            <td class="px-6 py-4 text-center">
                                <div v-if="editingId === item.id" class="inline-block">
                                    <input v-model.number="editValue" type="number" step="0.01" min="0" @blur="finishEdit(item)" @keyup.enter="finishEdit(item)" @keyup.escape="cancelEdit" class="w-20 px-3 py-1.5 bg-white dark:bg-slate-900 border-2 border-blue-500 rounded-lg text-center text-sm font-bold text-slate-900 dark:text-slate-100 outline-none" /></div>
                                <button v-else @click="startEdit(item)" class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-bold cursor-pointer transition-all hover:scale-105" :class="getStockClass(item)">
                                    {{ getDisplayQty(item) }} {{ item.unit }}
                                    <svg class="w-3.5 h-3.5 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
                                </button>
                                <button @click="openLotModal(item)" class="ml-2 p-1.5 text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-all" title="Adicionar Lote">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
                                </button>
                            </td>
                            <td class="px-6 py-4 text-center hidden md:table-cell"><span class="text-sm" :class="item.last_audit ? 'text-slate-600 dark:text-slate-300' : 'text-slate-400 dark:text-slate-500 italic'">{{ item.last_audit ? formatDate(item.last_audit) : 'Nunca' }}</span></td>
                        </tr>
                    </tbody>
                </table>
                <div v-if="!loading && filteredItems.length === 0" class="p-12 text-center"><p class="text-slate-500 dark:text-slate-400 font-medium">Nenhum item encontrado</p></div>
            </div>
            <transition name="slide">
                <div v-if="pendingCount > 0" class="fixed bottom-0 left-0 right-0 bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border-t border-slate-200 dark:border-slate-700/50 p-4 z-40">
                    <div class="max-w-7xl mx-auto flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center"><svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg></div>
                            <div><p class="font-bold text-slate-900 dark:text-white">{{ pendingCount }} alterações pendentes</p><p class="text-sm text-slate-500 dark:text-slate-400">Clique em salvar para confirmar</p></div>
                        </div>
                        <div class="flex items-center gap-3">
                            <button @click="discardChanges" class="px-4 py-2 text-sm font-bold text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors">Descartar</button>
                            <button @click="saveChanges" :disabled="saving" class="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-xl text-sm font-bold text-white transition-all flex items-center gap-2 disabled:opacity-50">
                                <svg v-if="saving" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                {{ saving ? 'Salvando...' : 'Salvar Contagem' }}
                            </button>
                        </div>
                    </div>
                </div>
                </div>
            </transition>
            </transition>
            <lot-modal :show="showLotModal" :item="selectedItem" @close="showLotModal = false" @save="onLotSaved" />
            <events-modal :show="showEventsModal" @close="showEventsModal = false" />
        </div>
    `,
    setup(props, { emit }) {
        const loading = ref(true), saving = ref(false), items = ref([]), search = ref(''), filterCategory = ref('all'), editingId = ref(null), editValue = ref(0);
        const showLotModal = ref(false), selectedItem = ref(null), showEventsModal = ref(false);
        const pendingChanges = reactive({});
        const filteredItems = computed(() => items.value.filter(item => {
            if (search.value && !item.name.toLowerCase().includes(search.value.toLowerCase())) return false;
            if (filterCategory.value !== 'all' && item.category !== filterCategory.value) return false;
            return true;
        }));
        const pendingCount = computed(() => Object.keys(pendingChanges).length);
        function getDisplayQty(item) { return pendingChanges[item.id]?.newQty ?? item.current_stock; }
        function getStockClass(item) { const qty = getDisplayQty(item); if (qty === 0) return 'bg-red-500/20 text-red-400'; if (qty < 10) return 'bg-yellow-500/20 text-yellow-400'; return 'bg-emerald-500/20 text-emerald-400'; }
        function startEdit(item) { editingId.value = item.id; editValue.value = getDisplayQty(item); nextTick(() => document.querySelector('input[type="number"]')?.focus()); }
        function finishEdit(item) { if (editValue.value !== item.current_stock) { pendingChanges[item.id] = { newQty: editValue.value }; } else { delete pendingChanges[item.id]; } editingId.value = null; }
        function cancelEdit() { editingId.value = null; }
        function discardChanges() { Object.keys(pendingChanges).forEach(k => delete pendingChanges[k]); }
        async function saveChanges() {
            saving.value = true;
            try {
                const itemsToSave = Object.entries(pendingChanges).map(([item_id, data]) => ({ item_id, quantity: data.newQty, note: 'Contagem via SPA' }));
                const res = await fetch('/stock/bulk-update', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ items: itemsToSave }) });
                if (!res.ok) throw new Error('Failed');
                emit('toast', { message: 'Alterações salvas!', type: 'success' });
                discardChanges(); await fetchItems();
            } catch (err) { emit('toast', { message: 'Erro ao salvar', type: 'error' }); }
            finally { saving.value = false; }
        }
        function formatDate(iso) { return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }); }
        function exportCSV() { window.location.href = '/stock/export'; }
        async function fetchItems() { loading.value = true; try { items.value = await fetch('/stock/items').then(r => r.json()); } catch (err) { console.error(err); } finally { loading.value = false; } }
        onMounted(fetchItems);

        function openLotModal(item) { selectedItem.value = item; showLotModal.value = true; }
        function onLotSaved() { showLotModal.value = false; emit('toast', { message: 'Lote adicionado!', type: 'success' }); }

        return { loading, saving, items, search, filterCategory, editingId, editValue, pendingChanges, filteredItems, pendingCount, showLotModal, selectedItem, showEventsModal, getDisplayQty, getStockClass, startEdit, finishEdit, cancelEdit, discardChanges, saveChanges, formatDate, exportCSV, openLotModal, onLotSaved };
    }
};

// ========== CONFIG MODAL ==========
const ConfigModal = {
    props: ['show', 'config'],
    emits: ['close', 'save', 'refresh'],
    template: `
        <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="$emit('close')">
            <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
                <!-- Header -->
                <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-800/50">
                    <div class="flex items-center gap-3">
                        <div class="p-2 bg-blue-100 dark:bg-blue-500/20 rounded-xl">
                            <svg class="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                        </div>
                        <div>
                            <h3 class="text-lg font-bold text-slate-900 dark:text-white">Ajustes de Operação</h3>
                            <p class="text-xs text-slate-500 dark:text-slate-400">Personalize como o sistema toma decisões</p>
                        </div>
                    </div>
                    <button @click="$emit('close')" class="text-slate-400 hover:text-slate-900 dark:hover:text-white p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                    </button>
                </div>
                
                <!-- Body -->
                <form @submit.prevent="save" class="p-6 space-y-8 max-h-[70vh] overflow-y-auto">
                    
                    <!-- Section 1: Meta de Estoque -->
                    <div class="space-y-4">
                        <div class="flex items-center gap-2">
                            <div class="p-1.5 bg-blue-100 dark:bg-blue-500/20 rounded-lg">
                                <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>
                            </div>
                            <h4 class="text-sm font-bold text-slate-700 dark:text-slate-700 dark:text-slate-200 uppercase tracking-wide">Meta de Estoque (Cobertura)</h4>
                        </div>
                        <p class="text-xs text-slate-500 dark:text-slate-400 -mt-2">Quantos dias de vendas você quer garantir ter em estoque? Isso define o tamanho da sua despensa.</p>
                        
                        <div class="grid grid-cols-3 gap-4">
                            <!-- Classe A -->
                            <div class="bg-slate-100 dark:bg-slate-700/30 p-4 rounded-xl border border-slate-200 dark:border-slate-700/50">
                                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-3">Itens de Alto Giro (A)</label>
                                <div class="flex items-center justify-between gap-2">
                                    <button type="button" @click="form.coverage_days_target_A = Math.max(1, form.coverage_days_target_A - 1)" class="w-9 h-9 rounded-full bg-slate-200 dark:bg-slate-600 shadow border border-slate-300 dark:border-slate-500 flex items-center justify-center text-slate-700 dark:text-slate-700 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-500 active:scale-95 transition-all">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path></svg>
                                    </button>
                                    <span class="text-2xl font-mono font-bold text-slate-900 dark:text-white">{{ form.coverage_days_target_A }}</span>
                                    <button type="button" @click="form.coverage_days_target_A++" class="w-9 h-9 rounded-full bg-slate-200 dark:bg-slate-600 shadow border border-slate-300 dark:border-slate-500 flex items-center justify-center text-slate-700 dark:text-slate-700 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-500 active:scale-95 transition-all">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                                    </button>
                                </div>
                                <div class="text-center mt-2 text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold tracking-widest">DIAS</div>
                            </div>
                            
                            <!-- Classe B -->
                            <div class="bg-slate-100 dark:bg-slate-700/30 p-4 rounded-xl border border-slate-200 dark:border-slate-700/50">
                                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-3">Giro Médio (B)</label>
                                <div class="flex items-center justify-between gap-2">
                                    <button type="button" @click="form.coverage_days_target_B = Math.max(1, form.coverage_days_target_B - 1)" class="w-9 h-9 rounded-full bg-slate-200 dark:bg-slate-600 shadow border border-slate-300 dark:border-slate-500 flex items-center justify-center text-slate-700 dark:text-slate-700 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-500 active:scale-95 transition-all">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path></svg>
                                    </button>
                                    <span class="text-2xl font-mono font-bold text-slate-900 dark:text-white">{{ form.coverage_days_target_B }}</span>
                                    <button type="button" @click="form.coverage_days_target_B++" class="w-9 h-9 rounded-full bg-slate-200 dark:bg-slate-600 shadow border border-slate-300 dark:border-slate-500 flex items-center justify-center text-slate-700 dark:text-slate-700 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-500 active:scale-95 transition-all">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                                    </button>
                                </div>
                                <div class="text-center mt-2 text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold tracking-widest">DIAS</div>
                            </div>
                            
                            <!-- Classe C -->
                            <div class="bg-slate-100 dark:bg-slate-700/30 p-4 rounded-xl border border-slate-200 dark:border-slate-700/50">
                                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-3">Giro Baixo (C)</label>
                                <div class="flex items-center justify-between gap-2">
                                    <button type="button" @click="form.coverage_days_target_C = Math.max(1, form.coverage_days_target_C - 1)" class="w-9 h-9 rounded-full bg-slate-200 dark:bg-slate-600 shadow border border-slate-300 dark:border-slate-500 flex items-center justify-center text-slate-700 dark:text-slate-700 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-500 active:scale-95 transition-all">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path></svg>
                                    </button>
                                    <span class="text-2xl font-mono font-bold text-slate-900 dark:text-white">{{ form.coverage_days_target_C }}</span>
                                    <button type="button" @click="form.coverage_days_target_C++" class="w-9 h-9 rounded-full bg-slate-200 dark:bg-slate-600 shadow border border-slate-300 dark:border-slate-500 flex items-center justify-center text-slate-700 dark:text-slate-700 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-500 active:scale-95 transition-all">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                                    </button>
                                </div>
                                <div class="text-center mt-2 text-[10px] text-slate-500 dark:text-slate-400 uppercase font-bold tracking-widest">DIAS</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="h-px bg-slate-200 dark:bg-slate-700"></div>
                    
                    <!-- Section 2: Risco & Fornecedores -->
                    <div class="space-y-4">
                        <div class="flex items-center gap-2">
                            <div class="p-1.5 bg-amber-100 dark:bg-amber-500/20 rounded-lg">
                                <svg class="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                            </div>
                            <h4 class="text-sm font-bold text-slate-700 dark:text-slate-700 dark:text-slate-200 uppercase tracking-wide">Risco & Fornecedores</h4>
                        </div>
                        
                        <div class="grid grid-cols-2 gap-6">
                            <!-- Alerta de Validade -->
                            <div>
                                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Alerta de Validade</label>
                                <p class="text-[10px] text-slate-500 dark:text-slate-400 mb-2">Avisar quando faltar X dias para vencer.</p>
                                <div class="flex items-center gap-2">
                                    <button type="button" @click="form.perishable_risk_threshold_days = Math.max(1, form.perishable_risk_threshold_days - 1)" class="w-8 h-8 rounded bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 flex items-center justify-center text-slate-600 dark:text-slate-300">
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path></svg>
                                    </button>
                                    <input type="number" v-model.number="form.perishable_risk_threshold_days" class="flex-1 text-center text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded py-2 font-bold text-slate-900 dark:text-white" readonly>
                                    <button type="button" @click="form.perishable_risk_threshold_days++" class="w-8 h-8 rounded bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 flex items-center justify-center text-slate-600 dark:text-slate-300">
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Histórico de Análise -->
                            <div>
                                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Histórico de Análise</label>
                                <p class="text-[10px] text-slate-500 dark:text-slate-400 mb-2">Quantos dias passados usar para calcular a média.</p>
                                <div class="flex items-center gap-2">
                                    <button type="button" @click="form.forecast_window_days = Math.max(7, form.forecast_window_days - 5)" class="w-8 h-8 rounded bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 flex items-center justify-center text-slate-600 dark:text-slate-300">
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path></svg>
                                    </button>
                                    <input type="number" v-model.number="form.forecast_window_days" class="flex-1 text-center text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded py-2 font-bold text-slate-900 dark:text-white" readonly>
                                    <button type="button" @click="form.forecast_window_days += 5" class="w-8 h-8 rounded bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 flex items-center justify-center text-slate-600 dark:text-slate-300">
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Segurança Fornecedor -->
                        <div class="pt-2">
                            <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-2">Segurança contra Atrasos de Fornecedor (Fator)</label>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase block mb-1">Produtos Prontos</span>
                                    <div class="flex items-center gap-2">
                                        <button type="button" @click="form.supplier_variability_finished = Math.max(1, parseFloat((form.supplier_variability_finished - 0.1).toFixed(1)))" class="w-8 h-8 rounded bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 flex items-center justify-center text-slate-600 dark:text-slate-300">
                                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path></svg>
                                        </button>
                                        <input type="number" step="0.1" v-model.number="form.supplier_variability_finished" class="flex-1 text-center text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded py-2 font-bold text-slate-900 dark:text-white" readonly>
                                        <button type="button" @click="form.supplier_variability_finished = parseFloat((form.supplier_variability_finished + 0.1).toFixed(1))" class="w-8 h-8 rounded bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 flex items-center justify-center text-slate-600 dark:text-slate-300">
                                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                                        </button>
                                    </div>
                                </div>
                                <div>
                                    <span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase block mb-1">Ingredientes</span>
                                    <div class="flex items-center gap-2">
                                        <button type="button" @click="form.supplier_variability_ingredient = Math.max(1, parseFloat((form.supplier_variability_ingredient - 0.1).toFixed(1)))" class="w-8 h-8 rounded bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 flex items-center justify-center text-slate-600 dark:text-slate-300">
                                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"></path></svg>
                                        </button>
                                        <input type="number" step="0.1" v-model.number="form.supplier_variability_ingredient" class="flex-1 text-center text-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded py-2 font-bold text-slate-900 dark:text-white" readonly>
                                        <button type="button" @click="form.supplier_variability_ingredient = parseFloat((form.supplier_variability_ingredient + 0.1).toFixed(1))" class="w-8 h-8 rounded bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 flex items-center justify-center text-slate-600 dark:text-slate-300">
                                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </form>
                
                <!-- Footer -->
                <div class="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex justify-end gap-3 bg-slate-50 dark:bg-slate-800/50">
                    <button type="button" @click="$emit('close')" class="px-4 py-2.5 rounded-lg text-sm font-bold text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">Cancelar</button>
                    <button @click="save" class="px-6 py-2.5 rounded-lg text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 transition-colors flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                        Salvar Alterações
                    </button>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            form: { coverage_days_target_A: 3, coverage_days_target_B: 5, coverage_days_target_C: 7, forecast_window_days: 30, supplier_variability_finished: 1.2, supplier_variability_ingredient: 1.3, perishable_risk_threshold_days: 3 }
        };
    },
    watch: {
        config: { handler(cfg) { if (cfg) Object.assign(this.form, cfg); }, immediate: true }
    },
    methods: {
        save() {
            this.$emit('save', { ...this.form });
            // Emitir refresh para atualizar alertas após salvar
            this.$emit('refresh');
        }
    }
};
// ========== LOT MODAL ==========
const LotModal = {
    props: ['show', 'item'],
    emits: ['close', 'save'],
    template: `
        <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="$emit('close')">
            <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md border border-slate-200 dark:border-slate-700 overflow-hidden transform transition-all">
                <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-800/50">
                     <h3 class="text-lg font-bold text-slate-900 dark:text-white">Adicionar Lote</h3>
                     <button @click="$emit('close')" class="text-slate-400 hover:text-slate-900 dark:hover:text-white"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
                </div>
                <form @submit.prevent="save" class="p-6 space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Item</label>
                        <p class="font-bold text-slate-900 dark:text-white">{{ item?.name }}</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Quantidade</label>
                        <input v-model.number="form.quantity" type="number" step="0.01" required class="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Validade</label>
                        <input v-model="form.expires_at" type="date" required class="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                    <div class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg p-3 mb-2">
                        <p class="text-xs text-amber-700 dark:text-amber-400 font-medium flex items-start gap-2">
                            <svg class="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                            </svg>
                            <span>Informar lote <strong>não altera</strong> o estoque total. Use esta função apenas para controle de validade.</span>
                        </p>
                    </div>
                    <div class="pt-4 flex justify-end gap-3">
                        <button type="button" @click="$emit('close')" class="px-4 py-2 rounded-lg text-sm font-medium text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700">Cancelar</button>
                        <button type="submit" :disabled="saving" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-bold flex items-center gap-2">
                             <svg v-if="saving" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                             {{ saving ? 'Salvando...' : 'Adicionar' }}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `,
    data() { return { form: { quantity: '', expires_at: '' }, saving: false }; },
    methods: {
        async save() {
            this.saving = true;
            try {
                const res = await fetch('/stock/lots', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ item_id: this.item.id, quantity: this.form.quantity, expires_at: this.form.expires_at })
                });
                if (!res.ok) throw new Error('Failed');
                this.$emit('save');
                this.form.quantity = ''; this.form.expires_at = '';
            } catch (e) { console.error(e); alert('Erro ao salvar lote'); }
            finally { this.saving = false; }
        }
    }
};

// ========== EVENTS MODAL ==========
const EventsModal = {
    props: ['show'],
    emits: ['close'],
    template: `
        <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="$emit('close')">
            <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-4xl border border-slate-200 dark:border-slate-700 overflow-hidden transform transition-all h-[80vh] flex flex-col">
                <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-800/50">
                     <h3 class="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                        <svg class="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                        Calendário de Eventos & Sazonalidade
                     </h3>
                     <button @click="$emit('close')" class="text-slate-400 hover:text-slate-900 dark:hover:text-white"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
                </div>
                
                <div class="flex-1 flex overflow-hidden">
                    <!-- Left: Form -->
                    <div class="w-1/3 border-r border-slate-200 dark:border-slate-700 p-6 overflow-y-auto bg-slate-50/50 dark:bg-slate-900/30">
                        <h4 class="text-sm font-bold text-slate-700 dark:text-slate-300 mb-4 uppercase tracking-wide">Novo Evento</h4>
                        <form @submit.prevent="addEvent" class="space-y-4">
                            <div>
                                <label class="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-1">Nome do Evento</label>
                                <input v-model="form.name" type="text" required placeholder="Ex: Carnaval" class="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-purple-500 outline-none">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-1">Data</label>
                                <input v-model="form.date" type="date" required class="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-purple-500 outline-none">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-1">Fator de Impacto (Demanda)</label>
                                <p class="text-[10px] text-slate-400 mb-2">1.0 = Normal, 1.2 = +20% demanda, 0.5 = -50% demanda</p>
                                <div class="flex items-center gap-2">
                                     <input v-model.number="form.factor" type="number" step="0.1" min="0" max="5" required class="w-20 px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg text-sm font-bold text-center text-slate-900 dark:text-white focus:ring-2 focus:ring-purple-500 outline-none">
                                     <input type="range" v-model.number="form.factor" min="0" max="3" step="0.1" class="flex-1 accent-purple-600">
                                </div>
                            </div>
                             <div>
                                <label class="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-1">Nota (Opcional)</label>
                                <input v-model="form.note" type="text" class="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-600 rounded-lg text-sm text-slate-900 dark:text-white focus:ring-2 focus:ring-purple-500 outline-none">
                            </div>
                            
                            <button type="submit" :disabled="submitting" class="w-full py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2">
                                <svg v-if="submitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                {{ submitting ? 'Adicionando...' : 'Adicionar Evento' }}
                            </button>
                        </form>
                    </div>
                    
                    <!-- Right: List -->
                    <div class="flex-1 p-6 overflow-y-auto">
                        <div v-if="loading" class="space-y-3">
                            <div class="h-16 skeleton rounded-xl"></div><div class="h-16 skeleton rounded-xl"></div>
                        </div>
                        <div v-else-if="events.length === 0" class="h-full flex flex-col items-center justify-center text-slate-400">
                             <svg class="w-12 h-12 mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                             <p>Nenhum evento cadastrado.</p>
                        </div>
                        <div v-else class="space-y-3">
                             <div v-for="evt in events" :key="evt.id" class="bg-white dark:bg-slate-800/50 p-4 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center justify-between group hover:border-purple-500/50 transition-colors">
                                  <div class="flex items-center gap-4">
                                      <div class="w-12 h-12 rounded-lg bg-slate-100 dark:bg-slate-700 flex flex-col items-center justify-center border border-slate-200 dark:border-slate-600">
                                          <span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase leading-none">{{ formatDateMonth(evt.date) }}</span>
                                          <span class="text-xl font-bold text-slate-900 dark:text-white leading-none mt-0.5">{{ formatDateDay(evt.date) }}</span>
                                      </div>
                                      <div>
                                          <h5 class="font-bold text-slate-900 dark:text-white">{{ evt.name }}</h5>
                                          <div class="flex items-center gap-2 mt-1">
                                              <span class="text-xs px-2 py-0.5 rounded-full font-bold" :class="getFactorClass(evt.factor)">
                                                  {{ evt.factor }}x
                                              </span>
                                              <span v-if="evt.note" class="text-xs text-slate-500 dark:text-slate-400 italic truncate max-w-[200px]">{{ evt.note }}</span>
                                          </div>
                                      </div>
                                  </div>
                                  <button @click="deleteEvent(evt.id)" class="p-2 text-slate-400 hover:text-red-500 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors opacity-0 group-hover:opacity-100">
                                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                  </button>
                             </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            loading: true, submitting: false, events: [],
            form: { name: '', date: '', factor: 1.2, note: '' }
        };
    },
    watch: { show: { handler(v) { if (v) this.fetchEvents(); } } },
    methods: {
        async fetchEvents() {
            this.loading = true;
            try { this.events = await fetch('/events/').then(r => r.json()); }
            catch (err) { console.error(err); }
            finally { this.loading = false; }
        },
        async addEvent() {
            this.submitting = true;
            try {
                const res = await fetch('/events/', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.form)
                });
                if (!res.ok) throw new Error();
                await this.fetchEvents();
                this.form = { name: '', date: '', factor: 1.2, note: '' }; // Reset
            } catch (e) { alert('Erro ao adicionar evento'); }
            finally { this.submitting = false; }
        },
        async deleteEvent(id) {
            if (!confirm('Remover este evento?')) return;
            try {
                await fetch('/events/' + id, { method: 'DELETE' });
                await this.fetchEvents();
            } catch (e) { alert('Erro ao remover'); }
        },
        getFactorClass(f) {
            if (f > 1.0) return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400';
            if (f < 1.0) return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
            return 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300';
        },
        formatDateDay(d) { return new Date(d).getUTCDate(); },
        formatDateMonth(d) { return new Date(d).toLocaleString('pt-BR', { month: 'short', timeZone: 'UTC' }).toUpperCase().replace('.', ''); }
    }
};

window.SpaComponents.StockView = StockView;
window.SpaComponents.ConfigModal = ConfigModal;
window.SpaComponents.LotModal = LotModal;
window.SpaComponents.EventsModal = EventsModal;
