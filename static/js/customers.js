// Variáveis globais
let allCustomers = [];
let selectedCustomer = null;
const detailsModal = new bootstrap.Modal(document.getElementById('detailsModal'));
const saleDetailsModal = new bootstrap.Modal(document.getElementById('saleDetailsModal'));

// Funções de manipulação do DOM
const showAlert = (message, type = 'success') => {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.getElementById('alerts').appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
};

const toggleForm = show => {
    const form = document.getElementById('customerForm');
    form.style.display = show ? 'block' : 'none';
    if (!show) {
        form.reset();
        selectedCustomer = null;
    }
    document.getElementById('customersTable').parentElement.style.display = show ? 'none' : 'block';
};

const updateCustomerRow = customer => {
    const row = document.querySelector(`tr[data-id="${customer.id}"]`);
    if (row) {
        row.innerHTML = createCustomerRow(customer);
        addRowEventListeners(row);
    } else {
        const tbody = document.querySelector('#customersTable tbody');
        const newRow = document.createElement('tr');
        newRow.dataset.id = customer.id;
        newRow.innerHTML = createCustomerRow(customer);
        addRowEventListeners(newRow);
        tbody.appendChild(newRow);
    }
};

const addRowEventListeners = row => {
    // Botão Visualizar
    row.querySelector('.view-details').addEventListener('click', async () => {
        const id = row.dataset.id;
        try {
            const response = await fetch(`/api/clientes/${id}`);
            const result = await response.json();
            
            if (result.success) {
                const customer = result.data;
                fillCustomerDetails(customer);
                detailsModal.show();
                loadCustomerHistory(customer.id);
            } else {
                showAlert(result.message || 'Erro ao carregar cliente', 'danger');
            }
        } catch (error) {
            console.error('Erro ao carregar cliente:', error);
            showAlert('Erro ao carregar cliente', 'danger');
        }
    });
    
    // Botão Editar
    row.querySelector('.edit-customer').addEventListener('click', async () => {
        const id = row.dataset.id;
        try {
            const response = await fetch(`/api/clientes/${id}`);
            const result = await response.json();
            
            if (result.success) {
                selectedCustomer = result.data;
                fillCustomerForm(selectedCustomer);
                toggleForm(true);
            } else {
                showAlert(result.message || 'Erro ao carregar cliente', 'danger');
            }
        } catch (error) {
            console.error('Erro ao carregar cliente:', error);
            showAlert('Erro ao carregar cliente', 'danger');
        }
    });
    
    // Botão Excluir
    row.querySelector('.delete-customer').addEventListener('click', () => {
        const id = row.dataset.id;
        deleteCustomer(id);
    });
};

const updateTableEventListeners = () => {
    const rows = document.querySelectorAll('#customersTable tbody tr');
    rows.forEach(addRowEventListeners);
};

const createCustomerRow = customer => {
    const statusClass = customer.status === 'active' ? 'success' : 'danger';
    const statusText = customer.status === 'active' ? 'Ativo' : 'Bloqueado';
    
    return `
        <td>${customer.registration || ''}</td>
        <td>${customer.name}</td>
        <td>${customer.cpf || ''}</td>
        <td>${customer.phone || ''}</td>
        <td class="text-end">${utils.formatMoney(customer.credit_limit)}</td>
        <td class="text-end">${utils.formatMoney(customer.current_debt)}</td>
        <td><span class="badge bg-${statusClass}">${statusText}</span></td>
        <td>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-primary view-details" data-id="${customer.id}">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-outline-secondary edit-customer" data-id="${customer.id}">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-outline-danger delete-customer" data-id="${customer.id}">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </td>
    `;
};

const fillCustomerForm = customer => {
    const form = document.getElementById('customerForm');
    form.querySelector('#name').value = customer.name;
    form.querySelector('#cpf').value = customer.cpf || '';
    form.querySelector('#email').value = customer.email || '';
    form.querySelector('#phone').value = customer.phone || '';
    form.querySelector('#address').value = customer.address || '';
    form.querySelector('#credit_limit').value = customer.credit_limit || 0;
    form.querySelector('#status').value = customer.status || 'active';
};

