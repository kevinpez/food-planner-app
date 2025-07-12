import os
from config import Config
import json
import base64

# Initialize Anthropic client
client = None

# Initialize OpenAI client for GPT-4o Vision
openai_client = None

def get_client():
    global client
    if client is None and Config.ANTHROPIC_API_KEY:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        except Exception as e:
            print(f"Error initializing Anthropic client: {str(e)}")
            client = False
    return client

def get_openai_client():
    global openai_client
    if openai_client is None and hasattr(Config, 'OPENAI_API_KEY') and Config.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            # Initialize with minimal parameters to avoid conflicts
            openai_client = OpenAI(
                api_key=Config.OPENAI_API_KEY,
                timeout=30.0
            )
        except Exception as e:
            print(f"Error initializing OpenAI client: {str(e)}")
            openai_client = False
    return openai_client

def extract_barcode_from_image(image_path):
    """Extract barcode from image using GPT-4o Vision"""
    
    client = get_openai_client()
    if not client:
        raise Exception("OpenAI API key not configured for barcode scanning")
    
    try:
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Create the prompt for barcode detection
        prompt = """
        Look at this image and extract any barcode numbers you can see. 
        Focus on finding UPC barcodes (typically 12 digits) or EAN barcodes (typically 13 digits).
        
        Rules:
        1. Only return the numeric barcode if you can clearly see one
        2. Return just the numbers, no other text
        3. If you cannot clearly read a barcode, return "NONE"
        4. Look for barcodes on product packaging
        
        Return only the barcode number or "NONE".
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        
        # Validate the result
        if result == "NONE" or not result.isdigit():
            return None
        
        # Check if it's a valid UPC/EAN length
        if len(result) not in [12, 13, 14]:
            return None
        
        return result
        
    except Exception as e:
        print(f"Error extracting barcode: {str(e)}")
        raise Exception(f"Failed to extract barcode from image: {str(e)}")

def get_meal_recommendation(recent_logs, dietary_restrictions, calorie_goal, preferred_cuisine, recommendation_type='meal'):
    """Get AI-powered meal recommendation using Anthropic Claude or OpenAI"""
    
    # Try Anthropic first, then fallback to OpenAI
    anthropic_client = get_client()
    openai_client = get_openai_client()
    
    if not anthropic_client and not openai_client:
        return "AI recommendations are not available. Please configure either Anthropic or OpenAI API key."
    
    try:
        # Prepare context from recent food logs
        recent_foods = []
        total_recent_calories = 0
        
        for log in recent_logs:
            food_info = {
                'name': log.food.name,
                'brand': log.food.brand,
                'quantity': log.quantity,
                'calories': log.get_calories(),
                'meal_type': log.meal_type,
                'date': log.logged_at.strftime('%Y-%m-%d')
            }
            recent_foods.append(food_info)
            total_recent_calories += log.get_calories()
        
        # Create prompt for AI
        prompt = f"""
        You are a helpful nutrition assistant. Based on the following information about a user's recent food intake, 
        provide a personalized {recommendation_type} recommendation.
        
        USER PROFILE:
        - Daily calorie goal: {calorie_goal} calories
        - Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
        - Preferred cuisine: {preferred_cuisine or 'No preference'}
        
        RECENT FOOD INTAKE (last 10 items):
        {json.dumps(recent_foods, indent=2) if recent_foods else 'No recent food logs'}
        
        GUIDELINES:
        1. Consider the user's calorie goal and recent intake
        2. Respect dietary restrictions
        3. Consider preferred cuisine if specified
        4. Provide specific, actionable recommendations
        5. Include estimated calorie information
        6. Keep recommendations realistic and achievable
        7. Focus on nutritional balance
        
        Please provide a {recommendation_type} recommendation in 2-3 sentences. Be specific about food suggestions 
        and include brief reasoning for your recommendation.
        """
        
        # Get response from available AI provider
        if anthropic_client:
            response = anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=300,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.content[0].text
        
        elif openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                max_tokens=300,
                temperature=0.7,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            return response.choices[0].message.content
    
    except Exception as e:
        print(f"Error getting AI recommendation: {str(e)}")
        return f"I'd be happy to help with meal recommendations, but I'm having trouble connecting to the AI service right now. Consider balancing your meals with lean proteins, whole grains, and plenty of vegetables to meet your {calorie_goal} calorie goal."

def get_health_insights(food_logs, user_preferences):
    """Get health insights based on food intake patterns"""
    
    anthropic_client = get_client()
    openai_client = get_openai_client()
    
    if not anthropic_client and not openai_client:
        return "Health insights are not available. Please configure either Anthropic or OpenAI API key."
    
    try:
        # Analyze food patterns
        meal_patterns = {}
        total_calories = 0
        food_categories = {}
        
        for log in food_logs:
            # Track meal patterns
            meal_type = log.meal_type
            if meal_type not in meal_patterns:
                meal_patterns[meal_type] = {'count': 0, 'calories': 0}
            meal_patterns[meal_type]['count'] += 1
            meal_patterns[meal_type]['calories'] += log.get_calories()
            
            total_calories += log.get_calories()
            
            # Simple food categorization based on name
            food_name = log.food.name.lower()
            if any(word in food_name for word in ['vegetable', 'fruit', 'salad', 'spinach', 'broccoli']):
                food_categories['fruits_vegetables'] = food_categories.get('fruits_vegetables', 0) + 1
            elif any(word in food_name for word in ['chicken', 'fish', 'beef', 'protein', 'egg']):
                food_categories['proteins'] = food_categories.get('proteins', 0) + 1
            elif any(word in food_name for word in ['bread', 'rice', 'pasta', 'grain']):
                food_categories['grains'] = food_categories.get('grains', 0) + 1
        
        days_tracked = len(set(log.logged_at.date() for log in food_logs))
        avg_daily_calories = total_calories / days_tracked if days_tracked > 0 else 0
        
        prompt = f"""
        You are a nutrition expert analyzing a user's eating patterns. Provide helpful health insights based on the following data:
        
        USER PROFILE:
        - Daily calorie goal: {user_preferences.get('calorie_goal', 2000)} calories
        - Dietary restrictions: {', '.join(user_preferences.get('dietary_restrictions', [])) if user_preferences.get('dietary_restrictions') else 'None'}
        
        EATING PATTERNS (last {days_tracked} days):
        - Average daily calories: {avg_daily_calories:.0f}
        - Total calories tracked: {total_calories:.0f}
        - Meal patterns: {json.dumps(meal_patterns, indent=2)}
        - Food categories: {json.dumps(food_categories, indent=2)}
        
        Please provide 3-4 specific, actionable health insights based on this data. Focus on:
        1. Calorie balance relative to goals
        2. Meal timing and frequency
        3. Food variety and nutritional balance
        4. Specific recommendations for improvement
        
        Keep insights positive and encouraging while being honest about areas for improvement.
        """
        
        if anthropic_client:
            response = anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=400,
                temperature=0.6,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.content[0].text
        
        elif openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                max_tokens=400,
                temperature=0.6,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.choices[0].message.content
    
    except Exception as e:
        print(f"Error getting health insights: {str(e)}")
        return "I'm having trouble analyzing your eating patterns right now. Keep tracking your meals and aim for a balanced diet with plenty of fruits, vegetables, lean proteins, and whole grains."

def get_food_alternatives(food_name, dietary_restrictions):
    """Get healthier alternatives for a specific food"""
    
    anthropic_client = get_client()
    openai_client = get_openai_client()
    
    if not anthropic_client and not openai_client:
        return "Food alternatives are not available. Please configure either Anthropic or OpenAI API key."
    
    try:
        prompt = f"""
        You are a nutrition expert. A user is looking for healthier alternatives to "{food_name}".
        
        USER CONSTRAINTS:
        - Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
        
        Please suggest 3-4 healthier alternatives that:
        1. Are similar in taste or texture
        2. Are generally lower in calories or higher in nutritional value
        3. Respect the user's dietary restrictions
        4. Are commonly available
        
        Format your response as a simple list with brief explanations for each alternative.
        """
        
        if anthropic_client:
            response = anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=250,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.content[0].text
        
        elif openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                max_tokens=250,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.choices[0].message.content
    
    except Exception as e:
        print(f"Error getting food alternatives: {str(e)}")
        return f"Consider healthier alternatives to {food_name} such as options that are baked instead of fried, have less added sugar, or include more whole grains and vegetables."

def analyze_daily_nutrition(daily_logs, calorie_goal):
    """Analyze a single day's nutrition and provide feedback"""
    
    anthropic_client = get_client()
    openai_client = get_openai_client()
    
    if not anthropic_client and not openai_client:
        return "Nutrition analysis is not available. Please configure either Anthropic or OpenAI API key."
    
    try:
        total_calories = sum(log.get_calories() for log in daily_logs)
        meals_by_type = {}
        
        for log in daily_logs:
            meal_type = log.meal_type
            if meal_type not in meals_by_type:
                meals_by_type[meal_type] = []
            meals_by_type[meal_type].append({
                'food': log.food.name,
                'calories': log.get_calories(),
                'quantity': log.quantity
            })
        
        prompt = f"""
        You are a nutrition expert analyzing a user's daily food intake. Provide a brief analysis and suggestions.
        
        DAILY INTAKE:
        - Total calories: {total_calories:.0f}
        - Calorie goal: {calorie_goal}
        - Meals: {json.dumps(meals_by_type, indent=2)}
        
        Please provide:
        1. A brief assessment of the day's nutrition
        2. What went well
        3. One specific suggestion for improvement
        4. Keep it encouraging and under 100 words
        """
        
        if anthropic_client:
            response = anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=150,
                temperature=0.6,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.content[0].text
        
        elif openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                max_tokens=150,
                temperature=0.6,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.choices[0].message.content
    
    except Exception as e:
        print(f"Error analyzing daily nutrition: {str(e)}")
        return f"Your daily intake was {total_calories:.0f} calories. Keep tracking your meals and aim for balanced nutrition throughout the day."