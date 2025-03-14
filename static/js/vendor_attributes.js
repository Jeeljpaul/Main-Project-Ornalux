// Function to fetch category attributes
function fetchCategoryAttributes() {
    const categoryId = $('#category').val();
    
    if (!categoryId) {
        $('#attributes-section').hide().empty();
        return;
    }
    
    $.ajax({
        url: '/get-category-attributes/',
        data: { category_id: categoryId },
        success: function(response) {
            if (response.success && response.attributes) {
                displayCategoryAttributes(response.attributes);
            } else {
                $('#attributes-section').hide().empty();
            }
        },
        error: function() {
            $('#attributes-section').hide().empty();
            console.error('Failed to fetch category attributes');
        }
    });
}

// Function to display category attributes
function displayCategoryAttributes(attributes) {
    const container = $('#attributes-section');
    container.empty();
    
    if (attributes.length === 0) {
        container.hide();
        return;
    }
    
    let html = '<h4 class="mt-4">Category Attributes</h4>';
    
    attributes.forEach(attr => {
        const inputId = `attribute_${attr.id}`;
        html += `
            <div class="form-group">
                <label for="${inputId}">${attr.name}</label>
                ${generateAttributeInput(attr, inputId)}
            </div>
        `;
    });
    
    container.html(html).show();
    initializeAttributeHandlers();
}

// Function to generate appropriate input based on attribute type
function generateAttributeInput(attribute, inputId) {
    switch (attribute.data_type.toLowerCase()) {
        case 'number':
            return `
                <input type="number" 
                       class="form-control attribute-input" 
                       id="${inputId}"
                       name="${inputId}"
                       ${attribute.min !== null ? `min="${attribute.min}"` : ''}
                       ${attribute.max !== null ? `max="${attribute.max}"` : ''}
                       ${attribute.required ? 'required' : ''}>
            `;
            
        case 'boolean':
            return `
                <select class="form-control attribute-input" 
                        id="${inputId}"
                        name="${inputId}"
                        ${attribute.required ? 'required' : ''}>
                    <option value="">Select Option</option>
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                </select>
            `;
            
        case 'select':
            if (attribute.options) {
                const options = attribute.options.map(opt => 
                    `<option value="${opt.value}">${opt.label}</option>`
                ).join('');
                
                return `
                    <select class="form-control attribute-input" 
                            id="${inputId}"
                            name="${inputId}"
                            ${attribute.required ? 'required' : ''}>
                        <option value="">Select Option</option>
                        ${options}
                    </select>
                `;
            }
            // Fallback to text input if no options provided
            
        case 'text':
        default:
            return `
                <input type="text" 
                       class="form-control attribute-input" 
                       id="${inputId}"
                       name="${inputId}"
                       ${attribute.required ? 'required' : ''}>
            `;
    }
}

// Function to initialize attribute input handlers
function initializeAttributeHandlers() {
    $('.attribute-input').on('change input', function() {
        validateAttributeInput($(this));
    });
}

// Function to validate attribute input
function validateAttributeInput(input) {
    const value = input.val();
    const isRequired = input.prop('required');
    
    if (isRequired && !value) {
        input.addClass('is-invalid');
        return false;
    }
    
    if (input.attr('type') === 'number') {
        const min = parseFloat(input.attr('min'));
        const max = parseFloat(input.attr('max'));
        const numValue = parseFloat(value);
        
        if (value && (
            (min !== null && numValue < min) || 
            (max !== null && numValue > max)
        )) {
            input.addClass('is-invalid');
            return false;
        }
    }
    
    input.removeClass('is-invalid');
    return true;
}

// Function to collect all attribute values
function collectAttributeValues() {
    const attributes = {};
    $('.attribute-input').each(function() {
        const input = $(this);
        const id = input.attr('id').replace('attribute_', '');
        const value = input.val();
        
        if (value) {
            attributes[id] = {
                value: value,
                type: input.attr('type') === 'number' ? 'number' : 'string'
            };
        }
    });
    return attributes;
}

// Function to validate all attributes
function validateAllAttributes() {
    let isValid = true;
    $('.attribute-input').each(function() {
        if (!validateAttributeInput($(this))) {
            isValid = false;
        }
    });
    return isValid;
}

// Document Ready Event Handlers
$(document).ready(function() {
    // Category change handler
    $('#category').change(function() {
        fetchCategoryAttributes();
    });
    
    // Form submit handler
    $('#product-form').submit(function(e) {
        if (!validateAllAttributes()) {
            e.preventDefault();
            alert('Please check the category attributes. Some values are invalid.');
        }
        
        // Collect and store attribute values
        const attributeValues = collectAttributeValues();
        $('#category_attributes').val(JSON.stringify(attributeValues));
    });
    
    // Initialize attributes if category is pre-selected
    if ($('#category').val()) {
        fetchCategoryAttributes();
    }
}); 