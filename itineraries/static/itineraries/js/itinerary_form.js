// JavaScript for itinerary form handling

document.addEventListener('DOMContentLoaded', function() {
    const stopsContainer = document.getElementById('stops-container');
    const addStopBtn = document.getElementById('add-stop-btn');
    const formsetManagement = document.querySelector('[name$="-TOTAL_FORMS"]');
    
    if (!stopsContainer || !addStopBtn || !formsetManagement) {
        console.error('Required elements not found');
        return;
    }

    // Update stop numbers
    function updateStopNumbers() {
        const stopRows = stopsContainer.querySelectorAll('.stop-form-row:not([style*="display: none"])');
        stopRows.forEach((row, index) => {
            const stopNumber = row.querySelector('.stop-number');
            if (stopNumber) {
                stopNumber.textContent = `Stop ${index + 1}`;
            }
            
            // Auto-update order fields
            const orderInput = row.querySelector('.order-input');
            if (orderInput && !orderInput.value) {
                orderInput.value = index + 1;
            }
        });
    }

    // Add new stop
    addStopBtn.addEventListener('click', function() {
        const totalForms = parseInt(formsetManagement.value);
        const template = document.getElementById('stop-form-template');
        
        if (!template) {
            console.error('Template not found');
            return;
        }

        // Clone template content
        const newForm = template.content.cloneNode(true);
        const newFormDiv = newForm.querySelector('.stop-form-row');
        
        // Replace __prefix__ with actual index
        const formHtml = newFormDiv.innerHTML.replace(/__prefix__/g, totalForms);
        newFormDiv.innerHTML = formHtml;
        newFormDiv.dataset.formIndex = totalForms;
        newFormDiv.classList.add('new');
        
        // Set default order value
        const orderInput = newFormDiv.querySelector('.order-input');
        if (orderInput) {
            orderInput.value = totalForms + 1;
        }

        // Append to container
        stopsContainer.appendChild(newFormDiv);
        
        // Update total forms count
        formsetManagement.value = totalForms + 1;
        
        // Update stop numbers
        updateStopNumbers();
        
        // Add delete handler to new form
        const deleteBtn = newFormDiv.querySelector('.delete-stop-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', handleDeleteStop);
        }

        // Remove animation class after animation completes
        setTimeout(() => {
            newFormDiv.classList.remove('new');
        }, 300);
    });

    // Handle stop deletion
    function handleDeleteStop(event) {
        const stopRow = event.target.closest('.stop-form-row');
        if (!stopRow) return;

        const totalForms = parseInt(formsetManagement.value);
        
        // Check if this is the only stop
        const visibleStops = stopsContainer.querySelectorAll('.stop-form-row:not([style*="display: none"])');
        if (visibleStops.length <= 1) {
            alert('You must have at least one stop in your itinerary.');
            return;
        }

        // Check if this form has an ID (meaning it exists in database)
        const idInput = stopRow.querySelector('[name$="-id"]');
        const deleteInput = stopRow.querySelector('[name$="-DELETE"]');
        
        if (idInput && idInput.value) {
            // Mark for deletion (for existing forms)
            if (deleteInput) {
                deleteInput.checked = true;
            }
            stopRow.style.display = 'none';
        } else {
            // Just remove from DOM (for new forms)
            stopRow.remove();
            
            // Decrease total forms count
            formsetManagement.value = totalForms - 1;
        }

        // Update stop numbers
        updateStopNumbers();
    }

    // Attach delete handlers to existing delete buttons
    const deleteButtons = document.querySelectorAll('.delete-stop-btn');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', handleDeleteStop);
    });

    // Initialize stop numbers
    updateStopNumbers();

    // Form validation
    const form = document.getElementById('itinerary-form');
    if (form) {
        form.addEventListener('submit', function(event) {
            const visibleStops = stopsContainer.querySelectorAll('.stop-form-row:not([style*="display: none"])');
            
            if (visibleStops.length === 0) {
                event.preventDefault();
                alert('Please add at least one stop to your itinerary.');
                return false;
            }

            // Check for duplicate orders
            const orders = [];
            let hasDuplicates = false;
            
            visibleStops.forEach(row => {
                const orderInput = row.querySelector('.order-input');
                const deleteInput = row.querySelector('[name$="-DELETE"]');
                
                // Skip if marked for deletion
                if (deleteInput && deleteInput.checked) {
                    return;
                }
                
                if (orderInput && orderInput.value) {
                    const order = parseInt(orderInput.value);
                    if (orders.includes(order)) {
                        hasDuplicates = true;
                    }
                    orders.push(order);
                }
            });

            if (hasDuplicates) {
                event.preventDefault();
                alert('Each stop must have a unique order number. Please check your order values.');
                return false;
            }

            return true;
        });
    }

    // Auto-sort by order when order changes
    stopsContainer.addEventListener('change', function(event) {
        if (event.target.classList.contains('order-input')) {
            const allRows = Array.from(stopsContainer.querySelectorAll('.stop-form-row:not([style*="display: none"])'));
            
            allRows.sort((a, b) => {
                const orderA = parseInt(a.querySelector('.order-input')?.value || 999);
                const orderB = parseInt(b.querySelector('.order-input')?.value || 999);
                return orderA - orderB;
            });

            // Re-append in sorted order
            allRows.forEach(row => {
                stopsContainer.appendChild(row);
            });

            updateStopNumbers();
        }
    });
});
