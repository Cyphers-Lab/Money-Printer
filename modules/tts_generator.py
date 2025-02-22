import os
from typing import Optional, Dict
import azure.cognitiveservices.speech as speechsdk
import tempfile
from pydub import AudioSegment

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)

AZURE_VOICES = {
    'Jenny': 'en-US-JennyMultilingualNeural',
    'Guy': 'en-US-GuyNeural',
    'Aria': 'en-US-AriaNeural',
    'Davis': 'en-US-DavisNeural',
    'Jane': 'en-US-JaneNeural',
    'Jason': 'en-US-JasonNeural',
    'Nancy': 'en-US-NancyNeural',
    'Sara': 'en-US-SaraNeural',
    'Tony': 'en-US-TonyNeural'
}

class TTSGenerator:
    """Generates text-to-speech audio using Azure neural voices."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.AZURE_TTS_KEY:
            raise ValueError("AZURE_TTS_KEY is required for TTS generation")
            
        # Initialize speech config with specific endpoints
        try:
            logger.info(f"Initializing Azure Speech Service in region: {settings.AZURE_TTS_REGION}")
            self.speech_config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_TTS_KEY,
                region=settings.AZURE_TTS_REGION
            )
            # Set specific endpoints for the service
            self.speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
            self.speech_config.speech_synthesis_voice_name = settings.AZURE_TTS_VOICE
            
            # Test the configuration with a simple synthesis
            test_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
            test_result = test_synthesizer.speak_text_async("Test").get()
            
            if test_result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                if test_result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = speechsdk.CancellationDetails(test_result)
                    if cancellation_details.reason == speechsdk.CancellationReason.Error:
                        raise ValueError(f"Speech service error: {cancellation_details.error_details}")
                raise ValueError(f"Speech synthesis test failed: {test_result.reason}")
                
            logger.info(f"Successfully initialized TTS with region: {settings.AZURE_TTS_REGION}")
            
        except Exception as e:
            logger.error(f"Failed to initialize speech config: {str(e)}")
            raise ValueError(f"Failed to initialize Azure Speech service. Please check your credentials. Error: {str(e)}")
        
    def get_available_voices(self) -> Dict[str, str]:
        """Get list of available TTS voices.
        
        Returns:
            Dictionary of voice names and their IDs
        """
        return AZURE_VOICES
    
    def set_voice(self, voice_id: str) -> bool:
        """Set TTS voice by ID.
        
        Args:
            voice_id: ID of voice to use
            
        Returns:
            True if voice was set successfully, False otherwise
        """
        try:
            self.speech_config.speech_synthesis_voice_name = voice_id
            logger.info(f"Set TTS voice to {voice_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to set voice {voice_id}: {e}")
            return False
        
    def _adjust_audio_speed(self, audio_path: str, target_duration: int) -> Optional[str]:
        """Adjust audio speed to fit within target duration.
        
        Args:
            audio_path: Path to input audio file
            target_duration: Target duration in seconds
            
        Returns:
            Path to adjusted audio file or None if adjustment fails
        """
        try:
            # Load audio
            audio = AudioSegment.from_mp3(audio_path)
            current_duration = len(audio) / 1000  # Convert to seconds
            
            if current_duration > target_duration:
                # Calculate required speed multiplier
                speed_factor = current_duration / target_duration
                
                # Speed up audio using pydub
                adjusted_audio = audio.speedup(playback_speed=speed_factor)
                
                # Save to new file
                adjusted_path = os.path.join(self.settings.TEMP_DIR, "narration_adjusted.mp3")
                adjusted_audio.export(adjusted_path, format="mp3")
                
                logger.info(f"Audio adjusted from {current_duration:.1f}s to {target_duration:.1f}s")
                return adjusted_path
                
            return audio_path
            
        except Exception as e:
            logger.error(f"Failed to adjust audio speed: {e}")
            return None
    
    def generate_audio(self, text: str) -> Optional[str]:
        """Convert text to speech using Azure neural voices.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Path to generated audio file or None if generation fails
        """
        try:
            # Generate audio file path
            output_path = os.path.join(self.settings.TEMP_DIR, "narration.mp3")
            
            # Start with basic SSML without prosody adjustments
            ssml_text = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'
                        f'<voice name="{self.speech_config.speech_synthesis_voice_name}">{text}</voice>'
                        f'</speak>')
            
            logger.info(f"Using SSML: {ssml_text}")
            
            # Create a speech synthesizer
            audio_config = speechsdk.AudioConfig(filename=output_path)
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Generate speech
            result = synthesizer.speak_ssml_async(ssml_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Check and adjust audio duration if needed
                final_path = self._adjust_audio_speed(output_path, self.settings.MAX_VIDEO_LENGTH)
                if not final_path:
                    return None
                
                logger.info(f"Successfully generated audio file at {final_path}")
                return final_path
            else:
                if result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = speechsdk.CancellationDetails(result)
                    error_msg = f"Speech synthesis canceled: {cancellation_details.reason}. "
                    if cancellation_details.reason == speechsdk.CancellationReason.Error:
                        error_msg += f"Error details: {cancellation_details.error_details}"
                    logger.error(error_msg)
                else:
                    logger.error(f"Speech synthesis failed with reason: {result.reason}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")
            return None
