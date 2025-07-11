import requests
from models import db, Food
from config import Config

def search_food_by_upc(upc_code):
    """Search for food by UPC code using Open Food Facts API"""
    url = f"{Config.OPEN_FOOD_FACTS_BASE_URL}/{upc_code}.json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 1:  # Product found
            product = data.get('product', {})
            
            # Extract nutrition data
            nutriments = product.get('nutriments', {})
            nutrition_data = {
                'calories_per_100g': nutriments.get('energy-kcal_100g', 0),
                'protein_per_100g': nutriments.get('proteins_100g', 0),
                'carbs_per_100g': nutriments.get('carbohydrates_100g', 0),
                'fat_per_100g': nutriments.get('fat_100g', 0),
                'fiber_per_100g': nutriments.get('fiber_100g', 0),
                'sugar_per_100g': nutriments.get('sugars_100g', 0),
                'sodium_per_100g': nutriments.get('sodium_100g', 0)
            }
            
            # Create new food item
            food = Food(
                upc_code=upc_code,
                name=product.get('product_name', f'Product {upc_code}'),
                brand=product.get('brands', ''),
                ingredients=product.get('ingredients_text', '')
            )
            food.set_nutrition_data(nutrition_data)
            
            # Save to database
            db.session.add(food)
            db.session.commit()
            
            return food
        
        return None
    
    except requests.RequestException as e:
        print(f"Error searching UPC {upc_code}: {str(e)}")
        return None
    except Exception as e:
        print(f"Error processing UPC {upc_code}: {str(e)}")
        return None

def search_food_by_name(query):
    """Search for food by name using Open Food Facts API"""
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    
    params = {
        'search_terms': query,
        'search_simple': 1,
        'action': 'process',
        'json': 1,
        'page_size': 10
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        foods = []
        
        if data.get('products'):
            for product in data['products'][:10]:  # Limit to 10 results
                # Skip products without names
                if not product.get('product_name'):
                    continue
                
                # Check if we already have this product
                upc_code = product.get('code')
                existing_food = None
                if upc_code:
                    existing_food = Food.query.filter_by(upc_code=upc_code).first()
                
                if existing_food:
                    foods.append(existing_food)
                    continue
                
                # Extract nutrition data
                nutriments = product.get('nutriments', {})
                nutrition_data = {
                    'calories_per_100g': nutriments.get('energy-kcal_100g', 0),
                    'protein_per_100g': nutriments.get('proteins_100g', 0),
                    'carbs_per_100g': nutriments.get('carbohydrates_100g', 0),
                    'fat_per_100g': nutriments.get('fat_100g', 0),
                    'fiber_per_100g': nutriments.get('fiber_100g', 0),
                    'sugar_per_100g': nutriments.get('sugars_100g', 0),
                    'sodium_per_100g': nutriments.get('sodium_100g', 0)
                }
                
                # Create new food item
                food = Food(
                    upc_code=upc_code,
                    name=product.get('product_name', 'Unknown Product'),
                    brand=product.get('brands', ''),
                    ingredients=product.get('ingredients_text', '')
                )
                food.set_nutrition_data(nutrition_data)
                
                # Save to database
                db.session.add(food)
                foods.append(food)
            
            # Commit all new foods
            if foods:
                db.session.commit()
        
        return foods
    
    except requests.RequestException as e:
        print(f"Error searching for '{query}': {str(e)}")
        return []
    except Exception as e:
        print(f"Error processing search for '{query}': {str(e)}")
        return []

def get_nutrition_info(food_id):
    """Get detailed nutrition information for a food item"""
    food = Food.query.get(food_id)
    if not food:
        return None
    
    nutrition_data = food.get_nutrition_data()
    
    # Calculate nutrition info for different serving sizes
    nutrition_info = {
        'food_name': food.name,
        'brand': food.brand,
        'per_100g': nutrition_data,
        'per_serving': {},
        'ingredients': food.ingredients
    }
    
    # If we have a typical serving size, calculate per serving
    # This could be enhanced with serving size data from the API
    serving_size = 100  # Default serving size in grams
    
    for nutrient, value in nutrition_data.items():
        if isinstance(value, (int, float)):
            nutrition_info['per_serving'][nutrient.replace('_per_100g', '_per_serving')] = value * (serving_size / 100)
    
    return nutrition_info

def validate_nutrition_data(nutrition_data):
    """Validate nutrition data before saving"""
    required_fields = ['calories_per_100g']
    
    for field in required_fields:
        if field not in nutrition_data:
            return False, f"Missing required field: {field}"
    
    # Check for reasonable values
    calories = nutrition_data.get('calories_per_100g', 0)
    if calories < 0 or calories > 1000:
        return False, "Calories per 100g must be between 0 and 1000"
    
    return True, "Valid"

def update_food_from_api(food_id):
    """Update existing food item with fresh data from API"""
    food = Food.query.get(food_id)
    if not food or not food.upc_code:
        return False, "Food not found or no UPC code"
    
    try:
        updated_food = search_food_by_upc(food.upc_code)
        if updated_food:
            # Update existing food with new data
            food.name = updated_food.name
            food.brand = updated_food.brand
            food.ingredients = updated_food.ingredients
            food.nutrition_data = updated_food.nutrition_data
            
            # Remove the temporary food created by search_food_by_upc
            db.session.delete(updated_food)
            db.session.commit()
            
            return True, "Food updated successfully"
        else:
            return False, "Could not fetch updated data from API"
    
    except Exception as e:
        return False, f"Error updating food: {str(e)}"