const fillCustomerDetails = customer => {
    // Informações pessoais
    document.getElementById('detail-name').textContent = customer.name;
    document.getElementById('detail-cpf').textContent = customer.cpf || '-';
    document.getElementById('detail-email').textContent = customer.email || '-';
    document.getElementById('detail-phone').textContent = customer.phone || '-';
    document.getElementById('detail-address').textContent = customer.address || '-';
    
    // Informações financeiras
    document.getElementById('detail-credit-limit').textContent = utils.formatMoney(customer.credit_limit);
    document.getElementById('detail-current-debt').textContent = utils.formatMoney(customer.current_debt);
    
    const statusClass = customer.status === 'active' ? 'success' : 'danger';
    const statusText = customer.status === 'active' ? 'Ativo' : 'Bloqueado';
    document.getElementById('detail-status').innerHTML = `<span class="badge bg-${statusClass}">${statusText}</span>`;
    
    // Armazena o ID do cliente no modal para uso posterior
    document.getElementById('detailsModal').dataset.customerId = customer.id;
};

const fillSaleDetails = async saleId => {
    try {
        const response = await fetch(`/api/sales/${saleId}`);
        const result = await response.json();
        
        if (result.success && result.data) {
            const sale = result.data;
            console.log('Sale data:', sale); // Para debug
            
            // Preenche as informações da venda
            document.getElementById('sale-date').textContent = utils.formatDateTime(sale.date);
            document.getElementById('sale-total').textContent = utils.formatMoney(sale.total || 0);
            document.getElementById('sale-payment').textContent = sale.payment_method === 'crediario' ? 'Crediário' : 'À Vista';
            
            // Preenche a tabela de itens
            const tbody = document.querySelector('#saleItemsTable tbody');
            tbody.innerHTML = '';
            
            if (sale.items && sale.items.length > 0) {
                let total = 0;
                sale.items.forEach(item => {
                    const tr = document.createElement('tr');
                    const itemTotal = (item.quantity || 0) * (item.price || 0);
                    total += itemTotal;
                    
                    tr.innerHTML = `
                        <td>${item.product_code || '-'}</td>
                        <td>${item.product_name || '-'}</td>
                        <td>${item.quantity || 0}</td>
                        <td>${item.unit || 'un'}</td>
                        <td class="text-end">${utils.formatMoney(item.price || 0)}</td>
                        <td class="text-end">${utils.formatMoney(itemTotal)}</td>
                    `;
                    tbody.appendChild(tr);
                });
                
                // Atualiza o total da venda
                document.getElementById('sale-total').textContent = utils.formatMoney(total);
            } else {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhum item encontrado</td></tr>';
            }
            
            // Se for venda a prazo, mostra as parcelas
            const receivablesDiv = document.getElementById('sale-receivables');
            const receivablesTable = document.querySelector('#saleReceivablesTable tbody');
            
            if (sale.payment_method === 'crediario' && sale.receivables && sale.receivables.length > 0) {
                receivablesDiv.style.display = 'block';
                receivablesTable.innerHTML = '';
                
                sale.receivables.forEach(receivable => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${utils.formatDate(receivable.due_date)}</td>
                        <td class="text-end">${utils.formatMoney(receivable.amount || 0)}</td>
                        <td class="text-end">${utils.formatMoney(receivable.remaining_amount || 0)}</td>
                        <td><span class="badge bg-${receivable.status === 'paid' ? 'success' : 'warning'}">${receivable.status === 'paid' ? 'Pago' : 'Pendente'}</span></td>
                    `;
                    receivablesTable.appendChild(tr);
                });
            } else {
                receivablesDiv.style.display = 'none';
            }
            
            // Mostra o modal
            saleDetailsModal.show();
        } else {
            showAlert('Erro ao carregar detalhes da venda: ' + (result.error || 'Erro desconhecido'), 'danger');
        }
    } catch (error) {
        console.error('Erro ao carregar detalhes da venda:', error);
        showAlert('Erro ao carregar detalhes da venda', 'danger');
    }
};

// Funções de API
const loadCustomers = async () => {
    try {
        const response = await fetch('/api/clientes');
        const result = await response.json();
        
        if (result.success) {
            allCustomers = result.data;
            const tbody = document.querySelector('#customersTable tbody');
            tbody.innerHTML = '';
            
            allCustomers.forEach(customer => {
                const tr = document.createElement('tr');
                tr.dataset.id = customer.id;
                tr.innerHTML = createCustomerRow(customer);
                addRowEventListeners(tr);
                tbody.appendChild(tr);
            });
        } else {
            showAlert(result.message || 'Erro ao carregar clientes', 'danger');
        }
    } catch (error) {
        console.error('Erro ao carregar clientes:', error);
        showAlert('Erro ao carregar clientes', 'danger');
    }
};

const saveCustomer = async event => {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const customer = Object.fromEntries(formData.entries());
    
    // Validações
    if (!customer.name) {
        showAlert('Nome é obrigatório', 'danger');
        return;
    }
    
    try {
        const url = selectedCustomer ? `/api/clientes/${selectedCustomer.id}` : '/api/clientes';
        const method = selectedCustomer ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(customer)
        });
        
        const result = await response.json();
        
        if (result.success) {
            const customer = result.data || result.cliente;
            updateCustomerRow(customer);
            toggleForm(false);
            showAlert('Cliente salvo com sucesso');
        } else {
            showAlert(result.error || 'Erro ao salvar cliente', 'danger');
        }
    } catch (error) {
        console.error('Erro ao salvar cliente:', error);
        showAlert('Erro ao salvar cliente', 'danger');
    }
};

const deleteCustomer = async id => {
    if (!confirm('Tem certeza que deseja excluir este cliente?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/clientes/${id}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('Cliente excluído com sucesso!');
            const row = document.querySelector(`tr[data-id="${id}"]`);
            if (row) row.remove();
            allCustomers = allCustomers.filter(c => c.id !== id);
        } else {
            showAlert(result.message || 'Erro ao excluir cliente', 'danger');
        }
    } catch (error) {
        console.error('Erro ao excluir cliente:', error);
        showAlert('Erro ao excluir cliente', 'danger');
    }
};

const editCustomer = async id => {
    try {
        const response = await fetch(`/api/clientes/${id}`);
        const result = await response.json();
        
        if (result.success) {
            selectedCustomer = result.data;
            document.getElementById('registration').value = selectedCustomer.registration || '';
            document.getElementById('name').value = selectedCustomer.name;
            document.getElementById('cpf').value = selectedCustomer.cpf || '';
            document.getElementById('email').value = selectedCustomer.email || '';
            document.getElementById('phone').value = selectedCustomer.phone || '';
            document.getElementById('address').value = selectedCustomer.address || '';
            document.getElementById('credit_limit').value = selectedCustomer.credit_limit || 0;
            document.getElementById('status').value = selectedCustomer.status;
            toggleForm(true);
        } else {
            showAlert('Erro ao carregar dados do cliente', 'danger');
        }
    } catch (error) {
        console.error('Erro ao carregar cliente:', error);
        showAlert('Erro ao carregar cliente', 'danger');
    }
};

const showDetails = async id => {
    try {
        const response = await fetch(`/api/clientes/${id}`);
        const result = await response.json();
        
        if (result.success) {
            fillCustomerDetails(result.data);
            detailsModal.show();
        } else {
            showAlert(result.message || 'Erro ao carregar detalhes do cliente', 'danger');
        }
    } catch (error) {
        console.error('Erro ao carregar detalhes do cliente:', error);
        showAlert('Erro ao carregar detalhes do cliente', 'danger');
    }
};

const loadCustomerHistory = async customerId => {
    try {
        // Carrega vendas e parcelas
        const response = await fetch(`/api/clientes/${customerId}/sales`);
        const result = await response.json();
        
        if (result.success && result.data) {
            const { sales = [], receivables = [] } = result.data;
            
            // Preenche a tabela de vendas
            const salesTbody = document.querySelector('#salesTable tbody');
            salesTbody.innerHTML = '';
            
            if (sales.length > 0) {
                sales.forEach(sale => {
                    // Calcula o total somando os itens
                    let total = 0;
                    if (sale.items && sale.items.length > 0) {
                        total = sale.items.reduce((acc, item) => {
                            const itemTotal = (item.quantity || 0) * (item.price || 0);
                            return acc + itemTotal;
                        }, 0);
                    }
                    
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${utils.formatDateTime(sale.date) || '-'}</td>
                        <td class="text-end">${utils.formatMoney(total)}</td>
                        <td>${sale.payment_method === 'crediario' ? 'Crediário' : 'À Vista'}</td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary view-sale" data-id="${sale.id}">
                                <i class="bi bi-eye"></i>
                            </button>
                        </td>
                    `;
                    salesTbody.appendChild(tr);
                    
                    // Adiciona event listener para visualizar detalhes da venda
                    tr.querySelector('.view-sale').addEventListener('click', () => {
                        fillSaleDetails(sale.id);
                    });
                });
            } else {
                salesTbody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhuma venda encontrada</td></tr>';
            }
            
            // Preenche a tabela de contas a receber
            const receivablesTbody = document.querySelector('#receivablesTable tbody');
            receivablesTbody.innerHTML = '';
            
            if (receivables.length > 0) {
                receivables.forEach(receivable => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${utils.formatDate(receivable.due_date)}</td>
                        <td class="text-end">${utils.formatMoney(receivable.amount || 0)}</td>
                        <td class="text-end">${utils.formatMoney(receivable.remaining_amount || 0)}</td>
                        <td><span class="badge bg-${receivable.status === 'paid' ? 'success' : 'warning'}">${receivable.status === 'paid' ? 'Pago' : 'Pendente'}</span></td>
                    `;
                    receivablesTbody.appendChild(tr);
                });
            } else {
                receivablesTbody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhuma conta a receber encontrada</td></tr>';
            }
        } else {
            showAlert('Erro ao carregar histórico: ' + (result.error || 'Erro desconhecido'), 'danger');
        }
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
        showAlert('Erro ao carregar histórico', 'danger');
    }
};

const showSaleDetails = async saleId => {
    try {
        const response = await fetch(`/api/sales/${saleId}`);
        const result = await response.json();
        
        if (result.success) {
            fillSaleDetails(saleId);
            saleDetailsModal.show();
        } else {
            showAlert(result.message || 'Erro ao carregar detalhes da venda', 'danger');
        }
    } catch (error) {
        console.error('Erro ao carregar detalhes da venda:', error);
        showAlert('Erro ao carregar detalhes da venda', 'danger');
    }
};

const payReceivable = async id => {
    if (!confirm('Confirmar recebimento?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/receivables/${id}/pay`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('Pagamento registrado com sucesso!');
            const customerId = document.querySelector('#detailsModal').dataset.customerId;
            loadCustomerHistory(customerId);
        } else {
            showAlert(result.message || 'Erro ao registrar pagamento', 'danger');
        }
    } catch (error) {
        console.error('Erro ao registrar pagamento:', error);
        showAlert('Erro ao registrar pagamento', 'danger');
    }
};

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadCustomers();
    
    // Botão Novo Cliente
    document.getElementById('newCustomerBtn').addEventListener('click', () => {
        selectedCustomer = null;
        document.getElementById('customerForm').reset();
        toggleForm(true);
    });
    
    // Botões Cancelar
    document.querySelectorAll('#cancelBtn').forEach(btn => {
        btn.addEventListener('click', () => toggleForm(false));
    });
    
    // Formulário
    document.getElementById('customerForm').addEventListener('submit', saveCustomer);
    
    // Filtro
    document.getElementById('search').addEventListener('input', event => {
        const search = event.target.value.toLowerCase();
        const tbody = document.querySelector('#customersTable tbody');
        const rows = tbody.getElementsByTagName('tr');
        
        for (const row of rows) {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(search) ? '' : 'none';
        }
    });
    
    // Atualiza os event listeners da tabela
    updateTableEventListeners();
});
