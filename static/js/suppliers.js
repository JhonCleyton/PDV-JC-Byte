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

// Função para formatar CNPJ
function formatCNPJ(cnpj) {
    return cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}

// Função para formatar telefone
function formatPhone(phone) {
    return phone.replace(/^(\d{2})(\d{4,5})(\d{4})$/, "($1) $2-$3");
}

// Função para formatar CEP
function formatCEP(cep) {
    return cep.replace(/^(\d{5})(\d{3})$/, "$1-$2");
}

// Função para carregar fornecedores
function loadSuppliers() {
    const search = document.getElementById('search').value;

    fetch(`/api/suppliers?search=${search}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#suppliersTable tbody');
                tbody.innerHTML = '';

                data.data.forEach(supplier => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${supplier.name}</td>
                        <td>${supplier.cnpj ? formatCNPJ(supplier.cnpj) : ''}</td>
                        <td>${supplier.phone ? formatPhone(supplier.phone) : ''}</td>
                        <td>${supplier.city}${supplier.state ? ' - ' + supplier.state : ''}</td>
                        <td>${supplier.products_count}</td>
                        <td>
                            <button class="btn btn-sm btn-primary edit-supplier" data-id="${supplier.id}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-danger delete-supplier" data-id="${supplier.id}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });

                // Adicionar eventos aos botões
                document.querySelectorAll('.edit-supplier').forEach(button => {
                    button.addEventListener('click', () => editSupplier(button.dataset.id));
                });

                document.querySelectorAll('.delete-supplier').forEach(button => {
                    button.addEventListener('click', () => deleteSupplier(button.dataset.id));
                });
            }
        });
}

// Função para buscar CEP
function searchCEP(cep) {
    fetch(`https://viacep.com.br/ws/${cep}/json/`)
        .then(response => response.json())
        .then(data => {
            if (!data.erro) {
                document.getElementById('address').value = data.logradouro;
                document.getElementById('city').value = data.localidade;
                document.getElementById('state').value = data.uf;
            }
        });
}

// Função para editar fornecedor
function editSupplier(id) {
    fetch(`/api/suppliers/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const supplier = data.data;
                document.getElementById('name').value = supplier.name;
                document.getElementById('cnpj').value = supplier.cnpj;
                document.getElementById('email').value = supplier.email;
                document.getElementById('phone').value = supplier.phone;
                document.getElementById('address').value = supplier.address;
                document.getElementById('city').value = supplier.city;
                document.getElementById('state').value = supplier.state;
                document.getElementById('zip_code').value = supplier.zip_code;
                document.getElementById('contact_name').value = supplier.contact_name;
                document.getElementById('payment_terms').value = supplier.payment_terms;

                document.getElementById('supplierForm').dataset.id = id;
                document.getElementById('supplierForm').style.display = 'block';
            }
        });
}

// Função para deletar fornecedor
function deleteSupplier(id) {
    if (confirm('Tem certeza que deseja excluir este fornecedor?')) {
        fetch(`/api/suppliers/${id}`, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Fornecedor excluído com sucesso!');
                    loadSuppliers();
                } else {
                    showAlert(data.message, 'danger');
                }
            });
    }
}

// Eventos
document.addEventListener('DOMContentLoaded', () => {
    // Carregar dados iniciais
    loadSuppliers();

    // Evento de busca
    document.getElementById('search').addEventListener('input', loadSuppliers);

    // Evento de novo fornecedor
    document.getElementById('newSupplierBtn').addEventListener('click', () => {
        document.getElementById('supplierForm').reset();
        delete document.getElementById('supplierForm').dataset.id;
        document.getElementById('supplierForm').style.display = 'block';
    });

    // Evento de busca de CEP
    document.getElementById('zip_code').addEventListener('blur', (e) => {
        const cep = e.target.value.replace(/\D/g, '');
        if (cep.length === 8) {
            searchCEP(cep);
        }
    });

    // Evento de cancelar
    document.getElementById('cancelBtn').addEventListener('click', () => {
        document.getElementById('supplierForm').style.display = 'none';
    });

    // Evento de salvar
    document.getElementById('supplierForm').addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        const id = e.target.dataset.id;
        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/suppliers/${id}` : '/api/suppliers';

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert(id ? 'Fornecedor atualizado com sucesso!' : 'Fornecedor cadastrado com sucesso!');
                    document.getElementById('supplierForm').style.display = 'none';
                    loadSuppliers();
                } else {
                    showAlert(data.message, 'danger');
                }
            });
    });

    // Máscaras de entrada
    document.getElementById('cnpj').addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 14) value = value.slice(0, 14);
        if (value.length === 14) {
            value = formatCNPJ(value);
        }
        e.target.value = value;
    });

    document.getElementById('phone').addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 11) value = value.slice(0, 11);
        if (value.length === 10 || value.length === 11) {
            value = formatPhone(value);
        }
        e.target.value = value;
    });

    document.getElementById('zip_code').addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 8) value = value.slice(0, 8);
        if (value.length === 8) {
            value = formatCEP(value);
        }
        e.target.value = value;
    });
});
