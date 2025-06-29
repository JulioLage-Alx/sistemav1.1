// ========================================
// SISTEMA DE CREDIÁRIO - AÇOUGUE
// JavaScript Principal
// ========================================

// Variáveis globais
let isLoading = false;
let currentNotifications = [];

// ========================================
// INICIALIZAÇÃO
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Sistema iniciado...');
    initializeSystem();
});

function initializeSystem() {
    // Configurar eventos globais
    setupGlobalEvents();
    
    // Configurar modais
    setupModals();
    
    // Configurar notificações
    setupNotifications();
    
    // Configurar máscaras de input
    setupInputMasks();
    
    // Auto-save em formulários (opcional)
    setupAutoSave();
    
    console.log('Sistema inicializado com sucesso!');
}

// ========================================
// EVENTOS GLOBAIS
// ========================================

function setupGlobalEvents() {
    // Escape para fechar modais
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
    
    // Prevenir submit duplo em formulários
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.dataset.submitting === 'true') {
            e.preventDefault();
            return false;
        }
        form.dataset.submitting = 'true';
        
        // Reset após 3 segundos
        setTimeout(() => {
            form.dataset.submitting = 'false';
        }, 3000);
    });
    
    // Auto-logout após inatividade (30 minutos)
    let inactivityTimer;
    function resetInactivityTimer() {
        clearTimeout(inactivityTimer);
        inactivityTimer = setTimeout(() => {
            if (window.location.pathname !== '/login') {
                mostrarNotificacao('Sessão expirada por inatividade', 'warning');
                setTimeout(() => {
                    window.location.href = '/logout';
                }, 2000);
            }
        }, 30 * 60 * 1000); // 30 minutos
    }
    
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
        document.addEventListener(event, resetInactivityTimer, true);
    });
    
    resetInactivityTimer();
}

// ========================================
// SISTEMA DE MODAIS
// ========================================

function setupModals() {
    // Fechar modal ao clicar fora
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            closeModal(e.target.id);
        }
    });
}

function abrirModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Focar no primeiro input se houver
        const firstInput = modal.querySelector('input, select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
        
        // Adicionar evento de escape específico
        modal.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal(modalId);
            }
        });
    }
}

function fecharModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        
        // Limpar dados do formulário se necessário
        const form = modal.querySelector('form');
        if (form && form.dataset.clearOnClose !== 'false') {
            form.reset();
        }
    }
}

function closeModal(modalId) {
    fecharModal(modalId);
}

function closeAllModals() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (modal.style.display === 'block') {
            fecharModal(modal.id);
        }
    });
}

// ========================================
// SISTEMA DE NOTIFICAÇÕES
// ========================================

function setupNotifications() {
    // Container para notificações
    if (!document.getElementById('notificationsContainer')) {
        const container = document.createElement('div');
        container.id = 'notificationsContainer';
        container.style.cssText = `
            position: fixed;
            top: 2rem;
            right: 2rem;
            z-index: 2000;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
}

function mostrarNotificacao(mensagem, tipo = 'info', duracao = 5000) {
    const container = document.getElementById('notificationsContainer');
    if (!container) return;
    
    const id = 'notif_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    const notification = document.createElement('div');
    notification.id = id;
    notification.className = `notification ${tipo}`;
    notification.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>${mensagem}</span>
            <button onclick="removerNotificacao('${id}')" style="background: none; border: none; color: inherit; cursor: pointer; font-size: 1.2rem; padding: 0 0 0 1rem;">×</button>
        </div>
    `;
    
    container.appendChild(notification);
    currentNotifications.push(id);
    
    // Auto-remover após duração especificada
    if (duracao > 0) {
        setTimeout(() => {
            removerNotificacao(id);
        }, duracao);
    }
    
    // Limitar número de notificações simultâneas
    if (currentNotifications.length > 5) {
        removerNotificacao(currentNotifications[0]);
    }
}

function removerNotificacao(id) {
    const notification = document.getElementById(id);
    if (notification) {
        notification.style.animation = 'slideOutRight 0.3s ease forwards';
        setTimeout(() => {
            notification.remove();
            currentNotifications = currentNotifications.filter(notifId => notifId !== id);
        }, 300);
    }
}

// ========================================
// SISTEMA DE LOADING
// ========================================

function mostrarLoading(texto = 'Carregando...') {
    if (isLoading) return;
    
    isLoading = true;
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        const textElement = overlay.querySelector('.loading-text');
        if (textElement) {
            textElement.textContent = texto;
        }
        overlay.style.display = 'flex';
    }
}

