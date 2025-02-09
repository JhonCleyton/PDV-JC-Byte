// Variáveis globais
let selectedCustomer = null;
let selectedProduct = null;
let saleItems = [];

// Função para formatar valores monetários
function formatMoney(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Função para formatar CPF
function formatCPF(cpf) {
    return cpf.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, "$1.$2.$3-$4");
}

// Função para formatar telefone
function formatPhone(phone) {
    return phone.replace(/^(\d{2})(\d{4,5})(\d{4})$/, "($1) $2-$3");
}

// Função para atualizar total da venda
function updateSaleTotal() {
    const total = saleItems.reduce((sum, item) => sum + item.total, 0);
    document.getElementById('sale-total').textContent = formatMoney(total);
    return total;
}

// Função para atualizar troco
function updateChange() {
    const total = updateSaleTotal();
    const amountPaid = parseFloat(document.getElementById('amount-paid').value) || 0;
    const change = amountPaid - total;
    document.getElementById('change').value = change.toFixed(2);
}

// Função para carregar clientes
function loadCustomers(search = '') {
    fetch(`/api/customers?search=${search}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#customer-table tbody');
                tbody.innerHTML = '';

                data.data.forEach(customer => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${customer.name}</td>
                        <td>${customer.cpf ? formatCPF(customer.cpf) : ''}</td>
                        <td>${customer.phone ? formatPhone(customer.phone) : ''}</td>
                        <td>${formatMoney(customer.credit_limit)}</td>
                        <td>
                            <button class="btn btn-sm btn-primary select-customer" data-customer='${JSON.stringify(customer)}'>
                                Selecionar
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

                // Adicionar eventos aos botões
                document.querySelectorAll('.select-customer').forEach(button => {
                    button.addEventListener('click', () => {
                        selectedCustomer = JSON.parse(button.dataset.customer);
                        updateCustomerInfo();
                        const modal = bootstrap.Modal.getInstance(document.getElementById('customerModal'));
                        modal.hide();
                    });
                });
            }
        });
}

// Função para atualizar informações do cliente
function updateCustomerInfo() {
    const container = document.getElementById('customer-info');
    if (selectedCustomer) {
        container.innerHTML = `
            <h6>${selectedCustomer.name}</h6>
            <p class="mb-1">${selectedCustomer.cpf ? formatCPF(selectedCustomer.cpf) : ''}</p>
            <p class="mb-1">${selectedCustomer.phone ? formatPhone(selectedCustomer.phone) : ''}</p>
            <p class="mb-1">Limite: ${formatMoney(selectedCustomer.credit_limit)}</p>
            <p class="mb-0">Disponível: ${formatMoney(selectedCustomer.available_credit)}</p>
        `;
    } else {
        container.innerHTML = '<p class="text-muted">Nenhum cliente selecionado</p>';
    }
}

// Função para carregar produtos
function loadProducts(search = '') {
    fetch(`/api/products?search=${search}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                const tbody = document.querySelector('#product-table tbody');
                tbody.innerHTML = '';

                data.data.forEach(product => {
                    if (product) {  
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${product.code || ''}</td>
                            <td>${product.name || ''}</td>
                            <td class="text-end">${formatMoney(product.price || 0)}</td>
                            <td class="text-end">${product.stock || 0}</td>
                            <td>
                                <button class="btn btn-sm btn-primary select-product" data-product='${JSON.stringify(product)}'>
                                    Selecionar
                                </button>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    }
                });

                // Adicionar eventos aos botões
                document.querySelectorAll('.select-product').forEach(button => {
                    button.addEventListener('click', () => {
                        try {
                            selectedProduct = JSON.parse(button.dataset.product);
                            const modal = bootstrap.Modal.getInstance(document.getElementById('productModal'));
                            modal.hide();
                            
                            // Abre o modal de quantidade
                            const quantityModal = new bootstrap.Modal(document.getElementById('quantityModal'));
                            quantityModal.show();
                        } catch (error) {
                            console.error('Erro ao selecionar produto:', error);
                            alert('Erro ao selecionar produto. Por favor, tente novamente.');
                        }
                    });
                });
            } else {
                console.error('Erro ao carregar produtos:', data.error);
            }
        })
        .catch(error => {
            console.error('Erro ao carregar produtos:', error);
        });
}

