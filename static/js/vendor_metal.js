// Metal Configurations
const metalConfigs = {
    'gold': {
        purities: [
            { value: '24', label: '24K - 99.9%' },
            { value: '22', label: '22K - 91.6%' },
            { value: '18', label: '18K - 75.0%' },
            { value: '14', label: '14K - 58.5%' }
        ],
        step: 0.01,
        min: 0
    },
    'silver': {
        purities: [
            { value: '999', label: '999 - Fine Silver' },
            { value: '925', label: '925 - Sterling Silver' },
            { value: '900', label: '900 - Coin Silver' }
        ],
        step: 0.1,
        min: 0
    },
    'platinum': {
        purities: [
            { value: '950', label: '950 - Pure Platinum' },
            { value: '900', label: '900 - Platinum Alloy' }
        ],
        step: 0.01,
        min: 0
    }
};

// Function to fetch and update metal rate
function fetchAndUpdateMetalRate() {
    const metalType = $('#metal_type').val();
    const purity = $('#metal_purity').val();
    
    if (!metalType || !purity) {
        $('#current_rate_display').val('0');
        $('#current_rate').val('0');
        return;
    }

    $('#current_rate_display').val('Loading...');
    
    $.ajax({
        url: '/get-metal-rate/',
        data: {
            metal_type: metalType,
            purity: purity
        },
        success: function(response) {
            if (response.success) {
                const rate = response.rate;
                const formattedRate = new Intl.NumberFormat('en-IN', {
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 2
                }).format(rate);
                $('#current_rate_display').val(formattedRate);
                $('#current_rate').val(rate);
                calculateMetalCost();
            } else {
                $('#current_rate_display').val('0');
                $('#current_rate').val('0');
                calculateMetalCost();
            }
        },
        error: function() {
            $('#current_rate_display').val('0');
            $('#current_rate').val('0');
            calculateMetalCost();
        }
    });
}

// Function to calculate metal cost
function calculateMetalCost() {
    const weight = parseFloat($('#metal_weight').val()) || 0;
    const rate = parseFloat($('#current_rate').val()) || 0;
    const purity = $('#metal_purity').val();
    let purityPercentage = 1;
    
    // Calculate purity percentage based on metal type
    const metalType = $('#metal_type').val();
    if (metalType === 'gold') {
        purityPercentage = parseInt(purity) / 24;
    } else {
        purityPercentage = parseInt(purity) / 1000;
    }
    
    const totalCost = weight * rate * purityPercentage;
    
    $('#metal_cost_display').val(new Intl.NumberFormat('en-IN').format(Math.round(totalCost)));
    $('#metal_cost').val(totalCost.toFixed(2));
    
    calculateTotal(); // Update total price including making charges
}

// Function to update purity options based on metal type
function updatePurityOptions() {
    const metalType = $('#metal_type').val();
    const puritySelect = $('#metal_purity');
    puritySelect.empty();
    
    if (metalType && metalConfigs[metalType]) {
        puritySelect.append('<option value="">Select Purity</option>');
        metalConfigs[metalType].purities.forEach(purity => {
            puritySelect.append(`<option value="${purity.value}">${purity.label}</option>`);
        });
        
        // Update weight input step and min values
        $('#metal_weight').attr({
            'step': metalConfigs[metalType].step,
            'min': metalConfigs[metalType].min
        });
    } else {
        puritySelect.append('<option value="">Select Metal Type First</option>');
    }
    
    // Reset rate and cost
    $('#current_rate_display').val('0');
    $('#current_rate').val('0');
    $('#metal_cost_display').val('0');
    $('#metal_cost').val('0');
    calculateTotal();
}

// Document Ready Event Handlers
$(document).ready(function() {
    // Metal type change handler
    $('#metal_type').change(function() {
        updatePurityOptions();
    });
    
    // Metal purity change handler
    $('#metal_purity').change(function() {
        fetchAndUpdateMetalRate();
    });
    
    // Metal weight change handler
    $('#metal_weight').on('input change', function() {
        calculateMetalCost();
    });
    
    // Initialize metal type options if present
    if ($('#metal_type').length) {
        updatePurityOptions();
    }
}); 