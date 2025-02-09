// Função para formatar números como moeda
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Função para atualizar os dados do dashboard
function updateDashboard() {
    fetch('/api/dashboard/today')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Atualiza as contas a receber
                document.getElementById('totalReceivables').textContent = 
                    formatCurrency(data.data.receivables.total).replace('R$', '').trim();
                document.getElementById('totalReceived').textContent = 
                    formatCurrency(data.data.receivables.received).replace('R$', '').trim();
                document.getElementById('totalPending').textContent = 
                    formatCurrency(data.data.receivables.pending).replace('R$', '').trim();
                document.getElementById('totalOverdue').textContent = 
                    formatCurrency(data.data.receivables.overdue).replace('R$', '').trim();
                
                // Atualiza as contas a pagar
                document.getElementById('totalPayables').textContent = 
                    formatCurrency(data.data.payables).replace('R$', '').trim();
            }
        })
        .catch(error => console.error('Erro ao atualizar dashboard:', error));
}

// Atualiza o dashboard quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    updateDashboard();
    
    // Atualiza a cada 5 minutos
    setInterval(updateDashboard, 5 * 60 * 1000);
});
