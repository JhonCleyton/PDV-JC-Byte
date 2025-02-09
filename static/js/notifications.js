// Função para carregar notificações do servidor
function loadNotifications() {
    $.get('/api/notifications', function(response) {
        if (response.success) {
            updateNotificationBadge(response.data);
            updateNotificationList(response.data);
            if (window.location.pathname === '/') {
                showPopupNotifications(response.data);
            }
        }
    });
}

// Atualiza o badge com o número de notificações não lidas
function updateNotificationBadge(notifications) {
    const unreadCount = notifications.filter(n => !n.read).length;
    const $badge = $('#notification-count');
    
    $badge.text(unreadCount);
    if (unreadCount > 0) {
        $badge.show();
    } else {
        $badge.hide();
    }
}

// Atualiza a lista de notificações no dropdown
function updateNotificationList(notifications) {
    const $list = $('#notification-list');
    $list.empty();
    
    if (notifications.length === 0) {
        $list.append('<li class="no-notifications">Nenhuma notificação</li>');
        return;
    }

    notifications.forEach(notification => {
        const timeAgo = moment(notification.created_at).fromNow();
        const itemClass = `notification-item ${notification.read ? '' : 'unread'} ${notification.type}`;
        
        const item = `
            <li class="${itemClass}" data-id="${notification.id}">
                <div class="message">${notification.message}</div>
                <div class="d-flex justify-content-between align-items-center">
                    <small class="time">${timeAgo}</small>
                    ${notification.read ? '' : '<button class="btn btn-sm btn-link mark-read">Marcar como lida</button>'}
                </div>
            </li>
        `;
        $list.append(item);
    });
}

// Mostra popup com novas notificações
function showPopupNotifications(notifications) {
    const unreadNotifications = notifications.filter(n => !n.read);
    if (unreadNotifications.length > 0) {
        const notificationList = unreadNotifications
            .map(n => `<div class="notification-item ${n.type}">
                         <div class="message">${n.message}</div>
                      </div>`)
            .join('');
        
        Swal.fire({
            title: 'Novas Notificações',
            html: `<div class="notification-popup">${notificationList}</div>`,
            icon: 'info',
            confirmButtonText: 'OK',
            width: 400
        });
    }
}

// Marca uma notificação como lida
function markAsRead(id) {
    $.post(`/api/notifications/${id}/read`, function(response) {
        if (response.success) {
            loadNotifications();
        }
    });
}

// Inicialização quando o documento estiver pronto
$(document).ready(function() {
    // Carrega notificações iniciais
    loadNotifications();
    
    // Recarrega notificações a cada 5 minutos
    setInterval(loadNotifications, 300000);
    
    // Handler para marcar notificação como lida
    $(document).on('click', '.mark-read', function(e) {
        e.preventDefault();
        e.stopPropagation();
        const $item = $(this).closest('.notification-item');
        markAsRead($item.data('id'));
    });
    
    // Handler para clicar na notificação
    $(document).on('click', '.notification-item', function() {
        const id = $(this).data('id');
        const type = $(this).data('type');
        
        // Se a notificação não foi lida, marca como lida
        if (!$(this).hasClass('read')) {
            markAsRead(id);
        }
        
        // Redireciona baseado no tipo de notificação
        switch(type) {
            case 'receivable_due':
                window.location.href = '/contas-a-receber';
                break;
            case 'payable_due':
                window.location.href = '/contas-a-pagar';
                break;
            case 'product_expiry':
            case 'stock_low':
            case 'stock_critical':
                window.location.href = '/produtos';
                break;
        }
    });
});
