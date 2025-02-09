// Variáveis globais
let itens = [];
let clienteAtual = null;
let vendaAutorizada = false;

// Modais
const modalConsultaPreco = new bootstrap.Modal(document.getElementById('modalConsultaPreco'));
const modalConsultaDividas = new bootstrap.Modal(document.getElementById('modalConsultaDividas'));
const modalPagamentoDivida = new bootstrap.Modal(document.getElementById('modalPagamentoDivida'));
const modalFinalizarVenda = new bootstrap.Modal(document.getElementById('modalFinalizarVenda'));
const modalConfirmSemLimite = new bootstrap.Modal(document.getElementById('modalConfirmSemLimite'));

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Atalhos de teclado
    document.addEventListener('keydown', function(e) {
        if (e.key === 'F2') {
            e.preventDefault();
            consultarPreco();
        } else if (e.key === 'F3') {
            e.preventDefault();
            consultarDividas();
        } else if (e.key === 'F4') {
            e.preventDefault();
            finalizarVenda();
        }
    });

    // Input de produto
    const inputProduto = document.getElementById('inputProduto');
    if (inputProduto) {
        inputProduto.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                processarEntrada(e.target.value);
                e.target.value = '';
            }
        });
    }

    // Botões de consulta
    const btnConsultarPreco = document.getElementById('consultarPreco');
    if (btnConsultarPreco) {
        btnConsultarPreco.addEventListener('click', consultarPreco);
    }

    const btnConsultarDividas = document.getElementById('consultarDividas');
    if (btnConsultarDividas) {
        btnConsultarDividas.addEventListener('click', consultarDividas);
    }

    const btnFinalizarVenda = document.getElementById('finalizarVenda');
    if (btnFinalizarVenda) {
        btnFinalizarVenda.addEventListener('click', finalizarVenda);
    }

    const btnConfirmarVenda = document.getElementById('confirmarVenda');
    if (btnConfirmarVenda) {
        btnConfirmarVenda.addEventListener('click', confirmarVenda);
    }

    const btnBuscarDividas = document.getElementById('buscarDividas');
    if (btnBuscarDividas) {
        btnBuscarDividas.addEventListener('click', buscarDividas);
    }

    // Event listener para o método de pagamento
    const metodoPagamento = document.getElementById('metodoPagamento');
    if (metodoPagamento) {
        metodoPagamento.addEventListener('change', toggleParcelas);
    }

    // Event listener para cálculo de troco
    const valorRecebido = document.getElementById('valorRecebido');
    if (valorRecebido) {
        valorRecebido.addEventListener('input', calcularTroco);
    }

    // Reset do form de autorização quando o modal fechar
    const modalConfirmSemLimite = document.getElementById('modalConfirmSemLimite');
    if (modalConfirmSemLimite) {
        modalConfirmSemLimite.addEventListener('hidden.bs.modal', function() {
            const formAutorizacao = document.getElementById('formAutorizacao');
            if (formAutorizacao) {
                formAutorizacao.reset();
            }
            vendaAutorizada = false;
        });
    }

    // Event listeners para consulta de preço
    const inputConsultaPreco = document.getElementById('codigoConsulta');
    const btnBuscarProduto = document.getElementById('buscarProduto');

    if (inputConsultaPreco) {
        inputConsultaPreco.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                buscarProduto();
            }
        });
    }

    if (btnBuscarProduto) {
        btnBuscarProduto.addEventListener('click', buscarProduto);
    }

    // Event listener para pagamento de dívida
    const btnPagarDivida = document.getElementById('pagarDivida');
    if (btnPagarDivida) {
        btnPagarDivida.addEventListener('click', pagarDivida);
    }

    // Botão de autorizar venda
    document.getElementById('btnAutorizar').addEventListener('click', async function() {
        const username = document.getElementById('authUser').value;
        const password = document.getElementById('authPass').value;
        
        if (!username || !password) {
            alert('Por favor, preencha usuário e senha');
            return;
        }
        
        await solicitarAutorizacao(username, password);
    });
});

// Funções de processamento
function processarEntrada(entrada) {
    const match = entrada.match(/^(\d*[.,]?\d*)\*(\d+)$/);
    if (match) {
        const quantidade = parseFloat(match[1].replace(',', '.'));
        const codigo = match[2];
        adicionarProduto(codigo, quantidade);
    } else {
        adicionarProduto(entrada, 1);
    }
}

