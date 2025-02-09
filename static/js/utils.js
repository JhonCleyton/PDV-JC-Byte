// Utility functions
const utils = {
    // Função para formatar valores monetários
    formatMoney: function(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    },

    // Função para formatar datas
    formatDate: function(date) {
        if (!date) return '-';
        try {
            return new Intl.DateTimeFormat('pt-BR', {
                dateStyle: 'short'
            }).format(new Date(date));
        } catch (e) {
            console.error('Error formatting date:', e);
            return '-';
        }
    },

    // Função para formatar data e hora
    formatDateTime: function(isoString) {
        if (!isoString) return '-';
        try {
            const date = new Date(isoString);
            if (isNaN(date.getTime())) return '-';

            return new Intl.DateTimeFormat('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(date);
        } catch (e) {
            console.error('Error formatting datetime:', e);
            return '-';
        }
    }
};

// Expose utils as a global object
window.utils = utils;
