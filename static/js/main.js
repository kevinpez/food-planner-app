// Main JavaScript for Food Planner

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.classList.contains('show')) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }
        }, 5000);
    });

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card, .food-item, .ai-recommendation');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});

// UPC Scanner functionality
function initializeUPCScanner() {
    const scanButton = document.getElementById('scan-barcode');
    const upcInput = document.getElementById('upc-input');
    
    if (scanButton && upcInput) {
        scanButton.addEventListener('click', function() {
            // For now, we'll use a simple prompt
            // In a full implementation, we would use camera API
            const upc = prompt('Enter UPC code:');
            if (upc) {
                upcInput.value = upc;
                searchFoodByUPC(upc);
            }
        });
    }
}

// Search for food by UPC code
async function searchFoodByUPC(upc) {
    const resultsDiv = document.getElementById('search-results');
    if (!resultsDiv) return;
    
    resultsDiv.innerHTML = '<div class="spinner"></div>';
    
    try {
        const response = await fetch(`/api/food/search-upc/${upc}`);
        const data = await response.json();
        
        if (data.success) {
            displayFoodSearchResults([data.food]);
        } else {
            resultsDiv.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = '<div class="alert alert-danger">Error searching for food. Please try again.</div>';
        console.error('Error searching food:', error);
    }
}

// Display food search results
function displayFoodSearchResults(foods) {
    const resultsDiv = document.getElementById('search-results');
    if (!resultsDiv) return;
    
    if (foods.length === 0) {
        resultsDiv.innerHTML = '<div class="alert alert-info">No foods found.</div>';
        return;
    }
    
    let html = '<div class="row">';
    foods.forEach(food => {
        const nutrition = food.nutrition_data || {};
        const calories = nutrition.calories_per_100g || 0;
        
        html += `
            <div class="col-md-6 mb-3">
                <div class="card food-result-card" data-food-id="${food.id}">
                    <div class="card-body">
                        <h6 class="card-title">${food.name}</h6>
                        <p class="card-text">
                            <small class="text-muted">${food.brand || 'Unknown brand'}</small><br>
                            <span class="calories-badge">${calories} cal/100g</span>
                        </p>
                        <button class="btn btn-primary btn-sm" onclick="selectFood(${food.id})">
                            Select Food
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    resultsDiv.innerHTML = html;
}

// Select a food for logging
function selectFood(foodId) {
    const quantityInput = document.getElementById('quantity-input');
    const mealTypeSelect = document.getElementById('meal-type-select');
    
    if (!quantityInput || !mealTypeSelect) {
        alert('Please complete the food logging form');
        return;
    }
    
    const quantity = parseFloat(quantityInput.value);
    const mealType = mealTypeSelect.value;
    
    if (!quantity || quantity <= 0) {
        alert('Please enter a valid quantity');
        return;
    }
    
    logFood(foodId, quantity, mealType);
}

// Log a food item
async function logFood(foodId, quantity, mealType) {
    try {
        const response = await fetch('/api/food/log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                food_id: foodId,
                quantity: quantity,
                meal_type: mealType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Food logged successfully!');
            window.location.href = '/dashboard/';
        } else {
            alert('Error logging food: ' + data.message);
        }
    } catch (error) {
        alert('Error logging food. Please try again.');
        console.error('Error logging food:', error);
    }
}

// Get AI recommendation
async function getAIRecommendation(type = 'meal') {
    const button = document.getElementById('ai-recommend-btn');
    const resultsDiv = document.getElementById('ai-recommendations');
    
    if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Getting recommendation...';
    }
    
    try {
        const response = await fetch('/api/ai/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ type: type })
        });
        
        const data = await response.json();
        
        if (data.success && resultsDiv) {
            const recommendationHtml = `
                <div class="ai-recommendation fade-in">
                    <h6><i class="fas fa-robot me-2"></i>${data.recommendation.type} Recommendation</h6>
                    <p>${data.recommendation.text}</p>
                </div>
            `;
            resultsDiv.innerHTML = recommendationHtml + resultsDiv.innerHTML;
        } else {
            alert('Error getting AI recommendation: ' + (data.message || 'Unknown error'));
        }
    } catch (error) {
        alert('Error getting AI recommendation. Please try again.');
        console.error('Error getting AI recommendation:', error);
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-robot me-2"></i>Get AI Recommendation';
        }
    }
}

// Initialize components when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeUPCScanner();
    
    // Add event listeners for AI recommendation buttons
    const aiButton = document.getElementById('ai-recommend-btn');
    if (aiButton) {
        aiButton.addEventListener('click', () => getAIRecommendation('meal'));
    }
});