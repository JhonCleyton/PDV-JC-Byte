// Funções para busca de produtos
function initProductSearch() {
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('product-search')) {
            const searchInput = e.target;
            const query = searchInput.value;
            
            if (query.length >= 3) {
                fetch(`/api/produtos/search?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showProductResults(searchInput, data.products);
                        }
                    });
            }
        }
    });
}

function showProductResults(searchInput, products) {
    let resultsDiv = searchInput.parentElement.querySelector('.search-results');
    if (!resultsDiv) {
        resultsDiv = document.createElement('div');
        resultsDiv.className = 'search-results dropdown-menu w-100';
        searchInput.parentElement.appendChild(resultsDiv);
    }
    
    resultsDiv.innerHTML = '';
    products.forEach(product => {
        const item = document.createElement('a');
        item.href = '#';
        item.className = 'dropdown-item';
        item.dataset.id = product.id;
        item.dataset.code = product.code;
        item.dataset.name = product.name;
        item.dataset.cost = product.cost_price;
        item.textContent = `${product.code} - ${product.name}`;
        
        item.addEventListener('click', function(e) {
            e.preventDefault();
            selectProduct(searchInput, product);
            resultsDiv.innerHTML = '';
            resultsDiv.classList.remove('show');
        });
        
        resultsDiv.appendChild(item);
    });
    
    resultsDiv.classList.add('show');
}

function selectProduct(searchInput, product) {
    const row = searchInput.closest('tr');
    searchInput.value = `${product.code} - ${product.name}`;
    row.querySelector('.product-id').value = product.id;
    const priceInput = row.querySelector('.price');
    priceInput.value = product.cost_price;
    priceInput.dispatchEvent(new Event('input'));
}

// Funções para novo fornecedor
function saveNewSupplier() {
    const data = {
        name: document.getElementById('supplierName').value,
        cnpj: document.getElementById('supplierCnpj').value,
        email: document.getElementById('supplierEmail').value,
        phone: document.getElementById('supplierPhone').value,
        address: document.getElementById('supplierAddress').value,
        city: document.getElementById('supplierCity').value,
        state: document.getElementById('supplierState').value,
        zip_code: document.getElementById('supplierZipCode').value
    };

    fetch('/api/fornecedores', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Adiciona o novo fornecedor ao select
            const supplierSelect = document.getElementById('supplier_id');
            const option = new Option(data.supplier.name, data.supplier.id);
            supplierSelect.add(option);
            supplierSelect.value = data.supplier.id;
            
            // Fecha o modal
            const modal = document.getElementById('modalNewSupplier');
            const modalInstance = bootstrap.Modal.getInstance(modal);
            modalInstance.hide();
            
            // Limpa o formulário
            document.getElementById('formNewSupplier').reset();
            
            // Mostra mensagem de sucesso
            Swal.fire({
                title: 'Sucesso!',
                text: 'Fornecedor cadastrado com sucesso!',
                icon: 'success'
            });
        } else {
            throw new Error(data.error || 'Erro ao cadastrar fornecedor');
        }
    })
    .catch(error => {
        Swal.fire({
            title: 'Erro!',
            text: error.message,
            icon: 'error'
        });
    });
}

// Funções para novo produto
function calculateSellingPrice() {
    const costPrice = parseFloat(document.getElementById('productCostPrice').value) || 0;
    const markup = parseFloat(document.getElementById('productMarkup').value) || 0;
    const sellingPrice = costPrice * (1 + markup / 100);
    document.getElementById('productSellingPrice').value = sellingPrice.toFixed(2);
}

function saveNewProduct() {
    const data = {
        code: document.getElementById('productCode').value,
        name: document.getElementById('productName').value,
        description: document.getElementById('productDescription').value,
        cost_price: parseFloat(document.getElementById('productCostPrice').value) || 0,
        markup: parseFloat(document.getElementById('productMarkup').value) || 0,
        selling_price: parseFloat(document.getElementById('productSellingPrice').value) || 0,
        min_stock: parseInt(document.getElementById('productMinStock').value) || 0,
        max_stock: parseInt(document.getElementById('productMaxStock').value) || 0,
        stock: 0,  // Novo produto começa com estoque zero
        unit: document.getElementById('productUnit').value,
        category_id: document.getElementById('productCategory').value || null,
        status: 'active'  // Novo produto começa ativo
    };

    fetch('/api/produtos', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Seleciona o produto recém criado no campo de busca
            const activeRow = document.querySelector('.product-search:focus')?.closest('tr');
            if (activeRow) {
                const searchInput = activeRow.querySelector('.product-search');
                selectProduct(searchInput, data.product);
            }
            
            // Fecha o modal
            const modal = document.getElementById('modalNewProduct');
            const modalInstance = bootstrap.Modal.getInstance(modal);
            modalInstance.hide();
            
            // Limpa o formulário
            document.getElementById('formNewProduct').reset();
            
            // Mostra mensagem de sucesso
            Swal.fire({
                title: 'Sucesso!',
                text: 'Produto cadastrado com sucesso!',
                icon: 'success'
            });
        } else {
            throw new Error(data.error || 'Erro ao cadastrar produto');
        }
    })
    .catch(error => {
        Swal.fire({
            title: 'Erro!',
            text: error.message,
            icon: 'error'
        });
    });
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    initProductSearch();
    
    // Adiciona a primeira linha de produto
    addProductRow();

    // Event listeners para atualizar subtotais
    document.getElementById('productRows').addEventListener('input', function(e) {
        if (e.target.classList.contains('quantity') || e.target.classList.contains('price')) {
            updateSubtotal(e.target.closest('tr'));
            updateTotal();
        }
    });

    // Event listener para calcular preço de venda
    document.getElementById('productCostPrice').addEventListener('input', calculateSellingPrice);
    document.getElementById('productMarkup').addEventListener('input', calculateSellingPrice);

    // Form submission
    document.getElementById('invoiceForm').addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('Form submitted');
        
        // Validação básica
        const supplier = document.getElementById('supplier_id').value;
        if (!supplier) {
            Swal.fire({
                title: 'Erro!',
                text: 'Por favor, selecione um fornecedor',
                icon: 'error'
            });
            return;
        }

        const products = document.querySelectorAll('.product-id');
        const selectedProducts = new Set();
        let hasProducts = false;
        
        for (let input of products) {
            const productId = input.value;
            if (productId) {
                hasProducts = true;
                if (selectedProducts.has(productId)) {
                    Swal.fire({
                        title: 'Erro!',
                        text: 'Produto duplicado encontrado. Por favor, remova a duplicata.',
                        icon: 'error'
                    });
                    return;
                }
                selectedProducts.add(productId);
            }
        }

        if (!hasProducts) {
            Swal.fire({
                title: 'Erro!',
                text: 'Por favor, adicione pelo menos um produto',
                icon: 'error'
            });
            return;
        }

        // Prepara os dados do formulário em formato JSON
        const formData = {
            invoice_number: document.getElementById('invoice_number').value,
            supplier_id: parseInt(document.getElementById('supplier_id').value),
            invoice_date: document.getElementById('invoice_date').value,
            payment_date: document.getElementById('payment_date').value,
            payment_method: document.getElementById('payment_method').value,
            status: document.getElementById('status').value,
            notes: document.getElementById('notes').value,
            items: []
        };

        // Adiciona os itens da nota
        document.querySelectorAll('#productRows tr').forEach(function(row) {
            const productId = row.querySelector('.product-id')?.value;
            if (productId) {
                formData.items.push({
                    product_id: parseInt(productId),
                    quantity: parseFloat(row.querySelector('.quantity').value) || 0,
                    price: parseFloat(row.querySelector('.price').value) || 0
                });
            }
        });

        console.log('Sending data:', formData);

        // Envio do formulário
        fetch('/api/notas-fiscais', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Erro ao salvar a nota fiscal');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            if (data.success) {
                Swal.fire({
                    title: 'Sucesso!',
                    text: data.message,
                    icon: 'success'
                }).then(() => {
                    window.location.href = '/notas-fiscais';
                });
            } else {
                throw new Error(data.error || 'Erro ao salvar a nota fiscal');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                title: 'Erro!',
                text: error.message,
                icon: 'error'
            });
        });
    });
});

// Função para adicionar nova linha de produto
function addProductRow() {
    const template = document.getElementById('productRowTemplate');
    const tbody = document.getElementById('productRows');
    const clone = template.content.cloneNode(true);
    tbody.appendChild(clone);
}

// Função para remover linha de produto
function removeProductRow(button) {
    const tbody = document.getElementById('productRows');
    if (tbody.children.length > 1) {
        button.closest('tr').remove();
        updateTotal();
    } else {
        alert('A nota fiscal deve ter pelo menos um produto');
    }
}

// Função para atualizar subtotal de uma linha
function updateSubtotal(row) {
    const quantity = parseFloat(row.querySelector('.quantity').value) || 0;
    const price = parseFloat(row.querySelector('.price').value) || 0;
    const subtotal = quantity * price;
    row.querySelector('.subtotal').value = subtotal.toFixed(2);
    updateTotal();
}

// Função para atualizar o total da nota fiscal
function updateTotal() {
    const subtotals = Array.from(document.querySelectorAll('.subtotal'))
        .map(input => parseFloat(input.value) || 0);
    const total = subtotals.reduce((acc, curr) => acc + curr, 0);
    document.getElementById('total').value = total.toFixed(2);
}