function esconderLoading() {
    isLoading = false;
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// ========================================
// MÁSCARAS DE INPUT
// ========================================

function setupInputMasks() {
    // Máscara de CPF
    document.addEventListener('input', function(e) {
        if (e.target.dataset.mask === 'cpf') {
            e.target.value = aplicarMascaraCPF(e.target.value);
        }
    });
    
    // Máscara de CNPJ
    document.addEventListener('input', function(e) {
        if (e.target.dataset.mask === 'cnpj') {
            e.target.value = aplicarMascaraCNPJ(e.target.value);
        }
    });
    
    // Máscara de telefone
    document.addEventListener('input', function(e) {
        if (e.target.dataset.mask === 'telefone') {
            e.target.value = aplicarMascaraTelefone(e.target.value);
        }
    });
    
    // Máscara de moeda
    document.addEventListener('input', function(e) {
        if (e.target.dataset.mask === 'moeda') {
            e.target.value = aplicarMascaraMoeda(e.target.value);
        }
    });
}

function aplicarMascaraCPF(valor) {
    valor = valor.replace(/\D/g, '');
    valor = valor.replace(/(\d{3})(\d)/, '$1.$2');
    valor = valor.replace(/(\d{3})(\d)/, '$1.$2');
    valor = valor.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    return valor;
}

function aplicarMascaraCNPJ(valor) {
    valor = valor.replace(/\D/g, '');
    valor = valor.replace(/(\d{2})(\d)/, '$1.$2');
    valor = valor.replace(/(\d{3})(\d)/, '$1.$2');
    valor = valor.replace(/(\d{3})(\d)/, '$1/$2');
    valor = valor.replace(/(\d{4})(\d{1,2})$/, '$1-$2');
    return valor;
}

function aplicarMascaraTelefone(valor) {
    valor = valor.replace(/\D/g, '');
    if (valor.length >= 11) {
        valor = valor.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    } else if (valor.length >= 10) {
        valor = valor.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    } else if (valor.length >= 6) {
        valor = valor.replace(/(\d{2})(\d{4})(\d)/, '($1) $2-$3');
    } else if (valor.length >= 2) {
        valor = valor.replace(/(\d{2})(\d)/, '($1) $2');
    }
    return valor;
}

function aplicarMascaraMoeda(valor) {
    valor = valor.replace(/\D/g, '');
    valor = valor.replace(/(\d)(\d{2})$/, '$1,$2');
    valor = valor.replace(/(?=(\d{3})+(\D))\B/g, '.');
    return valor;
}

// ========================================
// UTILITÁRIOS DE FORMATAÇÃO
// ========================================

function formatar_moeda(valor) {
    try {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    } catch {
        return `R$ ${parseFloat(valor || 0).toFixed(2).replace('.', ',')}`;
    }
}

function formatar_data(data) {
    try {
        if (!data) return '';
        if (typeof data === 'string') {
            data = new Date(data);
        }
        return data.toLocaleDateString('pt-BR');
    } catch {
        return data;
    }
}

function formatar_data_hora(data) {
    try {
        if (!data) return '';
        if (typeof data === 'string') {
            data = new Date(data);
        }
        return data.toLocaleString('pt-BR');
    } catch {
        return data;
    }
}

function formatar_telefone(telefone) {
    if (!telefone) return '';
    const limpo = telefone.replace(/\D/g, '');
    
    if (limpo.length === 11) {
        return `(${limpo.substr(0, 2)}) ${limpo.substr(2, 5)}-${limpo.substr(7)}`;
    } else if (limpo.length === 10) {
        return `(${limpo.substr(0, 2)}) ${limpo.substr(2, 4)}-${limpo.substr(6)}`;
    }
    
    return telefone;
}

function formatar_cpf(cpf) {
    if (!cpf) return '';
    const limpo = cpf.replace(/\D/g, '');
    
    if (limpo.length === 11) {
        return `${limpo.substr(0, 3)}.${limpo.substr(3, 3)}.${limpo.substr(6, 3)}-${limpo.substr(9)}`;
    }
    
    return cpf;
}

// ========================================
// VALIDAÇÕES
// ========================================

function validarCPF(cpf) {
    if (!cpf) return true; // CPF é opcional
    
    cpf = cpf.replace(/\D/g, '');
    
    if (cpf.length !== 11) return false;
    if (/^(\d)\1{10}$/.test(cpf)) return false;
    
    let soma = 0;
    for (let i = 0; i < 9; i++) {
        soma += parseInt(cpf.charAt(i)) * (10 - i);
    }
    let resto = 11 - (soma % 11);
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf.charAt(9))) return false;
    
    soma = 0;
    for (let i = 0; i < 10; i++) {
        soma += parseInt(cpf.charAt(i)) * (11 - i);
    }
    resto = 11 - (soma % 11);
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf.charAt(10))) return false;
    
    return true;
}

