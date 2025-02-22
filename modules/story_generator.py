import json
import time
from typing import Dict, Optional
import requests
from requests.exceptions import RequestException
import os
import re

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)

class StoryGenerator:
    """Generates story content using Ollama."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.endpoint = "http://localhost:11434/api/generate"
        self.story_file = os.path.join(settings.OUTPUT_DIR, "generated_story.txt")
        
    def _clean_story(self, text: str) -> str:
        """Clean up the story text by removing markup and extra whitespace.
        
        Args:
            text: Raw story text from Ollama
            
        Returns:
            Cleaned story text
        """
        # Remove <think> tags and content
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # Remove any other XML-like tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def _make_request(self, prompt: str, retries: int = 0) -> Optional[str]:
        """Make API request to Ollama with retry logic.
        
        Args:
            prompt: The story generation prompt
            retries: Current retry attempt
            
        Returns:
            Generated story text or None if all retries fail
        """
        try:
            response = requests.post(
                self.endpoint,
                json={
                    "model": "deepseek-r1:32b",  # Can be configured in settings
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json().get('response', '')
            
        except RequestException as e:
            if retries < self.settings.MAX_RETRIES:
                logger.warning(f"Ollama request failed, retrying... ({retries + 1}/{self.settings.MAX_RETRIES})")
                time.sleep(self.settings.RETRY_DELAY)
                return self._make_request(prompt, retries + 1)
            else:
                logger.error(f"Failed to generate story after {self.settings.MAX_RETRIES} retries: {e}")
                return None
    
    def generate_story(self) -> Optional[str]:
        """Generate a story suitable for short video narration.
        
        Returns:
            Generated story text or None if generation fails
        """
        prompt = """
        Create a short, suspenseful tech horror story suitable for video narration. The story should:
        - Be concise (fitting within 180 seconds when read aloud)
        - Have a clear beginning, middle, and end
        - Focus on modern technology gone wrong (AI, smart homes, social media, etc.)
        - Build tension through atmosphere rather than violence
        - Include subtle horror elements without being explicitly graphic
        - End with an unsettling technological twist
        - Be between 200-250 words
        
        Format the response as a single cohesive story in a Black Mirror style, without any additional commentary.
        Avoid gore, explicit violence, or extreme horror - focus on psychological tension and technological unease.
        """
        
        story = self._make_request(prompt)
        if story:
            # Clean up the story text
            story = self._clean_story(story)
            # Save the story to a file
            try:
                with open(self.story_file, 'w') as f:
                    f.write(story)
                logger.info(f"Story saved to {self.story_file}")
            except IOError as e:
                logger.error(f"Failed to save story to file: {e}")
            
            logger.info("Successfully generated story")
            return story
        
        logger.error("Failed to generate story")
        return None 