/**
 * Improved Itinerary Form with Drag-and-Drop Functionality
 * FIXED VERSION - Properly handles deletions and reordering
 */

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('stops-container');
    const addBtn = document.getElementById('add-stop-btn');
    const form = document.getElementById('itinerary-form');
    const managementForm = document.querySelector('input[name$="-TOTAL_FORMS"]');
    
    if (!container || !addBtn || !form || !managementForm) {
        console.error('Required elements not found');
        return;
    }
    
    console.log('Itinerary form: Initializing...');
    
    // Initialize Sortable for drag-and-drop
    const sortable = new Sortable(container, {
        animation: 150,
        handle: '.drag-handle',
        ghostClass: 'sortable-ghost',
        onEnd: function() {
            console.log('Drag ended, updating numbers');
            updateStopNumbers();
        }
    });
    
    /**
     * Update stop numbers and order fields after reordering
     * FIXED: Properly handles visible vs hidden stops
     */
    function updateStopNumbers() {
        const stops = Array.from(container.querySelectorAll('.stop-item'))
            .filter(stop => stop.style.display !== 'none');
        
        console.log(`Updating ${stops.length} visible stops`);
        
        stops.forEach((stop, index) => {
            // Update visible stop number
            const stopNumSpan = stop.querySelector('.stop-num');
            if (stopNumSpan) {
                stopNumSpan.textContent = index + 1;
            }
            
            // Update hidden order field
            const orderField = stop.querySelector('.order-field, input[name$="-order"]');
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
        
        if (!template) {
            console.error('Template not found');
            return;
        }
        
        console.log(`Adding new stop, current total: ${totalForms}`);
        
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
        console.log(`New stop added, total forms now: ${totalForms + 1}`);
        
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
     * FIXED: Properly marks for deletion and renumbers remaining stops
     */
    function removeStop(stopElement) {
        // Check if this is the last remaining visible stop
        const visibleStops = Array.from(container.querySelectorAll('.stop-item'))
            .filter(stop => stop.style.display !== 'none');
        
        if (visibleStops.length <= 1) {
            alert('You must have at least one stop in your itinerary.');
            return;
        }
        
        console.log('Removing stop');
        
        // Check if this stop has an ID (i.e., it's saved in the database)
        const idInput = stopElement.querySelector('input[name$="-id"]');
        
        // Always just mark for deletion and hide - don't remove from DOM
        const deleteInput = stopElement.querySelector('input[name$="-DELETE"]');
        if (deleteInput) {
            deleteInput.checked = true;
        }
        stopElement.style.display = 'none';
        
        console.log('Stop marked for deletion and hidden');
        
        // Update stop numbers for remaining visible stops
        updateStopNumbers();
    }
    
    /**
     * Initialize remove buttons for existing stops
     */
    function initializeRemoveButtons() {
        const removeBtns = container.querySelectorAll('.remove-stop-btn');
        console.log(`Initializing ${removeBtns.length} remove buttons`);
        removeBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const stopElement = this.closest('.stop-item');
                removeStop(stopElement);
            });
        });
    }
    
    /**
     * Form validation before submit
     * FIXED: Only validates visible stops
     */
    function validateForm(e) {
        console.log('Validating form before submission');
        
        // Update order fields one final time
        updateStopNumbers();
        
        const visibleStops = Array.from(container.querySelectorAll('.stop-item'))
            .filter(stop => stop.style.display !== 'none');
        
        console.log(`Found ${visibleStops.length} visible stops`);
        
        if (visibleStops.length === 0) {
            e.preventDefault();
            alert('Your itinerary must have at least one stop.');
            return false;
        }
        
        // Check for duplicate locations among visible stops
        const locationIds = [];
        let hasDuplicate = false;
        
        visibleStops.forEach(stop => {
            const locationSelect = stop.querySelector('select[name$="-location"]');
            const deleteInput = stop.querySelector('input[name$="-DELETE"]');
            
            // Skip if marked for deletion
            if (deleteInput && deleteInput.checked) {
                return;
            }
            
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
        
        console.log('Form validation passed');
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
    
    console.log('Itinerary form: Initialization complete');
    console.log(`Initial TOTAL_FORMS: ${managementForm.value}`);
});