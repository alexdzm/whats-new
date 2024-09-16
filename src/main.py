import logging
import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, HttpUrl, validator
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from dotenv import load_dotenv

load_dotenv()

from models import Event

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class URLInput(BaseModel):
    urls: List[str]

    @validator('urls', each_item=True, pre=True)
    def validate_url(cls, v):
        if isinstance(v, str):
            # If the URL doesn't start with a scheme, prepend 'https://'
            if not v.startswith(('http://', 'https://')):
                v = 'https://' + v
            # If the URL starts with 'www.', prepend 'https://'
            elif v.startswith('www.'):
                v = 'https://' + v
        return v

crawler = None

@app.on_event("startup")
async def startup_event():
    global crawler
    logger.info("Initializing WebCrawler...")
    crawler = WebCrawler()
    crawler.warmup()
    logger.info("WebCrawler initialized and warmed up.")

@app.post("/events/", response_model=List[Event])
async def get_events(url_input: URLInput, request: Request):
    logger.info(f"Received request to fetch events for URLs: {url_input.urls}")
    events = []
    for url in url_input.urls:
        logger.info(f"Processing URL: {url}")
        try:
            result = crawler.run(
                url=url,
                word_count_threshold=1,
                extraction_strategy= LLMExtractionStrategy(
                    provider= "openai/gpt-4",
                    api_token = os.environ("OPENAI_API_KEY"),
                    schema=Event.schema(),
                    extraction_type="schema",
                    instruction="""You are an experienced music events analyst. You will be given the content of a website, you must return a list of events from it"""
                ),            
                bypass_cache=True,
            )
            logger.info(f"Successfully extracted events from {url}. Event count: {len(result)}")
            events.extend(result)
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error processing URL {url}: {str(e)}")
    
    logger.info(f"Returning {len(events)} events in total.")
    return events

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Events API"}

# Debug endpoints
@app.get("/debug/log")
async def debug_log():
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    return {"message": "Debug logs generated"}

@app.get("/debug/crawler")
async def debug_crawler():
    if crawler:
        return {"status": "initialized", "type": str(type(crawler))}
    return {"status": "not initialized"}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response