function adicionarProduto(codigo, quantidade) {
    fetch(`/api/produtos/${codigo}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const produto = data.product;
                const item = {
                    id: produto.id,
                    codigo: produto.code,
                    nome: produto.name,
                    quantidade: quantidade,
                    unidade: produto.unit,
                    preco: produto.selling_price,
                    total: quantidade * produto.selling_price
                };
                
                itens.push(item);
                atualizarTabela();
                atualizarTotal();
            } else {
                alert('Produto não encontrado!');
            }
        });
}

// Funções de atualização da UI
function atualizarTabela() {
    const tbody = document.querySelector('#itemsTable tbody');
    tbody.innerHTML = '';
    
    itens.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.codigo}</td>
            <td>${item.nome}</td>
            <td>${item.quantidade.toFixed(3)}</td>
            <td>${item.unidade}</td>
            <td>R$ ${item.preco.toFixed(2)}</td>
            <td>R$ ${item.total.toFixed(2)}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="removerItem(${index})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function atualizarTotal() {
    const total = calcularTotal();
    document.getElementById('totalVenda').textContent = total.toFixed(2);
}

function calcularTotal() {
    return itens.reduce((sum, item) => sum + item.total, 0);
}

function calcularTroco() {
    const total = parseFloat(document.getElementById('totalVendaFinal').value);
    const recebido = parseFloat(this.value) || 0;
    const troco = recebido - total;
    document.getElementById('trocoVenda').value = troco >= 0 ? troco.toFixed(2) : '0.00';
}

// Funções de manipulação de itens
function removerItem(index) {
    itens.splice(index, 1);
    atualizarTabela();
    atualizarTotal();
}

// Funções de consulta
function consultarPreco() {
    modalConsultaPreco.show();
    const inputConsultaPreco = document.getElementById('codigoConsulta');
    if (inputConsultaPreco) {
        inputConsultaPreco.value = '';
        inputConsultaPreco.focus();
    }
}

function buscarProduto() {
    const busca = document.getElementById('codigoConsulta').value.trim();
    if (!busca) {
        alert('Digite um código ou nome para buscar');
        return;
    }

    fetch(`/api/produtos/buscar?q=${encodeURIComponent(busca)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById('tabelaConsultaPreco');
                tbody.innerHTML = '';
                
                data.data.forEach(produto => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${produto.code}</td>
                        <td>${produto.name}</td>
                        <td>${formatMoney(produto.selling_price)}</td>
                        <td>${produto.stock}</td>
                        <td>${produto.unit}</td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                alert(data.error || 'Erro ao buscar produtos');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao buscar produtos');
        });
}

function consultarDividas() {
    modalConsultaDividas.show();
}

function buscarDividas() {
    const matricula = document.getElementById('matriculaDividas').value;
    
    // Primeiro busca o cliente pela matrícula
    fetch(`/buscar/${matricula}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Agora busca as dívidas do cliente
                return fetch(`/api/clientes/${data.customer.id}/dividas`);
            } else {
                throw new Error('Cliente não encontrado');
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#tabelaDividas tbody');
                tbody.innerHTML = '';
                
                data.dividas.forEach(divida => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${divida.due_date ? new Date(divida.due_date).toLocaleDateString() : '-'}</td>
                        <td>${formatMoney(divida.amount)}</td>
                        <td>${formatMoney(divida.paid_amount)}</td>
                        <td>${formatMoney(divida.remaining_amount)}</td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="pagarDividaParcial(${divida.id})">
                                Pagar
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } else {
                alert(data.error || 'Erro ao buscar dívidas');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao buscar dívidas');
        });
}

// Funções de pagamento
function pagarDividaParcial(dividaId) {
    const modalPagamentoDivida = document.getElementById('modalPagamentoDivida');
    if (!modalPagamentoDivida) {
        console.error('Modal de pagamento não encontrado');
        return;
    }

    // Limpa os campos do formulário
    const formPagamento = modalPagamentoDivida.querySelector('form');
    if (formPagamento) {
        formPagamento.reset();
    }

    // Define o ID da dívida
    const inputDividaId = document.getElementById('dividaId');
    if (inputDividaId) {
        inputDividaId.value = dividaId;
    }

    // Mostra o modal
    const modal = bootstrap.Modal.getInstance(modalPagamentoDivida) || new bootstrap.Modal(modalPagamentoDivida);
    modal.show();
}

function pagarDivida() {
    const dividaId = document.getElementById('dividaId')?.value;
    const valorInput = document.getElementById('valorPagamento');
    const formaPagamentoInput = document.getElementById('formaPagamentoDivida');

    if (!dividaId || !valorInput || !formaPagamentoInput) {
        alert('Erro: Campos necessários não encontrados');
        return;
    }

    const valor = parseFloat(valorInput.value);
    if (isNaN(valor) || valor <= 0) {
        alert('Digite um valor válido para o pagamento');
        return;
    }

    const formaPagamento = formaPagamentoInput.value;
    if (!formaPagamento) {
        alert('Selecione uma forma de pagamento');
        return;
    }

    fetch(`/api/dividas/${dividaId}/pagar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            valor: valor,
            forma_pagamento: formaPagamento
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Pagamento realizado com sucesso!');
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalPagamentoDivida'));
            if (modal) {
                modal.hide();
            }
            buscarDividas(); // Atualiza a lista de dívidas
        } else {
            alert(data.error || 'Erro ao processar pagamento');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao processar pagamento');
    });
}

