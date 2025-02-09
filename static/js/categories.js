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
    const search = document.getElementById('search').value;

    fetch(`/api/categories?search=${search}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#categoriesTable tbody');
                tbody.innerHTML = '';

                // Atualizar select de categoria pai
                const parentSelect = document.getElementById('parent_id');
                parentSelect.innerHTML = '<option value="">Nenhuma</option>';

                data.data.forEach(category => {
                    // Adicionar à tabela
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${category.name}</td>
                        <td>${category.description || ''}</td>
                        <td>${category.parent ? category.parent.name : ''}</td>
                        <td>${category.products_count}</td>
                        <td>
                            <button class="btn btn-sm btn-primary edit-category" data-id="${category.id}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-danger delete-category" data-id="${category.id}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);

                    // Adicionar ao select de categoria pai
                    const option = new Option(category.name, category.id);
                    parentSelect.add(option);
                });

                // Adicionar eventos aos botões
                document.querySelectorAll('.edit-category').forEach(button => {
                    button.addEventListener('click', () => editCategory(button.dataset.id));
                });

                document.querySelectorAll('.delete-category').forEach(button => {
                    button.addEventListener('click', () => deleteCategory(button.dataset.id));
                });
            }
        });
}

// Função para editar categoria
function editCategory(id) {
    fetch(`/api/categories/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const category = data.data;
                document.getElementById('name').value = category.name;
                document.getElementById('description').value = category.description;
                document.getElementById('parent_id').value = category.parent_id || '';

                document.getElementById('categoryForm').dataset.id = id;
                document.getElementById('categoryForm').style.display = 'block';
            }
        });
}

// Função para deletar categoria
function deleteCategory(id) {
    if (confirm('Tem certeza que deseja excluir esta categoria?')) {
        fetch(`/api/categories/${id}`, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Categoria excluída com sucesso!');
                    loadCategories();
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

    // Evento de busca
    document.getElementById('search').addEventListener('input', loadCategories);

    // Evento de nova categoria
    document.getElementById('newCategoryBtn').addEventListener('click', () => {
        document.getElementById('categoryForm').reset();
        delete document.getElementById('categoryForm').dataset.id;
        document.getElementById('categoryForm').style.display = 'block';
    });

    // Evento de cancelar
    document.getElementById('cancelBtn').addEventListener('click', () => {
        document.getElementById('categoryForm').style.display = 'none';
    });

    // Evento de salvar
    document.getElementById('categoryForm').addEventListener('submit', (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        const id = e.target.dataset.id;
        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/categories/${id}` : '/api/categories';

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
                    showAlert(id ? 'Categoria atualizada com sucesso!' : 'Categoria cadastrada com sucesso!');
                    document.getElementById('categoryForm').style.display = 'none';
                    loadCategories();
                } else {
                    showAlert(data.message, 'danger');
                }
            });
    });
});
