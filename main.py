import os
import argparse
from typing import Optional

from config.settings import Settings
from modules.story_generator import StoryGenerator
from modules.image_generator import ImageGenerator
from modules.tts_generator import TTSGenerator
from modules.video_synthesizer import VideoSynthesizer
from utils.logger import setup_logger

logger = setup_logger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate AI-powered video')
    parser.add_argument('--ollama-endpoint', help='Ollama API endpoint')
    parser.add_argument('--ollama-model', help='Ollama model to use')
    parser.add_argument('--dalle-key', help='DALL-E API key')
    parser.add_argument('--output-dir', help='Output directory')
    return parser.parse_args()

def main() -> Optional[str]:
    """Main application entry point.
    
    Returns:
        Path to generated video or None if generation fails
    """
    # Parse arguments
    args = parse_args()
    
    # Override environment variables with command line arguments
    if args.ollama_endpoint:
        os.environ['OLLAMA_ENDPOINT'] = args.ollama_endpoint
    if args.ollama_model:
        os.environ['OLLAMA_MODEL'] = args.ollama_model
    if args.dalle_key:
        os.environ['DALLE_API_KEY'] = args.dalle_key
    
    try:
        # Initialize settings
        settings = Settings()
        if args.output_dir:
            settings.OUTPUT_DIR = args.output_dir
            os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        
        # Initialize components
        story_gen = StoryGenerator(settings)
        image_gen = ImageGenerator(settings)
        tts_gen = TTSGenerator(settings)
        video_gen = VideoSynthesizer(settings)
        
        # Generate story
        logger.info("Generating story...")
        story = story_gen.generate_story()
        if not story:
            return None
            
        # Generate image
        logger.info("Generating image...")
        image_path = image_gen.generate_image(story)
        if not image_path:
            return None
            
        # Generate audio
        logger.info("Generating audio narration...")
        audio_path = tts_gen.generate_audio(story)
        if not audio_path:
            return None
            
        # Create video
        logger.info("Creating final video...")
        video_path = video_gen.create_video(image_path, audio_path)
        if not video_path:
            return None
            
        logger.info(f"Video generation complete! Output: {video_path}")
        return video_path
        
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        return None

if __name__ == "__main__":
    main() 