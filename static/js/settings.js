// Carregar usuários ao iniciar
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    loadCompanyInfo();
    loadPrinters();
    loadReceiptConfig();
});

// Função para carregar usuários
function loadUsers() {
    fetch('/api/users')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#users-table');
                tbody.innerHTML = '';

                data.data.forEach(user => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${user.name}</td>
                        <td>${user.username}</td>
                        <td>${formatRole(user.role)}</td>
                        <td>
                            <span class="badge bg-${user.status === 'active' ? 'success' : 'danger'}">
                                ${user.status === 'active' ? 'Ativo' : 'Inativo'}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="editUser(${user.id})">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        });
}

// Função para formatar função do usuário
function formatRole(role) {
    const roles = {
        'admin': 'Administrador',
        'manager': 'Gerente',
        'supervisor': 'Supervisor',
        'cashier': 'Caixa'
    };
    return roles[role] || role;
}

// Função para editar usuário
function editUser(id) {
    fetch(`/api/users/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const user = data.data;
                document.getElementById('user-id').value = user.id;
                document.getElementById('name').value = user.name;
                document.getElementById('username').value = user.username;
                document.getElementById('role').value = user.role;
                document.getElementById('status').value = user.status;
                document.getElementById('password').value = '';

                const modal = new bootstrap.Modal(document.getElementById('userModal'));
                modal.show();
            }
        });
}

// Função para salvar usuário
function saveUser() {
    const userId = document.getElementById('user-id').value;
    const password = document.getElementById('password').value;
    
    // Validar senha para novos usuários
    if (!userId && !password) {
        alert('A senha é obrigatória para novos usuários');
        return;
    }
    
    const data = {
        name: document.getElementById('name').value,
        username: document.getElementById('username').value,
        role: document.getElementById('role').value,
        status: document.getElementById('status').value
    };

    // Adicionar senha apenas se fornecida
    if (password) {
        data.password = password;
    }

    const method = userId ? 'PUT' : 'POST';
    const url = userId ? `/api/users/${userId}` : '/api/users';

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Erro ao salvar usuário');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('userModal'));
            modal.hide();
            loadUsers();
            clearForm();
        } else {
            alert(data.error || 'Erro ao salvar usuário');
        }
    })
    .catch(error => {
        alert(error.message);
    });
}

// Função para excluir usuário
function deleteUser(id) {
    if (confirm('Tem certeza que deseja excluir este usuário?')) {
        fetch(`/api/users/${id}`, {
            method: 'DELETE'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadUsers();
                } else {
                    alert(data.error);
                }
            });
    }
}

// Função para limpar formulário
function clearForm() {
    document.getElementById('user-form').reset();
    document.getElementById('user-id').value = '';
}

// Limpar formulário ao abrir modal
document.getElementById('userModal').addEventListener('show.bs.modal', function (event) {
    if (!document.getElementById('user-id').value) {
        clearForm();
    }
});

// Funções de configuração da empresa
function loadCompanyInfo() {
    fetch('/api/company')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const info = data.data;
                document.getElementById('company_name').value = info.name || '';
                document.getElementById('company_cnpj').value = info.cnpj || '';
                document.getElementById('company_ie').value = info.ie || '';
                document.getElementById('company_phone').value = info.phone || '';
                document.getElementById('company_email').value = info.email || '';
                document.getElementById('company_address').value = info.address || '';
                document.getElementById('company_city').value = info.city || '';
                document.getElementById('company_state').value = info.state || '';
                document.getElementById('company_zip').value = info.zip_code || '';
            }
        });
}

// Salvar dados da empresa
document.getElementById('company-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const data = {
        name: document.getElementById('company_name').value,
        cnpj: document.getElementById('company_cnpj').value,
        ie: document.getElementById('company_ie').value,
        phone: document.getElementById('company_phone').value,
        email: document.getElementById('company_email').value,
        address: document.getElementById('company_address').value,
        city: document.getElementById('company_city').value,
        state: document.getElementById('company_state').value,
        zip_code: document.getElementById('company_zip').value
    };
    
    fetch('/api/company', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Dados da empresa salvos com sucesso!');
        } else {
            alert(data.error || 'Erro ao salvar dados da empresa');
        }
    });
});

// Funções de configuração do cupom
function loadPrinters() {
    fetch('/api/printers')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const select = document.getElementById('printer_name');
                select.innerHTML = '';
                data.printers.forEach(printer => {
                    const option = document.createElement('option');
                    option.value = printer;
                    option.textContent = printer;
                    select.appendChild(option);
                });
            }
        });
}

function loadReceiptConfig() {
    fetch('/api/receipt-config')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const config = data.data;
                document.getElementById('printer_name').value = config.printer_name || '';
                document.getElementById('print_header').value = config.print_header || '';
                document.getElementById('print_footer').value = config.print_footer || '';
                document.getElementById('auto_print').checked = config.auto_print !== false;
            }
        });
}

// Salvar configurações do cupom
document.getElementById('receipt-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const data = {
        printer_name: document.getElementById('printer_name').value,
        print_header: document.getElementById('print_header').value,
        print_footer: document.getElementById('print_footer').value,
        auto_print: document.getElementById('auto_print').checked
    };
    
    fetch('/api/receipt-config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Configurações do cupom salvas com sucesso!');
        } else {
            alert(data.error || 'Erro ao salvar configurações do cupom');
        }
    });
});

// Testar impressão
function testarImpressao() {
    fetch('/api/test-print', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            printer_name: document.getElementById('printer_name').value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Cupom de teste enviado para impressão!');
        } else {
            alert(data.error || 'Erro ao imprimir cupom de teste');
        }
    });
}