// Função para adicionar item à venda
function addSaleItem() {
    const quantity = parseInt(document.getElementById('quantity').value);
    const discount = parseFloat(document.getElementById('discount').value) || 0;
    
    if (selectedProduct && quantity > 0) {
        const unitPrice = selectedProduct.selling_price;
        const total = quantity * unitPrice * (1 - discount / 100);

        const item = {
            product_id: selectedProduct.id,
            code: selectedProduct.code,
            name: selectedProduct.name,
            quantity: quantity,
            unit_price: unitPrice,
            discount: discount,
            total: total
        };

        saleItems.push(item);
        updateSaleItems();
        updateSaleTotal();

        // Limpar seleção
        selectedProduct = null;
        document.getElementById('quantity').value = '1';
        document.getElementById('discount').value = '0';

        const modal = bootstrap.Modal.getInstance(document.getElementById('quantityModal'));
        modal.hide();
    }
}

// Função para atualizar tabela de itens
function updateSaleItems() {
    const tbody = document.querySelector('#sale-items tbody');
    tbody.innerHTML = '';

    saleItems.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.code}</td>
            <td>${item.name}</td>
            <td class="text-end">${item.quantity}</td>
            <td class="text-end">${formatMoney(item.unit_price)}</td>
            <td class="text-end">${item.discount}%</td>
            <td class="text-end">${formatMoney(item.total)}</td>
            <td>
                <button class="btn btn-sm btn-danger remove-item" data-index="${index}">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // Adicionar eventos aos botões de remover
    document.querySelectorAll('.remove-item').forEach(button => {
        button.addEventListener('click', () => {
            const index = parseInt(button.dataset.index);
            saleItems.splice(index, 1);
            updateSaleItems();
            updateSaleTotal();
        });
    });
}

// Função para finalizar venda
async function finishSale() {
    if (!selectedCustomer) {
        alert('Selecione um cliente para continuar.');
        return;
    }

    if (saleItems.length === 0) {
        alert('Adicione pelo menos um item à venda.');
        return;
    }

    const paymentMethod = document.getElementById('payment-method').value;
    const amountPaid = parseFloat(document.getElementById('amount-paid').value) || 0;
    const total = updateSaleTotal();

    if (paymentMethod === 'cash' && amountPaid < total) {
        alert('O valor recebido é menor que o total da venda.');
        return;
    }

    const sale = {
        customer_id: selectedCustomer.id,
        items: saleItems,
        payment_method: paymentMethod,
        amount_paid: amountPaid
    };

    if (paymentMethod === 'credit') {
        sale.due_date = document.getElementById('due-date').value;
        
        // Verificar limite de crédito
        const currentDebt = parseFloat(selectedCustomer.current_debt) || 0;
        const creditLimit = parseFloat(selectedCustomer.credit_limit) || 0;
        
        if (currentDebt + total > creditLimit) {
            const proceed = confirm(`Atenção: Esta venda excederá o limite de crédito do cliente.\nLimite: ${formatMoney(creditLimit)}\nDívida Atual: ${formatMoney(currentDebt)}\nValor da Venda: ${formatMoney(total)}\n\nDeseja continuar?`);
            
            if (proceed) {
                // Solicitar credenciais do supervisor
                const username = prompt('Digite o nome de usuário do supervisor:');
                if (!username) return;
                
                const password = prompt('Digite a senha do supervisor:');
                if (!password) return;
                
                // Verificar credenciais
                try {
                    const response = await fetch('/api/users/verify', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ username, password })
                    });
                    
                    const data = await response.json();
                    
                    if (!data.success) {
                        alert(data.error || 'Credenciais inválidas');
                        return;
                    }
                    
                    // Adicionar ID do supervisor à venda
                    sale.supervisor_id = data.data.id;
                } catch (error) {
                    console.error('Erro:', error);
                    alert('Erro ao verificar credenciais');
                    return;
                }
            } else {
                return;
            }
        }
    }

    try {
        const response = await fetch('/api/sales', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(sale)
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Venda realizada com sucesso!');
            clearSale();
        } else {
            alert(data.error || 'Erro ao realizar venda');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao realizar venda');
    }
}

// Função para limpar venda
function clearSale() {
    selectedCustomer = null;
    selectedProduct = null;
    saleItems = [];
    
    updateCustomerInfo();
    updateSaleItems();
    updateSaleTotal();
    
    document.getElementById('payment-method').value = 'cash';
    document.getElementById('amount-paid').value = '';
    document.getElementById('change').value = '';
    document.getElementById('due-date').value = '';
    document.getElementById('credit-options').style.display = 'none';
}

