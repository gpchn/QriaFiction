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
                    applyTheme((c.theme || 'dark') !== 'light');
                } catch { applyTheme(true); }
            }

            function openImport() {
                openModal('导入项目',
                    '<label class="text-[13px] block mb-1.5" style="color:var(--fg-m)">ZIP 文件路径</label>' +
                    '<input id="m-zip" class="w-full h-10 px-3 text-[14px] rounded" style="background:var(--s2);border:1px solid var(--line);color:var(--fg)" placeholder="C:\\path\\to\\project.zip">',
                    async () => {
                        const v = (document.getElementById('m-zip') || {}).value?.trim();
                        if (!v) { toast('请输入路径', 'error'); return; }
                        try { ok(await pywebview.api.import_project(v)); await loadProjects(); toast('已导入'); }
                        catch (e) { toast(e.message, 'error'); }
                    });
            }

            function askDelete(p) {
                openModal('删除项目',
                    '<p class="text-[14px]" style="color:var(--fg-m)">确定删除「' + (p.title || p.name) + '」？</p>',
                    async () => {
                        try { ok(await pywebview.api.delete_project(p.id)); await loadProjects(); toast('已删除'); }
                        catch (e) { toast(e.message, 'error'); }
                    });
            }

            async function launch(id) {
                try {
                    const p = projects.value.find(x => x.id === id);
                    gameProjectName.value = p ? (p.title || p.name) : '';
                    ok(await pywebview.api.launch_project(id));
                    view.value = 'game';
                    messages.value = [];
                    gameStatus.value = '运行中...';
                }
                catch (e) { toast(e.message, 'error'); }
            }

            function openAddModel() {
                const inp = (id, ph, type) =>
                    '<div><label class="text-[13px] block mb-1.5" style="color:var(--fg-m)">' + ph + '</label>' +
                    '<input id="' + id + '" type="' + (type||'text') + '" class="w-full h-10 px-3 text-[14px] rounded" style="background:var(--s2);border:1px solid var(--line);color:var(--fg)" placeholder="' + ph + '"></div>';
                openModal('添加模型',
                    '<div class="space-y-3">' +
                    inp('m-name', '名称') +
                    '<div><label class="text-[13px] block mb-1.5" style="color:var(--fg-m)">提供商</label>' +
                    '<select id="m-prov" class="w-full h-10 px-3 text-[14px] rounded" style="background:var(--s2);border:1px solid var(--line);color:var(--fg)">' +
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
                    await pywebview.api.set_config_batch(JSON.stringify({
                        'default_ai_provider': cfg.value.default_ai_provider,
                        'window_width': cfg.value.window_width,
                        'window_height': cfg.value.window_height,
                        'theme': isDark.value ? 'dark' : 'light',
                    }));
                    toast('已保存');
                } catch (e) { toast(e.message, 'error'); }
            }

            const gameStatus = ref('就绪');
            const gameLoading = ref(false);
            const gameInputEnabled = ref(false);
            const gameInput = ref('');
            const gamePlaceholder = ref('输入...');
            const gameProjectName = ref('');
            const messages = ref([]);
            const msgContainer = ref(null);
            const showContinueHint = ref(false);

            function addMsg(type, text, name, color, avatar) {
                messages.value.push({ type, text, name: name || '', color: color || '', avatar: avatar || '' });
            }

            function enableInput(yes) {
                gameInputEnabled.value = yes;
                if (yes) nextTick(() => {
                    const el = document.querySelector('#app input[type="text"]');
                    if (el) el.focus();
                });
            }

            async function sendInput() {
                const t = gameInput.value.trim();
                if (!t || !gameInputEnabled.value) return;
                gameInput.value = '';
                addMsg('user', t, '你', '', '');
                enableInput(false);
                showContinueHint.value = false;
                try { await pywebview.api.submit_input(t); }
                catch (e) { console.error('submit_input error', e); }
            }

            async function backToLauncher() {
                try { await pywebview.api.return_to_launcher(); } catch {}
                view.value = 'launcher';
                messages.value = [];
                gameStatus.value = '就绪';
                gameInputEnabled.value = false;
                gameProjectName.value = '';
                showContinueHint.value = false;
                await loadProjects();
            }

            function onMsgAreaClick() {
                if (showContinueHint.value) {
                    showContinueHint.value = false;
                    pywebview.api.continue_game();
                }
            }

            function contrastColor(hex) {
                if (!hex) return 'var(--fg-m)';
                const r = parseInt(hex.slice(1,3), 16);
                const g = parseInt(hex.slice(3,5), 16);
                const b = parseInt(hex.slice(5,7), 16);
                const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
                return lum > 0.5 ? '#000000' : '#ffffff';
            }

            function colorBubble(hex) {
                if (!hex) return 'var(--s1)';
                const r = parseInt(hex.slice(1,3), 16);
                const g = parseInt(hex.slice(3,5), 16);
                const b = parseInt(hex.slice(5,7), 16);
                if (isDark.value) {
                    const f = 0.15;
                    return `rgba(${r},${g},${b},${f})`;
                } else {
                    const f = 0.12;
                    const br = Math.round(r + (255 - r) * (1 - f));
                    const bg = Math.round(g + (255 - g) * (1 - f));
                    const bb = Math.round(b + (255 - b) * (1 - f));
                    return `rgb(${br},${bg},${bb})`;
                }
            }

            window.addMessage = addMsg;
            window.setBackground = () => {};
            window.setStatus = (t) => { gameStatus.value = t; };
            window.getUserInput = (prompt) => {
                gameStatus.value = prompt;
                gamePlaceholder.value = prompt;
                enableInput(true);
            };
            window.handleInteract = (prompt, actions, fallbacks) => {
                gameStatus.value = prompt || '你想做什么？';
                gamePlaceholder.value = prompt || '输入...';
                enableInput(true);
            };
            window.showContinue = () => {
                showContinueHint.value = true;
            };

            watch(messages, () => {
                nextTick(() => {
                    const el = msgContainer.value;
                    if (el) el.scrollTop = el.scrollHeight;
                });
            }, { deep: true });

            onMounted(() => {
                Promise.all([loadProjects(), loadModels(), loadCfg()]);
            });

            return {
                view, page, isDark, tabs, currentPageTitle,
                projects, models, cfg,
                toasts, modal, openModal,
                toggleTheme, applyTheme,
                openImport, askDelete, launch,
                openAddModel, removeModel, saveCfg,
                gameStatus, gameLoading, gameInputEnabled, gameInput, gamePlaceholder, gameProjectName,
                messages, msgContainer, showContinueHint,
                sendInput, backToLauncher, onMsgAreaClick,
                contrastColor, colorBubble,
            };
        },
    }).mount('#app');
});
