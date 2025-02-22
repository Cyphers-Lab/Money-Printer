# Money-Printer

An AI-powered video generation tool that creates videos by combining generated stories, images, and text-to-speech narration.

## Features

- Story generation using Ollama LLM
- Image generation with DALL-E
- Text-to-speech narration using Azure TTS
- Automated video synthesis
- Configurable output resolution and video length
- Robust error handling and retry mechanisms

## Requirements

- Python 3.x
- Ollama server running locally or remotely
- DALL-E API key
- Azure TTS API key (for voice narration)
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Set the following environment variables:
- `DALLE_API_KEY`: DALL-E API key (required)
- `AZURE_TTS_KEY`: Azure Text-to-Speech API key
- `AZURE_TTS_REGION`: Azure region (default: ukwest)
- `AZURE_TTS_VOICE`: Voice ID (default: en-US-JasonNeural)
- `OLLAMA_ENDPOINT`: Ollama API endpoint (default: http://localhost:11434)
- `OLLAMA_MODEL`: Ollama model name (default: mistral)

## Usage

Run the script with:
```bash
python main.py [options]
```

Options:
- `--ollama-endpoint`: Override Ollama API endpoint
- `--ollama-model`: Override Ollama model
- `--dalle-key`: Override DALL-E API key
- `--output-dir`: Specify custom output directory

## Output

Generated videos are saved in the `output` directory. The process creates:
1. A generated story using Ollama
2. A matching image using DALL-E
3. Audio narration using Azure TTS
4. Final video combining the image and narration
