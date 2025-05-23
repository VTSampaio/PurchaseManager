// Purchase Request Form Management
let itemCounter = 0;

function initializeRequestForm() {
    // Setup event listeners - don't add item automatically
    document.getElementById('addItemBtn').addEventListener('click', addItem);
    
    // Validate form on change
    document.getElementById('requestForm').addEventListener('input', validateForm);
    document.getElementById('requestForm').addEventListener('change', validateForm);
    
    // Initial validation
    validateForm();
}

function addItem() {
    itemCounter++;
    
    const itemsContainer = document.getElementById('itemsContainer');
    const noItemsMessage = document.getElementById('noItemsMessage');
    
    // Hide no items message
    noItemsMessage.style.display = 'none';
    
    // Create item HTML with new detailed fields
    const itemHtml = `
        <div class="card mb-3 item-card" data-item-id="${itemCounter}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                    <i class="fas fa-box me-2"></i>Item ${itemCounter}
                </h6>
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeItem(${itemCounter})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Descrição de Insumos *</label>
                        <textarea class="form-control item-descricao" 
                                  name="descricao_insumos[]" 
                                  rows="2"
                                  required 
                                  placeholder="Descrição detalhada do insumo"></textarea>
                    </div>
                    <div class="col-md-2 mb-3">
                        <label class="form-label">QTD *</label>
                        <input type="number" 
                               class="form-control item-quantity" 
                               name="qtd[]" 
                               step="0.01"
                               min="0.01" 
                               required 
                               placeholder="1">
                    </div>
                    <div class="col-md-2 mb-3">
                        <label class="form-label">UND *</label>
                        <select class="form-select" name="und[]" required>
                            <option value="">Selecionar...</option>
                            <option value="UN">UN - Unidade</option>
                            <option value="M">M - Metro</option>
                            <option value="M²">M² - Metro Quadrado</option>
                            <option value="M³">M³ - Metro Cúbico</option>
                            <option value="KG">KG - Quilograma</option>
                            <option value="L">L - Litro</option>
                            <option value="PC">PC - Peça</option>
                            <option value="CJ">CJ - Conjunto</option>
                            <option value="DZ">DZ - Dúzia</option>
                            <option value="HR">HR - Hora</option>
                            <option value="DIA">DIA - Dia</option>
                            <option value="MÊS">MÊS - Mês</option>
                        </select>
                    </div>
                    <div class="col-md-2 mb-3">
                        <label class="form-label">Cód. Insumo</label>
                        <input type="text" 
                               class="form-control" 
                               name="cod_insumo[]" 
                               placeholder="COD123">
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-3 mb-3">
                        <label class="form-label">Período de Locação</label>
                        <input type="text" 
                               class="form-control" 
                               name="periodo_locacao[]" 
                               placeholder="Ex: 30 dias">
                    </div>
                    <div class="col-md-3 mb-3">
                        <label class="form-label">Demanda</label>
                        <input type="text" 
                               class="form-control" 
                               name="demanda[]" 
                               placeholder="Ex: Urgente">
                    </div>
                    <div class="col-md-3 mb-3">
                        <label class="form-label">Data de Entrega</label>
                        <input type="date" 
                               class="form-control" 
                               name="data_entrega[]">
                    </div>
                    <div class="col-md-3 mb-3">
                        <label class="form-label">Serviço/CPU</label>
                        <input type="text" 
                               class="form-control" 
                               name="servico_cpu[]" 
                               placeholder="Ex: Instalação">
                    </div>
                </div>
                <div class="row">
                    <div class="col-12 mb-3">
                        <label class="form-label">Observações</label>
                        <textarea class="form-control" 
                                  name="observacoes[]" 
                                  rows="2" 
                                  placeholder="Observações adicionais sobre o item"></textarea>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    itemsContainer.insertAdjacentHTML('beforeend', itemHtml);
    
    // Focus on the new item description field
    const newItemDescField = itemsContainer.querySelector(`[data-item-id="${itemCounter}"] .item-descricao`);
    newItemDescField.focus();
    
    // Validate form after adding item
    validateForm();
}

function removeItem(itemId) {
    const itemCard = document.querySelector(`[data-item-id="${itemId}"]`);
    
    // Confirm removal if there's content
    const itemDesc = itemCard.querySelector('.item-descricao').value;
    if (itemDesc.trim() && !confirm('Tem certeza que deseja remover este item?')) {
        return;
    }
    
    itemCard.remove();
    
    // Check if any items remain
    const remainingItems = document.querySelectorAll('.item-card');
    if (remainingItems.length === 0) {
        document.getElementById('noItemsMessage').style.display = 'block';
    }
    
    // Renumber remaining items
    renumberItems();
    
    // Validate form after removing item
    validateForm();
}

function renumberItems() {
    const itemCards = document.querySelectorAll('.item-card');
    itemCards.forEach((card, index) => {
        const itemNumber = index + 1;
        const header = card.querySelector('.card-header h6');
        header.innerHTML = `<i class="fas fa-box me-2"></i>Item ${itemNumber}`;
    });
}

function validateForm() {
    const requesterName = document.getElementById('requester_name').value.trim();
    const itemCards = document.querySelectorAll('.item-card');
    const submitBtn = document.getElementById('submitBtn');
    
    let isValid = true;
    
    // Check requester name
    if (!requesterName) {
        isValid = false;
    }
    
    // Check if there are items and they are valid
    let hasValidItems = false;
    itemCards.forEach(card => {
        const itemDesc = card.querySelector('.item-descricao').value.trim();
        const itemQuantity = parseFloat(card.querySelector('.item-quantity').value) || 0;
        const itemUnit = card.querySelector('select[name="und[]"]').value;
        
        if (itemDesc && itemQuantity > 0 && itemUnit) {
            hasValidItems = true;
        }
    });
    
    if (!hasValidItems) {
        isValid = false;
    }
    
    // Enable/disable submit button
    submitBtn.disabled = !isValid;
    
    return isValid;
}

// Form submission handling
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('requestForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                alert('Por favor, preencha todos os campos obrigatórios antes de enviar.');
                return false;
            }
            
            // Show loading state
            const submitBtn = document.getElementById('submitBtn');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enviando...';
            submitBtn.disabled = true;
            
            // If validation fails on server side, restore button
            setTimeout(() => {
                if (submitBtn.disabled) {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            }, 5000);
        });
    }
});

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});
