// Stone Section Counter
let stoneCounter = 1;

// Stone Configurations
const stoneConfigs = {
    'diamond': {
        weight: {
            label: 'Diamond Weight (carats)',
            step: 0.001,
            min: 0
        },
        count: {
            label: 'Number of Diamonds',
            min: 1
        },
        quality: {
            label: 'Diamond Quality',
            options: [
                { value: 'D-IF', label: 'D-IF (Flawless)' },
                { value: 'E-VVS1', label: 'E-VVS1 (Very Very Slightly Included 1)' },
                { value: 'F-VVS2', label: 'F-VVS2 (Very Very Slightly Included 2)' },
                { value: 'G-VS1', label: 'G-VS1 (Very Slightly Included 1)' },
                { value: 'H-VS2', label: 'H-VS2 (Very Slightly Included 2)' },
                { value: 'I-SI1', label: 'I-SI1 (Slightly Included 1)' },
                { value: 'J-SI2', label: 'J-SI2 (Slightly Included 2)' }
            ]
        }
    },
    'ruby': {
        weight: {
            label: 'Ruby Weight (carats)',
            step: 0.01,
            min: 0
        },
        count: {
            label: 'Number of Rubies',
            min: 1
        },
        quality: {
            label: 'Ruby Quality',
            options: [
                { value: 'pigeon-blood', label: 'Pigeon Blood (Premium)' },
                { value: 'vivid-red', label: 'Vivid Red (Fine)' },
                { value: 'medium-red', label: 'Medium Red (Good)' },
                { value: 'light-red', label: 'Light Red (Commercial)' }
            ]
        }
    },
    'sapphire': {
        weight: {
            label: 'Sapphire Weight (carats)',
            step: 0.01,
            min: 0
        },
        count: {
            label: 'Number of Sapphires',
            min: 1
        },
        quality: {
            label: 'Sapphire Quality',
            options: [
                { value: 'royal-blue', label: 'Royal Blue (Premium)' },
                { value: 'cornflower-blue', label: 'Cornflower Blue (Fine)' },
                { value: 'medium-blue', label: 'Medium Blue (Good)' },
                { value: 'light-blue', label: 'Light Blue (Commercial)' }
            ]
        }
    },
    'emerald': {
        weight: {
            label: 'Emerald Weight (carats)',
            step: 0.01,
            min: 0
        },
        count: {
            label: 'Number of Emeralds',
            min: 1
        },
        quality: {
            label: 'Emerald Quality',
            options: [
                { value: 'muzo-green', label: 'Muzo Green (Premium)' },
                { value: 'vivid-green', label: 'Vivid Green (Fine)' },
                { value: 'medium-green', label: 'Medium Green (Good)' },
                { value: 'light-green', label: 'Light Green (Commercial)' }
            ]
        }
    }
};

// Function to create new stone section
function createStoneSection() {
    stoneCounter++;
    const newSection = `
        <div class="stone-section mb-4">
            <div class="d-flex justify-content-between align-items-center">
                <h5>Stone ${stoneCounter}</h5>
                <button type="button" class="btn btn-danger btn-sm remove-stone">
                    <i class="fas fa-times"></i> Remove
                </button>
            </div>
            <div class="form-group">
                <label>Stone Type</label>
                <select class="form-control stonetype" name="stonetype[]">
                    <option value="">Select Stone Type</option>
                    ${generateStoneOptions()}
                </select>
            </div>
            <div class="stone-details-fields" style="display: none;">
                <!-- Dynamic stone fields will be loaded here -->
            </div>
            <div class="form-group">
                <label>Stone Cost</label>
                <input type="text" class="form-control stone-cost" readonly>
            </div>
        </div>
    `;
    $('#stone-sections').append(newSection);
}

// Function to generate stone type options
function generateStoneOptions() {
    return Object.keys(stoneConfigs).map(type => 
        `<option value="${type}">${type.charAt(0).toUpperCase() + type.slice(1)}</option>`
    ).join('');
}

// Function to fetch and update stone rate
function fetchAndUpdateStoneRate(stoneSection, stoneType, quality) {
    if (!stoneType || !quality) {
        stoneSection.find('.stone-rate-display').val('0');
        stoneSection.find('.stone-rate').val('0');
        return;
    }

    stoneSection.find('.stone-rate-display').val('Loading...');
    
    $.ajax({
        url: '/get-stone-rate/',
        data: {
            stone_type: stoneType,
            quality: quality
        },
        success: function(response) {
            if (response.success) {
                const rate = response.rate;
                const formattedRate = new Intl.NumberFormat('en-IN', {
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 2
                }).format(rate);
                stoneSection.find('.stone-rate-display').val(formattedRate);
                stoneSection.find('.stone-rate').val(rate);
                calculateStoneCost(stoneSection);
            } else {
                stoneSection.find('.stone-rate-display').val('0');
                stoneSection.find('.stone-rate').val('0');
                calculateStoneCost(stoneSection);
            }
        },
        error: function() {
            stoneSection.find('.stone-rate-display').val('0');
            stoneSection.find('.stone-rate').val('0');
            calculateStoneCost(stoneSection);
        }
    });
}

