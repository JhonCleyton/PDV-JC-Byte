// Função para animar mudança de valores
function animateValue(element, oldValue, newValue) {
    if (!element) return;
    
    // Remove classe anterior
    element.classList.remove('changed');
    
    // Força reflow para reiniciar animação
    void element.offsetWidth;
    
    // Adiciona classe para animar
    element.classList.add('changed');
    
    // Atualiza o valor
    if (typeof newValue === 'number') {
        const isMonetary = element.textContent.includes('R$');
        element.textContent = isMonetary ? `R$ ${newValue.toFixed(2)}` : newValue;
    } else {
        element.textContent = newValue;
    }
}

// Função para verificar se a resposta é um redirecionamento para o login
function isLoginRedirect(response) {
    return response.redirected || response.url.includes('/login');
}

// Atualiza os dados do dashboard
function updateDashboard() {
    console.log('Atualizando dashboard...');
    fetch('/management/api/dashboard/today', {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            console.log('Resposta recebida:', response);
            if (isLoginRedirect(response)) {
                console.log('Redirecionando para login...');
                window.location.href = '/login';
                return Promise.reject('Sessão expirada');
            }
            return response.json();
        })
        .then(data => {
            console.log('Dados recebidos:', data);
            if (data.success) {
                // Atualiza os cards
                const elements = {
                    'today-sales': data.data.sales,
                    'last-7-days-sales': data.data.sales_last_7_days,
                    'active-customers': data.data.active_customers,
                    'low-stock': data.data.low_stock,
                    'total-receivables': data.data.receivables,
                    'total-payables': data.data.payables
                };

                // Atualiza cada elemento se ele existir
                Object.entries(elements).forEach(([id, value]) => {
                    const element = document.getElementById(id);
                    if (element) {
                        const oldValue = element.textContent;
                        console.log(`Atualizando ${id}:`, oldValue, '->', value);
                        animateValue(element, oldValue, value);
                    }
                });
            } else {
                console.error('Erro nos dados:', data.error);
            }
        })
        .catch(error => {
            if (error !== 'Sessão expirada') {
                console.error('Erro ao atualizar dashboard:', error);
            }
        });
}

// Atualiza as últimas vendas
function updateRecentSales() {
    fetch('/management/api/dashboard/recent', {
        credentials: 'include'
    })
        .then(response => {
            if (isLoginRedirect(response)) {
                window.location.reload();
                return Promise.reject('Sessão expirada');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#recent-sales tbody');
                if (tbody) {
                    // Salva o scroll atual
                    const scrollPos = tbody.parentElement.scrollTop;
                    
                    tbody.innerHTML = '';
                    
                    data.data.forEach(sale => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>
                                <div class="d-flex px-2 py-1">
                                    <div class="d-flex flex-column justify-content-center">
                                        <h6 class="mb-0 text-sm">${new Date(sale.date).toLocaleDateString()}</h6>
                                        <p class="text-xs text-secondary mb-0">${new Date(sale.date).toLocaleTimeString()}</p>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <div class="d-flex px-2 py-1">
                                    <div class="d-flex flex-column justify-content-center">
                                        <h6 class="mb-0 text-sm">${sale.customer ? sale.customer.name : 'Cliente não identificado'}</h6>
                                        ${sale.customer ? `<p class="text-xs text-secondary mb-0">${sale.customer.registration_number || ''}</p>` : ''}
                                    </div>
                                </div>
                            </td>
                            <td class="text-end">
                                <p class="text-sm font-weight-bold mb-0">R$ ${sale.total.toFixed(2)}</p>
                            </td>
                            <td>
                                <span class="badge badge-sm bg-gradient-${sale.status === 'completed' ? 'success' : 'warning'}">
                                    ${sale.status === 'completed' ? 'Concluída' : 'Pendente'}
                                </span>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                    
                    // Restaura o scroll
                    tbody.parentElement.scrollTop = scrollPos;
                }
            }
        })
        .catch(error => {
            if (error !== 'Sessão expirada') {
                console.error('Erro ao atualizar vendas recentes:', error);
            }
        });
}

// Atualiza os produtos mais vendidos
function updateTopProducts() {
    fetch('/management/api/dashboard/top-selling', {
        credentials: 'include'
    })
        .then(response => {
            if (isLoginRedirect(response)) {
                window.location.reload();
                return Promise.reject('Sessão expirada');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#top-products tbody');
                if (tbody) {
                    // Salva o scroll atual
                    const scrollPos = tbody.parentElement.scrollTop;
                    
                    tbody.innerHTML = '';
                    
                    data.data.forEach(item => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>
                                <div class="d-flex px-2 py-1">
                                    <div class="d-flex flex-column justify-content-center">
                                        <h6 class="mb-0 text-sm">${item.product.name}</h6>
                                        <p class="text-xs text-secondary mb-0">Código: ${item.product.code || 'N/A'}</p>
                                    </div>
                                </div>
                            </td>
                            <td class="text-end">
                                <p class="text-sm font-weight-bold mb-0">${item.total_quantity.toFixed(2)}</p>
                            </td>
                            <td class="text-end">
                                <p class="text-sm font-weight-bold mb-0">R$ ${item.total_amount.toFixed(2)}</p>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                    
                    // Restaura o scroll
                    tbody.parentElement.scrollTop = scrollPos;
                }
            }
        })
        .catch(error => {
            if (error !== 'Sessão expirada') {
                console.error('Erro ao atualizar produtos mais vendidos:', error);
            }
        });
}

// Atualiza o dashboard a cada 30 segundos
document.addEventListener('DOMContentLoaded', function() {
    // Primeira atualização
    updateDashboard();
    updateRecentSales();
    updateTopProducts();
    
    // Atualizações periódicas
    setInterval(() => {
        updateDashboard();
        updateRecentSales();
        updateTopProducts();
    }, 30000);
});
