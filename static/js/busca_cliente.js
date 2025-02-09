function buscarCliente() {
    const matricula = document.getElementById('matriculaCliente').value.trim();
    
    if (!matricula) {
        alert('Por favor, digite a matrícula do cliente');
        return;
    }
    
    console.log('=== Buscando cliente ===');
    console.log('Registro original:', matricula);
    
    // Remove caracteres não numéricos
    const matriculaLimpa = matricula.replace(/\D/g, '');
    console.log('Registro limpo:', matriculaLimpa);
    
    console.log('\nTentando buscar por matrícula...');
    
    fetch(`/api/clientes/buscar/${matriculaLimpa}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.data) {
                window.clienteAtual = data.data;
                console.log('Cliente encontrado por matrícula:', window.clienteAtual.name);
                console.log('\nDados do cliente:');
                console.log('- ID:', window.clienteAtual.id);
                console.log('- Nome:', window.clienteAtual.name);
                console.log('- CPF:', window.clienteAtual.cpf);
                console.log('- Matrícula:', window.clienteAtual.registration);
                console.log('- Dict:', window.clienteAtual);
                
                document.getElementById('nomeCliente').textContent = window.clienteAtual.name;
                document.getElementById('limiteDisponivel').textContent = 
                    (window.clienteAtual.credit_limit - window.clienteAtual.current_debt).toFixed(2);
                document.getElementById('infoCliente').classList.remove('d-none');
            } else {
                alert('Cliente não encontrado');
                document.getElementById('infoCliente').classList.add('d-none');
                window.clienteAtual = null;
            }
        })
        .catch(error => {
            console.error('Erro ao buscar cliente:', error);
            alert('Erro ao buscar cliente');
            document.getElementById('infoCliente').classList.add('d-none');
            window.clienteAtual = null;
        });
}

// Adiciona event listener para o evento de pressionar Enter
document.addEventListener('DOMContentLoaded', () => {
    const inputMatricula = document.getElementById('matriculaCliente');
    if (inputMatricula) {
        inputMatricula.addEventListener('keypress', event => {
            if (event.key === 'Enter') {
                event.preventDefault();
                buscarCliente();
            }
        });
    }

    const btnBuscarCliente = document.getElementById('buscarCliente');
    if (btnBuscarCliente) {
        btnBuscarCliente.addEventListener('click', buscarCliente);
    }
});
