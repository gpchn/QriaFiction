const { createApp, ref, computed, nextTick, onMounted, watch } = Vue;

let _tid = 0;

window.addEventListener('pywebviewready', () => {
    createApp({
        setup() {
            const view = ref('launcher');
            const page = ref('projects');
            const isDark = ref(true);

            const tabs = [
                { id: 'projects', label: '项目' },
                { id: 'models', label: '模型' },
                { id: 'settings', label: '设置' },
            ];

            const currentPageTitle = computed(() => {
                const m = { projects: '项目', models: 'AI 模型', settings: '设置' };
                return m[page.value] || '';
            });

            const projects = ref([]);
            const models = ref([]);
            const cfg = ref({
                default_ai_provider: 'keyword',
                window_width: 1000,
                window_height: 700,
            });

            const toasts = ref([]);
            function toast(msg, type) {
                const id = ++_tid;
                toasts.value.push({ id, msg, type: type || 'ok' });
                setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id); }, 2200);
            }

            function ok(r) {
                if (!r) throw new Error('无响应');
                if (r.error) throw new Error(r.error.message);
                return r.data;
            }

            const modal = ref({ show: false, title: '', body: '', onOk: () => {} });
            function openModal(title, body, onOk) {
                modal.value = { show: true, title, body, onOk: onOk || (() => {}) };
            }

            function toggleTheme() { applyTheme(!isDark.value); }
            function applyTheme(dark) {
                isDark.value = dark;
                document.body.className = dark ? '' : 'light';
            }

            async function loadProjects() {
                try { projects.value = ok(await pywebview.api.get_projects()) || []; }
                catch { projects.value = []; }
            }
            async function loadModels() {
                try { models.value = ok(await pywebview.api.get_ai_models()) || []; }
                catch { models.value = []; }
            }
            async function loadCfg() {
                try {
                    const c = ok(await pywebview.api.get_config());
                    cfg.value.default_ai_provider = c.default_ai_provider || 'keyword';
                    cfg.value.window_width = c.window_width || 1000;
                    cfg.value.window_height = c.window_height || 700;
                    if (c.theme === 'light') applyTheme(false);
                } catch {}
            }

            function openImport() {
                openModal('导入项目',
                    '<label class="text-[11px] block mb-1.5" style="color:var(--fg-m)">ZIP 文件路径</label>' +
                    '<input id="m-zip" class="w-full h-9 px-3 text-[12px] rounded" style="background:var(--s2);border:1px solid var(--line);color:var(--fg)" placeholder="C:\\path\\to\\project.zip">',
                    async () => {
                        const v = (document.getElementById('m-zip') || {}).value?.trim();
                        if (!v) { toast('请输入路径', 'error'); return; }
                        try { ok(await pywebview.api.import_project(v)); await loadProjects(); toast('已导入'); }
                        catch (e) { toast(e.message, 'error'); }
                    });
            }

            function askDelete(p) {
                openModal('删除项目',
                    '<p class="text-[12px]" style="color:var(--fg-m)">确定删除「' + (p.title || p.name) + '」？</p>',
                    async () => {
                        try { ok(await pywebview.api.delete_project(p.id)); await loadProjects(); toast('已删除'); }
                        catch (e) { toast(e.message, 'error'); }
                    });
            }

            async function launch(id) {
                try { ok(await pywebview.api.launch_project(id)); view.value = 'game'; messages.value = []; }
                catch (e) { toast(e.message, 'error'); }
            }

            function openAddModel() {
                const inp = (id, ph, type) =>
                    '<div><label class="text-[11px] block mb-1.5" style="color:var(--fg-m)">' + ph + '</label>' +
                    '<input id="' + id + '" type="' + (type||'text') + '" class="w-full h-9 px-3 text-[12px] rounded" style="background:var(--s2);border:1px solid var(--line);color:var(--fg)" placeholder="' + ph + '"></div>';
                openModal('添加模型',
                    '<div class="space-y-3">' +
                    inp('m-name', '名称') +
                    '<div><label class="text-[11px] block mb-1.5" style="color:var(--fg-m)">提供商</label>' +
                    '<select id="m-prov" class="w-full h-9 px-3 text-[12px] rounded" style="background:var(--s2);border:1px solid var(--line);color:var(--fg)">' +
                    '<option value="openai">OpenAI</option><option value="deepseek">DeepSeek</option></select></div>' +
                    inp('m-model', '模型标识') +
                    inp('m-key', 'API Key', 'password') +
                    inp('m-base', 'Base URL（可选）') +
                    '</div>',
                    async () => {
                        const v = id => (document.getElementById(id) || {}).value?.trim() || '';
                        const d = { name: v('m-name'), provider: v('m-prov'), model: v('m-model'), api_key: v('m-key'), base_url: v('m-base') };
                        if (!d.name || !d.api_key) { toast('请填写必要信息', 'error'); return; }
                        try { ok(await pywebview.api.add_ai_model(JSON.stringify(d))); await loadModels(); toast('已添加'); }
                        catch (e) { toast(e.message, 'error'); }
                    });
            }

            async function removeModel(id) {
                try { ok(await pywebview.api.remove_ai_model(id)); await loadModels(); toast('已删除'); }
                catch (e) { toast(e.message, 'error'); }
            }

            async function saveCfg() {
                try {
                    await Promise.all([
                        pywebview.api.set_config('default_ai_provider', cfg.value.default_ai_provider),
                        pywebview.api.set_config('window_width', cfg.value.window_width),
                        pywebview.api.set_config('window_height', cfg.value.window_height),
                        pywebview.api.set_config('theme', isDark.value ? 'dark' : 'light'),
                    ]);
                    toast('已保存');
                } catch (e) { toast(e.message, 'error'); }
            }

            const gameStatus = ref('就绪');
            const gameLoading = ref(false);
            const gameInputEnabled = ref(false);
            const gameInput = ref('');
            const gamePlaceholder = ref('输入...');
            const messages = ref([]);
            const msgContainer = ref(null);

            let inputCb = null;
            let interactActions = null;
            let interactFallbacks = null;

            function addMsg(type, text, name, color, avatar) {
                messages.value.push({ type, text, name: name || '', color: color || '', avatar: avatar || '' });
            }

            function enableInput(yes) {
                gameInputEnabled.value = yes;
                if (yes) nextTick(() => {
                    const el = document.querySelector('[v-if="view === \'game\'"] input[type="text"]') ||
                               document.querySelector('.flex-1.overflow-y-auto + div input[type="text"]');
                    if (el) el.focus();
                });
            }

            async function sendInput() {
                const t = gameInput.value.trim();
                if (!t || !gameInputEnabled.value) return;
                gameInput.value = '';
                addMsg('user', t, '你', '', '');
                enableInput(false);

                if (inputCb) { inputCb(t); return; }

                if (interactActions) {
                    gameLoading.value = true;
                    gameStatus.value = '分析中...';
                    try {
                        const r = ok(await pywebview.api.ai_match(t, interactActions, interactFallbacks));
                        gameLoading.value = false;
                        if (r && r.matched) {
                            gameStatus.value = '已匹配';
                            interactActions = null;
                            interactFallbacks = null;
                            await pywebview.api.on_action_matched(r);
                        } else {
                            if (r && r.fallback) addMsg('system', r.fallback);
                            enableInput(true);
                        }
                    } catch (e) {
                        gameLoading.value = false;
                        addMsg('system', '错误: ' + e.message);
                        enableInput(true);
                    }
                }
            }

            async function backToLauncher() {
                try { await pywebview.api.return_to_launcher(); } catch {}
                view.value = 'launcher';
                messages.value = [];
                gameStatus.value = '就绪';
                gameInputEnabled.value = false;
                await loadProjects();
            }

            window.addMessage = addMsg;
            window.setBackground = (p) => {};
            window.setStatus = (t) => { gameStatus.value = t; };
            window.getUserInput = (prompt) => {
                gameStatus.value = prompt;
                gamePlaceholder.value = prompt;
                enableInput(true);
                return new Promise(resolve => { inputCb = v => { inputCb = null; resolve(v); }; });
            };
            window.handleInteract = (prompt, actions, fallbacks) => {
                interactActions = actions;
                interactFallbacks = fallbacks;
                gameStatus.value = prompt || '你想做什么？';
                gamePlaceholder.value = prompt || '输入...';
                enableInput(true);
            };
            window.sendGameInput = sendInput;

            watch(messages, () => {
                nextTick(() => {
                    const el = msgContainer.value;
                    if (el) el.scrollTop = el.scrollHeight;
                });
            }, { deep: true });

            onMounted(() => { Promise.all([loadProjects(), loadModels(), loadCfg()]); });

            return {
                view, page, isDark, tabs, currentPageTitle,
                projects, models, cfg,
                toasts, modal, openModal,
                toggleTheme, applyTheme,
                openImport, askDelete, launch,
                openAddModel, removeModel, saveCfg,
                gameStatus, gameLoading, gameInputEnabled, gameInput, gamePlaceholder,
                messages, msgContainer,
                sendInput, backToLauncher,
            };
        },
    }).mount('#app');
});