// Function to calculate stone cost
function calculateStoneCost(stoneSection) {
    const weight = parseFloat(stoneSection.find('.stone-weight').val()) || 0;
    const count = parseInt(stoneSection.find('.stone-count').val()) || 1;
    const rate = parseFloat(stoneSection.find('.stone-rate-display').val().replace(/,/g, '')) || 0;
    
    const totalCost = rate * weight * count;
    
    stoneSection.find('.stone-cost').val(new Intl.NumberFormat('en-IN').format(Math.round(totalCost)));
    stoneSection.find('.stone-cost-value').val(totalCost.toFixed(2));
    
    calculateTotalStoneCost();
}

// Function to calculate total stone cost
function calculateTotalStoneCost() {
    let totalStoneCost = 0;
    $('.stone-cost-value').each(function() {
        totalStoneCost += parseFloat($(this).val()) || 0;
    });
    
    $('#total_stone_cost_display').val(new Intl.NumberFormat('en-IN').format(Math.round(totalStoneCost)));
    $('#total_stone_cost').val(totalStoneCost.toFixed(2));
    
    calculateTotal();
}

// Function to calculate total price
function calculateTotal() {
    const metalCost = parseFloat($('#metal_cost').val()) || 0;
    const totalStoneCost = parseFloat($('#total_stone_cost').val()) || 0;
    const makingChargesPercentage = parseFloat($('#making_charges_percentage').val()) || 0;
    
    const makingCharges = (metalCost * makingChargesPercentage) / 100;
    
    $('#making_charges_display').val(new Intl.NumberFormat('en-IN').format(Math.round(makingCharges)));
    $('#making_charges').val(makingCharges.toFixed(2));
    
    const total = metalCost + totalStoneCost + makingCharges;
    
    $('#total_price_display').val(new Intl.NumberFormat('en-IN').format(Math.round(total)));
    $('#total_price').val(total.toFixed(2));
}

// Document Ready Event Handlers
$(document).ready(function() {
    // Add stone button click handler
    $('#add-stone-btn').click(function() {
        createStoneSection();
    });

    // Remove stone button click handler
    $(document).on('click', '.remove-stone', function() {
        $(this).closest('.stone-section').remove();
        calculateTotalStoneCost();
    });

    // Stone type change handler
    $(document).on('change', '.stonetype', function() {
        const selectedOption = $(this).find('option:selected');
        const stoneType = selectedOption.val();
        const stoneSection = $(this).closest('.stone-section');
        const stoneFields = stoneSection.find('.stone-details-fields');
        
        if (!stoneType) {
            stoneFields.hide().empty();
            stoneSection.find('.stone-cost').val('0');
            calculateTotalStoneCost();
            return;
        }

        const config = stoneConfigs[stoneType];
        if (config) {
            stoneFields.html(generateStoneFields(stoneType, config)).show();
            stoneSection.find('.stone-cost').val('0');
            stoneSection.find('.stone-rate-display').val('0');
            calculateTotalStoneCost();
        }
    });

    // Stone quality change handler
    $(document).on('change', '.stone-quality', function() {
        const stoneSection = $(this).closest('.stone-section');
        const stoneType = stoneSection.find('.stonetype').val();
        const quality = $(this).val();
        fetchAndUpdateStoneRate(stoneSection, stoneType, quality);
    });

    // Stone weight and count change handlers
    $(document).on('change', '.stone-weight, .stone-count', function() {
        const stoneSection = $(this).closest('.stone-section');
        calculateStoneCost(stoneSection);
    });

    // Metal weight and purity change handlers
    $('#metal_weight, #metal_purity').change(calculateMetalCost);
    $('#making_charges_percentage').on('input change', calculateTotal);

    // Initialize calculations
    calculateMetalCost();
});

// Function to generate stone fields
function generateStoneFields(stoneType, config) {
    return `
        <div class="form-group">
            <label>${config.weight.label}</label>
            <input type="number" 
                   class="form-control stone-weight" 
                   name="stone_weight[]"
                   step="${config.weight.step}"
                   min="${config.weight.min}"
                   required>
        </div>
        <div class="form-group">
            <label>${config.count.label}</label>
            <input type="number" 
                   class="form-control stone-count" 
                   name="stone_count[]"
                   min="${config.count.min}"
                   value="1"
                   required>
        </div>
        <div class="form-group">
            <label>${config.quality.label}</label>
            <select class="form-control stone-quality" 
                    name="stone_quality[]" 
                    required>
                <option value="">Select Quality</option>
                ${config.quality.options.map(opt => 
                    `<option value="${opt.value}">${opt.label}</option>`
                ).join('')}
            </select>
        </div>
        <div class="form-group">
            <label>Stone Rate (per carat)</label>
            <div class="input-group">
                <div class="input-group-prepend">
                    <span class="input-group-text">₹</span>
                </div>
                <input type="text" class="form-control stone-rate-display" readonly>
                <input type="hidden" class="stone-rate" name="stone_rate[]">
                <input type="hidden" class="stone-cost-value" name="stone_cost[]">
                <div class="input-group-append">
                    <span class="input-group-text">/carat</span>
                </div>
            </div>
        </div>
    `;
} 