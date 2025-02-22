import os
import time
from typing import Optional, Callable, Tuple
from contextlib import contextmanager
import random
from dataclasses import dataclass

from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
import numpy as np
from PIL import Image
import PIL.Image
# Patch PIL.Image.ANTIALIAS
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)

class VideoProcessingError(Exception):
    """Custom exception for video processing errors."""
    pass

@dataclass
class KenBurnsConfig:
    """Configuration for Ken Burns effect."""
    zoom_range: Tuple[float, float] = (1.0, 1.2)
    pan_range: Tuple[float, float] = (-0.5, 0.5)  # Fraction of frame size to pan
    direction: str = 'random'  # 'random', 'in', 'out'

class VideoSynthesizer:
    """Combines image and audio into final video with enhanced effects."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
    def _validate_inputs(self, image_path: str, audio_path: str) -> None:
        """Validate input files exist and are accessible."""
        if not os.path.exists(image_path):
            raise VideoProcessingError(f"Image file not found: {image_path}")
        if not os.path.exists(audio_path):
            raise VideoProcessingError(f"Audio file not found: {audio_path}")
            
        # Check file sizes
        if os.path.getsize(image_path) == 0:
            raise VideoProcessingError(f"Image file is empty: {image_path}")
        if os.path.getsize(audio_path) == 0:
            raise VideoProcessingError(f"Audio file is empty: {audio_path}")
            
        # Validate image can be opened and has valid dimensions
        try:
            with Image.open(image_path) as img:
                if not img.size or None in img.size:
                    raise VideoProcessingError(f"Invalid image dimensions: {image_path}")
                logger.info(f"Image dimensions: {img.size}")
        except Exception as e:
            raise VideoProcessingError(f"Failed to validate image: {e}")
    
    @contextmanager
    def _manage_clips(self, image_path: str, audio_path: str):
        """Resource management for video clips."""
        image_clip = audio_clip = None
        try:
            image_clip = ImageClip(image_path)
            if not hasattr(image_clip, 'size') or not image_clip.size or None in image_clip.size:
                raise VideoProcessingError("Failed to load image: invalid dimensions")
                
            audio_clip = AudioFileClip(audio_path)
            if not hasattr(audio_clip, 'duration') or not audio_clip.duration:
                raise VideoProcessingError("Failed to load audio: invalid duration")
                
            yield image_clip, audio_clip
        finally:
            if image_clip:
                try:
                    image_clip.close()
                except Exception as e:
                    logger.warning(f"Error closing image clip: {e}")
            if audio_clip:
                try:
                    audio_clip.close()
                except Exception as e:
                    logger.warning(f"Error closing audio clip: {e}")
    
    def _process_resolution(self, image: ImageClip) -> ImageClip:
        """Process image to match target resolution while preserving aspect ratio."""
        target_w, target_h = self.settings.OUTPUT_RESOLUTION
        
        if not hasattr(image, 'size') or not image.size or None in image.size:
            raise VideoProcessingError("Invalid ImageClip: missing or invalid size attribute")
            
        img_w, img_h = image.size
        logger.info(f"Processing image resolution: {img_w}x{img_h} -> {target_w}x{target_h}")
        
        # Calculate scaling factors
        scale_w = target_w / img_w
        scale_h = target_h / img_h
        scale = min(scale_w, scale_h)
        
        # Resize image maintaining aspect ratio
        new_size = (int(img_w * scale), int(img_h * scale))
        image = image.resize(new_size)
        
        # If image doesn't match target exactly, add padding
        if new_size != (target_w, target_h):
            padded = ImageClip(np.zeros((target_h, target_w, 3)), duration=image.duration)
            x = (target_w - new_size[0]) // 2
            y = (target_h - new_size[1]) // 2
            image = image.set_position((x, y))
            image = CompositeVideoClip([padded, image])
        
        return image
    
    def _apply_enhanced_ken_burns(self, clip: ImageClip, config: Optional[KenBurnsConfig] = None) -> ImageClip:
        """Apply enhanced Ken Burns effect with configurable parameters."""
        if not hasattr(clip, 'duration') or not clip.duration:
            raise VideoProcessingError("Cannot apply Ken Burns effect: clip duration not set")
            
        if config is None:
            config = KenBurnsConfig()
            
        duration = clip.duration
        logger.info(f"Applying Ken Burns effect with duration: {duration}s")
        
        direction = config.direction
        if direction == 'random':
            direction = random.choice(['in', 'out'])
            
        def ease_in_out(t):
            """Smooth easing function."""
            t = t / duration
            if t < 0.5:
                return 2 * t * t
            t = t - 1
            return 1 - 2 * t * t
        
        def zoom_effect(t):
            """Enhanced zoom effect with smooth easing."""
            zoom_start, zoom_end = config.zoom_range
            if direction == 'out':
                zoom_start, zoom_end = zoom_end, zoom_start
            progress = ease_in_out(t)
            return zoom_start + (zoom_end - zoom_start) * progress
        
        def pan_effect(t):
            """Enhanced pan effect with smooth easing."""
            progress = ease_in_out(t)
            pan_x = random.uniform(*config.pan_range) * progress
            pan_y = random.uniform(*config.pan_range) * progress
            # Return x, y coordinates as fractions of the frame size
            return (pan_x, pan_y)
        
        clip = clip.resize(zoom_effect)
        clip = clip.set_position(pan_effect)
        
        return clip
    
    def _prepare_video_clip(self, image: ImageClip, audio: AudioFileClip) -> ImageClip:
        """Prepare the video clip with proper duration and effects."""
        # First set the duration from audio
        if not audio.duration:
            raise VideoProcessingError("Invalid audio: missing duration")
            
        image = image.set_duration(audio.duration)
        logger.info(f"Set image duration to match audio: {audio.duration}s")
        
        return image
    
    def _render_final_video(
        self,
        image: ImageClip,
        audio: AudioFileClip,
        ken_burns_config: Optional[KenBurnsConfig] = None,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """Render the final video with progress reporting."""
        # Prepare base clip with duration
        image = self._prepare_video_clip(image, audio)
        
        # Apply Ken Burns effect after duration is set
        image = self._apply_enhanced_ken_burns(image, ken_burns_config)
        
        # Create final composite
        video = CompositeVideoClip([image])
        video = video.set_audio(audio)
        
        # Prepare output path
        output_path = os.path.join(
            self.settings.OUTPUT_DIR,
            f"generated_video_{int(time.time())}.mp4"
        )
        
        logger.info("Writing video file...")
        
        # Write video file with progress reporting
        video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            preset='medium',  # Balance between speed and quality
            bitrate='4000k',
            threads=4,
            logger=progress_callback
        )
        
        return output_path
    
    def create_video(
        self,
        image_path: str,
        audio_path: str,
        ken_burns_config: Optional[KenBurnsConfig] = None,
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """Create video from image and audio with enhanced features.
        
        Args:
            image_path: Path to input image
            audio_path: Path to input audio
            ken_burns_config: Optional configuration for Ken Burns effect
            progress_callback: Optional callback for progress reporting
            
        Returns:
            Path to output video or None if creation fails
            
        Raises:
            VideoProcessingError: If video processing fails
        """
        try:
            # Input validation
            self._validate_inputs(image_path, audio_path)
            
            # Process with resource management
            with self._manage_clips(image_path, audio_path) as (image, audio):
                # Verify audio duration
                if not audio.duration:
                    raise VideoProcessingError("Invalid audio: missing duration")
                
                if audio.duration > self.settings.MAX_VIDEO_LENGTH + self.settings.DURATION_TOLERANCE:
                    raise VideoProcessingError(
                        f"Audio duration ({audio.duration}s) exceeds maximum allowed length "
                        f"({self.settings.MAX_VIDEO_LENGTH}s) with tolerance of {self.settings.DURATION_TOLERANCE}s"
                    )
                
                # Process image resolution
                image = self._process_resolution(image)
                
                # Render final video (now includes Ken Burns effect application)
                output_path = self._render_final_video(image, audio, ken_burns_config, progress_callback)
                
                logger.info(f"Successfully created video at {output_path}")
                return output_path
                
        except VideoProcessingError as e:
            logger.error(f"Video processing error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in video creation: {e}")
            return None
