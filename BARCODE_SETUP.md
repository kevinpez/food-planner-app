# Barcode Scanning Feature Setup

## Overview
AI-powered barcode scanning has been added to your Flask food logging app. Users can now upload photos of product barcodes, which are processed using GPT-4o Vision to extract barcode numbers and then looked up in the Open Food Facts database.

## New Files Added

### Backend
- `routes/barcode.py` - New blueprint for barcode scanning routes
- Updated `services/ai_service.py` - Added GPT-4o Vision barcode extraction
- Updated `services/nutrition_api.py` - Added barcode lookup function
- Updated `config.py` - Added OpenAI API key configuration
- Updated `app.py` - Registered barcode blueprint

### Frontend  
- `templates/food/barcode_scan.html` - Photo upload and scanning interface
- Updated `templates/food/log.html` - Added "Photo Scan" option

### Dependencies
- Updated `requirements.txt` - Added openai==1.40.0

## Environment Variables Required

Add these to your `.env` file:

```bash
# Existing variables
ANTHROPIC_API_KEY=your_anthropic_key_here
SECRET_KEY=your_secret_key_here

# New for barcode scanning
OPENAI_API_KEY=your_openai_api_key_here
```

## Installation

1. Install new dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key in the environment variables

3. Restart your Flask application

## Usage Flow

1. User navigates to "Log Food" page
2. Clicks "Scan Photo" button  
3. Uploads photo containing a product barcode
4. AI extracts barcode number from image
5. Barcode is looked up in Open Food Facts database
6. User confirms quantity and meal type
7. Food is logged to their diary

## API Endpoints

- `GET /barcode/scan` - Display barcode scanning interface
- `POST /barcode/scan` - Process uploaded photo and extract barcode
- `POST /barcode/log-scanned` - Log the scanned food item

## Key Features

- **AI-Powered**: Uses GPT-4o Vision for barcode detection
- **Real-time Processing**: User waits on page with loading spinner
- **Temporary Storage**: Images are deleted after processing
- **Mobile Optimized**: Uses camera capture on mobile devices
- **Error Handling**: Graceful handling of failed scans
- **Integrated**: Seamlessly integrated with existing food logging

## Technical Implementation

### Barcode Extraction
- GPT-4o Vision analyzes uploaded images
- Extracts UPC/EAN barcodes (12-14 digits)
- Returns extracted barcode number or null if none found

### Food Lookup  
- Uses Open Food Facts API for nutrition data
- Creates new Food record if not in local database
- Returns structured nutrition data

### Security
- File upload validation (image types only)
- Temporary file cleanup
- CSRF protection on forms
- Input validation on barcode numbers

## Error Scenarios Handled

- No barcode detected in image
- Invalid file types
- Network errors with APIs  
- Missing nutrition data
- File upload failures

## Performance Considerations

- Images are processed server-side (not client-side)
- Temporary files are immediately cleaned up
- API timeouts are configured appropriately
- Expected usage: <100 scans/day (as per requirements)

## Testing

To test the feature:

1. Ensure OpenAI API key is configured
2. Navigate to `/food/log` 
3. Click "Scan Photo"
4. Upload a clear photo of a product barcode
5. Verify nutrition data is displayed
6. Complete the food logging process

## Troubleshooting

**"OpenAI API key not configured"**
- Set OPENAI_API_KEY environment variable

**"No barcode detected"**  
- Ensure photo has clear, readable barcode
- Try different angles or lighting
- Verify barcode is UPC/EAN format

**"Food not found in database"**
- Product may not be in Open Food Facts database
- Try manual UPC entry as fallback

## Future Enhancements

Potential improvements for v2:
- Multiple barcode detection in single image
- Offline barcode scanning capability  
- Product image recognition (non-barcode)
- Batch scanning of multiple products
- Custom product addition workflow