function validarEmail(email) {
    if (!email) return true; // Email é opcional
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function validarTelefone(telefone) {
    if (!telefone) return false;
    const limpo = telefone.replace(/\D/g, '');
    return limpo.length >= 10 && limpo.length <= 11;
}

function validarNumeroPositivo(valor) {
    const numero = parseFloat(valor);
    return !isNaN(numero) && numero > 0;
}

// ========================================
// NAVEGAÇÃO
// ========================================

function navegarPara(destino) {
    window.location.href = `/${destino}`;
}

function voltarPagina() {
    window.history.back();
}

function recarregarPagina() {
    window.location.reload();
}

// ========================================
// MENU MOBILE
// ========================================

function toggleMobileMenu() {
    const menu = document.querySelector('.nav-menu');
    if (menu) {
        menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
    }
}

// ========================================
// BUSCA GLOBAL
// ========================================

let searchTimeout;

function buscarGlobal(termo) {
    // Debounce para evitar muitas requisições
    clearTimeout(searchTimeout);
    
    if (termo.length < 2) {
        esconderResultadosBusca();
        return;
    }
    
    searchTimeout = setTimeout(() => {
        executarBuscaGlobal(termo);
    }, 300);
}

function executarBuscaGlobal(termo) {
    if (!termo || termo.length < 2) return;
    
    fetch(`/api/busca?q=${encodeURIComponent(termo)}`)
        .then(response => response.json())
        .then(data => {
            if (data.sucesso) {
                exibirResultadosBusca(data.resultados);
            } else {
                esconderResultadosBusca();
            }
        })
        .catch(error => {
            console.error('Erro na busca:', error);
            esconderResultadosBusca();
        });
}

function exibirResultadosBusca(resultados) {
    const container = document.getElementById('searchResults');
    if (!container) return;
    
    if (!resultados.clientes.length && !resultados.vendas.length) {
        container.innerHTML = '<div style="padding: 1rem; text-align: center; color: #6b7280;">Nenhum resultado encontrado</div>';
        container.style.display = 'block';
        return;
    }
    
    let html = '';
    
    if (resultados.clientes.length > 0) {
        html += '<div style="padding: 0.5rem 1rem; background: #f3f4f6; font-weight: 600; color: #374151;">Clientes</div>';
        resultados.clientes.forEach(cliente => {
            html += `
                <div style="padding: 0.75rem 1rem; border-bottom: 1px solid #e5e7eb; cursor: pointer; transition: background 0.2s;" 
                     onmouseover="this.style.background='#f9fafb'" 
                     onmouseout="this.style.background='white'"
                     onclick="navegarPara('clientes'); esconderResultadosBusca();">
                    <div style="font-weight: 500; color: #1f2937;">${cliente.nome}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">${cliente.telefone} - ${cliente.saldo_devedor_formatado} em aberto</div>
                </div>
            `;
        });
    }
    
    if (resultados.vendas.length > 0) {
        html += '<div style="padding: 0.5rem 1rem; background: #f3f4f6; font-weight: 600; color: #374151;">Vendas</div>';
        resultados.vendas.forEach(venda => {
            html += `
                <div style="padding: 0.75rem 1rem; border-bottom: 1px solid #e5e7eb; cursor: pointer; transition: background 0.2s;" 
                     onmouseover="this.style.background='#f9fafb'" 
                     onmouseout="this.style.background='white'"
                     onclick="navegarPara('vendas?venda_id=${venda.id}'); esconderResultadosBusca();">
                    <div style="font-weight: 500; color: #1f2937;">Venda #${venda.id} - ${venda.cliente_nome}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">${venda.valor_total_formatado} - ${venda.status_texto}</div>
                </div>
            `;
        });
    }
    
    container.innerHTML = html;
    container.style.display = 'block';
}

function esconderResultadosBusca() {
    const container = document.getElementById('searchResults');
    if (container) {
        container.style.display = 'none';
    }
}

function executarBusca() {
    const input = document.getElementById('searchGlobal');
    if (input && input.value.trim()) {
        executarBuscaGlobal(input.value.trim());
    }
}

// Esconder resultados ao clicar fora
document.addEventListener('click', function(e) {
    const container = document.getElementById('searchResults');
    const input = document.getElementById('searchGlobal');
    
    if (container && input && !container.contains(e.target) && e.target !== input) {
        esconderResultadosBusca();
    }
});

// ========================================
// AUTO-SAVE (OPCIONAL)
// ========================================

function setupAutoSave() {
    // Auto-save para formulários grandes (opcional)
    const formsToAutoSave = document.querySelectorAll('[data-autosave="true"]');
    
    formsToAutoSave.forEach(form => {
        const formId = form.id;
        if (!formId) return;
        
        // Carregar dados salvos
        loadAutoSavedData(form);
        
        // Salvar a cada mudança
        form.addEventListener('input', debounce(() => {
            saveFormData(form);
        }, 1000));
    });
}

function saveFormData(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    try {
        localStorage.setItem(`autosave_${form.id}`, JSON.stringify(data));
    } catch (error) {
        console.warn('Erro ao salvar dados automaticamente:', error);
    }
}

function loadAutoSavedData(form) {
    try {
        const savedData = localStorage.getItem(`autosave_${form.id}`);
        if (savedData) {
            const data = JSON.parse(savedData);
            
            Object.keys(data).forEach(name => {
                const field = form.querySelector(`[name="${name}"]`);
                if (field && data[name]) {
                    field.value = data[name];
                }
            });
        }
    } catch (error) {
        console.warn('Erro ao carregar dados salvos:', error);
    }
}

function clearAutoSavedData(formId) {
    try {
        localStorage.removeItem(`autosave_${formId}`);
    } catch (error) {
        console.warn('Erro ao limpar dados salvos:', error);
    }
}

// ========================================
// UTILITÁRIOS GERAIS
// ========================================

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            mostrarNotificacao('Copiado para a área de transferência!', 'success', 2000);
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        mostrarNotificacao('Copiado para a área de transferência!', 'success', 2000);
    } catch (err) {
        mostrarNotificacao('Erro ao copiar texto', 'error');
    }
    
    document.body.removeChild(textArea);
}

