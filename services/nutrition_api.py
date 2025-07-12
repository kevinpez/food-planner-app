import requests
from models import db, Food
from config import Config

def safe_float(value, default=0):
    """Safely convert value to float, return default if conversion fails"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def extract_enhanced_nutrition_data(nutriments):
    """Extract comprehensive nutritional data from Open Food Facts nutriments"""
    return {
        # Basic macronutrients (existing)
        'calories_per_100g': safe_float(nutriments.get('energy-kcal_100g', 0)),
        'protein_per_100g': safe_float(nutriments.get('proteins_100g', 0)),
        'carbs_per_100g': safe_float(nutriments.get('carbohydrates_100g', 0)),
        'fat_per_100g': safe_float(nutriments.get('fat_100g', 0)),
        'fiber_per_100g': safe_float(nutriments.get('fiber_100g', 0)),
        'sugar_per_100g': safe_float(nutriments.get('sugars_100g', 0)),
        'sodium_per_100g': safe_float(nutriments.get('sodium_100g', 0)),
        
        # Detailed fats (new)
        'saturated_fat_per_100g': safe_float(nutriments.get('saturated-fat_100g', 0)),
        'trans_fat_per_100g': safe_float(nutriments.get('trans-fat_100g', 0)),
        'cholesterol_per_100g': safe_float(nutriments.get('cholesterol_100g', 0)),
        'monounsaturated_fat_per_100g': safe_float(nutriments.get('monounsaturated-fat_100g', 0)),
        'polyunsaturated_fat_per_100g': safe_float(nutriments.get('polyunsaturated-fat_100g', 0)),
        
        # Omega fatty acids (new)
        'omega_3_per_100g': safe_float(nutriments.get('omega-3-fat_100g', 0)),
        'omega_6_per_100g': safe_float(nutriments.get('omega-6-fat_100g', 0)),
        'omega_9_per_100g': safe_float(nutriments.get('omega-9-fat_100g', 0)),
        
        # Essential minerals (new)
        'calcium_per_100g': safe_float(nutriments.get('calcium_100g', 0)),
        'iron_per_100g': safe_float(nutriments.get('iron_100g', 0)),
        'potassium_per_100g': safe_float(nutriments.get('potassium_100g', 0)),
        'magnesium_per_100g': safe_float(nutriments.get('magnesium_100g', 0)),
        'zinc_per_100g': safe_float(nutriments.get('zinc_100g', 0)),
        'phosphorus_per_100g': safe_float(nutriments.get('phosphorus_100g', 0)),
        'selenium_per_100g': safe_float(nutriments.get('selenium_100g', 0)),
        'iodine_per_100g': safe_float(nutriments.get('iodine_100g', 0)),
        'copper_per_100g': safe_float(nutriments.get('copper_100g', 0)),
        'manganese_per_100g': safe_float(nutriments.get('manganese_100g', 0)),
        
        # Important vitamins (new)
        'vitamin_c_per_100g': safe_float(nutriments.get('vitamin-c_100g', 0)),
        'vitamin_d_per_100g': safe_float(nutriments.get('vitamin-d_100g', 0)),
        'vitamin_a_per_100g': safe_float(nutriments.get('vitamin-a_100g', 0)),
        'vitamin_e_per_100g': safe_float(nutriments.get('vitamin-e_100g', 0)),
        'vitamin_k_per_100g': safe_float(nutriments.get('vitamin-k_100g', 0)),
        'vitamin_b1_per_100g': safe_float(nutriments.get('vitamin-b1_100g', 0)),
        'vitamin_b2_per_100g': safe_float(nutriments.get('vitamin-b2_100g', 0)),
        'vitamin_b3_per_100g': safe_float(nutriments.get('vitamin-b3_100g', 0)),
        'vitamin_b5_per_100g': safe_float(nutriments.get('vitamin-b5_100g', 0)),
        'vitamin_b6_per_100g': safe_float(nutriments.get('vitamin-b6_100g', 0)),
        'vitamin_b9_per_100g': safe_float(nutriments.get('vitamin-b9_100g', 0)),
        'vitamin_b12_per_100g': safe_float(nutriments.get('vitamin-b12_100g', 0)),
        'biotin_per_100g': safe_float(nutriments.get('biotin_100g', 0)),
        
        # Additional compounds (new)
        'caffeine_per_100g': safe_float(nutriments.get('caffeine_100g', 0)),
        'alcohol_per_100g': safe_float(nutriments.get('alcohol_100g', 0)),
        'taurine_per_100g': safe_float(nutriments.get('taurine_100g', 0))
    }

def extract_product_quality_data(product):
    """Extract quality scores and product metadata from Open Food Facts product data"""
    return {
        # Nutrition and processing scores
        'nutri_score_grade': product.get('nutriscore_grade', '').upper(),
        'nutri_score_score': safe_float(product.get('nutriscore_score')),
        'nova_group': safe_float(product.get('nova_group')),
        'ecoscore_grade': product.get('ecoscore_grade', '').upper(),
        'ecoscore_score': safe_float(product.get('ecoscore_score')),
        
        # Allergens and dietary info
        'allergens': product.get('allergens_tags', []),
        'traces': product.get('traces_tags', []),
        'is_vegan': 'en:vegan' in product.get('labels_tags', []),
        'is_vegetarian': 'en:vegetarian' in product.get('labels_tags', []),
        'is_organic': any('organic' in label.lower() for label in product.get('labels_tags', [])),
        'is_gluten_free': 'en:gluten-free' in product.get('labels_tags', []),
        'is_palm_oil_free': 'en:palm-oil-free' in product.get('labels_tags', []),
        
        # Product metadata
        'serving_size': product.get('serving_size', ''),
        'serving_quantity': safe_float(product.get('serving_quantity')),
        'quantity': product.get('quantity', ''),
        'packaging': product.get('packaging_tags', []),
        'categories': product.get('categories_tags', []),
        'countries': product.get('countries_tags', []),
        'origins': product.get('origins_tags', []),
        'manufacturing_places': product.get('manufacturing_places_tags', []),
        'labels': product.get('labels_tags', []),
        'stores': product.get('stores_tags', []),
        
        # Additional info
        'additives': product.get('additives_tags', []),
        'ingredients_analysis': product.get('ingredients_analysis_tags', []),
        'carbon_footprint': safe_float(product.get('carbon_footprint_100g')),
        'image_url': product.get('image_url', ''),
        'image_front_url': product.get('image_front_url', ''),
        'image_nutrition_url': product.get('image_nutrition_url', '')
    }

def search_food_by_upc(upc_code):
    """Search for food by UPC code using Open Food Facts API"""
    url = f"{Config.OPEN_FOOD_FACTS_BASE_URL}/{upc_code}.json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 1:  # Product found
            product = data.get('product', {})
            
            # Extract nutrition data using enhanced extraction
            nutriments = product.get('nutriments', {})
            nutrition_data = extract_enhanced_nutrition_data(nutriments)
            
            # Extract quality and metadata
            quality_data = extract_product_quality_data(product)
            
            # Create new food item
            food = Food(
                upc_code=upc_code,
                name=product.get('product_name', f'Product {upc_code}'),
                brand=product.get('brands', ''),
                ingredients=product.get('ingredients_text', '')
            )
            
            # Combine nutrition and quality data
            combined_data = {**nutrition_data, **quality_data}
            food.set_nutrition_data(combined_data)
            
            # Save to database
            db.session.add(food)
            db.session.commit()
            
            return food
        
        return None
    
    except requests.RequestException as e:
        return None
    except Exception as e:
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
                
                # Extract nutrition data using enhanced extraction
                nutriments = product.get('nutriments', {})
                nutrition_data = extract_enhanced_nutrition_data(nutriments)
                
                # Extract quality and metadata
                quality_data = extract_product_quality_data(product)
                
                # Create new food item
                food = Food(
                    upc_code=upc_code,
                    name=product.get('product_name', 'Unknown Product'),
                    brand=product.get('brands', ''),
                    ingredients=product.get('ingredients_text', '')
                )
                
                # Combine nutrition and quality data
                combined_data = {**nutrition_data, **quality_data}
                food.set_nutrition_data(combined_data)
                
                # Save to database
                db.session.add(food)
                foods.append(food)
            
            # Commit all new foods
            if foods:
                db.session.commit()
        
        return foods
    
    except requests.RequestException as e:
        return []
    except Exception as e:
        return []


def get_food_by_barcode(barcode):
    """Get food data by barcode for scanning feature - returns dict format"""
    url = f"{Config.OPEN_FOOD_FACTS_BASE_URL}/{barcode}.json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 1:  # Product found
            product = data.get('product', {})
            
            # Extract nutrition data using enhanced extraction
            nutriments = product.get('nutriments', {})
            nutrition_data = extract_enhanced_nutrition_data(nutriments)
            
            # Extract quality and metadata
            quality_data = extract_product_quality_data(product)
            
            # Return data in format expected by barcode scanner
            return {
                'name': product.get('product_name', f'Product {barcode}'),
                'brand': product.get('brands', ''),
                'ingredients': product.get('ingredients_text', ''),
                'nutrition': nutrition_data,
                'quality': quality_data
            }
        
        return None
    
    except requests.RequestException as e:
        return None
    except Exception as e:
        return None