// Funções de finalização de venda
function finalizarVenda() {
    if (itens.length === 0) {
        alert('Adicione itens à venda primeiro!');
        return;
    }
    
    const total = calcularTotal();
    document.getElementById('totalVendaFinal').value = total.toFixed(2);
    modalFinalizarVenda.show();
}

function toggleParcelas() {
    const formaPagamento = document.getElementById('formaPagamento').value;
    const divParcelas = document.getElementById('divParcelas');
    
    if (formaPagamento === 'crediario') {
        divParcelas.classList.remove('d-none');
        // Se não tiver cliente selecionado
        if (!window.clienteAtual) {
            alert('Por favor, selecione um cliente para venda no crediário');
            document.getElementById('formaPagamento').value = 'dinheiro';
            divParcelas.classList.add('d-none');
            return;
        }
    } else {
        divParcelas.classList.add('d-none');
    }
}

// Funções de autorização
async function solicitarAutorizacao(username, password) {
    try {
        const response = await fetch('/api/vendas/autorizar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            vendaAutorizada = true;
            modalConfirmSemLimite.hide();
            confirmarVenda();
        } else {
            alert(result.error || 'Erro ao autorizar venda');
        }
    } catch (error) {
        console.error('Erro ao autorizar venda:', error);
        alert('Erro ao autorizar venda');
    }
}

async function confirmarVenda() {
    const formaPagamento = document.getElementById('formaPagamento').value;
    const total = calcularTotal();
    
    // Se for crediário, verifica o cliente e limite
    if (formaPagamento === 'crediario') {
        // Se não tem cliente selecionado
        if (!window.clienteAtual) {
            alert('Selecione um cliente para venda no crediário');
            return;
        }
        
        // Se não está autorizada, verifica o limite
        if (!vendaAutorizada) {
            const limiteDisponivel = window.clienteAtual.credit_limit - window.clienteAtual.current_debt;
            if (limiteDisponivel < total) {
                document.getElementById('msgSemLimite').textContent = 
                    `O cliente ${window.clienteAtual.name} possui limite disponível de R$ ${limiteDisponivel.toFixed(2)}, ` +
                    `mas a venda atual é de R$ ${total.toFixed(2)}. Deseja autorizar mesmo assim?`;
                modalFinalizarVenda.hide();
                modalConfirmSemLimite.show();
                return;
            }
        }
    }
    
    // Continua com a venda
    try {
        const parcelas = [];
        if (formaPagamento === 'crediario') {
            const numParcelas = parseInt(document.getElementById('numParcelas').value);
            const valorParcela = total / numParcelas;
            
            for (let i = 0; i < numParcelas; i++) {
                const dataVencimento = new Date();
                dataVencimento.setMonth(dataVencimento.getMonth() + i + 1);
                parcelas.push({
                    due_date: dataVencimento.toISOString().split('T')[0],
                    amount: valorParcela
                });
            }
        }
        
        const venda = {
            customer_id: window.clienteAtual ? window.clienteAtual.id : null,
            items: itens.map(item => ({
                product_id: item.id,
                quantity: item.quantidade,
                price: item.preco
            })),
            payment_method: formaPagamento,
            authorized: vendaAutorizada,
            receivables: parcelas
        };

        // Adiciona o valor recebido se for pagamento em dinheiro
        if (formaPagamento === 'dinheiro') {
            const valorRecebido = parseFloat(document.getElementById('valorRecebido').value);
            if (!isNaN(valorRecebido)) {
                venda.received_amount = valorRecebido;
            }
        }
        
        const response = await fetch('/api/vendas', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(venda)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Venda realizada com sucesso!');
            location.reload();
        } else {
            alert(result.error || 'Erro ao finalizar venda');
        }
    } catch (error) {
        console.error('Erro ao finalizar venda:', error);
        alert('Erro ao finalizar venda');
    }
}

function formatMoney(value) {
    return `R$ ${value.toFixed(2)}`;
}