function formatarNumero(numero, casasDecimais = 2) {
    return parseFloat(numero || 0).toFixed(casasDecimais);
}

function gerarId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function isValidDate(date) {
    return date instanceof Date && !isNaN(date);
}

function calcularIdade(dataNascimento) {
    const hoje = new Date();
    const nascimento = new Date(dataNascimento);
    let idade = hoje.getFullYear() - nascimento.getFullYear();
    const m = hoje.getMonth() - nascimento.getMonth();
    
    if (m < 0 || (m === 0 && hoje.getDate() < nascimento.getDate())) {
        idade--;
    }
    
    return idade;
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ========================================
// HANDLERS DE ERRO GLOBAIS
// ========================================

window.addEventListener('error', function(event) {
    console.error('Erro JavaScript:', event.error);
    
    // Em produção, você pode querer enviar erros para um serviço de logging
    if (event.error && event.error.message) {
        mostrarNotificacao('Ocorreu um erro inesperado. Tente recarregar a página.', 'error');
    }
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Promise rejeitada:', event.reason);
    
    // Prevent default browser behavior
    event.preventDefault();
    
    mostrarNotificacao('Erro de conexão. Verifique sua internet.', 'error');
});

// ========================================
// CONEXÃO COM API
// ========================================

async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Erro na requisição:', error);
        throw error;
    }
}

// ========================================
// SHORTCUTS DE TECLADO
// ========================================

document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K para busca rápida
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('searchGlobal');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
    
    // Ctrl/Cmd + N para nova venda (se estiver na página certa)
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        if (window.location.pathname.includes('vendas')) {
            e.preventDefault();
            if (typeof abrirModalNovaVenda === 'function') {
                abrirModalNovaVenda();
            }
        }
    }
    
    // F5 ou Ctrl/Cmd + R para atualizar dados (não a página)
    if (e.key === 'F5' || ((e.ctrlKey || e.metaKey) && e.key === 'r')) {
        if (typeof atualizarDados === 'function') {
            e.preventDefault();
            atualizarDados();
        }
    }
});

// ========================================
// PERFORMANCE E OTIMIZAÇÕES
// ========================================

// Lazy loading para imagens (se houver)
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// Service Worker para cache (opcional, para modo offline)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // Primeiro verificar se o service worker existe
        fetch('/sw.js')
            .then(response => {
                if (response.ok) {
                    return navigator.serviceWorker.register('/sw.js');
                } else {
                    console.log('Service Worker não encontrado, continuando sem cache offline');
                    return null;
                }
            })
            .then(registration => {
                if (registration) {
                    console.log('SW registered: ', registration);
                }
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}

// ========================================
// ANALYTICS (OPCIONAL)
// ========================================

function trackEvent(eventName, eventData = {}) {
    // Implementar tracking se necessário
    console.log('Event tracked:', eventName, eventData);
}

// ========================================
// EXPORTAÇÃO PARA OUTROS SCRIPTS
// ========================================

// Disponibilizar funções globalmente se necessário
window.SistemaAcougue = {
    mostrarNotificacao,
    mostrarLoading,
    esconderLoading,
    abrirModal,
    fecharModal,
    formatar_moeda,
    formatar_data,
    validarCPF,
    validarEmail,
    navegarPara,
    apiRequest,
    trackEvent
};

console.log('Main.js carregado com sucesso!');