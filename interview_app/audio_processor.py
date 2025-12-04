"""
Audio Processing Module
Handles audio file conversion and processing for reliable video/audio merging
Uses soundfile, pydub, or ffmpeg for format conversion
"""
import os
import subprocess
import platform
from django.conf import settings


def get_ffmpeg_path():
    """Get FFmpeg executable path."""
    if platform.system() == 'Windows':
        possible_paths = [
            r"C:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe",
            r"C:\ffmpeg\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        ]
        
        for ffmpeg_path in possible_paths:
            if os.path.exists(ffmpeg_path):
                try:
                    result = subprocess.run(
                        [ffmpeg_path, '-version'],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        return ffmpeg_path
                except:
                    continue
    
    # Try system PATH
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            return 'ffmpeg'
    except:
        pass
    
    return None


def convert_audio_to_wav(input_path, output_path=None):
    """
    Convert audio file to WAV format using FFmpeg (most reliable method).
    
    Args:
        input_path: Path to input audio file (WebM, MP3, etc.)
        output_path: Optional output path. If None, creates .wav version of input.
    
    Returns:
        Path to converted WAV file, or None if conversion failed.
    """
    if not os.path.exists(input_path):
        print(f"❌ Audio file not found: {input_path}")
        return None
    
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        print(f"❌ FFmpeg not found - cannot convert audio")
        return None
    
    # Generate output path if not provided
    if output_path is None:
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_converted.wav"
    
    try:
        print(f"🔄 Converting audio to WAV: {input_path} -> {output_path}")
        
        # FFmpeg command to convert to WAV (PCM 16-bit, 44.1kHz, mono)
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-acodec', 'pcm_s16le',  # PCM 16-bit little-endian
            '-ar', '44100',          # Sample rate 44.1kHz
            '-ac', '1',              # Mono channel
            '-y',                    # Overwrite output
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / 1024 / 1024
            print(f"✅ Audio converted to WAV: {output_path} ({file_size:.2f} MB)")
            return output_path
        else:
            print(f"❌ Audio conversion failed:")
            print(f"   Return code: {result.returncode}")
            print(f"   Error: {result.stderr[:500] if result.stderr else result.stdout[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ Error converting audio: {e}")
        import traceback
        traceback.print_exc()
        return None


def convert_audio_to_mp3(input_path, output_path=None):
    """
    Convert audio file to MP3 format using FFmpeg.
    
    Args:
        input_path: Path to input audio file
        output_path: Optional output path. If None, creates .mp3 version of input.
    
    Returns:
        Path to converted MP3 file, or None if conversion failed.
    """
    if not os.path.exists(input_path):
        print(f"❌ Audio file not found: {input_path}")
        return None
    
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        print(f"❌ FFmpeg not found - cannot convert audio")
        return None
    
    # Generate output path if not provided
    if output_path is None:
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_converted.mp3"
    
    try:
        print(f"🔄 Converting audio to MP3: {input_path} -> {output_path}")
        
        # FFmpeg command to convert to MP3 (AAC codec, 192kbps)
        cmd = [
            ffmpeg_path,
            '-i', input_path,
            '-acodec', 'libmp3lame',  # MP3 codec
            '-b:a', '192k',            # Bitrate 192kbps
            '-ar', '44100',            # Sample rate 44.1kHz
            '-ac', '1',                # Mono channel
            '-y',                      # Overwrite output
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / 1024 / 1024
            print(f"✅ Audio converted to MP3: {output_path} ({file_size:.2f} MB)")
            return output_path
        else:
            print(f"❌ Audio conversion failed:")
            print(f"   Return code: {result.returncode}")
            print(f"   Error: {result.stderr[:500] if result.stderr else result.stdout[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ Error converting audio: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_audio_info(audio_path):
    """
    Get audio file information using FFprobe.
    
    Returns:
        dict with audio info (duration, sample_rate, channels, codec) or None
    """
    if not os.path.exists(audio_path):
        return None
    
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        return None
    
    # Get ffprobe path (usually same directory as ffmpeg)
    if platform.system() == 'Windows' and ffmpeg_path.endswith('.exe'):
        ffprobe_path = ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
    else:
        ffprobe_path = 'ffprobe'
    
    try:
        # Get audio stream information
        cmd = [
            ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-select_streams', 'a:0',  # First audio stream
            audio_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            if 'streams' in data and len(data['streams']) > 0:
                stream = data['streams'][0]
                return {
                    'duration': float(stream.get('duration', 0)),
                    'sample_rate': int(stream.get('sample_rate', 0)),
                    'channels': int(stream.get('channels', 0)),
                    'codec': stream.get('codec_name', 'unknown'),
                    'bitrate': int(stream.get('bit_rate', 0)) if stream.get('bit_rate') else None
                }
    except Exception as e:
        print(f"⚠️ Could not get audio info: {e}")
    
    return None


def verify_audio_file(audio_path):
    """
    Verify that audio file exists and is valid.
    
    Returns:
        True if audio file is valid, False otherwise
    """
    if not os.path.exists(audio_path):
        print(f"❌ Audio file does not exist: {audio_path}")
        return False
    
    file_size = os.path.getsize(audio_path)
    if file_size == 0:
        print(f"❌ Audio file is empty: {audio_path}")
        return False
    
    # Try to get audio info to verify it's a valid audio file
    info = get_audio_info(audio_path)
    if info:
        print(f"✅ Audio file verified: {audio_path}")
        print(f"   Duration: {info['duration']:.2f}s")
        print(f"   Sample rate: {info['sample_rate']}Hz")
        print(f"   Channels: {info['channels']}")
        print(f"   Codec: {info['codec']}")
        return True
    else:
        # File exists but can't read info - might still be valid
        print(f"⚠️ Could not read audio info, but file exists: {audio_path} ({file_size / 1024 / 1024:.2f} MB)")
        return True  # Assume valid if file exists and has size


def process_uploaded_audio(audio_path, convert_to_wav=True):
    """
    Process uploaded audio file: verify and optionally convert to WAV.
    
    Args:
        audio_path: Path to uploaded audio file
        convert_to_wav: If True, convert to WAV format for better compatibility
    
    Returns:
        Path to processed audio file (converted if conversion succeeded, original otherwise)
    """
    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return None
    
    # Verify audio file
    if not verify_audio_file(audio_path):
        print(f"❌ Audio file verification failed: {audio_path}")
        return None
    
    # Get file extension
    file_ext = os.path.splitext(audio_path)[1].lower()
    
    # If already WAV, return as-is
    if file_ext == '.wav':
        print(f"✅ Audio is already WAV format: {audio_path}")
        return audio_path
    
    # If convert_to_wav is True and file is not WAV, convert it
    if convert_to_wav:
        print(f"🔄 Converting audio to WAV for better compatibility...")
        converted_path = convert_audio_to_wav(audio_path)
        if converted_path and os.path.exists(converted_path):
            # Optionally remove original if conversion succeeded
            # (Keep original for now in case of issues)
            print(f"✅ Using converted WAV file: {converted_path}")
            return converted_path
        else:
            print(f"⚠️ Conversion failed, using original: {audio_path}")
            return audio_path
    else:
        # Try to convert to MP3 if not WAV
        if file_ext not in ['.mp3', '.wav']:
            print(f"🔄 Converting audio to MP3 for better compatibility...")
            converted_path = convert_audio_to_mp3(audio_path)
            if converted_path and os.path.exists(converted_path):
                print(f"✅ Using converted MP3 file: {converted_path}")
                return converted_path
        
        return audio_path







