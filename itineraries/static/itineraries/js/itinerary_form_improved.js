/**
 * Improved Itinerary Form with Drag-and-Drop Functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('stops-container');
    const addBtn = document.getElementById('add-stop-btn');
    const form = document.getElementById('itinerary-form');
    const managementForm = document.querySelector('[name="stops-TOTAL_FORMS"]');
    
    // Initialize Sortable for drag-and-drop
    const sortable = new Sortable(container, {
        animation: 150,
        handle: '.drag-handle',
        ghostClass: 'sortable-ghost',
        onEnd: function() {
            updateStopNumbers();
        }
    });
    
    /**
     * Update stop numbers and order fields after reordering
     */
    function updateStopNumbers() {
        const stops = container.querySelectorAll('.stop-item');
        stops.forEach((stop, index) => {
            // Update visible stop number
            const stopNumSpan = stop.querySelector('.stop-num');
            if (stopNumSpan) {
                stopNumSpan.textContent = index + 1;
            }
            
            // Update hidden order field
            const orderField = stop.querySelector('.order-field');
            if (orderField) {
                orderField.value = index + 1;
            }
        });
    }
    
    /**
     * Add a new stop form
     */
    function addStop() {
        const totalForms = parseInt(managementForm.value);
        const template = document.getElementById('stop-form-template');
        const newStop = template.content.cloneNode(true);
        
        // Replace __prefix__ with the actual form index
        const stopDiv = newStop.querySelector('.stop-item');
        stopDiv.setAttribute('data-form-index', totalForms);
        
        // Update all input names and IDs
        stopDiv.innerHTML = stopDiv.innerHTML.replace(/__prefix__/g, totalForms);
        
        // Append to container
        container.appendChild(stopDiv);
        
        // Update total forms count
        managementForm.value = totalForms + 1;
        
        // Update stop numbers
        updateStopNumbers();
        
        // Add remove button handler to the new stop
        const removeBtn = container.lastElementChild.querySelector('.remove-stop-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', function() {
                removeStop(container.lastElementChild);
            });
        }
    }
    
    /**
     * Remove a stop form
     */
    function removeStop(stopElement) {
        // Check if this is the last remaining stop
        const stops = container.querySelectorAll('.stop-item');
        if (stops.length <= 1) {
            alert('You must have at least one stop in your itinerary.');
            return;
        }
        
        // Check if this stop has an ID (i.e., it's saved in the database)
        const idInput = stopElement.querySelector('[name$="-id"]');
        if (idInput && idInput.value) {
            // Mark for deletion instead of removing
            const deleteInput = stopElement.querySelector('[name$="-DELETE"]');
            if (deleteInput) {
                deleteInput.checked = true;
            }
            // Hide the element
            stopElement.style.display = 'none';
        } else {
            // Remove from DOM entirely
            stopElement.remove();
            
            // Update total forms count
            const totalForms = parseInt(managementForm.value);
            managementForm.value = totalForms - 1;
        }
        
        // Update stop numbers
        updateStopNumbers();
    }
    
    /**
     * Initialize remove buttons for existing stops
     */
    function initializeRemoveButtons() {
        const removeBtns = container.querySelectorAll('.remove-stop-btn');
        removeBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const stopElement = this.closest('.stop-item');
                removeStop(stopElement);
            });
        });
    }
    
    /**
     * Form validation before submit
     */
    function validateForm(e) {
        const visibleStops = Array.from(container.querySelectorAll('.stop-item'))
            .filter(stop => stop.style.display !== 'none');
        
        if (visibleStops.length === 0) {
            e.preventDefault();
            alert('Your itinerary must have at least one stop.');
            return false;
        }
        
        // Check for duplicate locations
        const locationIds = [];
        let hasDuplicate = false;
        
        visibleStops.forEach(stop => {
            const locationSelect = stop.querySelector('[name$="-location"]');
            if (locationSelect && locationSelect.value) {
                if (locationIds.includes(locationSelect.value)) {
                    hasDuplicate = true;
                } else {
                    locationIds.push(locationSelect.value);
                }
            }
        });
        
        if (hasDuplicate) {
            e.preventDefault();
            alert('You cannot add the same location multiple times to an itinerary.');
            return false;
        }
        
        return true;
    }
    
    // Initialize
    initializeRemoveButtons();
    updateStopNumbers();
    
    // Event listeners
    if (addBtn) {
        addBtn.addEventListener('click', addStop);
    }
    
    if (form) {
        form.addEventListener('submit', validateForm);
    }
});