// Função para visualizar detalhes da venda
function viewSale(id) {
    fetch(`/api/sales/${id}`)
        .then(response => response.json())
        .then(response => {
            if (response.success) {
                const sale = response.data;
                
                // Calcula o total da venda somando os subtotais dos itens
                const total = sale.items.reduce((acc, item) => acc + (item.subtotal || 0), 0);
                
                let itemsHtml = sale.items.map(item => `
                    <tr>
                        <td>${item.product_name || 'Produto não encontrado'}</td>
                        <td>${item.quantity} ${item.unit || 'un'}</td>
                        <td>${formatMoney(item.price)}</td>
                        <td>${formatMoney(item.subtotal)}</td>
                    </tr>
                `).join('');

                const modalContent = `
                    <div class="modal-header">
                        <h5 class="modal-title">Detalhes da Venda #${sale.id}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <p><strong>Cliente:</strong> ${sale.customer ? sale.customer.name : '-'}</p>
                                <p><strong>Data:</strong> ${new Date(sale.date).toLocaleString()}</p>
                            </div>
                            <div class="col-md-6">
                                <p><strong>Forma de Pagamento:</strong> ${sale.payment_method}</p>
                                <p><strong>Status:</strong> ${sale.status || '-'}</p>
                            </div>
                        </div>
                        <div class="table-responsive">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Produto</th>
                                        <th>Quantidade</th>
                                        <th>Preço Unit.</th>
                                        <th>Subtotal</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${itemsHtml}
                                </tbody>
                                <tfoot>
                                    <tr>
                                        <td colspan="3" class="text-end"><strong>Total:</strong></td>
                                        <td><strong>${formatMoney(total)}</strong></td>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>
                        ${sale.payment_method === 'crediario' && sale.receivables ? `
                            <div class="mt-3">
                                <h6>Parcelas</h6>
                                <div class="table-responsive">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>Vencimento</th>
                                                <th>Valor</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${sale.receivables.map(receivable => `
                                                <tr>
                                                    <td>${new Date(receivable.due_date).toLocaleDateString()}</td>
                                                    <td>${formatMoney(receivable.amount)}</td>
                                                    <td>${receivable.status}</td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                        <button type="button" class="btn btn-primary" onclick="printSale(${sale.id})">Imprimir</button>
                    </div>
                `;

                const modal = document.getElementById('saleModal');
                modal.querySelector('.modal-content').innerHTML = modalContent;
                const modalInstance = new bootstrap.Modal(modal);
                modalInstance.show();
            } else {
                alert('Erro ao carregar detalhes da venda');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao carregar detalhes da venda');
        });
}

// Função para imprimir venda
function printSale(id) {
    fetch(`/api/sales/${id}/print`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mostra mensagem de sucesso
            alert('Cupom enviado para impressão!');
        } else {
            // Mostra mensagem de erro
            alert('Erro ao imprimir: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Erro ao imprimir:', error);
        alert('Erro ao imprimir. Por favor, tente novamente.');
    });
}

// Eventos
document.addEventListener('DOMContentLoaded', () => {
    // Eventos específicos da página de PDV (nova venda)
    const customerSearch = document.getElementById('customer-search');
    const productSearch = document.getElementById('product-search');
    const selectCustomer = document.getElementById('select-customer');
    const selectProduct = document.getElementById('select-product');
    const addItem = document.getElementById('add-item');
    const amountPaid = document.getElementById('amount-paid');
    const finishSaleBtn = document.getElementById('finish-sale');

    if (customerSearch) {
        customerSearch.addEventListener('input', (e) => {
            const search = e.target.value;
            if (search.length >= 3) {
                loadCustomers(search);
            }
        });
    }

    if (productSearch) {
        productSearch.addEventListener('input', (e) => {
            const search = e.target.value;
            if (search.length >= 3) {
                loadProducts(search);
            }
        });
    }

    if (selectCustomer) {
        selectCustomer.addEventListener('click', () => {
            const modal = new bootstrap.Modal(document.getElementById('customerModal'));
            modal.show();
            loadCustomers(customerSearch.value);
        });
    }

    if (selectProduct) {
        selectProduct.addEventListener('click', () => {
            const modal = new bootstrap.Modal(document.getElementById('productModal'));
            modal.show();
            loadProducts(productSearch.value);
        });
    }

    if (addItem) {
        addItem.addEventListener('click', addSaleItem);
    }

    if (amountPaid) {
        amountPaid.addEventListener('input', updateChange);
    }

    if (finishSaleBtn) {
        finishSaleBtn.addEventListener('click', finishSale);
    }
});
