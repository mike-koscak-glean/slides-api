#!/usr/bin/env python3
"""
Google Slides API Service for Glean Agent Integration
Simple internal tool for reading and writing slide content with formatting.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import os
import logging
import traceback
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = FastAPI(
    title="Slides Content API",
    description="API for reading and writing Google Slides content with formatting details",
    version="1.0.0"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SCOPES = ['https://www.googleapis.com/auth/presentations']
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service-account.json')

# Request/Response Models
class SlideReadRequest(BaseModel):
    document_id: str

class SlideReadResponse(BaseModel):
    document_id: str
    title: str
    total_slides: int
    slides: List[Dict[str, Any]]
    empty_cells: Dict[str, Dict[str, Dict[str, str]]]  # Organized object IDs for writing

class UseCase(BaseModel):
    number: int
    title: str
    description: str
    department: str
    impact: str
    data_sources: str
    weekly_time_saved: Optional[str] = None

class SlideWriteRequest(BaseModel):
    document_id: str
    use_cases: List[UseCase]

class SlideWriteResponse(BaseModel):
    success: bool
    message: str
    use_cases_written: int
    document_url: str

def authenticate():
    """Authenticate using service account credentials"""
    try:
        logger.info(f"Attempting to load service account from: {SERVICE_ACCOUNT_FILE}")
        
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
            
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        logger.info("Service account credentials loaded successfully")
        return credentials
        
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise

def extract_text_from_element(element):
    """Extract text content from a slide element"""
    text_content = []
    if 'textElements' in element:
        for text_element in element['textElements']:
            if 'textRun' in text_element:
                text_content.append(text_element['textRun']['content'])
    return ''.join(text_content)

def extract_slide_content(slide, slide_index):
    """Extract all content from a single slide"""
    slide_data = {
        'slide_index': slide_index,
        'slide_id': slide.get('objectId', ''),
        'elements': []
    }
    
    if 'pageElements' not in slide:
        return slide_data
    
    for element in slide['pageElements']:
        element_data = {
            'object_id': element.get('objectId', ''),
            'element_type': None,
            'content': '',
            'position': None,
            'size': None
        }
        
        # Extract position and size
        if 'transform' in element:
            transform = element['transform']
            element_data['position'] = {
                'x': transform.get('translateX', 0),
                'y': transform.get('translateY', 0)
            }
            element_data['size'] = {
                'width': transform.get('scaleX', 0),
                'height': transform.get('scaleY', 0)
            }
        
        # Extract text content from shapes
        if 'shape' in element:
            element_data['element_type'] = 'shape'
            shape = element['shape']
            if 'text' in shape and 'textElements' in shape['text']:
                element_data['content'] = extract_text_from_element(shape['text'])
        
        # Extract text content from text boxes
        elif 'textBox' in element:
            element_data['element_type'] = 'textBox'
            text_box = element['textBox']
            if 'text' in text_box and 'textElements' in text_box['text']:
                element_data['content'] = extract_text_from_element(text_box['text'])
        
        slide_data['elements'].append(element_data)
    
    return slide_data

def identify_empty_cells(slides_data):
    """Identify empty table cells organized for writing use cases"""
    empty_cells = {}
    
    # Focus on slides 3-6 (typical use case slides)
    target_slides = [slide for slide in slides_data['slides'] if slide['slide_index'] in [3, 4, 5, 6]]
    
    for slide in target_slides:
        slide_id = slide['slide_id']
        empty_elements = [elem for elem in slide['elements'] if elem['content'].strip() == '']
        
        if len(empty_elements) >= 4:  # At least one row of table cells
            # Organize empty cells into table structure
            # This assumes a standard table layout - adjust based on your template
            row_cells = {}
            
            # Group empty elements by Y position (rows)
            y_positions = {}
            for elem in empty_elements:
                if elem['position']:
                    y = elem['position']['y']
                    if y not in y_positions:
                        y_positions[y] = []
                    y_positions[y].append(elem)
            
            # Sort by Y position and organize into rows
            sorted_rows = sorted(y_positions.items())
            for row_idx, (y_pos, row_elements) in enumerate(sorted_rows):
                if len(row_elements) >= 4:  # Full row (description, department, impact, data_sources)
                    # Sort by X position
                    row_elements.sort(key=lambda x: x['position']['x'] if x['position'] else 0)
                    
                    row_key = f"row{row_idx + 1}"
                    row_cells[row_key] = {
                        'description': row_elements[0]['object_id'],
                        'department': row_elements[1]['object_id'], 
                        'impact': row_elements[2]['object_id'],
                        'data_sources': row_elements[3]['object_id']
                    }
            
            if row_cells:
                empty_cells[slide_id] = row_cells
    
    return empty_cells

def write_title_description_to_cell(object_id, title, description):
    """Create requests to write title (8pt bold) + description (7pt) to a cell"""
    full_text = f"{title} {description}"
    
    requests = [
        {
            'insertText': {
                'objectId': object_id,
                'text': full_text,
                'insertionIndex': 0
            }
        },
        # Format title (8pt bold Arial)
        {
            'updateTextStyle': {
                'objectId': object_id,
                'textRange': {
                    'type': 'FIXED_RANGE',
                    'startIndex': 0,
                    'endIndex': len(title)
                },
                'style': {
                    'fontFamily': 'Arial',
                    'fontSize': {'magnitude': 8, 'unit': 'PT'},
                    'bold': True,
                    'foregroundColor': {'opaqueColor': {'themeColor': 'DARK1'}}
                },
                'fields': 'fontFamily,fontSize,bold,foregroundColor'
            }
        },
        # Format description (7pt Arial)
        {
            'updateTextStyle': {
                'objectId': object_id,
                'textRange': {
                    'type': 'FIXED_RANGE',
                    'startIndex': len(title),
                    'endIndex': len(full_text)
                },
                'style': {
                    'fontFamily': 'Arial',
                    'fontSize': {'magnitude': 7, 'unit': 'PT'},
                    'foregroundColor': {'opaqueColor': {'themeColor': 'DARK1'}}
                },
                'fields': 'fontFamily,fontSize,foregroundColor'
            }
        }
    ]
    
    return requests

def write_text_to_cell(object_id, text, font_size=8):
    """Create requests to write text to a cell with specified font size"""
    return [
        {
            'insertText': {
                'objectId': object_id,
                'text': text,
                'insertionIndex': 0
            }
        },
        {
            'updateTextStyle': {
                'objectId': object_id,
                'textRange': {'type': 'ALL'},
                'style': {
                    'fontFamily': 'Arial',
                    'fontSize': {'magnitude': font_size, 'unit': 'PT'},
                    'foregroundColor': {'opaqueColor': {'themeColor': 'DARK1'}}
                },
                'fields': 'fontFamily,fontSize,foregroundColor'
            }
        }
    ]

@app.get("/")
async def root():
    return {"message": "Slides Content API", "version": "1.0.0"}

@app.post("/slides/read", response_model=SlideReadResponse)
async def read_slides(request: SlideReadRequest):
    """
    Read slide content and structure with formatting details.
    Returns organized object IDs for writing use cases.
    """
    try:
        logger.info(f"Reading slides for document: {request.document_id}")
        
        credentials = authenticate()
        service = build('slides', 'v1', credentials=credentials)
        
        logger.info("Google Slides service created successfully")
        
        # Get the presentation
        presentation = service.presentations().get(
            presentationId=request.document_id
        ).execute()
        
        # Extract data from all slides
        slides_data = {
            'presentation_id': request.document_id,
            'title': presentation.get('title', ''),
            'total_slides': len(presentation.get('slides', [])),
            'slides': []
        }
        
        slides = presentation.get('slides', [])
        for i, slide in enumerate(slides):
            slide_data = extract_slide_content(slide, i + 1)
            slides_data['slides'].append(slide_data)
        
        # Identify empty cells for writing
        empty_cells = identify_empty_cells(slides_data)
        
        return SlideReadResponse(
            document_id=request.document_id,
            title=slides_data['title'],
            total_slides=slides_data['total_slides'],
            slides=slides_data['slides'],
            empty_cells=empty_cells
        )
        
    except HttpError as e:
        logger.error(f"Google API error: {e}")
        if e.resp.status == 404:
            raise HTTPException(status_code=404, detail=f"Document not found: {request.document_id}")
        elif e.resp.status == 403:
            raise HTTPException(status_code=403, detail=f"Access denied to document: {request.document_id}. Ensure service account has view access.")
        else:
            raise HTTPException(status_code=500, detail=f"Google API error: {e}")
    except FileNotFoundError as e:
        logger.error(f"Service account file not found: {e}")
        raise HTTPException(status_code=500, detail="Service account configuration error")
    except Exception as e:
        logger.error(f"Unexpected error reading slides: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error reading slides: {str(e)}")

@app.post("/slides/write", response_model=SlideWriteResponse)
async def write_slides(request: SlideWriteRequest):
    """
    Write use cases to slide template with proper formatting.
    Requires document to have empty table template structure.
    """
    try:
        credentials = authenticate()
        service = build('slides', 'v1', credentials=credentials)
        
        # First read the current structure to get object IDs
        read_request = SlideReadRequest(document_id=request.document_id)
        slide_data = await read_slides(read_request)
        
        empty_cells = slide_data.empty_cells
        if not empty_cells:
            raise HTTPException(
                status_code=400, 
                detail="No empty table structure found in slides. Ensure template has empty table cells."
            )
        
        # Organize slides by ID
        slide_ids = list(empty_cells.keys())
        all_requests = []
        use_case_index = 0
        
        for slide_index, slide_id in enumerate(slide_ids):
            if use_case_index >= len(request.use_cases):
                break
                
            # Determine how many use cases for this slide
            remaining_use_cases = len(request.use_cases) - use_case_index
            use_cases_for_slide = min(2, remaining_use_cases) if slide_index < len(slide_ids) - 1 else remaining_use_cases
            
            slide_cells = empty_cells[slide_id]
            rows = [key for key in slide_cells.keys() if key.startswith('row')]
            
            for row_index in range(min(use_cases_for_slide, len(rows))):
                if use_case_index >= len(request.use_cases):
                    break
                    
                use_case = request.use_cases[use_case_index]
                row_key = rows[row_index]
                
                if row_key not in slide_cells:
                    break
                    
                row_cells = slide_cells[row_key]
                
                # Description cell (with bold title)
                title = f"{use_case.number}. {use_case.title}"
                desc_requests = write_title_description_to_cell(
                    row_cells['description'],
                    title,
                    f" {use_case.description}"
                )
                all_requests.extend(desc_requests)
                
                # Department cell (8pt)
                dept_requests = write_text_to_cell(
                    row_cells['department'],
                    use_case.department,
                    font_size=8
                )
                all_requests.extend(dept_requests)
                
                # Impact cell (7pt)
                impact_requests = write_text_to_cell(
                    row_cells['impact'],
                    use_case.impact,
                    font_size=7
                )
                all_requests.extend(impact_requests)
                
                # Data sources cell (8pt)
                data_requests = write_text_to_cell(
                    row_cells['data_sources'],
                    use_case.data_sources,
                    font_size=8
                )
                all_requests.extend(data_requests)
                
                use_case_index += 1
        
        # Execute the requests
        if all_requests:
            response = service.presentations().batchUpdate(
                presentationId=request.document_id,
                body={'requests': all_requests}
            ).execute()
            
            document_url = f"https://docs.google.com/presentation/d/{request.document_id}"
            
            return SlideWriteResponse(
                success=True,
                message=f"Successfully wrote {use_case_index} use cases to slides",
                use_cases_written=use_case_index,
                document_url=document_url
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="No valid table cells found to write use cases"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing slides: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)