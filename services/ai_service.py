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
        raise Exception(f"Failed to extract barcode from image: {str(e)}")

def _call_ai_service(prompt, max_tokens=300, temperature=0.7):
    """Helper function to call AI service with fallback logic"""
    anthropic_client = get_client()
    openai_client = get_openai_client()
    
    if not anthropic_client and not openai_client:
        return None
    
    try:
        if anthropic_client:
            response = anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        elif openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
    except Exception as e:
        return None

def get_meal_recommendation(recent_logs, dietary_restrictions, calorie_goal, preferred_cuisine, recommendation_type='meal'):
    """Get AI-powered meal recommendation using Anthropic Claude or OpenAI"""
    
    if not get_client() and not get_openai_client():
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
        
        # Get response from AI service
        result = _call_ai_service(prompt, max_tokens=300, temperature=0.7)
        if result:
            return result
        else:
            return f"I'd be happy to help with meal recommendations, but I'm having trouble connecting to the AI service right now. Consider balancing your meals with lean proteins, whole grains, and plenty of vegetables to meet your {calorie_goal} calorie goal."
    
    except Exception as e:
        return f"I'd be happy to help with meal recommendations, but I'm having trouble connecting to the AI service right now. Consider balancing your meals with lean proteins, whole grains, and plenty of vegetables to meet your {calorie_goal} calorie goal."

