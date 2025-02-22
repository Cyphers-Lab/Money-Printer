import os
from typing import Optional
import requests
from PIL import Image
from io import BytesIO

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)

class ImageGenerator:
    """Generates images using DALL-E API based on story content."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.DALLE_API_KEY
        
    def _generate_image_prompt(self, story: str) -> str:
        """Convert story text into an appropriate image generation prompt.
        
        Args:
            story: The story text
            
        Returns:
            Image generation prompt
        """
        # Create a tech-noir atmosphere
        base_prompt = "Create a modern, minimalist tech scene with dramatic lighting and shadows. "
        style_prompt = "Style: Cyberpunk-inspired digital art, muted colors with neon accents, clean lines. "
        content_prompt = f"Scene showing: {story[:200]}"
        safety_prompt = "Focus on technological elements and atmosphere. Avoid explicit horror or disturbing imagery. Keep it subtle and psychological."
        
        prompt = f"{base_prompt}{style_prompt}{content_prompt}. {safety_prompt}"
        return prompt
        
    def generate_image(self, story: str) -> Optional[str]:
        """Generate an image based on the story content.
        
        Args:
            story: The story text
            
        Returns:
            Path to generated image or None if generation fails
        """
        prompt = self._generate_image_prompt(story)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json={
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "hd",
                    "style": "natural"  # Use natural style for more predictable results
                }
            )
            response.raise_for_status()
            
            # Download and save the image
            image_url = response.json()['data'][0]['url']
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            image = Image.open(BytesIO(image_response.content))
            
            # Save image
            output_path = os.path.join(self.settings.TEMP_DIR, "generated_image.png")
            image.save(output_path, "PNG")
            
            logger.info(f"Successfully generated and saved image to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            return None 