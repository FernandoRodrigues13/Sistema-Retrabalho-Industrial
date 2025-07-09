document.addEventListener('DOMContentLoaded', function() {
    // --- FUNÇÕES GLOBAIS ---
    const notificacaoContainer = document.getElementById('notificacao-container');
    function mostrarNotificacao(mensagem, tipo = 'info', duracao = 3500) { if (!notificacaoContainer) return; const notificacaoDiv = document.createElement('div'); notificacaoDiv.className = `notificacao ${tipo}`; notificacaoDiv.innerHTML = `<span>${mensagem}</span><button class="fechar-notificacao" aria-label="Fechar">×</button>`; notificacaoDiv.querySelector('.fechar-notificacao').onclick = () => removerNotificacao(notificacaoDiv); notificacaoContainer.appendChild(notificacaoDiv); requestAnimationFrame(() => { notificacaoDiv.classList.add('mostrar'); }); setTimeout(() => removerNotificacao(notificacaoDiv), duracao); }
    function removerNotificacao(notificacaoDiv) { if (!notificacaoDiv || !notificacaoDiv.parentElement) return; notificacaoDiv.classList.remove('mostrar'); notificacaoDiv.classList.add('saindo'); notificacaoDiv.addEventListener('transitionend', () => { if (notificacaoDiv.parentElement) { notificacaoDiv.remove(); } }, { once: true }); }
    
    // --- FUNÇÃO DE FETCH ATUALIZADA ---
    async function buscarDados(url) {
      try {
        const response = await fetch(url);
        if (response.status === 401) {
          // Sessão expirou ou não está logado, redireciona para a página de login
          window.location.href = '/login';
          return; // Para a execução
        }
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ erro: 'Erro desconhecido.' }));
          throw new Error(errorData.erro);
        }
        return await response.json();
      } catch (error) {
        throw new Error(error.message || 'Erro de conexão.');
      }
    }

    // --- NOVA FUNÇÃO PARA VERIFICAR LOGIN E ATUALIZAR HEADER ---
    async function verificarStatusLogin() {
        const nomeUsuarioSpan = document.getElementById('nome-usuario-logado');
        if (!nomeUsuarioSpan) return; // Se não houver o span, estamos na página de login

        try {
            const userInfo = await buscarDados('/api/user/info');
            if (userInfo && userInfo.nome) {
                nomeUsuarioSpan.textContent = `Olá, ${userInfo.nome}`;
            } else {
                window.location.href = '/logout';
            }
        } catch (error) {
            console.error("Erro ao buscar informações do usuário:", error);
            window.location.href = '/login';
        }
    }
    
    // --- LÓGICA DE INICIALIZAÇÃO ---
    const path = window.location.pathname;
    
    if (!path.includes('/login')) {
        // Se não for a página de login, verifica o status do login primeiro.
        verificarStatusLogin().then(() => {
            // Depois de verificar, inicializa a lógica da página correta
            if (path.includes('/cadastros')) {
                initCadastros();
            } else if (path.includes('/dashboard')) {
                initDashboard();
            } else { // Página padrão é apontamentos
                initApontamentos();
            }
        });
    }

    // --- INICIALIZAÇÃO DA PÁGINA DE APONTAMENTOS ---
    function initApontamentos() {
        const hdnApontamentoId = document.getElementById('hdnApontamentoId'); const txtMatricula = document.getElementById('txtMatriculaOperador'); const txtNomeOperador = document.getElementById('txtNomeOperador'); const txtIdProduto = document.getElementById('txtIdProduto'); const txtCodEntrada = document.getElementById('txtCodEntrada'); const txtDescricao = document.getElementById('txtDescricao'); const txtCodSaida = document.getElementById('txtCodSaida'); const txtBeneficiamento = document.getElementById('txtBeneficiamento'); const txtUnidade = document.getElementById('txtUnidade'); const txtIdSetor = document.getElementById('txtIdSetor'); const txtNomeSetor = document.getElementById('txtNomeSetor'); const txtIdMotivo = document.getElementById('txtIdMotivo'); const txtNomeMotivo = document.getElementById('txtNomeMotivo'); const txtQuantidade = document.getElementById('txtQuantidadeRetrabalho'); const btnSalvarApontamento = document.getElementById('btnSalvarApontamento'); const btnLimparFormulario = document.getElementById('btnLimparFormulario'); const corpoTabela = document.getElementById('corpoTabelaApontamentos'); const infoPagina = document.getElementById('infoPagina'); const btnPaginaAnterior = document.getElementById('btnPaginaAnterior'); const btnProximaPagina = document.getElementById('btnProximaPagina'); const filtroDataDe = document.getElementById('txtFiltroDataDe'); const filtroDataAte = document.getElementById('txtFiltroDataAte'); const filtroIdProduto = document.getElementById('txtFiltroIdProduto'); const btnAplicarFiltro = document.getElementById('btnAplicarFiltro'); const btnLimparFiltros = document.getElementById('btnLimparFiltros'); const btnExportarCSV = document.getElementById('btnExportarCSV');
        let estadoPagina = { atual: 1, itensPorPagina: 20 }, filtrosAtuais = {}, modoEdicao = false;
        const camposFluxo = [txtMatricula, txtIdProduto, txtIdSetor, txtIdMotivo, txtQuantidade, btnSalvarApontamento];
        function focarProximoCampo(campoAtual) { const i = camposFluxo.indexOf(campoAtual); if (i > -1 && i < camposFluxo.length - 1) { camposFluxo[i + 1].focus(); } }
        function limparFormularioApontamento() { document.getElementById('form-retrabalho').reset(); [txtNomeOperador, txtCodEntrada, txtDescricao, txtCodSaida, txtBeneficiamento, txtUnidade, txtNomeSetor, txtNomeMotivo].forEach(el => { if (el) el.value = ''; }); if (hdnApontamentoId) hdnApontamentoId.value = ''; modoEdicao = false; document.querySelector('#secao-cadastro-retrabalho h2').textContent = 'Registrar Novo Retrabalho'; btnSalvarApontamento.textContent = 'Registrar'; btnLimparFormulario.textContent = 'Limpar'; if (txtMatricula) txtMatricula.focus(); }
        async function buscarOperador() { if (txtNomeOperador) txtNomeOperador.value = ''; if (!txtMatricula.value) return; try { const data = await buscarDados(`/api/operador/${txtMatricula.value.trim()}`); txtNomeOperador.value = data.nome; focarProximoCampo(txtMatricula); } catch (error) { mostrarNotificacao(error.message, 'erro'); } }
        async function buscarProdutoPorId() { [txtCodEntrada, txtDescricao, txtCodSaida, txtBeneficiamento, txtUnidade].forEach(el => { if (el) el.value = '' }); if (!txtIdProduto.value) return; try { const data = await buscarDados(`/api/produto/${txtIdProduto.value.trim()}`); if(txtCodEntrada) txtCodEntrada.value = data.cod_entrada || ''; if(txtDescricao) txtDescricao.value = data.descricao || ''; if(txtCodSaida) txtCodSaida.value = data.cod_saida || ''; if(txtBeneficiamento) txtBeneficiamento.value = data.beneficiamento || ''; if(txtUnidade) txtUnidade.value = data.und || ''; focarProximoCampo(txtIdProduto); } catch (error) { mostrarNotificacao(error.message, 'erro'); } }
        async function buscarSetorPorId() { if (txtNomeSetor) txtNomeSetor.value = ''; if (!txtIdSetor.value) return; try { const data = await buscarDados(`/api/setor/${txtIdSetor.value.trim().toUpperCase()}`); txtNomeSetor.value = data.nome; focarProximoCampo(txtIdSetor); } catch (error) { mostrarNotificacao(error.message, 'erro'); } }
        async function buscarMotivoPorId() { if (txtNomeMotivo) txtNomeMotivo.value = ''; if (!txtIdMotivo.value) return; try { const data = await buscarDados(`/api/motivo/${txtIdMotivo.value.trim()}`); txtNomeMotivo.value = data.motivo; focarProximoCampo(txtIdMotivo); } catch (error) { mostrarNotificacao(error.message, 'erro'); } }
        async function salvarApontamento() { if (!txtNomeOperador.value || !txtCodEntrada.value || !txtNomeSetor.value || !txtNomeMotivo.value || !txtQuantidade.value || parseFloat(txtQuantidade.value) <= 0) { mostrarNotificacao("Preencha todos os campos corretamente.", "erro"); return; } const dados = { matriculaOperador: txtMatricula.value.trim(), codEntrada: txtCodEntrada.value.trim(), quantidade: parseFloat(txtQuantidade.value), setorId: txtIdSetor.value.trim(), motivoId: parseInt(txtIdMotivo.value) }; const idEdicao = hdnApontamentoId.value; const ehUpdate = idEdicao && modoEdicao; const url = ehUpdate ? `/api/apontamentos/retrabalho/${idEdicao}` : '/api/apontamentos/retrabalho'; const method = ehUpdate ? 'PUT' : 'POST'; fetch(url, { method: method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dados) }).then(response => { if (!response.ok) { return response.json().then(err => { throw new Error(err.erro || "Erro do servidor") }); } return response.json(); }).then(resultado => { mostrarNotificacao(resultado.mensagem, 'sucesso'); limparFormularioApontamento(); carregarApontamentosRetrabalho(ehUpdate ? estadoPagina.atual : 1); }).catch(e => { console.error("Falha ao salvar:", e); mostrarNotificacao(e.message, 'erro'); }); }
        async function carregarApontamentoParaEdicao(id) { try { const data = await buscarDados(`/api/apontamento/retrabalho/${id}`); hdnApontamentoId.value = data.id; txtMatricula.value = data.matricula_operador; txtNomeOperador.value = data.nome_operador; txtIdProduto.value = data.produto_id; txtCodEntrada.value = data.cod_entrada; txtDescricao.value = data.descricao_produto; txtCodSaida.value = data.cod_saida; txtBeneficiamento.value = data.beneficiamento; txtUnidade.value = data.und; txtIdSetor.value = data.setor_codigo; txtNomeSetor.value = data.nome_setor; txtIdMotivo.value = data.motivo_retrabalho_id; txtNomeMotivo.value = data.motivo_retrabalho; txtQuantidade.value = data.quantidade; modoEdicao = true; document.querySelector('#secao-cadastro-retrabalho h2').textContent = `Editando Apontamento #${id}`; btnSalvarApontamento.textContent = 'Salvar Alterações'; btnLimparFormulario.textContent = 'Cancelar Edição'; window.scrollTo({ top: 0, behavior: 'smooth' }); txtMatricula.focus(); } catch (error) { mostrarNotificacao(error.message, 'erro'); } }
        async function carregarApontamentosRetrabalho(pagina = 1) { if (!corpoTabela) return; corpoTabela.innerHTML = '<tr><td colspan="10" class="celula-mensagem-tabela">Carregando...</td></tr>'; filtrosAtuais = { dataDe: filtroDataDe.value, dataAte: filtroDataAte.value, idProduto: filtroIdProduto.value.trim() }; const params = new URLSearchParams({ page: pagina, per_page: estadoPagina.itensPorPagina }); for(const key in filtrosAtuais) { if(filtrosAtuais[key]) { params.append(key, filtrosAtuais[key]); } } try { const data = await buscarDados(`/api/apontamentos/retrabalho?${params.toString()}`); corpoTabela.innerHTML = ''; if (!data.items || data.items.length === 0) { corpoTabela.innerHTML = '<tr><td colspan="10" class="celula-mensagem-tabela">Nenhum apontamento encontrado.</td></tr>'; } else { data.items.forEach(ap => { corpoTabela.innerHTML += `<tr><td>${ap.data||''}</td><td>${ap.hora||''}</td><td>${ap.turno||''}</td><td>${ap.matricula_operador} - ${ap.nome_operador||''}</td><td>${ap.cod_entrada||''}</td><td>${ap.descricao_produto||''}</td><td>${ap.nome_setor||''}</td><td>${ap.motivo_retrabalho||''}</td><td>${ap.quantidade}</td><td class="acoes-tabela"><button class="btn-acao-tabela btn-editar" data-id="${ap.id}">Editar</button><button class="btn-acao-tabela btn-excluir" data-id="${ap.id}">Excluir</button></td></tr>`; }); } if(infoPagina) infoPagina.textContent = `Página ${data.current_page} de ${data.total_pages}`; if(btnPaginaAnterior) btnPaginaAnterior.disabled = !data.has_prev; if(btnProximaPagina) btnProximaPagina.disabled = !data.has_next; estadoPagina.atual = data.current_page; } catch (e) { corpoTabela.innerHTML = `<tr><td colspan="10" class="celula-mensagem-tabela">Falha ao carregar o histórico.</td></tr>`; mostrarNotificacao(e.message, 'erro'); } }
        async function exportarParaCSV() { const params = new URLSearchParams(filtrosAtuais); mostrarNotificacao('Gerando arquivo CSV...', 'info'); try { const response = await fetch(`/api/apontamentos/exportar?${params.toString()}`); if (!response.ok) throw new Error('Falha ao gerar o arquivo.'); const blob = await response.blob(); const url = window.URL.createObjectURL(blob); const a = document.createElement('a'); a.style.display = 'none'; a.href = url; const disposition = response.headers.get('Content-Disposition'); let filename = 'apontamentos.csv'; if (disposition && disposition.includes('attachment')) { const filenameMatch = disposition.match(/filename="?([^"]+)"?/); if (filenameMatch && filenameMatch[1]) { filename = filenameMatch[1]; } } a.download = filename; document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(url); a.remove(); } catch(error) { mostrarNotificacao('Erro ao gerar o arquivo CSV.', 'erro'); } }
        function configurarFluxoEnter() { const campos = [txtMatricula, txtIdProduto, txtIdSetor, txtIdMotivo, txtQuantidade, btnSalvarApontamento]; campos.forEach((campo) => { if (campo && campo.id !== 'btnSalvarApontamento') { campo.addEventListener('keydown', function(event) { if (event.key === 'Enter') { event.preventDefault(); campo.blur(); } }); } }); if(txtQuantidade) { txtQuantidade.addEventListener('keydown', (event) => { if(event.key === 'Enter') { event.preventDefault(); btnSalvarApontamento.focus(); btnSalvarApontamento.click(); } }); } }
        if(txtMatricula) txtMatricula.addEventListener('blur', buscarOperador);
        if(txtIdProduto) txtIdProduto.addEventListener('blur', buscarProdutoPorId);
        if(txtIdSetor) txtIdSetor.addEventListener('blur', buscarSetorPorId);
        if(txtIdMotivo) txtIdMotivo.addEventListener('blur', buscarMotivoPorId);
        if(btnSalvarApontamento) btnSalvarApontamento.addEventListener('click', salvarApontamento);
        if(btnLimparFormulario) btnLimparFormulario.addEventListener('click', limparFormularioApontamento);
        if(btnAplicarFiltro) btnAplicarFiltro.addEventListener('click', () => carregarApontamentosRetrabalho(1));
        if(btnLimparFiltros) btnLimparFiltros.addEventListener('click', () => { if(filtroDataDe) filtroDataDe.value = ''; if(filtroDataAte) filtroDataAte.value = ''; if(filtroIdProduto) filtroIdProduto.value = ''; carregarApontamentosRetrabalho(1); });
        if(btnExportarCSV) btnExportarCSV.addEventListener('click', exportarParaCSV);
        if(btnPaginaAnterior) btnPaginaAnterior.addEventListener('click', () => carregarApontamentosRetrabalho(estadoPagina.atual - 1));
        if(btnProximaPagina) btnProximaPagina.addEventListener('click', () => carregarApontamentosRetrabalho(estadoPagina.atual + 1));
        if(corpoTabela) corpoTabela.addEventListener('click', async (e) => { const target = e.target; const id = target.dataset.id; if (target.classList.contains('btn-editar')) { if (id) carregarApontamentoParaEdicao(id); } if (target.classList.contains('btn-excluir')) { if (id && confirm('Tem certeza?')) { try { const r = await fetch(`/api/apontamentos/retrabalho/${id}`, { method: 'DELETE' }); const d = await r.json(); if (!r.ok) { throw new Error(d.erro || "Erro ao excluir.") } mostrarNotificacao(d.mensagem, 'sucesso'); carregarApontamentosRetrabalho(estadoPagina.atual); } catch (err) { mostrarNotificacao(err.message, 'erro'); } } } });
        carregarApontamentosRetrabalho();
        configurarFluxoEnter();
    }
    
    // --- INICIALIZAÇÃO DA PÁGINA DE CADASTROS ---
    function initCadastros() {
        const abasBtn = document.querySelectorAll('.aba-btn'); const conteudosAbas = document.querySelectorAll('.conteudo-aba');
        abasBtn.forEach(btn => {
            btn.addEventListener('click', () => {
                abasBtn.forEach(b => b.classList.remove('active')); btn.classList.add('active');
                conteudosAbas.forEach(c => c.classList.remove('visivel'));
                const abaAtiva = document.getElementById(`conteudo-aba-${btn.dataset.aba}`);
                if (abaAtiva) abaAtiva.classList.add('visivel');
                if (btn.dataset.aba === 'operadores') carregarOperadores();
                if (btn.dataset.aba === 'produtos') carregarProdutos();
                if (btn.dataset.aba === 'setores') carregarSetores();
                if (btn.dataset.aba === 'motivos') carregarMotivos();
            });
        });
        const formOp = document.getElementById('form-operador'); const tabelaOp = document.getElementById('corpoTabelaOperadores'); const hdnMatriculaOriginal = document.getElementById('hdnMatriculaOriginal'); const txtOpMatricula = document.getElementById('txtOpMatricula'); const txtOpNome = document.getElementById('txtOpNome'); const btnSalvarOp = document.getElementById('btnSalvarOp'); const btnCancelarOp = document.getElementById('btnCancelarOp'); const tituloFormOp = document.querySelector('#conteudo-aba-operadores h2');
        async function carregarOperadores() { try { const operadores = await buscarDados('/api/operadores'); tabelaOp.innerHTML = ''; operadores.forEach(op => { tabelaOp.innerHTML += `<tr><td>${op.matricula}</td><td>${op.nome}</td><td class="acoes-tabela"><button class="btn-acao-tabela btn-editar" data-matricula="${op.matricula}" data-nome="${op.nome}">Editar</button><button class="btn-acao-tabela btn-excluir" data-matricula="${op.matricula}">Excluir</button></td></tr>`; }); } catch (error) { mostrarNotificacao(error.message, 'erro'); } }
        function limparFormOp() { formOp.reset(); hdnMatriculaOriginal.value = ''; tituloFormOp.textContent = 'Gerenciar Operadores'; btnSalvarOp.textContent = 'Adicionar'; btnCancelarOp.classList.add('oculto'); txtOpMatricula.readOnly = false; }
        formOp.addEventListener('submit', async (e) => { e.preventDefault(); const matriculaOriginal = hdnMatriculaOriginal.value; const ehEdicao = !!matriculaOriginal; const url = ehEdicao ? `/api/operadores/${matriculaOriginal}` : '/api/operadores'; const method = ehEdicao ? 'PUT' : 'POST'; try { const response = await fetch(url, { method: method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ matricula: txtOpMatricula.value, nome: txtOpNome.value }) }); const resultado = await response.json(); mostrarNotificacao(resultado.mensagem || resultado.erro, response.ok ? 'sucesso' : 'erro'); if (response.ok) { limparFormOp(); carregarOperadores(); } } catch (error) { mostrarNotificacao('Erro de conexão.', 'erro'); } });
        tabelaOp.addEventListener('click', (e) => { if (e.target.classList.contains('btn-editar')) { const matricula = e.target.dataset.matricula; const nome = e.target.dataset.nome; hdnMatriculaOriginal.value = matricula; txtOpMatricula.value = matricula; txtOpNome.value = nome; tituloFormOp.textContent = `Editando Operador: ${matricula}`; btnSalvarOp.textContent = 'Salvar'; btnCancelarOp.classList.remove('oculto'); txtOpMatricula.readOnly = true; } if (e.target.classList.contains('btn-excluir')) { const matricula = e.target.dataset.matricula; if (confirm(`Tem certeza?`)) { fetch(`/api/operadores/${matricula}`, { method: 'DELETE' }).then(r => r.json()).then(res => { mostrarNotificacao(res.mensagem || res.erro, res.erro ? 'erro' : 'sucesso'); carregarOperadores(); }); } } });
        if(btnCancelarOp) btnCancelarOp.addEventListener('click', limparFormOp);
        const tabelaProd = document.getElementById('corpoTabelaProdutos'); const paginacaoProdContainer = document.getElementById('paginacao-produtos'); const infoPaginaProd = document.getElementById('infoPaginaProd'); const btnProdPaginaAnterior = document.getElementById('btnProdPaginaAnterior'); const btnProdProximaPagina = document.getElementById('btnProdProximaPagina'); let estadoPaginaProd = { atual: 1 };
        async function carregarProdutos(pagina = 1) { if (!tabelaProd) return; tabelaProd.innerHTML = `<tr><td colspan="6" class="celula-mensagem-tabela">Carregando produtos...</td></tr>`; try { const data = await buscarDados(`/api/produtos?page=${pagina}`); tabelaProd.innerHTML = ''; if (!data.items || data.items.length === 0) { tabelaProd.innerHTML = `<tr><td colspan="6" class="celula-mensagem-tabela">Nenhum produto encontrado.</td></tr>`; paginacaoProdContainer.style.display = 'none'; } else { paginacaoProdContainer.style.display = 'flex'; data.items.forEach(p => { tabelaProd.innerHTML += `<tr><td>${p.id}</td><td>${p.cod_entrada}</td><td>${p.cod_saida || ''}</td><td>${p.descricao}</td><td>${p.beneficiamento || ''}</td><td>${p.und}</td></tr>`; }); estadoPaginaProd.atual = data.current_page; infoPaginaProd.textContent = `Página ${data.current_page} de ${data.total_pages}`; btnProdPaginaAnterior.disabled = !data.has_prev; btnProdProximaPagina.disabled = !data.has_next; } } catch (error) { mostrarNotificacao(error.message, 'erro'); tabelaProd.innerHTML = `<tr><td colspan="6" class="celula-mensagem-tabela">Erro ao carregar.</td></tr>`; } }
        if(btnProdPaginaAnterior) btnProdPaginaAnterior.addEventListener('click', () => { if (!btnProdPaginaAnterior.disabled) carregarProdutos(estadoPaginaProd.atual - 1); });
        if(btnProdProximaPagina) btnProdProximaPagina.addEventListener('click', () => { if (!btnProdProximaPagina.disabled) carregarProdutos(estadoPaginaProd.atual + 1); });
        const tabelaSetores = document.getElementById('corpoTabelaSetores'); const formSetor = document.getElementById('form-setor'); const hdnCodigoOriginalSetor = document.getElementById('hdnCodigoOriginalSetor'); const txtSetorCodigo = document.getElementById('txtSetorCodigo'); const txtSetorNome = document.getElementById('txtSetorNome'); const btnSalvarSetor = document.getElementById('btnSalvarSetor'); const btnCancelarSetor = document.getElementById('btnCancelarSetor'); const tituloFormSetor = document.querySelector('#conteudo-aba-setores h2');
        async function carregarSetores() { try { const setores = await buscarDados('/api/setores'); tabelaSetores.innerHTML = ''; setores.forEach(s => { tabelaSetores.innerHTML += `<tr><td>${s.codigo}</td><td>${s.nome}</td><td class="acoes-tabela"><button class="btn-acao-tabela btn-editar" data-codigo="${s.codigo}" data-nome="${s.nome}">Editar</button><button class="btn-acao-tabela btn-excluir" data-codigo="${s.codigo}">Excluir</button></td></tr>`; }); } catch (error) { mostrarNotificacao(error.message, 'erro'); } }
        function limparFormSetor() { formSetor.reset(); hdnCodigoOriginalSetor.value = ''; tituloFormSetor.textContent = 'Gerenciar Setores'; btnSalvarSetor.textContent = 'Adicionar'; btnCancelarSetor.classList.add('oculto'); txtSetorCodigo.readOnly = false; }
        formSetor.addEventListener('submit', async (e) => { e.preventDefault(); const codigoOriginal = hdnCodigoOriginalSetor.value; const ehEdicao = !!codigoOriginal; const url = ehEdicao ? `/api/setores/${codigoOriginal}` : '/api/setores'; const method = ehEdicao ? 'PUT' : 'POST'; try { const response = await fetch(url, { method: method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ codigo: txtSetorCodigo.value, nome: txtSetorNome.value }) }); const resultado = await response.json(); mostrarNotificacao(resultado.mensagem || resultado.erro, response.ok ? 'sucesso' : 'erro'); if (response.ok) { limparFormSetor(); carregarSetores(); } } catch (error) { mostrarNotificacao('Erro de conexão.', 'erro'); } });
        tabelaSetores.addEventListener('click', (e) => { if (e.target.classList.contains('btn-editar')) { const codigo = e.target.dataset.codigo; const nome = e.target.dataset.nome; hdnCodigoOriginalSetor.value = codigo; txtSetorCodigo.value = codigo; txtSetorNome.value = nome; tituloFormSetor.textContent = `Editando Setor: ${codigo}`; btnSalvarSetor.textContent = 'Salvar'; btnCancelarSetor.classList.remove('oculto'); txtSetorCodigo.readOnly = true; } if (e.target.classList.contains('btn-excluir')) { const codigo = e.target.dataset.codigo; if (confirm(`Tem certeza?`)) { fetch(`/api/setores/${codigo}`, { method: 'DELETE' }).then(r => r.json()).then(res => { mostrarNotificacao(res.mensagem || res.erro, res.erro ? 'erro' : 'sucesso'); carregarSetores(); }); } } });
        if(btnCancelarSetor) btnCancelarSetor.addEventListener('click', limparFormSetor);
        const formMotivo = document.getElementById('form-motivo'); const tabelaMotivos = document.getElementById('corpoTabelaMotivos'); const hdnIdOriginalMotivo = document.getElementById('hdnIdOriginalMotivo'); const txtMotivoId = document.getElementById('txtMotivoId'); const txtMotivoDescricao = document.getElementById('txtMotivoDescricao'); const btnSalvarMotivo = document.getElementById('btnSalvarMotivo'); const btnCancelarMotivo = document.getElementById('btnCancelarMotivo'); const tituloFormMotivo = document.querySelector('#conteudo-aba-motivos h2');
        async function carregarMotivos() { try { const motivos = await buscarDados('/api/motivos'); tabelaMotivos.innerHTML = ''; motivos.forEach(m => { tabelaMotivos.innerHTML += `<tr><td>${m.id}</td><td>${m.motivo}</td><td class="acoes-tabela"><button class="btn-acao-tabela btn-editar" data-id="${m.id}" data-motivo="${m.motivo}">Editar</button><button class="btn-acao-tabela btn-excluir" data-id="${m.id}">Excluir</button></td></tr>`; }); } catch (error) { mostrarNotificacao(error.message, 'erro'); } }
        function limparFormMotivo() { formMotivo.reset(); hdnIdOriginalMotivo.value = ''; tituloFormMotivo.textContent = 'Gerenciar Motivos'; btnSalvarMotivo.textContent = 'Adicionar'; btnCancelarMotivo.classList.add('oculto'); txtMotivoId.readOnly = false; }
        formMotivo.addEventListener('submit', async (e) => { e.preventDefault(); const idOriginal = hdnIdOriginalMotivo.value; const ehEdicao = !!idOriginal; const url = ehEdicao ? `/api/motivos/${idOriginal}` : '/api/motivos'; const method = ehEdicao ? 'PUT' : 'POST'; try { const response = await fetch(url, { method: method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ id: txtMotivoId.value, motivo: txtMotivoDescricao.value, id_novo: txtMotivoId.value }) }); const resultado = await response.json(); mostrarNotificacao(resultado.mensagem || resultado.erro, response.ok ? 'sucesso' : 'erro'); if (response.ok) { limparFormMotivo(); carregarMotivos(); } } catch (error) { mostrarNotificacao('Erro de conexão.', 'erro'); } });
        tabelaMotivos.addEventListener('click', (e) => { if (e.target.classList.contains('btn-editar')) { const id = e.target.dataset.id; const motivo = e.target.dataset.motivo; hdnIdOriginalMotivo.value = id; txtMotivoId.value = id; txtMotivoDescricao.value = motivo; tituloFormMotivo.textContent = `Editando Motivo #${id}`; btnSalvarMotivo.textContent = 'Salvar'; btnCancelarMotivo.classList.remove('oculto'); txtMotivoId.readOnly = true; } if (e.target.classList.contains('btn-excluir')) { const id = e.target.dataset.id; if (confirm(`Tem certeza?`)) { fetch(`/api/motivos/${id}`, { method: 'DELETE' }).then(r => r.json()).then(res => { mostrarNotificacao(res.mensagem || res.erro, res.erro ? 'erro' : 'sucesso'); carregarMotivos(); }); } } });
        if(btnCancelarMotivo) btnCancelarMotivo.addEventListener('click', limparFormMotivo);
        
        carregarOperadores();
    }
    
    // --- INICIALIZAÇÃO DA PÁGINA DO DASHBOARD ---
    function initDashboard() {
        if (typeof ChartDataLabels === 'undefined') { console.error("ChartDataLabels não foi carregado."); return; }
        Chart.register(ChartDataLabels);
        const elementos = { filtroPeriodo: document.getElementById('filtroPeriodoDashboard'), rangePersonalizado: document.getElementById('rangePersonalizado'), dataDe: document.getElementById('txtDataDashboardDe'), dataAte: document.getElementById('txtDataDashboardAte'), btnAtualizar: document.getElementById('btnAtualizarDashboard'), kpiQtdPecas: document.getElementById('kpiQtdPecas'), kpiQtdKg: document.getElementById('kpiQtdKg'), kpiValorTotal: document.getElementById('kpiValorTotal'), kpiTurno1: document.getElementById('kpiTurno1'), kpiTurno2: document.getElementById('kpiTurno2'), kpiTurno3: document.getElementById('kpiTurno3') };
        let charts = {};
        const formatDate = (date) => date.toISOString().split('T')[0];
        async function carregarDadosDashboard() {
            let dataDeStr, dataAteStr;
            const periodo = elementos.filtroPeriodo.value; const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
            elementos.rangePersonalizado.classList.toggle('oculto', periodo !== 'personalizado');
            if (periodo === 'hoje') { dataDeStr = dataAteStr = formatDate(hoje); } 
            else if (periodo === 'ultimos7dias') { dataAteStr = formatDate(hoje); const dataInicio = new Date(); dataInicio.setDate(hoje.getDate() - 6); dataDeStr = formatDate(dataInicio); } 
            else if (periodo === 'mesAtual') { dataAteStr = formatDate(hoje); const dataInicio = new Date(hoje.getFullYear(), hoje.getMonth(), 1); dataDeStr = formatDate(dataInicio); } 
            else if (periodo === 'personalizado') { if (!elementos.dataDe.value || !elementos.dataAte.value) { mostrarNotificacao('Selecione as datas.', 'aviso'); return; } dataDeStr = elementos.dataDe.value; dataAteStr = elementos.dataAte.value; }
            try {
                const data = await buscarDados(`/api/dashboard?dataDe=${dataDeStr}&dataAte=${dataAteStr}`);
                elementos.kpiQtdPecas.textContent = parseFloat(data.kpis.quantidade_pecas || 0).toLocaleString('pt-BR');
                elementos.kpiQtdKg.textContent = parseFloat(data.kpis.quantidade_kg || 0).toLocaleString('pt-BR');
                elementos.kpiValorTotal.textContent = parseFloat(data.kpis.valor_total || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
                const totalTurnos = (data.kpis.turno1_total || 0) + (data.kpis.turno2_total || 0) + (data.kpis.turno3_total || 0);
                elementos.kpiTurno1.textContent = totalTurnos > 0 ? `${((data.kpis.turno1_total / totalTurnos) * 100).toFixed(1)}%` : '0%';
                elementos.kpiTurno2.textContent = totalTurnos > 0 ? `${((data.kpis.turno2_total / totalTurnos) * 100).toFixed(1)}%` : '0%';
                elementos.kpiTurno3.textContent = totalTurnos > 0 ? `${((data.kpis.turno3_total / totalTurnos) * 100).toFixed(1)}%` : '0%';
                
                atualizarGrafico(charts, 'graficoProducaoSetor', { tipo: 'bar', dados: data.producao_por_setor, dataKey: 'total', labelKey: 'nome', cor: '#3498db', comLinha: true, formato: 'numero' });
                atualizarGrafico(charts, 'graficoTopProdutos', { tipo: 'bar', dados: data.top_produtos, dataKey: 'total', labelKey: 'cod_entrada', cor: '#2ecc71', comLinha: true, formato: 'numero' });
                atualizarGrafico(charts, 'graficoTopMotivos', { tipo: 'bar', dados: data.top_motivos, dataKey: 'total', labelKey: 'motivo', cor: '#e74c3c', comLinha: true, formato: 'numero' });
                atualizarGrafico(charts, 'graficoValorSetor', { tipo: 'bar', dados: data.valor_por_setor, dataKey: 'total_valor', labelKey: 'nome', cor: '#9b59b6', comLinha: true, formato: 'moeda' });
            } catch (error) { mostrarNotificacao(error.message, 'erro'); }
        }
        function atualizarGrafico(chartInstances, canvasId, config) {
            const ctx = document.getElementById(canvasId); if (!ctx) return;
            if (chartInstances[canvasId]) chartInstances[canvasId].destroy();
            const labels = config.dados.map(item => item[config.labelKey]);
            const dataValues = config.dados.map(item => item[config.dataKey]);
            const datasets = [{ type: 'bar', data: dataValues, backgroundColor: config.cor, barThickness: 40 }];
            if (config.comLinha) { datasets.push({ type: 'line', data: dataValues, borderColor: '#f1c40f', tension: 0.4, pointRadius: 0, datalabels: { display: false } }); }
            const options = { responsive: true, maintainAspectRatio: false, layout: { padding: { top: 30 } }, plugins: { legend: { display: false }, datalabels: { display: true, anchor: 'end', align: 'top', offset: 8, color: '#333', font: { weight: 'bold' }, formatter: (value) => { if (config.formato === 'moeda') return 'R$ ' + value.toLocaleString('pt-BR', {minimumFractionDigits: 2}); return value.toLocaleString('pt-BR'); } } }, scales: (config.tipo === 'bar') ? { x: { grid: { display: false } }, y: { display: false, beginAtZero: true, grace: '10%'} } : { x: { display: false }, y: { display: false } } };
            chartInstances[canvasId] = new Chart(ctx.getContext('2d'), { type: 'bar', data: { labels, datasets }, options });
        }
        
        elementos.filtroPeriodo.addEventListener('change', () => { if(elementos.filtroPeriodo.value !== 'personalizado') carregarDadosDashboard(); });
        elementos.btnAtualizar.addEventListener('click', carregarDadosDashboard);
        carregarDadosDashboard();
    }
});