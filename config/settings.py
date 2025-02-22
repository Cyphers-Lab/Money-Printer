import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    """Application settings and configuration."""
    
    # API Endpoints and Keys
    OLLAMA_ENDPOINT: str = os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434')
    OLLAMA_MODEL: str = os.getenv('OLLAMA_MODEL', 'mistral')
    DALLE_API_KEY: str = os.getenv('DALLE_API_KEY', '') # DALL-E API key
    
    # Video Settings
    MAX_VIDEO_LENGTH: int = 180  # seconds
    DURATION_TOLERANCE: float = 0.5  # seconds - tolerance for audio/video duration checks
    OUTPUT_RESOLUTION: tuple[int, int] = (1024, 1024)  # Width, height tuple
    
    # Azure TTS Settings
    AZURE_TTS_KEY: str = os.getenv('AZURE_TTS_KEY', '') # Azure Text-to-Speech API key
    AZURE_TTS_REGION: str = os.getenv('AZURE_TTS_REGION', 'ukwest')
    AZURE_TTS_VOICE: str = os.getenv('AZURE_TTS_VOICE', 'en-US-JasonNeural')
    TTS_RATE: int = 0  # Percentage change (-100 to +100)
    TTS_PITCH: int = 0  # Percentage change (-100 to +100)
    
    # File Paths
    TEMP_DIR: str = 'temp'
    OUTPUT_DIR: str = 'output'
    
    # API Retry Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # seconds
    
    def __post_init__(self):
        """Validate settings and create necessary directories."""
        if not self.DALLE_API_KEY:
            raise ValueError("DALLE_API_KEY environment variable is required")
            
        # Create necessary directories
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
