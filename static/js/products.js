// Função para formatar valores monetários
function formatMoney(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Função para mostrar alertas
function showAlert(message, type = 'success') {
    const alertDiv = document.getElementById('alerts');
    alertDiv.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
}

// Função para carregar categorias
function loadCategories() {
    fetch('/api/categories')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const categoryFilter = document.getElementById('categoryFilter');
                const categorySelect = document.getElementById('category_id');
                
                data.data.forEach(category => {
                    const option = new Option(category.name, category.id);
                    categoryFilter.add(option.cloneNode(true));
                    categorySelect.add(option);
                });
            }
        });
}

// Função para carregar fornecedores
function loadSuppliers() {
    fetch('/api/suppliers')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const supplierFilter = document.getElementById('supplierFilter');
                const supplierSelect = document.getElementById('supplier_id');
                
                data.data.forEach(supplier => {
                    const option = new Option(supplier.name, supplier.id);
                    supplierFilter.add(option.cloneNode(true));
                    supplierSelect.add(option);
                });
            }
        });
}

// Função para carregar produtos
function loadProducts() {
    const search = document.getElementById('search').value;
    const category = document.getElementById('categoryFilter').value;
    const supplier = document.getElementById('supplierFilter').value;
    const stock = document.getElementById('stockFilter').value;

    fetch(`/api/products?search=${search}&category_id=${category}&supplier_id=${supplier}&stock_status=${stock}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#productsTable tbody');
                tbody.innerHTML = '';

                data.data.forEach(product => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${product.code}</td>
                        <td>${product.name}</td>
                        <td>${product.category.name}</td>
                        <td>${product.supplier.name}</td>
                        <td class="text-end">${formatMoney(product.selling_price)}</td>
                        <td class="text-end">
                            <span class="badge bg-${product.stock <= product.min_stock ? 'danger' : 'success'}">
                                ${product.stock}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-primary edit-product" data-id="${product.id}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-danger delete-product" data-id="${product.id}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

                // Adicionar eventos aos botões
                document.querySelectorAll('.edit-product').forEach(button => {
                    button.addEventListener('click', () => editProduct(button.dataset.id));
                });

                document.querySelectorAll('.delete-product').forEach(button => {
                    button.addEventListener('click', () => deleteProduct(button.dataset.id));
                });
            }
        });
}

// Função para calcular preço de venda
function calculateSellingPrice() {
    const costPrice = parseFloat(document.getElementById('cost_price').value) || 0;
    const markup = parseFloat(document.getElementById('markup').value) || 0;
    const sellingPrice = costPrice * (1 + markup / 100);
    document.getElementById('selling_price').value = sellingPrice.toFixed(2);
}

// Função para editar produto
function editProduct(id) {
    fetch(`/api/products/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const product = data.data;
                document.getElementById('code').value = product.code || '';
                document.getElementById('name').value = product.name || '';
                document.getElementById('description').value = product.description || '';
                document.getElementById('category_id').value = product.category_id || '';
                document.getElementById('supplier_id').value = product.supplier_id || '';
                document.getElementById('cost_price').value = product.cost_price || 0;
                document.getElementById('markup').value = product.markup || 0;
                document.getElementById('selling_price').value = product.selling_price || 0;
                document.getElementById('stock').value = product.stock || 0;
                document.getElementById('min_stock').value = product.min_stock || 0;
                document.getElementById('max_stock').value = product.max_stock || 0;
                document.getElementById('unit').value = product.unit || 'un';
                document.getElementById('status').value = product.status || 'active';

                document.getElementById('productForm').dataset.id = id;
                document.getElementById('productForm').style.display = 'block';
            } else {
                showAlert(data.error || 'Erro ao carregar produto', 'danger');
            }
        })
        .catch(error => {
            showAlert('Erro ao carregar produto: ' + error.message, 'danger');
        });
}

// Função para deletar produto
function deleteProduct(id) {
    if (confirm('Tem certeza que deseja excluir este produto?')) {
        fetch(`/api/products/${id}`, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Produto excluído com sucesso!');
                    loadProducts();
                } else {
                    showAlert(data.message, 'danger');
                }
            });
    }
}

// Eventos
document.addEventListener('DOMContentLoaded', () => {
    // Carregar dados iniciais
    loadCategories();
    loadSuppliers();
    loadProducts();

    // Eventos de filtro
    document.getElementById('search').addEventListener('input', loadProducts);
    document.getElementById('categoryFilter').addEventListener('change', loadProducts);
    document.getElementById('supplierFilter').addEventListener('change', loadProducts);
    document.getElementById('stockFilter').addEventListener('change', loadProducts);

    // Evento de novo produto
    document.getElementById('newProductBtn').addEventListener('click', () => {
        document.getElementById('productForm').reset();
        delete document.getElementById('productForm').dataset.id;
        document.getElementById('productForm').style.display = 'block';
    });

    // Eventos do formulário
    document.getElementById('cost_price').addEventListener('input', calculateSellingPrice);
    document.getElementById('markup').addEventListener('input', calculateSellingPrice);

    // Evento de cancelar
    document.getElementById('cancelBtn').addEventListener('click', () => {
        document.getElementById('productForm').style.display = 'none';
    });

    // Evento de salvar
    document.getElementById('productForm').addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);
        const data = {};
        
        // Converte os valores para o formato correto
        for (let [key, value] of formData.entries()) {
            switch (key) {
                case 'cost_price':
                case 'selling_price':
                case 'markup':
                case 'stock':
                case 'min_stock':
                case 'max_stock':
                    data[key] = parseFloat(value) || 0;
                    break;
                case 'category_id':
                case 'supplier_id':
                    data[key] = value ? parseInt(value) : null;
                    break;
                default:
                    data[key] = value;
            }
        }

        const id = e.target.dataset.id;
        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/products/${id}` : '/api/products';

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showAlert(id ? 'Produto atualizado com sucesso!' : 'Produto cadastrado com sucesso!');
                document.getElementById('productForm').style.display = 'none';
                loadProducts();
            } else {
                showAlert(result.error || 'Erro ao salvar produto', 'danger');
            }
        })
        .catch(error => {
            showAlert('Erro ao salvar produto: ' + error.message, 'danger');
        });
    });
});
