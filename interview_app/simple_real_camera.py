import time
# OpenCV import with fallback (optional dependency)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False
    print("⚠️ Warning: opencv-python not available. Camera and video processing features will be disabled.")
import numpy as np
import os
import subprocess
import platform
from datetime import datetime
from fractions import Fraction
from django.conf import settings
import threading
import wave
try:
    import av
    PYAV_AVAILABLE = True
except ImportError:
    PYAV_AVAILABLE = False
    print("⚠️ PyAV not available - install with: pip install av")

try:
    import pyaudio
    PYAudio_AVAILABLE = True
except ImportError:
    PYAudio_AVAILABLE = False
    print("⚠️ PyAudio not available - install with: pip install pyaudio")

try:
    # MoviePy 2.x uses direct imports from moviepy, not moviepy.editor
    from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip
    MOVIEPY_AVAILABLE = True
    MOVIEPY_VERSION = 2
except ImportError:
    try:
        # Fallback for MoviePy 1.x
        from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
        MOVIEPY_AVAILABLE = True
        MOVIEPY_VERSION = 1
    except ImportError:
        MOVIEPY_AVAILABLE = False
        MOVIEPY_VERSION = None
        print("⚠️ MoviePy not available - install with: pip install moviepy")


def merge_video_audio_moviepy(video_path, audio_file_path, output_path, video_start_timestamp=None, audio_start_timestamp=None, video_duration=None):
    """
    Merge video and audio using MoviePy - simple and reliable Python library.
    MoviePy handles synchronization automatically based on timestamps.
    
    Args:
        video_path: Path to video file (MP4)
        audio_file_path: Path to audio file (WAV, MP3, etc.)
        output_path: Path to save merged video
        video_start_timestamp: Unix timestamp when video recording started
        audio_start_timestamp: Unix timestamp when audio recording started
        video_duration: Video duration in seconds (if None, will use video duration)
    
    Returns:
        True if successful, False otherwise
    """
    if not MOVIEPY_AVAILABLE:
        raise ImportError("MoviePy is required for video/audio merging. Install with: pip install moviepy")
    
    try:
        print(f"🔄 Merging video and audio using MoviePy...")
        print(f"   Video: {video_path}")
        print(f"   Audio: {audio_file_path}")
        print(f"   Output: {output_path}")
        
        # Convert all paths to absolute paths
        video_path = os.path.normpath(video_path)
        audio_file_path = os.path.normpath(audio_file_path)
        output_path = os.path.normpath(output_path)
        
        if not os.path.isabs(video_path):
            video_path = os.path.join(settings.MEDIA_ROOT, video_path)
            video_path = os.path.normpath(video_path)
        
        if not os.path.isabs(audio_file_path):
            audio_file_path = os.path.join(settings.MEDIA_ROOT, audio_file_path)
            audio_file_path = os.path.normpath(audio_file_path)
        
        if not os.path.isabs(output_path):
            output_path = os.path.join(settings.MEDIA_ROOT, output_path)
            output_path = os.path.normpath(output_path)
        
        video_path = os.path.abspath(video_path)
        audio_file_path = os.path.abspath(audio_file_path)
        output_path = os.path.abspath(output_path)
        
        # Verify files exist
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"   ✅ Absolute video path: {video_path}")
        print(f"   ✅ Absolute audio path: {audio_file_path}")
        print(f"   ✅ Absolute output path: {output_path}")
        
        # Load video and audio clips
        print(f"   📹 Loading video clip...")
        video_clip = VideoFileClip(video_path)
        video_duration_actual = video_clip.duration
        print(f"   📹 Video duration: {video_duration_actual:.2f}s")
        
        print(f"   🎙️ Loading audio clip...")
        audio_clip = AudioFileClip(audio_file_path)
        audio_duration_actual = audio_clip.duration
        print(f"   🎙️ Audio duration: {audio_duration_actual:.2f}s")
        
        # Calculate synchronization offset
        audio_start_offset = 0.0
        if video_start_timestamp and audio_start_timestamp:
            time_diff = audio_start_timestamp - video_start_timestamp
            print(f"   🕐 Synchronization analysis:")
            print(f"      Video started at: {video_start_timestamp:.6f}")
            print(f"      Audio started at: {audio_start_timestamp:.6f}")
            print(f"      Time difference: {time_diff:.6f}s ({(time_diff * 1000):.2f}ms)")
            
            if abs(time_diff) > 0.01:  # More than 10ms difference
                if time_diff < 0:
                    # Audio started before video - trim beginning of audio
                    audio_start_offset = abs(time_diff)
                    print(f"   ⏱️ Audio started {abs(time_diff):.3f}s BEFORE video - trimming first {audio_start_offset:.3f}s")
                    # MoviePy 2.x uses slicing (__getitem__), MoviePy 1.x uses subclip
                    try:
                        # Try MoviePy 2.x method first (slicing)
                        audio_clip = audio_clip[audio_start_offset:]
                    except (TypeError, AttributeError, IndexError):
                        try:
                            # Try MoviePy 1.x subclip method
                            audio_clip = audio_clip.subclip(audio_start_offset)
                        except AttributeError:
                            # Last resort: reload and trim using ffmpeg
                            print(f"   ⚠️ MoviePy trimming methods not available, using ffmpeg workaround...")
                            import tempfile
                            temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                            temp_audio_path = temp_audio.name
                            temp_audio.close()
                            # Use ffmpeg to trim audio starting from offset
                            import subprocess
                            subprocess.run([
                                'ffmpeg', '-i', audio_file_path, '-ss', str(audio_start_offset),
                                '-c', 'copy', temp_audio_path, '-y'
                            ], capture_output=True, check=True)
                            audio_clip.close()
                            audio_clip = AudioFileClip(temp_audio_path)
                else:
                    # Audio started after video - add silence at beginning
                    audio_start_offset = time_diff
                    print(f"   ⏱️ Audio started {time_diff:.3f}s AFTER video - adding {audio_start_offset:.3f}s silence")
                    # Import CompositeAudioClip and AudioClip based on MoviePy version
                    if MOVIEPY_VERSION == 2:
                        try:
                            from moviepy import CompositeAudioClip, AudioClip
                        except ImportError:
                            # Try alternative import path
                            from moviepy.audio import CompositeAudioClip, AudioClip
                    else:
                        try:
                            from moviepy.audio.AudioClip import CompositeAudioClip, AudioClip
                        except ImportError:
                            from moviepy.editor import CompositeAudioClip, AudioClip
                    silence = AudioClip(lambda t: [0.0, 0.0], duration=audio_start_offset, fps=audio_clip.fps)
                    audio_clip = CompositeAudioClip([silence, audio_clip])
            else:
                print(f"   ✅ Perfect synchronization! Time difference: {(time_diff * 1000):.1f}ms (< 10ms)")
        
        # CRITICAL: Always use video duration as authoritative
        # Audio is often longer because it may start earlier or stop later
        # We MUST trim audio to match video exactly for perfect sync
        final_duration = video_duration_actual
        print(f"   🎯 Using video duration as authoritative: {final_duration:.2f}s")
        
        if audio_clip.duration > video_duration_actual:
            print(f"   ⚠️ Audio ({audio_clip.duration:.2f}s) is LONGER than video ({final_duration:.2f}s)")
            print(f"   🔧 Trimming audio to match video duration exactly (removing {audio_clip.duration - final_duration:.2f}s from end)")
            # MoviePy 2.x uses slicing (__getitem__), MoviePy 1.x uses subclip
            try:
                # Try MoviePy 2.x method first (slicing)
                audio_clip = audio_clip[:final_duration]
            except (TypeError, AttributeError, IndexError):
                try:
                    # Try MoviePy 1.x subclip method
                    audio_clip = audio_clip.subclip(0, final_duration)
                except AttributeError:
                    # Last resort: use ffmpeg to trim audio
                    print(f"   ⚠️ MoviePy trimming methods not available, using ffmpeg workaround...")
                    import tempfile
                    import subprocess
                    temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                    temp_audio_path = temp_audio.name
                    temp_audio.close()
                    # Use ffmpeg to trim audio to exact duration
                    subprocess.run([
                        'ffmpeg', '-i', audio_file_path, '-t', str(final_duration),
                        '-c', 'copy', temp_audio_path, '-y'
                    ], capture_output=True, check=True)
                    audio_clip.close()
                    audio_clip = AudioFileClip(temp_audio_path)
            print(f"   ✅ Audio trimmed to: {audio_clip.duration:.2f}s")
        elif audio_clip.duration < video_duration_actual:
            print(f"   ⚠️ Audio ({audio_clip.duration:.2f}s) is SHORTER than video ({final_duration:.2f}s)")
            print(f"   ⚠️ This is unusual - audio should be longer. Trimming video to match audio.")
            print(f"   ⚠️ Video will lose {final_duration - audio_clip.duration:.2f}s from end")
            final_duration = audio_clip.duration
            # MoviePy 2.x uses slicing (__getitem__), MoviePy 1.x uses subclip
            try:
                # Try MoviePy 2.x method first (slicing)
                video_clip = video_clip[:final_duration]
            except (TypeError, AttributeError, IndexError):
                try:
                    # Try MoviePy 1.x subclip method
                    video_clip = video_clip.subclip(0, final_duration)
                except AttributeError:
                    # Fallback: use subclip with explicit start/end
                    video_clip = video_clip.subclip(t_start=0, t_end=final_duration)
            print(f"   ✅ Video trimmed to: {final_duration:.2f}s")
        else:
            print(f"   ✅ Audio and video durations match perfectly: {final_duration:.2f}s")
        
        # Set audio to video
        print(f"   🔗 Combining video and audio...")
        # MoviePy 2.x uses with_audio, MoviePy 1.x uses set_audio
        if MOVIEPY_VERSION == 2:
            # MoviePy 2.x: use with_audio method
            try:
                final_clip = video_clip.with_audio(audio_clip)
                print(f"   ✅ Using MoviePy 2.x with_audio method")
            except AttributeError:
                # Fallback: try CompositeVideoClip
                try:
                    final_clip = CompositeVideoClip([video_clip]).with_audio(audio_clip)
                    print(f"   ✅ Using MoviePy 2.x CompositeVideoClip.with_audio method")
                except AttributeError:
                    raise Exception("MoviePy 2.x audio combination methods not available")
        else:
            # MoviePy 1.x: use set_audio method
            try:
                final_clip = video_clip.set_audio(audio_clip)
                print(f"   ✅ Using MoviePy 1.x set_audio method")
            except AttributeError:
                # Fallback: try CompositeVideoClip
                try:
                    final_clip = CompositeVideoClip([video_clip]).set_audio(audio_clip)
                    print(f"   ✅ Using MoviePy 1.x CompositeVideoClip.set_audio method")
                except AttributeError:
                    raise Exception("MoviePy 1.x audio combination methods not available")
        
        # Write output file
        print(f"   💾 Writing merged video to: {output_path}")
        print(f"   📊 Final clip duration: {final_clip.duration:.2f}s")
        print(f"   📊 Video duration: {video_clip.duration:.2f}s")
        print(f"   📊 Audio duration (after sync): {audio_clip.duration:.2f}s")
        
        try:
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=video_clip.fps,
                preset='medium',
                bitrate='5000k',
                audio_bitrate='192k',
                verbose=False,  # Reduce MoviePy output
                logger=None  # Suppress MoviePy progress bars
            )
            print(f"   ✅ MoviePy write_videofile completed")
        except Exception as e:
            print(f"   ❌ MoviePy write_videofile failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Clean up clips
        video_clip.close()
        audio_clip.close()
        final_clip.close()
        
        # Verify output file
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Merged video file was not created: {output_path}")
        
        merged_file_size = os.path.getsize(output_path)
        if merged_file_size == 0:
            raise ValueError(f"Merged video file is empty: {output_path}")
        
        print(f"✅ MoviePy merge completed successfully!")
        print(f"   Output path: {output_path}")
        print(f"   Output file size: {merged_file_size / 1024 / 1024:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Error merging video and audio with MoviePy: {e}")
        import traceback
        traceback.print_exc()
        return False


def merge_video_audio_ffmpeg(video_path, audio_file_path, output_path, video_start_timestamp=None, audio_start_timestamp=None, video_duration=None):
    """
    Merge video and audio using FFmpeg (subprocess) - more reliable than PyAV.
    FFmpeg handles synchronization perfectly and is the industry standard.
    
    Args:
        video_path: Path to video file (MP4)
        audio_file_path: Path to audio file (WAV, MP3, WEBM, etc.)
        output_path: Path to save merged video
        video_start_timestamp: Unix timestamp when video recording started
        audio_start_timestamp: Unix timestamp when audio recording started
        video_duration: Video duration in seconds (if None, will be calculated from video)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"🔄 Merging video and audio using FFmpeg...")
        print(f"   Video: {video_path}")
        print(f"   Audio: {audio_file_path}")
        print(f"   Output: {output_path}")
        
        # CRITICAL: Convert all paths to absolute paths for accurate file access
        video_path = os.path.normpath(video_path)
        audio_file_path = os.path.normpath(audio_file_path)
        output_path = os.path.normpath(output_path)
        
        # Convert to absolute paths if they're relative
        if not os.path.isabs(video_path):
            video_path = os.path.join(settings.MEDIA_ROOT, video_path)
            video_path = os.path.normpath(video_path)
        
        if not os.path.isabs(audio_file_path):
            audio_file_path = os.path.join(settings.MEDIA_ROOT, audio_file_path)
            audio_file_path = os.path.normpath(audio_file_path)
        
        if not os.path.isabs(output_path):
            output_path = os.path.join(settings.MEDIA_ROOT, output_path)
            output_path = os.path.normpath(output_path)
        
        # Get absolute paths
        video_path = os.path.abspath(video_path)
        audio_file_path = os.path.abspath(audio_file_path)
        output_path = os.path.abspath(output_path)
        
        # Verify all files exist
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"   ✅ Absolute video path: {video_path}")
        print(f"   ✅ Absolute audio path: {audio_file_path}")
        print(f"   ✅ Absolute output path: {output_path}")
        
        # Get video duration using ffprobe if not provided
        if video_duration is None or video_duration == 0:
            try:
                probe_cmd = [
                    'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1', video_path
                ]
                result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    video_duration = float(result.stdout.strip())
                    print(f"   📹 Video duration from ffprobe: {video_duration:.2f}s")
                else:
                    print(f"   ⚠️ Could not get video duration from ffprobe, will use audio duration")
            except Exception as e:
                print(f"   ⚠️ Error getting video duration: {e}")
        
        # Calculate synchronization offset
        audio_delay = 0.0
        if video_start_timestamp and audio_start_timestamp:
            time_diff = audio_start_timestamp - video_start_timestamp
            print(f"   🕐 Synchronization analysis:")
            print(f"      Video started at: {video_start_timestamp:.6f}")
            print(f"      Audio started at: {audio_start_timestamp:.6f}")
            print(f"      Time difference: {time_diff:.6f}s ({(time_diff * 1000):.2f}ms)")
            
            if abs(time_diff) > 0.01:  # More than 10ms difference
                if time_diff > 0:
                    # Audio started AFTER video - add delay to audio
                    audio_delay = time_diff
                    print(f"   ⏱️ Audio started {time_diff:.3f}s AFTER video - will delay audio by {audio_delay:.3f}s")
                else:
                    # Audio started BEFORE video - trim beginning of audio
                    audio_delay = 0.0
                    audio_trim_start = abs(time_diff)
                    print(f"   ⏱️ Audio started {abs(time_diff):.3f}s BEFORE video - will trim first {audio_trim_start:.3f}s of audio")
                    # Use -ss to skip beginning of audio
                    audio_file_path = f"{audio_file_path} -ss {audio_trim_start}"
            else:
                print(f"   ✅ Perfect synchronization! Time difference: {(time_diff * 1000):.1f}ms (< 10ms)")
        
        # Build FFmpeg command for merging
        ffmpeg_cmd = ['ffmpeg', '-y', '-i', video_path]
        
        # Handle audio input with trimming if needed
        audio_trim_start = 0.0
        if video_start_timestamp and audio_start_timestamp:
            time_diff = audio_start_timestamp - video_start_timestamp
            if time_diff < 0:
                # Audio started before video - trim beginning of audio
                audio_trim_start = abs(time_diff)
                # Use -ss before -i to trim input (more efficient)
                ffmpeg_cmd.extend(['-ss', str(audio_trim_start), '-i', audio_file_path])
                print(f"   🔧 Trimming first {audio_trim_start:.3f}s from audio input")
            else:
                # Audio started after video - will add delay later
                ffmpeg_cmd.extend(['-i', audio_file_path])
                if time_diff > 0.01:
                    audio_delay = time_diff
        else:
            ffmpeg_cmd.extend(['-i', audio_file_path])
        
        # Map video and audio streams with proper synchronization
        # Use shortest to ensure both streams end together
        if audio_delay > 0.01:
            # Audio started after video - use itsoffset to delay audio
            ffmpeg_cmd.extend([
                '-itsoffset', str(audio_delay),
                '-map', '1:a',  # Map delayed audio
                '-map', '0:v',   # Map video
            ])
        else:
            # Normal mapping (or audio already trimmed)
            ffmpeg_cmd.extend([
                '-map', '0:v',   # Map video
                '-map', '1:a',   # Map audio
            ])
        
        # Codec options
        ffmpeg_cmd.extend([
            '-c:v', 'copy',      # Copy video codec (no re-encoding for speed)
            '-c:a', 'aac',       # Encode audio as AAC (browser-compatible)
            '-b:a', '192k',      # Audio bitrate
            '-ar', '44100',      # Audio sample rate
            '-ac', '1',          # Mono audio
        ])
        
        # Ensure video duration matches (trim to shortest stream)
        if video_duration and video_duration > 0:
            ffmpeg_cmd.extend(['-t', str(video_duration)])
            print(f"   🎯 Trimming to video duration: {video_duration:.2f}s")
        
        # Output format options for browser compatibility
        ffmpeg_cmd.extend([
            '-shortest',         # End when shortest stream ends (ensures sync)
            '-movflags', '+faststart',  # Enable faststart for web streaming
            output_path
        ])
        
        print(f"   🔧 FFmpeg command: {' '.join(ffmpeg_cmd)}")
        
        # Run FFmpeg
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            print(f"   ❌ FFmpeg failed with return code {result.returncode}")
            print(f"   Error output: {result.stderr}")
            raise RuntimeError(f"FFmpeg merge failed: {result.stderr}")
        
        # Verify output file exists and has content
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Merged video file was not created: {output_path}")
        
        merged_file_size = os.path.getsize(output_path)
        if merged_file_size == 0:
            raise ValueError(f"Merged video file is empty: {output_path}")
        
        # Verify the file has both video and audio streams
        try:
            probe_cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', output_path
            ]
            video_check = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
            
            probe_cmd = [
                'ffprobe', '-v', 'error', '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', output_path
            ]
            audio_check = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
            
            if 'video' not in video_check.stdout.lower():
                raise ValueError(f"Merged file {output_path} does not contain a video stream.")
            if 'audio' not in audio_check.stdout.lower():
                raise ValueError(f"Merged file {output_path} does not contain an audio stream.")
            
            print(f"✅ Merged file verified: contains both video and audio streams")
        except Exception as e:
            print(f"   ⚠️ Could not verify streams: {e}")
            # Don't fail - file exists and has content
        
        print(f"✅ FFmpeg merge completed successfully!")
        print(f"   Output path: {output_path}")
        print(f"   Output file size: {merged_file_size / 1024 / 1024:.2f} MB")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return False
    except subprocess.TimeoutExpired:
        print(f"❌ FFmpeg merge timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error merging video and audio: {e}")
        import traceback
        traceback.print_exc()
        return False


def merge_video_audio_pyav(video_path, audio_file_path, output_path, video_start_timestamp=None, audio_start_timestamp=None, video_duration=None):
    """
    DEPRECATED: Use merge_video_audio_ffmpeg instead.
    Merge video and audio using PyAV (pure Python, no FFmpeg subprocess).
    
    Args:
        video_path: Path to video file (MP4)
        audio_file_path: Path to audio file (WAV, MP3, etc.)
        output_path: Path to save merged video
        video_start_timestamp: Unix timestamp when video recording started
        audio_start_timestamp: Unix timestamp when audio recording started
        video_duration: Video duration in seconds (if None, will be calculated)
    
    Returns:
        True if successful, False otherwise
    """
    # Redirect to FFmpeg function
    print(f"⚠️ PyAV merge function called - redirecting to FFmpeg (more reliable)")
    return merge_video_audio_ffmpeg(video_path, audio_file_path, output_path, video_start_timestamp, audio_start_timestamp, video_duration)
    
    try:
        print(f"🔄 Merging video and audio using PyAV...")
        print(f"   Video: {video_path}")
        print(f"   Audio: {audio_file_path}")
        print(f"   Output: {output_path}")
        
        # CRITICAL: Convert all paths to absolute paths for accurate file access
        # Normalize paths first to handle separators correctly
        video_path = os.path.normpath(video_path)
        audio_file_path = os.path.normpath(audio_file_path)
        output_path = os.path.normpath(output_path)
        
        # Convert to absolute paths if they're relative
        # settings is already imported at the top of the file
        if not os.path.isabs(video_path):
            # Try to resolve relative to MEDIA_ROOT first
            video_path = os.path.join(settings.MEDIA_ROOT, video_path)
            video_path = os.path.normpath(video_path)
        
        if not os.path.isabs(audio_file_path):
            # Try to resolve relative to MEDIA_ROOT first
            audio_file_path = os.path.join(settings.MEDIA_ROOT, audio_file_path)
            audio_file_path = os.path.normpath(audio_file_path)
        
        if not os.path.isabs(output_path):
            # Try to resolve relative to MEDIA_ROOT first
            output_path = os.path.join(settings.MEDIA_ROOT, output_path)
            output_path = os.path.normpath(output_path)
        
        # Get absolute paths (resolve any symlinks or relative components)
        video_path = os.path.abspath(video_path)
        audio_file_path = os.path.abspath(audio_file_path)
        output_path = os.path.abspath(output_path)
        
        # Verify all files exist before proceeding
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"   ✅ Absolute video path: {video_path}")
        print(f"   ✅ Absolute audio path: {audio_file_path}")
        print(f"   ✅ Absolute output path: {output_path}")
        print(f"   ✅ Video exists: {os.path.exists(video_path)}")
        print(f"   ✅ Audio exists: {os.path.exists(audio_file_path)}")
        print(f"   ✅ Output directory exists: {os.path.exists(output_dir)}")
        
        # Open input video container
        video_container = av.open(video_path)
        video_stream = video_container.streams.video[0]
        
        # Get video duration if not provided
        if video_duration is None or video_duration == 0:
            if video_stream.duration:
                video_duration = float(video_stream.duration * video_stream.time_base)
            elif video_container.duration:
                video_duration = float(video_container.duration) / av.time_base
            else:
                # Estimate from frames
                frame_count = 0
                for frame in video_container.decode(video_stream):
                    frame_count += 1
                # Get frame rate (PyAV uses average_rate)
                fps = 5.0  # Default to our recording rate
                if hasattr(video_stream, 'average_rate') and video_stream.average_rate:
                    fps = float(video_stream.average_rate)
                elif hasattr(video_stream, 'rate') and video_stream.rate:
                    fps = float(video_stream.rate)
                video_duration = frame_count / fps if fps > 0 else 0
                video_container.seek(0)  # Reset to beginning
        
        # Open input audio container
        audio_container = av.open(audio_file_path)
        audio_stream = audio_container.streams.audio[0]
        
        # Get audio duration
        audio_duration = 0
        if audio_stream.duration:
            audio_duration = float(audio_stream.duration * audio_stream.time_base)
        elif audio_container.duration:
            audio_duration = float(audio_container.duration) / av.time_base
        
        print(f"   📹 Video duration: {video_duration:.2f}s")
        print(f"   🎙️ Audio duration: {audio_duration:.2f}s")
        
        # CRITICAL: Always use video duration as authoritative
        # Video duration is the source of truth - audio will be trimmed to match exactly
        # This ensures perfect synchronization regardless of when audio started/stopped
        final_audio_duration = video_duration if video_duration > 0 else audio_duration
        print(f"   🎯 Using video duration as authoritative: {final_audio_duration:.2f}s")
        print(f"   ✅ Audio will be trimmed to match video exactly (perfect sync)")
        
        # CRITICAL: Calculate audio synchronization offset
        # This determines how much to skip from the beginning of audio to align with video
        audio_skip_seconds = 0.0  # How much audio to skip from the beginning
        audio_padding_seconds = 0.0  # How much silence to add at the beginning (if audio started after video)
        
        if video_start_timestamp and audio_start_timestamp:
            time_diff = audio_start_timestamp - video_start_timestamp  # Positive = audio started after video
            
            print(f"   🕐 Synchronization analysis:")
            print(f"      Video started at: {video_start_timestamp:.6f}")
            print(f"      Audio started at: {audio_start_timestamp:.6f}")
            print(f"      Time difference: {time_diff:.6f}s ({(time_diff * 1000):.2f}ms)")
            
            if abs(time_diff) > 0.05:  # More than 50ms difference
                if time_diff > 0:
                    # Audio started AFTER video - need to add silence/padding at start of audio
                    audio_padding_seconds = time_diff
                    print(f"   ⏱️ Audio started {time_diff:.3f}s AFTER video")
                    print(f"   🔧 Will add {audio_padding_seconds:.3f}s of silence at audio start")
                else:
                    # Audio started BEFORE video - need to skip beginning of audio
                    audio_skip_seconds = abs(time_diff)
                    print(f"   ⏱️ Audio started {abs(time_diff):.3f}s BEFORE video")
                    print(f"   🔧 Will skip first {audio_skip_seconds:.3f}s of audio")
            else:
                print(f"   ✅ Perfect synchronization! Time difference: {(time_diff * 1000):.1f}ms (< 50ms)")
                print(f"   ✅ No adjustment needed - both started at exact same time!")
        else:
            print(f"   ⚠️ Timestamps not provided - assuming perfect synchronization")
            print(f"      video_start_timestamp: {video_start_timestamp}")
            print(f"      audio_start_timestamp: {audio_start_timestamp}")
        
        # Verify audio duration is sufficient
        if audio_duration < final_audio_duration:
            print(f"   ⚠️ WARNING: Audio ({audio_duration:.2f}s) is shorter than video ({final_audio_duration:.2f}s)")
            print(f"   ⚠️ Video will be trimmed to match audio duration")
            final_audio_duration = audio_duration  # Use shorter duration
        elif audio_duration > final_audio_duration:
            print(f"   ✅ Audio ({audio_duration:.2f}s) is longer than video ({final_audio_duration:.2f}s) - will trim audio to match")
        else:
            print(f"   ✅ Audio and video durations match perfectly!")
        
        # Create output container with explicit format for MP4
        # Ensure proper MP4 container format for browser compatibility
        output_container = av.open(output_path, mode='w', format='mp4')
        
        # Get frame rate from video stream (PyAV uses average_rate or calculate from time_base)
        if hasattr(video_stream, 'average_rate') and video_stream.average_rate:
            fps = float(video_stream.average_rate)
        elif hasattr(video_stream, 'rate') and video_stream.rate:
            fps = float(video_stream.rate)
        else:
            # Calculate from time_base if available, otherwise default to 5 fps (our recording rate)
            if video_stream.time_base:
                # Try to estimate from duration and frame count
                fps = 5.0  # Default to our recording rate
            else:
                fps = 5.0  # Default to our recording rate
        
        print(f"   📹 Video FPS: {fps}")
        
        # Convert FPS to Fraction for PyAV (required format)
        # Use limit_denominator for better precision
        fps_fraction = Fraction(fps).limit_denominator(1000) if fps > 0 else Fraction(5, 1)
        
        # Add video stream to output (re-encode with H.264 for browser compatibility)
        output_video_stream = output_container.add_stream('libx264', rate=fps_fraction)
        output_video_stream.width = video_stream.width
        output_video_stream.height = video_stream.height
        output_video_stream.pix_fmt = 'yuv420p'  # Required for browser compatibility
        # Configure H.264 codec options for browser compatibility
        output_video_stream.options = {
            'preset': 'medium',  # Balance between speed and quality
            'crf': '23',  # Constant Rate Factor (lower = better quality)
            'profile': 'baseline',  # Baseline profile for maximum browser compatibility
            'level': '3.1',  # H.264 level
            'movflags': '+faststart'  # Enable faststart for web streaming (moov atom at beginning)
        }
        print(f"   📹 Video stream configured: {output_video_stream.width}x{output_video_stream.height}, {fps:.2f} fps, H.264 baseline")
        
        # Add audio stream to output (encode as AAC)
        # CRITICAL: Configure audio stream properly for AAC encoding
        # Use explicit layout parameter when creating stream
        try:
            # Try creating stream with explicit mono layout
            output_audio_stream = output_container.add_stream('aac', rate=44100, layout='mono')
            print(f"   ✅ Audio stream created with mono layout")
        except Exception as e:
            print(f"   ⚠️ Could not create stream with layout: {e}, creating without layout")
            output_audio_stream = output_container.add_stream('aac', rate=44100)
        
        # Configure codec context for mono audio and bitrate
        try:
            # Set bitrate using options (most reliable method)
            output_audio_stream.options = {
                'ac': '1',      # Audio channels: 1 (mono)
                'b:a': '192k',  # Audio bitrate: 192kbps
                'ar': '44100'   # Sample rate: 44100Hz
            }
            print(f"   ✅ Audio stream options configured: mono, 192kbps, 44100Hz")
        except Exception as e:
            print(f"   ⚠️ Could not set audio options: {e}")
        
        # Log final audio stream configuration
        try:
            print(f"   📊 Output audio stream config:")
            print(f"      Format: {output_audio_stream.format}")
            print(f"      Layout: {output_audio_stream.layout}")
            print(f"      Rate: {output_audio_stream.rate}")
            if hasattr(output_audio_stream, 'codec_context'):
                print(f"      Codec context channels: {getattr(output_audio_stream.codec_context, 'channels', 'N/A')}")
        except Exception as e:
            print(f"   ⚠️ Could not log audio stream config: {e}")
        
        # CRITICAL: Seek audio to skip beginning if audio started before video
        if audio_skip_seconds > 0.05:  # More than 50ms to skip
            # Calculate seek timestamp in audio stream's time base
            seek_pts = int(audio_skip_seconds / audio_stream.time_base)
            try:
                audio_container.seek(seek_pts, stream=audio_stream)
                print(f"   🔧 Seeking audio to skip first {audio_skip_seconds:.3f}s (pts={seek_pts})")
            except Exception as e:
                print(f"   ⚠️ Could not seek audio: {e}, will process from beginning")
                audio_skip_seconds = 0.0  # Reset skip if seeking fails
        else:
            # Reset audio container to beginning if no skipping needed
            try:
                audio_container.seek(0, stream=audio_stream)
            except:
                pass
            print(f"   ✅ Audio starting from beginning (no skip needed)")
        
        # CRITICAL: Process video frames first - video duration is authoritative
        video_frame_count = 0
        video_time_processed = 0.0
        frame_duration = 1.0 / fps if fps > 0 else 0.2  # Default to 0.2s per frame (5fps)
        
        for frame in video_container.decode(video_stream):
            # Stop if we've reached the final duration (use shorter of video/audio)
            if video_time_processed + frame_duration > final_audio_duration:
                # Don't add this frame - we've reached the limit
                break
            
            # Re-encode video frame
            for packet in output_video_stream.encode(frame):
                output_container.mux(packet)
            video_frame_count += 1
            video_time_processed += frame_duration
        
        # Flush video encoder
        for packet in output_video_stream.encode():
            output_container.mux(packet)
        
        print(f"   📹 Processed {video_frame_count} video frames ({video_time_processed:.2f}s)")
        print(f"   🎯 Video duration used as authoritative: {final_audio_duration:.2f}s")
        
        # Process audio frames (with duration limit)
        audio_frame_count = 0
        # CRITICAL: Initialize audio_time_processed accounting for skipped audio
        # This tracks position in the SOURCE audio file (after seeking)
        audio_time_processed = audio_skip_seconds  # Start from skip point
        
        # CRITICAL: Always create resampler to ensure audio frames match output format exactly
        # PyAV requires exact format matching for encoding, so we always resample
        resampler = None
        needs_resampling = True  # Always resample to ensure compatibility
        
        print(f"   🔧 Audio format conversion:")
        print(f"      Input: format={audio_stream.format.name}, layout={audio_stream.layout.name}, rate={audio_stream.rate}")
        print(f"      Output: format={output_audio_stream.format.name}, layout={output_audio_stream.layout.name}, rate={output_audio_stream.rate}")
        
        try:
            resampler = av.AudioResampler(
                format=output_audio_stream.format,
                layout=output_audio_stream.layout,
                rate=output_audio_stream.rate
            )
            print(f"   ✅ Audio resampler created successfully")
        except Exception as e:
            print(f"   ⚠️ Could not create resampler: {e}")
            print(f"   ⚠️ Will attempt direct encoding (may fail if formats don't match exactly)")
            needs_resampling = False
            import traceback
            traceback.print_exc()
        
        print(f"   🎙️ Starting audio frame processing...")
        print(f"   📊 Audio timeline: skip={audio_skip_seconds:.3f}s, padding={audio_padding_seconds:.3f}s")
        audio_frames_decoded = 0
        
        # CRITICAL: Add silence padding if audio started after video
        # This ensures audio timeline aligns with video timeline starting from 0
        if audio_padding_seconds > 0.05:
            print(f"   🔇 Adding {audio_padding_seconds:.3f}s of silence at audio start (audio started after video)")
            # Create silence frame(s) to pad the beginning
            import numpy as np
            silence_samples = int(audio_padding_seconds * output_audio_stream.rate)
            silence_frame = av.AudioFrame.from_ndarray(
                np.zeros((silence_samples, 1), dtype=np.float32),
                format=output_audio_stream.format.name,
                layout=output_audio_stream.layout.name
            )
            silence_frame.sample_rate = output_audio_stream.rate
            silence_frame.pts = 0  # Start at beginning of timeline
            
            try:
                # Encode silence frames
                packets = list(output_audio_stream.encode(silence_frame))
                for packet in packets:
                    output_container.mux(packet)
                audio_frame_count += 1
                # Note: audio_time_processed tracks SOURCE audio position, not timeline position
                # Padding doesn't affect source position, so we don't increment it here
                print(f"   ✅ Added {audio_padding_seconds:.3f}s of silence padding")
            except Exception as e:
                print(f"   ⚠️ Could not add silence padding: {e}")
                audio_padding_seconds = 0.0  # Reset if padding fails
        
        # Track audio timeline offset (accounts for skipped audio)
        audio_timeline_offset = audio_skip_seconds  # Audio timeline starts after skip
        
        for frame in audio_container.decode(audio_stream):
            audio_frames_decoded += 1
            
            # CRITICAL: Check if we've reached the duration limit (video duration is authoritative)
            frame_duration = float(frame.samples) / frame.sample_rate
            
            # Calculate where this frame should be in the final timeline
            # Account for padding and skip
            frame_timeline_position = audio_time_processed - audio_skip_seconds + audio_padding_seconds
            
            if frame_timeline_position + frame_duration > final_audio_duration:
                # Trim the last frame if needed
                remaining_time = final_audio_duration - audio_time_processed
                if remaining_time > 0:
                    # Trim frame to remaining time
                    samples_to_keep = int(remaining_time * frame.sample_rate)
                    if samples_to_keep < frame.samples:
                        # Create new frame with fewer samples
                        import numpy as np
                        audio_array = frame.to_ndarray()
                        if len(audio_array.shape) > 1:
                            audio_array = audio_array[:samples_to_keep, :]
                        else:
                            audio_array = audio_array[:samples_to_keep]
                        frame = av.AudioFrame.from_ndarray(audio_array, format=frame.format.name, layout=frame.layout.name)
                        frame.sample_rate = frame.sample_rate
                        frame.pts = frame.pts
                
                # CRITICAL: Calculate correct PTS for trimmed frame
                # This frame should be at the end of the video timeline
                frame_timeline_position = audio_time_processed - audio_skip_seconds + audio_padding_seconds
                
                # CRITICAL: Always resample trimmed frame to match output stream format
                frames_to_encode = []
                if resampler:
                    try:
                        resampled = resampler.resample(frame)
                        if isinstance(resampled, list):
                            frames_to_encode = [f for f in resampled if f is not None]
                        elif resampled is not None:
                            frames_to_encode = [resampled]
                        else:
                            frames_to_encode = []
                    except Exception as e:
                        print(f"   ⚠️ Resampling trimmed frame failed: {e}")
                        frames_to_encode = []
                else:
                    # No resampler - try direct encoding
                    frame.pts = None  # Reset PTS
                    frames_to_encode = [frame]
                
                # Encode and mux all frames with correct PTS
                if not frames_to_encode:
                    print(f"   ⚠️ No frames to encode for final trimmed audio - audio may be incomplete")
                else:
                    for frame_to_encode in frames_to_encode:
                        if frame_to_encode is not None:
                            try:
                                # CRITICAL: Set PTS to align with video timeline
                                if output_audio_stream.time_base:
                                    frame_to_encode.pts = int(frame_timeline_position / output_audio_stream.time_base)
                                else:
                                    frame_to_encode.pts = None
                                
                                packets = list(output_audio_stream.encode(frame_to_encode))
                                if packets:
                                    for packet in packets:
                                        output_container.mux(packet)
                                    audio_frame_count += 1
                                else:
                                    print(f"   ⚠️ No packets generated for final trimmed audio frame")
                            except Exception as e:
                                print(f"   ⚠️ Error encoding final audio frame: {e}")
                                import traceback
                                traceback.print_exc()
                break
            
            # CRITICAL: Calculate correct PTS for this audio frame
            # PTS must align with video timeline (starting from 0)
            # Account for padding (if audio started after video) and skip (if audio started before video)
            # frame_timeline_position is where this frame should be in the final synchronized timeline
            frame_timeline_position = audio_time_processed - audio_skip_seconds + audio_padding_seconds
            
            # CRITICAL: Always resample audio frames to match output stream format
            # Even if formats appear to match, PyAV requires exact format compatibility
            frames_to_encode = []
            if resampler:
                try:
                    resampled = resampler.resample(frame)
                    # Resampler can return a single frame or a list of frames
                    if isinstance(resampled, list):
                        frames_to_encode = [f for f in resampled if f is not None]
                    elif resampled is not None:
                        frames_to_encode = [resampled]
                    else:
                        print(f"   ⚠️ Resampler returned None for frame at {audio_time_processed:.2f}s")
                        frames_to_encode = []
                except Exception as e:
                    print(f"   ⚠️ Resampling failed at {audio_time_processed:.2f}s: {e}")
                    # Try to convert frame format manually
                    try:
                        # Convert frame to output format
                        frame.pts = None  # Reset PTS for re-encoding
                        frames_to_encode = [frame]
                    except Exception as e2:
                        print(f"   ⚠️ Frame conversion also failed: {e2}")
                        frames_to_encode = []
            else:
                # No resampler - try direct encoding (may fail if formats don't match)
                try:
                    # Ensure frame format matches output
                    frame.pts = None  # Reset PTS
                    frames_to_encode = [frame]
                except Exception as e:
                    print(f"   ⚠️ Frame preparation failed: {e}")
                    frames_to_encode = []
            
            # Re-encode all frames with correct PTS
            if not frames_to_encode:
                print(f"   ⚠️ No frames to encode at {audio_time_processed:.2f}s (timeline pos: {frame_timeline_position:.2f}s) - skipping")
            else:
                for frame_to_encode in frames_to_encode:
                    if frame_to_encode is not None:
                        try:
                            # CRITICAL: Set PTS to align with video timeline
                            # PTS is in output stream's time base
                            # Calculate PTS based on timeline position (where frame should be in final video)
                            if output_audio_stream.time_base:
                                frame_to_encode.pts = int(frame_timeline_position / output_audio_stream.time_base)
                            else:
                                # Fallback: let encoder set PTS automatically
                                frame_to_encode.pts = None
                            
                            # Ensure frame has correct sample rate and layout
                            if hasattr(frame_to_encode, 'sample_rate') and frame_to_encode.sample_rate != output_audio_stream.rate:
                                print(f"   ⚠️ Frame sample rate mismatch: {frame_to_encode.sample_rate} vs {output_audio_stream.rate}")
                            
                            # Encode the frame
                            packets = list(output_audio_stream.encode(frame_to_encode))
                            if packets:
                                for packet in packets:
                                    output_container.mux(packet)
                                audio_frame_count += 1
                            else:
                                print(f"   ⚠️ No packets generated for audio frame at timeline {frame_timeline_position:.2f}s")
                        except Exception as e:
                            print(f"   ⚠️ Error encoding audio frame at timeline {frame_timeline_position:.2f}s: {e}")
                            import traceback
                            traceback.print_exc()
                            # Continue with next frame instead of failing completely
            
            # Update audio_time_processed AFTER processing (tracks position in source audio file)
            audio_time_processed += frame_duration
            
            # Log progress every 10 seconds
            if int(audio_time_processed) % 10 == 0 and audio_time_processed > 0:
                print(f"   🎙️ Processed {audio_time_processed:.1f}s of audio ({audio_frame_count} frames)")
        
        # Flush audio encoder (get any remaining packets)
        try:
            for packet in output_audio_stream.encode():
                output_container.mux(packet)
        except Exception as e:
            print(f"   ⚠️ Error flushing audio encoder: {e}")
        
        # CRITICAL: Properly close containers to finalize the file
        # This ensures the MP4 file is properly formatted and can be played
        try:
            output_container.close()
            print(f"   ✅ Output container closed successfully")
        except Exception as e:
            print(f"   ⚠️ Error closing output container: {e}")
            import traceback
            traceback.print_exc()
        
        video_container.close()
        audio_container.close()
        
        # CRITICAL: Verify the merged file was actually created and has content
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Merged video file was not created: {output_path}")
        
        merged_file_size = os.path.getsize(output_path)
        if merged_file_size == 0:
            raise ValueError(f"Merged video file is empty: {output_path}")
        
        # Verify the file is a valid MP4 by trying to open it
        try:
            verify_container = av.open(output_path)
            video_streams = [s for s in verify_container.streams if s.type == 'video']
            audio_streams = [s for s in verify_container.streams if s.type == 'audio']
            verify_container.close()
            
            if len(video_streams) == 0:
                raise ValueError(f"Merged file has no video stream: {output_path}")
            if len(audio_streams) == 0:
                raise ValueError(f"Merged file has no audio stream: {output_path}")
            
            print(f"   ✅ File format verified: {len(video_streams)} video stream(s), {len(audio_streams)} audio stream(s)")
        except Exception as e:
            print(f"   ⚠️ Could not verify file format: {e}")
            # Don't fail - file exists and has content, format verification is optional
        
        print(f"✅ PyAV merge completed successfully!")
        print(f"   Video frames processed: {video_frame_count}")
        print(f"   Audio frames decoded: {audio_frames_decoded}")
        print(f"   Audio frames encoded: {audio_frame_count}")
        print(f"   Output path: {output_path}")
        print(f"   Output file size: {merged_file_size / 1024 / 1024:.2f} MB")
        print(f"   ✅ Merged file verified: exists={os.path.exists(output_path)}, size={merged_file_size} bytes")
        
        # CRITICAL: Verify audio was actually encoded
        if audio_frame_count == 0:
            raise ValueError(f"No audio frames were encoded! Audio frames decoded: {audio_frames_decoded}, but none encoded. Video will have NO audio.")
        elif audio_frame_count < audio_frames_decoded / 2:
            print(f"   ⚠️ WARNING: Only {audio_frame_count} audio frames encoded out of {audio_frames_decoded} decoded")
            print(f"   ⚠️ This may indicate encoding issues - video may have reduced audio quality")
        
        return True
        
    except Exception as e:
        print(f"❌ PyAV merge failed: {e}")
        import traceback
        traceback.print_exc()
        return False


class _VideoCapture:
    def __init__(self, camera_index=0):
        print(f"🎥 Attempting to open camera {camera_index}")
        self.cap = None
        
        if not CV2_AVAILABLE or cv2 is None:
            print("❌ OpenCV (cv2) not available - camera features disabled")
            return
        
        try:
            # Try DirectShow backend first (works on Windows)
            self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            
            # If DirectShow fails, try default backend
            if not self.cap.isOpened():
                print(f"❌ DirectShow failed for camera {camera_index}, trying default...")
                self.cap = cv2.VideoCapture(camera_index)
            
            if not self.cap.isOpened():
                print(f"❌ Failed to open camera {camera_index}")
                # Try different camera indices
                for i in range(1, 5):
                    print(f"🎥 Trying camera {i} with DirectShow...")
                    self.cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                    if self.cap.isOpened():
                        print(f"✅ Successfully opened camera {i}")
                        break
                    else:
                        print(f"❌ DirectShow failed for camera {i}, trying default...")
                        self.cap = cv2.VideoCapture(i)
                        if self.cap.isOpened():
                            print(f"✅ Successfully opened camera {i} with default backend")
                            break
                else:
                    print(f"❌ No cameras found - will use fallback frames")
                    self.cap = None
                    return
            
            if self.cap and self.cap.isOpened():
                # Set camera properties
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                print(f"✅ Camera configured successfully")
                
                # Give camera a moment to initialize
                time.sleep(0.3)
                
                # Warm up camera by reading multiple frames (cameras often need this)
                # Flush any stale frames in the buffer
                for i in range(5):
                    ret, _ = self.cap.read()
                    if ret:
                        break
                    time.sleep(0.1)
                
                # Test reading a frame to ensure it's working
                ret, test_frame = self.cap.read()
                if ret and test_frame is not None:
                    print(f"✅ Camera test frame captured: {test_frame.shape}")
                else:
                    print(f"⚠️ Camera test frame failed, but camera is opened - will retry in capture loop")
        except Exception as e:
            print(f"❌ Camera initialization error: {e}")
            self.cap = None
        
    def isOpened(self) -> bool:
        return self.cap is not None and self.cap.isOpened()
    
    def read(self):
        if self.cap and self.cap.isOpened():
            return self.cap.read()
        return False, None
    
    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None


class SimpleRealVideoCamera:
    """Simple synchronous camera implementation."""

    def __init__(self, session_id):
        self.session_id = session_id
        print(f"🎥 Initializing simple camera for session {session_id}")
        self.video = _VideoCapture()
        print(f"🎥 Camera isOpened: {self.video.isOpened()}")
        
        self._last_warning_state = {
            "no_person_warning_active": False,
            "multiple_people": False,
            "phone_detected": False,
            "no_person": False,
            "low_concentration": False,
            "tab_switched": False,
            "excessive_noise": False,
            "multiple_speakers": False,
        }
        # NEW: frame buffer and thread control
        self._frame_lock = None
        self._latest_frame = None
        self._running = False
        
        # Warning tracking for counts
        self._warning_counts = {}
        self._last_warning_logged = {}  # Track last time each warning was logged to avoid spam
        
        # Cached fallback frame to avoid regenerating
        self._cached_fallback_frame = None
        self._fallback_frame_cache_time = 0
        self._fallback_print_time = 0  # Track when we last printed fallback warning
        
        # YOLO model - NOT loaded during initialization (only during technical interview)
        self._yolo = None
        self._yolo_loaded = False
        self._proctoring_active = False  # Flag to track if proctoring/warning capture is active
        
        # Video recording - record raw video frames in parallel with YOLO detection
        self._video_writer = None
        self._recording_active = False
        self._video_file_path = None
        self._frame_width = 640
        self._frame_height = 480
        self._fps = 5  # Record at 5 fps to match actual capture rate (sleep 0.2s = 5 fps)
        # Note: This FPS matches the frame capture rate in _capture_and_detect_loop (time.sleep(0.2) = 5 fps)
        self._last_frame_time = None
        self._frame_timestamps = []  # Track frame timestamps for accurate playback
        
        # NEW: start basic frame capture loop (without YOLO) if camera available
        # This allows camera to work for identity verification without YOLO
        try:
            import threading
            import cv2
            if self.video.isOpened():
                self._frame_lock = threading.Lock()
                self._running = True
                # Give camera a moment to fully initialize before starting capture
                time.sleep(0.3)
                # Start basic frame capture only (no YOLO detection yet)
                self._detector_thread = threading.Thread(target=self._capture_and_detect_loop, daemon=True)
                self._detector_thread.start()
                print(f"✅ Basic camera frame capture started for session {self.session_id} (YOLO not loaded yet)")
            else:
                print(f"⚠️ Camera not opened - cannot start frame capture for session {self.session_id}")
        except Exception as e:
            print(f"⚠️ Failed to start frame capture loop: {e}")
            import traceback
            traceback.print_exc()
    
    def activate_yolo_proctoring(self):
        """Activate YOLO model and start proctoring warnings when technical interview starts"""
        if self._yolo_loaded:
            print(f"✅ YOLO already loaded for session {self.session_id}")
            self._proctoring_active = True
            return True
        
        try:
            from ultralytics import YOLO
            from django.conf import settings
            import os
            try:
                # Load YOLO model only when technical interview starts
                # Use absolute path from BASE_DIR: BASE_DIR/yolov8n.pt
                model_path = os.path.join(settings.BASE_DIR, 'yolov8n.pt')
                if os.path.exists(model_path):
                    self._yolo = YOLO(model_path)
                    print(f"✅ YOLOv8 model loaded from: {model_path}")
                else:
                    # Fallback: try current directory
                    fallback_path = 'yolov8n.pt'
                    self._yolo = YOLO(fallback_path)
                    print(f"✅ YOLOv8 model loaded from fallback path: {fallback_path}")
                self._yolo_loaded = True
                self._proctoring_active = True
                print(f"✅ YOLOv8 model loaded and proctoring activated for session {self.session_id}")
                # Start video recording when proctoring starts
                self.start_video_recording()
                return True
            except Exception as e:
                print(f"⚠️ Could not load yolov8n.pt: {e}")
                self._yolo = None
                return False
        except Exception as e:
            print(f"ℹ️ ultralytics not installed; falling back to Haar cascade. {e}")
            return False
    
    def start_video_recording(self, synchronized_start_time=None):
        """Start recording video frames to a file. Returns the exact start timestamp for synchronization.
        
        Args:
            synchronized_start_time: Optional future timestamp to start at (for perfect sync with audio).
                                    If provided, video will wait until this exact time to start recording.
        """
        if self._recording_active:
            print(f"⚠️ Video recording already active for session {self.session_id}")
            return getattr(self, '_recording_start_timestamp', None)
        
        try:
            import time
            
            # CRITICAL: If synchronized_start_time is provided, use it as the authoritative start time
            # This ensures both video and audio start at the EXACT same moment
            # IMPORTANT: Set _recording_start_timestamp IMMEDIATELY to synchronized_start_time
            # This ensures the timestamp is available even before first frame is written
            if synchronized_start_time:
                self._synchronized_start_time = synchronized_start_time
                self._recording_start_timestamp = synchronized_start_time  # Set immediately for synchronization
                print(f"🕐 Using synchronized start time: {synchronized_start_time}")
                print(f"   ⏱️ Will start recording at exact time (current: {time.time()}, wait: {(synchronized_start_time - time.time()) * 1000:.1f}ms)")
                print(f"   ✅ Video start timestamp set IMMEDIATELY: {self._recording_start_timestamp}")
                print(f"   ✅ Audio should use this EXACT timestamp for perfect synchronization!")
            else:
                # Calculate a future timestamp (500ms from now) to allow frontend to prepare
                # This accounts for network delay and frontend initialization
                current_time = time.time()
                self._synchronized_start_time = current_time + 0.5  # 500ms in the future
                self._recording_start_timestamp = self._synchronized_start_time  # Set immediately
                print(f"🕐 Calculated synchronized start time: {self._synchronized_start_time} (500ms from now)")
                print(f"   ✅ Video start timestamp set IMMEDIATELY: {self._recording_start_timestamp}")
            
            self._first_frame_written = False  # Flag to track first frame
            # Store the synchronized time for the capture loop to use
            # But DON'T set _recording_start_timestamp until first frame is written
            
            # Create video directories if they don't exist
            # Raw videos (without audio) go to interview_videos_raw/
            # Merged videos (with audio) go to interview_videos_merged/
            raw_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_raw')
            merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
            os.makedirs(raw_video_dir, exist_ok=True)
            os.makedirs(merged_video_dir, exist_ok=True)
            
            # Generate video filename with session ID and timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            video_filename = f"{self.session_id}_{timestamp}.mp4"
            # Save raw video (without audio) to interview_videos_raw/
            self._video_file_path = os.path.join(raw_video_dir, video_filename)
            
            # Check if cv2 is available
            if not CV2_AVAILABLE or cv2 is None:
                print("❌ OpenCV (cv2) not available - cannot create video writer")
                self._video_writer = None
                return None
            
            # Initialize VideoWriter with H.264 codec (browser-compatible)
            # Try different codecs in order of preference
            codecs_to_try = [
                ('avc1', 'H.264/AVC1 - Best browser compatibility'),
                ('H264', 'H.264 - Alternative'),
                ('XVID', 'XVID - Fallback'),
                ('mp4v', 'MP4V - Last resort')
            ]
            
            self._video_writer = None
            for codec_name, description in codecs_to_try:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec_name)
                    # Try to create video writer with this codec
                    test_writer = cv2.VideoWriter(
                        self._video_file_path,
                        fourcc,
                        self._fps,
                        (self._frame_width, self._frame_height)
                    )
                    # Test if it's actually opened
                    if test_writer.isOpened():
                        self._video_writer = test_writer
                        print(f"✅ Video writer created with codec: {codec_name} ({description})")
                        break
                    else:
                        test_writer.release()
                        print(f"⚠️ Codec {codec_name} failed to open, trying next...")
                except Exception as e:
                    print(f"⚠️ Error with codec {codec_name}: {e}")
                    continue
            
            # If all codecs failed, use default
            if self._video_writer is None:
                if CV2_AVAILABLE and cv2:
                    print(f"⚠️ All codecs failed, using default")
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    self._video_writer = cv2.VideoWriter(
                        self._video_file_path,
                        fourcc,
                        self._fps,
                        (self._frame_width, self._frame_height)
                    )
                else:
                    print("❌ OpenCV not available - cannot create video writer")
                    self._video_writer = None
            
            if self._video_writer.isOpened():
                self._recording_active = True
                print(f"✅ Video recording started for session {self.session_id}: {video_filename}")
                # CRITICAL: Return the synchronized start time (not the timestamp)
                # The timestamp will be set when the first frame is written
                # This ensures audio can start at the EXACT same moment for perfect synchronization
                synchronized_time = getattr(self, '_synchronized_start_time', None)
                if synchronized_time:
                    print(f"🕐 Video recording active - will start at synchronized time: {synchronized_time}")
                    print(f"   ✅ First frame timestamp will be set when frame is written at this exact time")
                    return synchronized_time
                else:
                    # Fallback: return current time + small delay
                    fallback_time = time.time() + 0.5
                    print(f"🕐 Video recording active - using fallback start time: {fallback_time}")
                    return fallback_time
            else:
                print(f"❌ Failed to open video writer for session {self.session_id}")
                self._video_writer = None
                return None
        except Exception as e:
            print(f"❌ Error starting video recording for session {self.session_id}: {e}")
            import traceback
            traceback.print_exc()
            self._video_writer = None
            return None
    
    def ensure_browser_compatible_video(self, video_path):
        """Convert video to H.264 format for browser compatibility using PyAV."""
        if not os.path.exists(video_path):
            return None
        
        try:
            # Use PyAV for conversion
            if not PYAV_AVAILABLE:
                print(f"⚠️ PyAV not available - cannot convert video")
                return video_path  # Return original if PyAV not available
            
            # Create converted video path
            base_name = os.path.splitext(video_path)[0]
            converted_video_path = f"{base_name}_converted.mp4"
            
            # Skip if already converted
            if '_converted' in video_path or '_with_audio' in video_path:
                print(f"✅ Video already converted: {video_path}")
                return video_path
            
            # Create converted video path
            base_name = os.path.splitext(video_path)[0]
            converted_video_path = f"{base_name}_converted.mp4"
            
            # Skip if already converted
            if '_converted' in video_path or '_with_audio' in video_path:
                print(f"✅ Video already converted: {video_path}")
                return video_path
            
            print(f"🔄 Converting video to H.264 for browser compatibility using PyAV: {video_path}")
            
            # Use PyAV to convert video
            try:
                # Open input video
                input_container = av.open(video_path)
                video_stream = input_container.streams.video[0]
                
                # Get frame rate from video stream (PyAV uses average_rate or calculate from time_base)
                if hasattr(video_stream, 'average_rate') and video_stream.average_rate:
                    fps = float(video_stream.average_rate)
                elif hasattr(video_stream, 'rate') and video_stream.rate:
                    fps = float(video_stream.rate)
                else:
                    # Calculate from time_base if available, otherwise default to 5 fps (our recording rate)
                    if video_stream.time_base:
                        # Try to estimate from duration and frame count
                        fps = 5.0  # Default to our recording rate
                    else:
                        fps = 5.0  # Default to our recording rate
                
                print(f"   📹 Video FPS: {fps}")
                
                # Convert FPS to Fraction for PyAV (required format)
                # Use limit_denominator for better precision
                fps_fraction = Fraction(fps).limit_denominator(1000) if fps > 0 else Fraction(5, 1)
                
                # Create output container
                output_container = av.open(converted_video_path, mode='w')
                
                # Add video stream with H.264 codec
                output_video_stream = output_container.add_stream('libx264', rate=fps_fraction)
                output_video_stream.width = video_stream.width
                output_video_stream.height = video_stream.height
                output_video_stream.pix_fmt = 'yuv420p'
                output_video_stream.options = {
                    'preset': 'medium',
                    'crf': '23',
                    'movflags': '+faststart'
                }
                
                # Copy video frames
                for frame in input_container.decode(video_stream):
                    for packet in output_video_stream.encode(frame):
                        output_container.mux(packet)
                
                # Flush encoder
                for packet in output_video_stream.encode():
                    output_container.mux(packet)
                
                # Close containers
                output_container.close()
                input_container.close()
                
                if os.path.exists(converted_video_path):
                    try:
                        os.remove(video_path)  # Remove original
                    except:
                        pass
                    print(f"✅ Video converted to H.264 using PyAV: {converted_video_path}")
                    return converted_video_path
                else:
                    print(f"⚠️ Video conversion failed - output file not created")
                    return video_path
            except Exception as e:
                print(f"⚠️ PyAV conversion error: {e}")
                import traceback
                traceback.print_exc()
                return video_path
        except Exception as e:
            print(f"⚠️ Error converting video: {e}")
            return video_path
    
    def stop_video_recording(self, audio_file_path=None, audio_start_timestamp=None, video_start_timestamp=None, synchronized_stop_time=None):
        """Stop recording and save video file. Optionally merge with audio using ffmpeg.
        
        Args:
            audio_file_path: Path to audio file to merge
            audio_start_timestamp: Unix timestamp when audio recording started (for sync)
            video_start_timestamp: Unix timestamp when video recording started (for sync)
            synchronized_stop_time: Optional future timestamp to stop at (for perfect sync with audio)
        """
        import time
        
        # CRITICAL: If synchronized_stop_time is provided, wait until that exact moment
        if synchronized_stop_time:
            current_time = time.time()
            if current_time < synchronized_stop_time:
                wait_time = synchronized_stop_time - current_time
                print(f"🕐 Video waiting {wait_time * 1000:.1f}ms until synchronized stop time: {synchronized_stop_time}")
                time.sleep(wait_time)
                print(f"✅ Reached synchronized stop time - stopping video now")
            # CRITICAL: Use synchronized_stop_time as authoritative timestamp (not current time after wait)
            # This ensures video and audio stop at the EXACT same timestamp for perfect synchronization
            video_stop_timestamp = synchronized_stop_time
            self._recording_stop_timestamp = video_stop_timestamp
            print(f"🕐 Video recording stop timestamp (using synchronized time): {video_stop_timestamp}")
            print(f"   ✅ Video and audio will stop at EXACT same timestamp - perfect synchronization!")
        else:
            # No synchronized stop time - use current time
            video_stop_timestamp = time.time()
            self._recording_stop_timestamp = video_stop_timestamp
            print(f"🕐 Video recording stop timestamp (no sync): {video_stop_timestamp}")
        
        # Allow merging even if recording was already stopped (for audio merge after cleanup)
        video_path = self._video_file_path
        
        # If recording is active, stop it first
        if self._recording_active:
            try:
                self._recording_active = False
                
                if self._video_writer:
                    self._video_writer.release()
                    self._video_writer = None
                    print(f"✅ Video recording stopped for session {self.session_id} at {video_stop_timestamp}")
            except Exception as e:
                print(f"⚠️ Error stopping video writer: {e}")
        
        # Debug logging
        print(f"🔍 stop_video_recording called:")
        print(f"   audio_file_path: {audio_file_path}")
        print(f"   video_path: {video_path}")
        print(f"   _recording_active: {self._recording_active}")
        
        # Auto-discover audio file if not provided
        if not audio_file_path:
            auto_audio_path = self._find_audio_file_for_session()
            if auto_audio_path:
                audio_file_path = auto_audio_path
                print(f"🔎 Auto-detected audio file for merging: {audio_file_path}")
            else:
                print(f"ℹ️ No auto-detected audio file found for session {self.session_id}")
        elif audio_file_path and not os.path.isabs(audio_file_path):
            # Convert relative paths to absolute
            audio_file_path = os.path.join(settings.MEDIA_ROOT, audio_file_path)
        
        # If no video path exists, try to find it from the session or file system
        if not video_path or not os.path.exists(video_path):
            print(f"⚠️ Video path not set or file doesn't exist: {video_path}")
            
            # First, try to find video file in file system by session_id
            # Search in both old and new folders for backward compatibility
            search_dirs = [
                os.path.join(settings.MEDIA_ROOT, 'interview_videos_raw'),
                os.path.join(settings.MEDIA_ROOT, 'interview_videos'),  # Old folder
            ]
            
            # Search for video files matching this session_id
            found_video = None
            for search_dir in search_dirs:
                if not os.path.exists(search_dir):
                    continue
                try:
                    for filename in os.listdir(search_dir):
                        # Match by session_id (UUID) - can be full UUID or partial
                        session_id_str = str(self.session_id)
                        if filename.startswith(session_id_str) and filename.endswith('.mp4'):
                            # Prefer non-converted, non-merged videos for merging
                            if '_converted' not in filename and '_with_audio' not in filename:
                                found_video = os.path.join(search_dir, filename)
                                print(f"✅ Found raw video file in filesystem: {found_video}")
                                break
                    # If no raw video found, try any video with this session_id (but not merged)
                    if not found_video:
                        for filename in os.listdir(search_dir):
                            session_id_str = str(self.session_id)
                            if filename.startswith(session_id_str) and filename.endswith('.mp4'):
                                if '_with_audio' not in filename:  # Don't use already merged videos
                                    found_video = os.path.join(search_dir, filename)
                                    print(f"✅ Found video file in filesystem (may be converted): {found_video}")
                                    break
                    if found_video:
                        break
                except Exception as e:
                    print(f"⚠️ Error searching video directory {search_dir}: {e}")
            
            # If still not found, try InterviewSession database lookup
            if not found_video:
                try:
                    from interview_app.models import InterviewSession
                    # Try to find session by session_id (UUID) or session_key
                    session = None
                    try:
                        # First try by session_id (UUID) - this is the primary key
                        session = InterviewSession.objects.get(id=self.session_id)
                        print(f"✅ Found InterviewSession by id (UUID): {session.id}")
                    except InterviewSession.DoesNotExist:
                        try:
                            # If that fails, try by session_key (hex string)
                            session = InterviewSession.objects.get(session_key=self.session_id)
                            print(f"✅ Found InterviewSession by session_key: {session.session_key}")
                        except InterviewSession.DoesNotExist:
                            # Try to find any session with matching session_id in session_key field (partial match)
                            sessions = InterviewSession.objects.filter(session_key__icontains=str(self.session_id)[:8])
                            if sessions.exists():
                                session = sessions.first()
                                print(f"✅ Found InterviewSession by partial match: {session.id}")
                            else:
                                print(f"⚠️ InterviewSession not found for session_id: {self.session_id}")
                    
                    if session:
                        if session.interview_video:
                            video_path_str = str(session.interview_video)
                            found_video = os.path.join(settings.MEDIA_ROOT, video_path_str)
                            
                            # If it's a converted video, try to find the original for merging
                            if '_converted' in video_path_str and os.path.exists(found_video):
                                # Look for original video (without _converted) for merging
                                original_name = video_path_str.replace('_converted', '')
                                original_path = os.path.join(settings.MEDIA_ROOT, original_name)
                                if os.path.exists(original_path):
                                    found_video = original_path
                                    print(f"✅ Found original video for merging (not converted): {found_video}")
                                else:
                                    print(f"⚠️ Original video not found, will use converted: {found_video}")
                            elif not os.path.exists(found_video):
                                print(f"⚠️ Video file from InterviewSession doesn't exist: {found_video}")
                                found_video = None
                            else:
                                print(f"✅ Found video file from InterviewSession: {found_video}")
                        else:
                            print(f"⚠️ No video path in InterviewSession (session found but no video)")
                            # Video might not be saved to DB yet, but exists on disk (found above)
                            if not found_video:
                                print(f"   Will search filesystem for video files...")
                    else:
                        print(f"⚠️ InterviewSession not found for session_id: {self.session_id}")
                        # Continue - we might find video in filesystem
                except Exception as e:
                    print(f"⚠️ Error looking up video from InterviewSession: {e}")
                    import traceback
                    traceback.print_exc()
            
            # If we found a video, use it
            if found_video and os.path.exists(found_video):
                video_path = found_video
                self._video_file_path = video_path
                print(f"✅ Using video file: {video_path}")
                print(f"   File size: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")
            else:
                # Last resort: search all video directories for any file with session_id
                print(f"⚠️ Video not found in standard locations, doing comprehensive search...")
                all_video_dirs = [
                    os.path.join(settings.MEDIA_ROOT, 'interview_videos_raw'),
                    os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged'),
                    os.path.join(settings.MEDIA_ROOT, 'interview_videos'),  # Old folder
                ]
                session_id_str = str(self.session_id)
                for search_dir in all_video_dirs:
                    if not os.path.exists(search_dir):
                        continue
                    try:
                        for filename in os.listdir(search_dir):
                            if session_id_str in filename and filename.endswith('.mp4'):
                                # Skip already merged videos if we're trying to merge
                                if audio_file_path and '_with_audio' in filename:
                                    continue
                                candidate_path = os.path.join(search_dir, filename)
                                if os.path.exists(candidate_path):
                                    found_video = candidate_path
                                    print(f"✅ Found video in comprehensive search: {found_video}")
                                    break
                        if found_video:
                            break
                    except Exception as e:
                        print(f"⚠️ Error searching {search_dir}: {e}")
                
                if found_video and os.path.exists(found_video):
                    video_path = found_video
                    self._video_file_path = video_path
                    print(f"✅ Using video file from comprehensive search: {video_path}")
                else:
                    print(f"❌ Could not find video file for session {self.session_id}")
                    print(f"   Searched in: {all_video_dirs}")
                    if audio_file_path:
                        print(f"   Cannot merge audio - video file doesn't exist")
                    return None
        
        # Log file details
        if audio_file_path:
            print(f"   audio_file_path exists: {os.path.exists(audio_file_path)}")
            if os.path.exists(audio_file_path):
                audio_size = os.path.getsize(audio_file_path) / 1024 / 1024
                print(f"   audio_file_size: {audio_size:.2f} MB")
        if video_path:
            print(f"   video_path exists: {os.path.exists(video_path)}")
            if os.path.exists(video_path):
                video_size = os.path.getsize(video_path) / 1024 / 1024
                print(f"   video_file_size: {video_size:.2f} MB")
        
        try:
            
            # If audio file is provided, merge video and audio using MoviePy (preferred) or FFmpeg
            if audio_file_path and os.path.exists(audio_file_path) and os.path.exists(video_path):
                print(f"🔍 Checking merge library availability...")
                print(f"   MoviePy available: {MOVIEPY_AVAILABLE}")
                print(f"   FFmpeg available: Checking...")
                
                ffmpeg_available = False
                try:
                    subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
                    ffmpeg_available = True
                    print(f"   FFmpeg available: True")
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    print(f"   FFmpeg available: False")
                
                if not MOVIEPY_AVAILABLE and not ffmpeg_available:
                    raise RuntimeError("Neither MoviePy nor FFmpeg is available for video/audio merging. Install MoviePy: pip install moviepy")
                
                try:
                    
                    # Verify and process audio file before merging
                    try:
                        from interview_app.audio_processor import verify_audio_file, process_uploaded_audio, get_audio_info
                        
                        # Verify audio file
                        if not verify_audio_file(audio_file_path):
                            print(f"⚠️ Audio file verification failed, but attempting merge anyway...")
                        
                        # Get audio info for debugging
                        audio_info = get_audio_info(audio_file_path)
                        if audio_info:
                            print(f"📊 Audio file info:")
                            print(f"   Duration: {audio_info['duration']:.2f}s")
                            print(f"   Sample rate: {audio_info['sample_rate']}Hz")
                            print(f"   Channels: {audio_info['channels']}")
                            print(f"   Codec: {audio_info['codec']}")
                        
                        # Process audio if needed (convert to WAV for better compatibility)
                        file_ext = os.path.splitext(audio_file_path)[1].lower()
                        if file_ext not in ['.wav', '.mp3', '.m4a', '.aac']:
                            print(f"🔄 Audio format ({file_ext}) may not be optimal, converting to WAV...")
                            processed_audio = process_uploaded_audio(audio_file_path, convert_to_wav=True)
                            if processed_audio and os.path.exists(processed_audio):
                                print(f"✅ Using processed audio: {processed_audio}")
                                audio_file_path = processed_audio
                            else:
                                print(f"⚠️ Audio processing failed, using original: {audio_file_path}")
                    except Exception as e:
                        print(f"⚠️ Error processing audio before merge: {e}")
                        # Continue with original audio file
                    
                    print(f"✅ FFmpeg available - using FFmpeg for merging (more reliable)")
                    
                    # CRITICAL: Convert all paths to absolute paths for accurate file access
                    # Normalize paths first to handle separators correctly
                    video_path = os.path.normpath(video_path)
                    audio_file_path = os.path.normpath(audio_file_path)
                    
                    # Convert to absolute paths if they're relative
                    if not os.path.isabs(video_path):
                        video_path = os.path.join(settings.MEDIA_ROOT, video_path)
                    video_path = os.path.normpath(video_path)
                    
                    if not os.path.isabs(audio_file_path):
                        audio_file_path = os.path.join(settings.MEDIA_ROOT, audio_file_path)
                    audio_file_path = os.path.normpath(audio_file_path)
                    
                    # Get absolute paths (resolve any symlinks or relative components)
                    video_path = os.path.abspath(video_path)
                    audio_file_path = os.path.abspath(audio_file_path)
                    
                    # Verify files exist before proceeding
                    if not os.path.exists(video_path):
                        raise FileNotFoundError(f"Video file not found: {video_path}")
                    if not os.path.exists(audio_file_path):
                        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
                    
                    # Create output path for merged video in interview_videos_merged/ folder
                    merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
                    merged_video_dir = os.path.abspath(os.path.normpath(merged_video_dir))
                    os.makedirs(merged_video_dir, exist_ok=True)
                    
                    # Get base filename (without directory)
                    video_basename = os.path.basename(video_path)
                    base_name = os.path.splitext(video_basename)[0]
                    # Remove any existing suffixes like _converted
                    if '_converted' in base_name:
                        base_name = base_name.replace('_converted', '')
                    
                    # Save merged video to interview_videos_merged/ folder
                    merged_video_filename = f"{base_name}_with_audio.mp4"
                    merged_video_path = os.path.join(merged_video_dir, merged_video_filename)
                    merged_video_path = os.path.abspath(os.path.normpath(merged_video_path))
                    
                    # Get file sizes for logging
                    video_size = os.path.getsize(video_path) / 1024 / 1024
                    audio_size = os.path.getsize(audio_file_path) / 1024 / 1024
                    print(f"📊 Merging video ({video_size:.2f} MB) with audio ({audio_size:.2f} MB)...")
                    print(f"   ✅ Absolute video path: {video_path}")
                    print(f"   ✅ Absolute audio path: {audio_file_path}")
                    print(f"   ✅ Absolute output path: {merged_video_path}")
                    print(f"   ✅ Video exists: {os.path.exists(video_path)}")
                    print(f"   ✅ Audio exists: {os.path.exists(audio_file_path)}")
                    print(f"   ✅ Output directory exists: {os.path.exists(merged_video_dir)}")
                    
                    # Get video start timestamp (prefer from first frame, fallback to parameter or attribute)
                    video_ts = None
                    if hasattr(self, '_recording_start_timestamp') and self._recording_start_timestamp:
                        video_ts = self._recording_start_timestamp
                        print(f"🕐 Video start timestamp (from first frame): {video_ts}")
                    elif video_start_timestamp:
                        video_ts = video_start_timestamp
                        print(f"🕐 Video start timestamp (from parameter): {video_ts}")
                    
                    # Call FFmpeg merge function
                    print(f"🔄 Calling merge_video_audio_ffmpeg with:")
                    print(f"   video_path: {video_path}")
                    print(f"   audio_file_path: {audio_file_path}")
                    print(f"   output_path: {merged_video_path}")
                    print(f"   video_start_timestamp: {video_ts}")
                    print(f"   audio_start_timestamp: {audio_start_timestamp}")
                    
                    # Use MoviePy for merging (preferred)
                    if MOVIEPY_AVAILABLE:
                        merge_success = merge_video_audio_moviepy(
                            video_path=video_path,
                            audio_file_path=audio_file_path,
                            output_path=merged_video_path,
                            video_start_timestamp=video_ts,
                            audio_start_timestamp=audio_start_timestamp,
                            video_duration=None  # Let MoviePy calculate from video
                        )
                    else:
                        # Fallback to FFmpeg if MoviePy not available
                        merge_success = merge_video_audio_ffmpeg(
                            video_path=video_path,
                            audio_file_path=audio_file_path,
                            output_path=merged_video_path,
                            video_start_timestamp=video_ts,
                            audio_start_timestamp=audio_start_timestamp,
                            video_duration=None  # Let FFmpeg calculate from video
                        )
                    
                    # CRITICAL: Verify merged file exists and has content
                    if not merge_success:
                        merge_lib_name = "MoviePy" if MOVIEPY_AVAILABLE else "FFmpeg"
                        print(f"❌ {merge_lib_name} merge function returned False!")
                        raise Exception(f"{merge_lib_name} merge function returned False")
                    
                    if not os.path.exists(merged_video_path):
                        print(f"❌ Merged video file does not exist at: {merged_video_path}")
                        raise FileNotFoundError(f"Merged video file not found: {merged_video_path}")
                    
                    merged_size = os.path.getsize(merged_video_path)
                    if merged_size == 0:
                        print(f"❌ Merged video file is empty (0 bytes): {merged_video_path}")
                        raise ValueError(f"Merged video file is empty: {merged_video_path}")
                    
                    merged_size_mb = merged_size / 1024 / 1024
                    print(f"✅ Merge verification passed!")
                    print(f"   Merged file exists: {os.path.exists(merged_video_path)}")
                    print(f"   Merged file size: {merged_size_mb:.2f} MB ({merged_size} bytes)")
                    print(f"   Merged file path: {merged_video_path}")
                    
                    # Remove original video without audio
                    try:
                        if os.path.exists(video_path) and video_path != merged_video_path:
                            os.remove(video_path)
                            print(f"🗑️ Removed original video without audio: {video_path}")
                        else:
                            print(f"ℹ️ Original video already removed or is same as merged: {video_path}")
                    except Exception as e:
                        print(f"⚠️ Could not remove original video: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    video_path = merged_video_path
                    self._video_file_path = merged_video_path
                    merge_lib_name = "MoviePy" if MOVIEPY_AVAILABLE else "FFmpeg"
                    print(f"✅ Video and audio merged successfully using {merge_lib_name}!")
                    print(f"   Final video path: {merged_video_path}")
                    print(f"   Final video size: {merged_size_mb:.2f} MB")
                    print(f"   Frame rate: 5 fps (preserved from recording)")
                    print(f"   ✅ ONLY merged video exists - original removed")
                        
                except ImportError as e:
                    print(f"❌ Merge library not available: {e}")
                    print(f"⚠️ Video saved without audio - MoviePy or FFmpeg is required for audio merging")
                    print(f"⚠️ Please install MoviePy with: pip install moviepy")
                except Exception as e:
                    print(f"❌ Error merging audio with video: {e}")
                    import traceback
                    traceback.print_exc()
                    print(f"⚠️ CRITICAL ERROR: Merge failed - video will be saved WITHOUT audio")
                    print(f"⚠️ This is a critical failure - the video should NOT be saved without audio")
                    # Don't save the video if merge failed - raise exception to prevent saving
                    raise Exception(f"Cannot save video without audio - merge failed: {str(e)}")
            else:
                # No audio file, but still try to convert to H.264 for browser compatibility
                if not audio_file_path:
                    print(f"⚠️ No audio_file_path provided - video will be saved without audio")
                elif not os.path.exists(audio_file_path):
                    print(f"⚠️ Audio file does not exist: {audio_file_path}")
                    print(f"   Current working directory: {os.getcwd()}")
                    print(f"   Checking if it's a relative path...")
                    # Try to find audio file in common locations
                    possible_locations = [
                        audio_file_path,
                        os.path.join(os.getcwd(), audio_file_path),
                        os.path.join(settings.MEDIA_ROOT, audio_file_path) if 'settings' in globals() else None,
                    ]
                    found_audio = None
                    for loc in possible_locations:
                        if loc and os.path.exists(loc):
                            print(f"   ✅ Found audio at: {loc}")
                            found_audio = loc
                            break
                    
                    # If we found the audio file, manually trigger merge
                    if found_audio and os.path.exists(video_path):
                        print(f"   🔄 Attempting merge with found audio path: {found_audio}")
                        # Normalize paths
                        video_path = os.path.normpath(video_path)
                        found_audio = os.path.normpath(found_audio)
                        
                        # Re-check the condition with found audio path
                        audio_file_path = found_audio
                        # Use PyAV to merge video and audio
                        try:
                            if not PYAV_AVAILABLE:
                                raise ImportError("PyAV is required for video/audio merging. Install with: pip install av")
                            
                            # Save merged video to interview_videos_merged/ folder
                            merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
                            os.makedirs(merged_video_dir, exist_ok=True)
                            video_basename = os.path.basename(video_path)
                            base_name = os.path.splitext(video_basename)[0]
                            if '_converted' in base_name:
                                base_name = base_name.replace('_converted', '')
                            merged_video_filename = f"{base_name}_with_audio.mp4"
                            merged_video_path = os.path.join(merged_video_dir, merged_video_filename)
                            merged_video_path = os.path.normpath(merged_video_path)
                            video_size = os.path.getsize(video_path) / 1024 / 1024
                            audio_size = os.path.getsize(found_audio) / 1024 / 1024
                            print(f"📊 Merging video ({video_size:.2f} MB) with audio ({audio_size:.2f} MB) using PyAV...")
                            
                            # Get video start timestamp
                            video_ts = None
                            if hasattr(self, '_recording_start_timestamp') and self._recording_start_timestamp:
                                video_ts = self._recording_start_timestamp
                            elif video_start_timestamp:
                                video_ts = video_start_timestamp
                            
                            # Use MoviePy for merging (preferred)
                            if MOVIEPY_AVAILABLE:
                                merge_success = merge_video_audio_moviepy(
                                    video_path=video_path,
                                    audio_file_path=found_audio,
                                    output_path=merged_video_path,
                                    video_start_timestamp=video_ts,
                                    audio_start_timestamp=audio_start_timestamp,
                                    video_duration=None
                                )
                                merge_lib = "MoviePy"
                            else:
                                # Fallback to FFmpeg
                                merge_success = merge_video_audio_ffmpeg(
                                    video_path=video_path,
                                    audio_file_path=found_audio,
                                    output_path=merged_video_path,
                                    video_start_timestamp=video_ts,
                                    audio_start_timestamp=audio_start_timestamp,
                                    video_duration=None
                                )
                                merge_lib = "FFmpeg"
                            
                            if merge_success and os.path.exists(merged_video_path):
                                merged_size = os.path.getsize(merged_video_path) / 1024 / 1024
                                if merged_size > 0:
                                    video_path = merged_video_path
                                    self._video_file_path = merged_video_path
                                    print(f"✅ Video and audio merged successfully using {merge_lib}!")
                                    print(f"   Output: {merged_video_path} ({merged_size:.2f} MB)")
                                else:
                                    print(f"❌ Merged video file is empty!")
                            else:
                                print(f"❌ {merge_lib} merge failed!")
                                raise Exception(f"{merge_lib} merge failed")
                        except Exception as e:
                            print(f"❌ Error in PyAV merge attempt: {e}")
                            import traceback
                            traceback.print_exc()
                            # Don't save video if merge failed
                            raise Exception(f"Cannot save video - PyAV merge failed: {str(e)}")
                elif not os.path.exists(video_path):
                    print(f"⚠️ Video file does not exist: {video_path}")
                    # Try to find video in raw folder
                    raw_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_raw')
                    if os.path.exists(raw_video_dir):
                        video_basename = os.path.basename(video_path) if video_path else None
                        if video_basename:
                            alt_path = os.path.join(raw_video_dir, video_basename)
                            if os.path.exists(alt_path):
                                video_path = alt_path
                                print(f"✅ Found video in raw folder: {video_path}")
                
                if os.path.exists(video_path):
                    try:
                        # Use PyAV to convert video
                        if PYAV_AVAILABLE:
                            converted_video_path = self.ensure_browser_compatible_video(video_path)
                            if converted_video_path:
                                video_path = converted_video_path
                        else:
                            print(f"⚠️ PyAV not available - skipping video conversion")
                    except Exception as e:
                        print(f"⚠️ Error converting video: {e}")
                        print(f"⚠️ Using original video: {video_path}")
            
            # Return the relative path for saving to InterviewSession
            # CRITICAL: Only return merged videos (with _with_audio suffix)
            if video_path and os.path.exists(video_path):
                # Normalize path
                video_path = os.path.normpath(video_path)
                
                # Verify file is not empty
                file_size = os.path.getsize(video_path)
                if file_size == 0:
                    print(f"❌ Video file is empty: {video_path}")
                    return None
                
                # CRITICAL CHECK: Only allow merged videos to be saved
                has_audio = '_with_audio' in video_path or 'interview_videos_merged' in video_path
                if not has_audio:
                    print(f"❌ CRITICAL ERROR: Attempting to return unmerged video path!")
                    print(f"   Path: {video_path}")
                    print(f"   This should NEVER happen - merge must succeed before returning path")
                    # Try to find merged version in interview_videos_merged/ folder
                    merged_video_dir = os.path.join(settings.MEDIA_ROOT, 'interview_videos_merged')
                    video_basename = os.path.basename(video_path)
                    base_name = os.path.splitext(video_basename)[0]
                    if '_converted' in base_name:
                        base_name = base_name.replace('_converted', '')
                    merged_filename = f"{base_name}_with_audio.mp4"
                    merged_path = os.path.join(merged_video_dir, merged_filename)
                    merged_path = os.path.normpath(merged_path)
                    if os.path.exists(merged_path):
                        print(f"   ✅ Found merged version, using: {merged_path}")
                        video_path = merged_path
                        has_audio = True
                        file_size = os.path.getsize(video_path)
                    else:
                        print(f"   ❌ Merged version not found: {merged_path}")
                        print(f"   ❌ REFUSING to return unmerged video path - raising exception")
                        raise Exception(f"Cannot return unmerged video path. Merge must succeed. Expected merged file at: {merged_path}")
                
                audio_status = "with merged audio"
                
                # Get relative path from MEDIA_ROOT
                relative_path = os.path.relpath(video_path, settings.MEDIA_ROOT)
                # Convert to forward slashes for Django
                relative_path = relative_path.replace('\\', '/')
                print(f"✅ Video file saved {audio_status}: {relative_path} ({file_size / 1024 / 1024:.2f} MB)")
                print(f"   ✅ Verified: Path contains '_with_audio' or is in interview_videos_merged/ - merge successful")
                return relative_path
            else:
                print(f"❌ Video file not found at {video_path}")
                return None
        except Exception as e:
            print(f"❌ Error stopping video recording for session {self.session_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _capture_and_detect_loop(self):
        """Continuously capture frames, update latest frame, and run simple face-based warnings."""
        # Load Haar cascade once (fallback if YOLO not available)
        face_cascade = None
        if CV2_AVAILABLE and cv2:
            try:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                face_cascade = cv2.CascadeClassifier(cascade_path)
            except Exception as e:
                print(f"⚠️ Failed to load Haar cascade: {e}")
                face_cascade = None
        else:
            print("⚠️ OpenCV not available - Haar cascade face detection disabled")
        
        import time
        import time as _t
        import threading
        import queue
        
        last_gray = None
        last_motion_ts = _t.time()
        LOW_MOTION_WINDOW_SEC = 8.0
        MOTION_LOW_THRESH = 2.5  # mean absolute diff threshold (tune if needed)
        
        # Background thread for saving snapshots and logging to DB (non-blocking)
        warning_queue = queue.Queue(maxsize=10)  # Limit queue size
        
        def _background_warning_logger():
            """Background thread to save snapshots and log to database without blocking detection."""
            while self._running:
                try:
                    # Get warning data from queue (with short timeout to prevent blocking)
                    warning_data = warning_queue.get(timeout=0.5)
                    if warning_data is None:
                        break
                    warning_type, frame_copy, snapshot_filename = warning_data
                    
                    # Save snapshot only if proctoring is active (technical interview started)
                    # Skip snapshot saving during identity verification
                    if self._proctoring_active and frame_copy is not None and snapshot_filename:
                        if not CV2_AVAILABLE or cv2 is None:
                            print("⚠️ OpenCV not available - cannot save snapshot")
                        else:
                            try:
                                img_dir = os.path.join(settings.MEDIA_ROOT, "proctoring_snaps")
                                os.makedirs(img_dir, exist_ok=True)
                                img_path = os.path.join(img_dir, snapshot_filename)
                                cv2.imwrite(img_path, frame_copy)
                                print(f"📸 Snapshot saved: {snapshot_filename}")
                            except Exception as e:
                                print(f"[Proctoring] Failed to save snapshot: {e}")
                    elif not self._proctoring_active:
                        # Proctoring not active - skip snapshot saving
                        print(f"⚠️ Skipping snapshot save - proctoring not active yet (still in identity verification)")
                    
                    # Log to database (with timeout to prevent blocking)
                    # Only log warnings if proctoring is active (technical interview started)
                    if self._proctoring_active:
                        try:
                            from .models import InterviewSession, WarningLog
                            from django.db import transaction
                            from django.core.files.base import ContentFile
                            import os
                            # Use select_for_update with nowait to prevent blocking
                            try:
                                session = InterviewSession.objects.select_for_update(nowait=True).get(id=self.session_id)
                                with transaction.atomic():
                                    # Save snapshot image to database
                                    snapshot_image_field = None
                                    if img_path and os.path.exists(img_path):
                                        try:
                                            with open(img_path, 'rb') as f:
                                                image_file = ContentFile(f.read(), name=snapshot_filename)
                                                snapshot_image_field = image_file
                                        except Exception as img_error:
                                            print(f"⚠️ Error reading snapshot image for DB: {img_error}")
                                    
                                    warning_log = WarningLog(
                                        session=session,
                                        warning_type=warning_type,
                                        snapshot=snapshot_filename
                                    )
                                    if snapshot_image_field:
                                        warning_log.snapshot_image = snapshot_image_field
                                    warning_log.save()
                                    print(f"✅ Warning logged to database with snapshot image: {snapshot_filename}")
                            except Exception as db_error:
                                # Skip database logging if it would block - snapshot is still saved
                                # Only print if it's not the expected "no column named snapshot" error
                                if 'snapshot' not in str(db_error).lower():
                                    print(f"⚠️ Database logging error (non-critical): {db_error}")
                        except Exception as e:
                            # Silently continue - snapshot was saved, DB logging is optional
                            print(f"⚠️ Error in database logging (non-critical): {e}")
                    else:
                        # Proctoring not active yet (still in identity verification), don't save warnings
                        print(f"⚠️ Warning detected but proctoring not active yet - skipping snapshot save")
                    
                    warning_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[Proctoring] Background logger error: {e}")
        
        logger_thread = threading.Thread(target=_background_warning_logger, daemon=True)
        logger_thread.start()
        self._warning_logger_queue = warning_queue
        
        # YOLO detection frequency - run every ~1.5 seconds to significantly reduce CPU usage
        last_yolo_time = _t.time()
        YOLO_INTERVAL = 1.5  # Run YOLO every 1.5 seconds (reduced from 0.5s for better performance)
        
        # Add debouncing for absence warning - require continuous absence for 3 seconds
        absence_start_time = None
        ABSENCE_THRESHOLD_SEC = 3.0  # Must be absent for 3 seconds before warning
        
        while self._running:
            try:
                # Check if video is still opened, try to reopen if needed (but don't spam logs)
                if not self.video.isOpened():
                    # Only print warning every 30 seconds to reduce log spam
                    now_check = _t.time()
                    if not hasattr(self, '_last_reopen_attempt_time'):
                        self._last_reopen_attempt_time = 0
                    if now_check - self._last_reopen_attempt_time > 30:
                        print(f"⚠️ Camera closed for session {str(self.session_id)[:8]}, attempting to reopen...")
                        self._last_reopen_attempt_time = now_check
                    
                    try:
                        if hasattr(self.video, 'cap') and self.video.cap:
                            self.video.release()
                        time.sleep(0.5)  # Brief pause before reopening
                        self.video = _VideoCapture()
                        if not self.video.isOpened():
                            time.sleep(2.0)  # Wait longer before retry
                            continue
                        else:
                            print(f"✅ Camera successfully reopened for session {str(self.session_id)[:8]}")
                            # Warm up the reopened camera
                            for i in range(5):
                                ret_warm, _ = self.video.read()
                                if ret_warm:
                                    break
                                time.sleep(0.1)
                            # Clear the frame buffer when camera reopens
                            if self._frame_lock is not None:
                                try:
                                    if self._frame_lock.acquire(blocking=False):
                                        try:
                                            self._latest_frame = None
                                        finally:
                                            self._frame_lock.release()
                                except:
                                    pass
                    except Exception as e:
                        if now_check - self._last_reopen_attempt_time <= 30:
                            # Only log if we haven't logged recently
                            pass
                        time.sleep(2.0)
                        continue
                
                # Try reading frame with retry logic
                ret, frame = None, None
                for attempt in range(3):  # Try up to 3 times
                    ret, frame = self.video.read()
                    if ret and frame is not None and frame.size > 0:
                        break
                    if attempt < 2:  # Don't sleep on last attempt
                        time.sleep(0.05)  # Small delay between retries
                
                if not ret or frame is None or frame.size == 0:
                    # Camera read failed - try to reopen if it's been closed
                    if not self.video.isOpened():
                        try:
                            if hasattr(self.video, 'cap') and self.video.cap:
                                self.video.release()
                            self.video = _VideoCapture()
                            if self.video.isOpened():
                                print(f"✅ Camera successfully reopened for session {str(self.session_id)[:8]}")
                                # Warm up the reopened camera
                                for i in range(3):
                                    ret, _ = self.video.read()
                                    if ret:
                                        break
                                    time.sleep(0.1)
                        except Exception as e:
                            pass
                    time.sleep(0.1)  # Increased sleep to reduce CPU when camera fails
                    continue
                
                # Record frame to video file (parallel with YOLO detection)
                if self._recording_active and self._video_writer is not None:
                    try:
                        current_time = _t.time()
                        
                        # CRITICAL: Wait for synchronized start time if specified
                        # This ensures video starts at the EXACT same moment as audio
                        if hasattr(self, '_synchronized_start_time') and self._synchronized_start_time:
                            if current_time < self._synchronized_start_time:
                                # Not time yet - sleep for precise timing (more accurate than continue)
                                wait_time = self._synchronized_start_time - current_time
                                if wait_time > 0.001:  # Only sleep if wait time is significant (>1ms)
                                    _t.sleep(min(wait_time, 0.1))  # Sleep up to 100ms at a time
                                continue
                            elif not self._first_frame_written:
                                # First frame at synchronized time - record EXACT timestamp
                                # CRITICAL: Use synchronized_start_time as authoritative timestamp (not current_time)
                                # This ensures video and audio use the SAME timestamp for perfect synchronization
                                self._first_frame_written = True
                                # ALWAYS use synchronized_start_time as authoritative timestamp
                                self._recording_start_timestamp = self._synchronized_start_time
                                print(f"🕐 FIRST FRAME WRITTEN at synchronized time: {self._recording_start_timestamp}")
                                print(f"   ✅ Using synchronized_start_time as authoritative timestamp")
                                print(f"   ✅ Video and audio will use SAME timestamp - perfect synchronization!")
                                print(f"   ⏱️ Current time: {current_time}, Difference: {(current_time - self._synchronized_start_time) * 1000:.2f}ms")
                        elif not self._first_frame_written:
                            # No synchronized time - record timestamp when first frame is written
                            self._first_frame_written = True
                            # Try to use synchronized_start_time if available
                            if hasattr(self, '_synchronized_start_time') and self._synchronized_start_time:
                                self._recording_start_timestamp = self._synchronized_start_time
                                print(f"🕐 FIRST FRAME WRITTEN - Using synchronized_start_time: {self._recording_start_timestamp}")
                            else:
                                self._recording_start_timestamp = current_time
                                print(f"🕐 FIRST FRAME WRITTEN - Video recording started at: {self._recording_start_timestamp}")
                        
                        # Resize frame to match recording dimensions if needed
                        if not CV2_AVAILABLE or cv2 is None:
                            print("⚠️ OpenCV not available - cannot resize frame")
                            frame_resized = frame
                        elif frame.shape[1] != self._frame_width or frame.shape[0] != self._frame_height:
                            frame_resized = cv2.resize(frame, (self._frame_width, self._frame_height))
                        else:
                            frame_resized = frame
                        
                        if self._last_frame_time is not None:
                            self._frame_timestamps.append(current_time - self._last_frame_time)
                        self._last_frame_time = current_time
                        
                        self._video_writer.write(frame_resized)
                    except Exception as e:
                        print(f"⚠️ Error writing frame to video: {e}")
                
                # Save latest frame (only update if lock is available quickly)
                if self._frame_lock is not None:
                    try:
                        # Use non-blocking lock acquisition to prevent blocking
                        if self._frame_lock.acquire(blocking=False):
                            try:
                                self._latest_frame = frame.copy()
                            finally:
                                self._frame_lock.release()
                        else:
                            # Lock is held, skip frame update this cycle (reduces blocking)
                            pass
                    except Exception:
                        pass
                
                # Run detections - YOLO only every 0.5s to reduce CPU usage
                has_person = False
                multiple_people = False
                phone_detected = False
                
                now_ts = _t.time()
                should_run_yolo = (now_ts - last_yolo_time) >= YOLO_INTERVAL

                # Only run YOLO if proctoring is active (technical interview has started)
                # Skip YOLO during identity verification
                if should_run_yolo and self._yolo is not None and self._proctoring_active:
                    try:
                        # Run YOLO with lower confidence for sensitivity; small imgsz for speed
                        results = self._yolo.predict(source=frame, imgsz=480, conf=0.35, iou=0.45, verbose=False)
                        if results and len(results) > 0:
                            r0 = results[0]
                            # Map class indices to names
                            names = r0.names if hasattr(r0, 'names') else getattr(self._yolo, 'names', {})
                            cls = r0.boxes.cls.cpu().numpy().tolist() if hasattr(r0, 'boxes') and r0.boxes is not None else []
                            labels = [str(names.get(int(c), str(int(c)))) for c in cls]
                            person_count = sum(1 for l in labels if l.lower() == 'person')
                            phone_count = sum(1 for l in labels if 'phone' in l.lower())
                            has_person = person_count >= 1
                            multiple_people = person_count >= 2
                            phone_detected = phone_count >= 1
                        last_yolo_time = now_ts
                    except Exception as e:
                        # Fall back to Haar if YOLO fails mid-run
                        print(f"⚠️ YOLO detection error; falling back to Haar: {e}")
                        self._yolo = None

                if self._yolo is None or not should_run_yolo:
                    # Haar-based fallback (always runs, or when YOLO skipped)
                    faces = []
                    try:
                        if face_cascade is not None:
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                    except Exception:
                        faces = []
                    face_count = len(faces) if faces is not None else 0
                    # Only update if YOLO didn't run (to preserve YOLO results)
                    if self._yolo is None or not should_run_yolo:
                        has_person = face_count >= 1
                        multiple_people = face_count >= 2
                    # phone_detected remains False in Haar fallback

                # Update warnings from detections with logging - ensure state is always fresh
                prev_no_person = self._last_warning_state.get("no_person", False)
                prev_warning_active = self._last_warning_state.get("no_person_warning_active", False)
                prev_multiple = self._last_warning_state.get("multiple_people", False)
                prev_phone = self._last_warning_state.get("phone_detected", False)
                
                # Debounced absence detection - require continuous absence for threshold duration
                now_abs = _t.time()
                if not has_person:
                    # Person is absent - start/continue tracking absence duration
                    if absence_start_time is None:
                        absence_start_time = now_abs
                    absence_duration = now_abs - absence_start_time
                    
                    # Only activate warning if absent for threshold duration
                    if absence_duration >= ABSENCE_THRESHOLD_SEC:
                        self._last_warning_state["no_person"] = True
                        self._last_warning_state["no_person_warning_active"] = True
                    else:
                        # Still within threshold - don't activate warning yet
                        self._last_warning_state["no_person"] = False
                        self._last_warning_state["no_person_warning_active"] = False
                else:
                    # Person is present - reset absence tracking immediately
                    absence_start_time = None
                    self._last_warning_state["no_person"] = False
                    self._last_warning_state["no_person_warning_active"] = False
                
                # Update other warning states
                self._last_warning_state["multiple_people"] = multiple_people
                self._last_warning_state["phone_detected"] = phone_detected
                
                # Clear warnings when conditions are no longer met
                if has_person and prev_warning_active:
                    # Person returned - clear no_person warnings
                    self._last_warning_logged.pop('no_person', None)
                if not multiple_people and prev_multiple:
                    # Multiple people cleared
                    self._last_warning_state["multiple_people"] = False
                if not phone_detected and prev_phone:
                    # Phone cleared
                    self._last_warning_state["phone_detected"] = False
                
                # Log warnings to database with snapshots when they occur (non-blocking via queue)
                self._log_warning_with_snapshot_async('multiple_people', multiple_people, prev_multiple, frame)
                self._log_warning_with_snapshot_async('phone_detected', phone_detected, prev_phone, frame)
                
                # Handle no_person warning - only log when warning becomes active (not just when person absent)
                current_warning_active = self._last_warning_state.get("no_person_warning_active", False)
                if current_warning_active and not prev_warning_active:
                    # Warning just became active - log it
                    self._log_warning_with_snapshot_async('no_person', True, False, frame, rate_limit_seconds=15)
                elif has_person and prev_warning_active:
                    # Person returned - reset rate limit when person returns
                    self._last_warning_logged.pop('no_person', None)

                # Motion-based detection (low concentration only)
                try:
                    if not CV2_AVAILABLE or cv2 is None:
                        # Skip motion detection if cv2 not available
                        last_gray = None
                        continue
                    gray_small = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray_small = cv2.resize(gray_small, (160, 120))
                    if last_gray is not None:
                        diff = cv2.absdiff(gray_small, last_gray)
                        motion_score = float(diff.mean())
                        now_ts = _t.time()
                        
                        # Low concentration detection
                        prev_low_concentration = self._last_warning_state.get("low_concentration", False)
                        if motion_score > MOTION_LOW_THRESH:
                            last_motion_ts = now_ts
                            # Clear low concentration when motion detected
                            if prev_low_concentration:
                                self._last_warning_state["low_concentration"] = False
                        # Low concentration if no meaningful motion for a window and a person present
                        low_concentration = has_person and (now_ts - last_motion_ts) >= LOW_MOTION_WINDOW_SEC
                        self._last_warning_state["low_concentration"] = low_concentration
                        
                        # Log low concentration warning with snapshot when first detected
                        if low_concentration and not prev_low_concentration:
                            self._log_warning_with_snapshot_async('low_concentration', True, False, frame)
                        # Clear when person moves
                        elif not low_concentration and prev_low_concentration:
                            self._last_warning_state["low_concentration"] = False
                    last_gray = gray_small
                except Exception as e:
                    # Motion detection errors are not critical - continue silently
                    pass
                # Sleep to cap CPU usage - increased to reduce load
                time.sleep(0.2)  # Increased from 0.1s to 0.2s to cut CPU usage in half
            except Exception as e:
                print(f"⚠️ Detection loop error: {e}")
                time.sleep(0.1)

    def get_frame(self) -> bytes:
        """Get a frame as JPEG bytes."""
        try:
            # Check if video is opened - if not, return fallback (don't try to reopen here as detection loop handles it)
            if not self.video.isOpened():
                return self._create_fallback_frame()
            
            frame = None
            # Try to get frame from detection loop buffer first (most efficient)
            # Use non-blocking lock to prevent get_frame() from blocking
            if self._frame_lock is not None:
                try:
                    if self._frame_lock.acquire(blocking=False):
                        try:
                            if self._latest_frame is not None:
                                frame = self._latest_frame.copy()
                        finally:
                            self._frame_lock.release()
                except Exception as e:
                    pass
            
            # If no buffered frame, read directly from camera (fallback)
            if frame is None:
                try:
                    # Try reading with retries
                    ret, tmp = None, None
                    import time as time_module
                    for attempt in range(3):
                        ret, tmp = self.video.read()
                        if ret and tmp is not None and tmp.size > 0:
                            break
                        if attempt < 2:
                            time_module.sleep(0.05)
                    
                    if ret and tmp is not None and tmp.size > 0:
                        frame = tmp
                        # Also update the buffer if we got a frame (non-blocking)
                        if self._frame_lock is not None:
                            try:
                                if self._frame_lock.acquire(blocking=False):
                                    try:
                                        self._latest_frame = frame.copy()
                                    finally:
                                        self._frame_lock.release()
                            except:
                                pass
                except Exception as e:
                    # Silently continue - fallback frame will be returned
                    pass
            
            # If we have a valid frame, add overlays and encode
            if frame is not None and frame.size > 0:
                try:
                    # Add overlays
                    import time as time_module
                    timestamp = time_module.strftime("%H:%M:%S")
                    cv2.putText(frame, timestamp, (20, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    session_text = f"Session: {str(self.session_id)[:8]}"
                    cv2.putText(frame, session_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Add "LIVE" indicator to show feed is active
                    cv2.rectangle(frame, (frame.shape[1] - 120, 10), (frame.shape[1] - 10, 40), (0, 255, 0), -1)
                    cv2.putText(frame, "LIVE", (frame.shape[1] - 110, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                    
                    # Encode as JPEG with lower quality for faster transmission
                    ok, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if ok and buf is not None and len(buf) > 0:
                        return buf.tobytes()
                except Exception as e:
                    print(f"[Camera] Error encoding frame: {e}")
                    pass
            
            # Fallback if all else fails
            return self._create_fallback_frame()
        except Exception as e:
            print(f"[Camera] Error in get_frame: {e}")
            return self._create_fallback_frame()

    def _create_fallback_frame(self) -> bytes:
        """Create a fallback frame when camera is not available."""
        # Only print warning every 10 seconds to reduce log spam
        now = time.time()
        if now - self._fallback_print_time > 10:
            print(f"⚠️ Camera not available for session {str(self.session_id)[:8]}... using fallback frames")
            self._fallback_print_time = now
        
        # Cache fallback frame for 1 second to avoid regenerating
        if self._cached_fallback_frame is None or (now - self._fallback_frame_cache_time) > 1.0:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add session info with green background box
            text = f"Session: {str(self.session_id)[:8]}"
            cv2.rectangle(frame, (10, 20), (630, 60), (0, 128, 0), -1)
            cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Add status message with background
            if not self.video.isOpened():
                status_text = "Camera Not Available"
                text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                cv2.rectangle(frame, (10, 70), (20 + text_size[0], 110), (0, 0, 128), -1)
                cv2.putText(frame, status_text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                status_text = "Camera Loading..."
                text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                cv2.rectangle(frame, (10, 70), (20 + text_size[0], 110), (128, 128, 128), -1)
                cv2.putText(frame, status_text, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Add timestamp with background
            timestamp = time.strftime("%H:%M:%S")
            text_size = cv2.getTextSize(timestamp, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(frame, (10, frame.shape[0] - 35), (20 + text_size[0], frame.shape[0] - 5), (64, 64, 64), -1)
            cv2.putText(frame, timestamp, (20, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add a pulsing indicator in the corner to show stream is alive
            import time as time_module
            pulse = int(time_module.time() * 2) % 2
            cv2.circle(frame, (620, 30), 10, (0, 255, 0) if pulse else (0, 128, 0), -1)
            
            ok, buf = cv2.imencode('.jpg', frame)
            if ok and buf is not None and len(buf) > 0:
                self._cached_fallback_frame = buf.tobytes()
                self._fallback_frame_cache_time = now
                return self._cached_fallback_frame
            else:
                # Last resort: return a minimal valid JPEG
                return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x01\xe0\x02\x80\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        else:
            # Return cached fallback frame
            return self._cached_fallback_frame

    def _log_warning_with_snapshot_async(self, warning_type, current_state, prev_state, frame, rate_limit_seconds=2):
        """Log warning to database with snapshot capture (non-blocking via background thread).
        
        Args:
            warning_type: Type of warning (e.g., 'multiple_people', 'phone_detected')
            current_state: Current warning state (True/False)
            prev_state: Previous warning state (True/False)
            frame: Current camera frame (numpy array)
            rate_limit_seconds: Minimum seconds between logs for same warning (default 2)
        """
        # Only log warnings if proctoring is active (technical interview has started)
        # Skip warnings during identity verification
        if not self._proctoring_active:
            return
        
        # Only log when warning first becomes active (transitions from False to True)
        if not current_state or prev_state:
            return
        
        # Rate limiting to avoid spam - increased for better performance
        now = time.time()
        last_logged = self._last_warning_logged.get(warning_type, 0)
        # Increased default rate limit to 10 seconds for most warnings, 15 seconds for no_person
        effective_rate_limit = 15 if warning_type == 'no_person' else (10 if rate_limit_seconds < 10 else rate_limit_seconds)
        if now - last_logged < effective_rate_limit:
            return
        
        # Update warning count and timestamp immediately (non-blocking)
        self._warning_counts[warning_type] = self._warning_counts.get(warning_type, 0) + 1
        self._last_warning_logged[warning_type] = now
        
        # Queue warning for background thread (non-blocking I/O)
        try:
            if hasattr(self, '_warning_logger_queue'):
                snapshot_filename = None
                if frame is not None:
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                    session_id_str = str(self.session_id)
                    snapshot_filename = f"{session_id_str}_{warning_type}_{ts}.jpg"
                
                # Copy frame to avoid reference issues
                frame_copy = frame.copy() if frame is not None else None
                
                # Try to put in queue (non-blocking if queue is full)
                try:
                    self._warning_logger_queue.put_nowait((warning_type, frame_copy, snapshot_filename))
                except:
                    # Queue full - skip this warning to avoid blocking
                    pass
        except Exception as e:
            print(f"[Proctoring] Failed to queue warning {warning_type}: {e}")

    def get_latest_warnings(self) -> dict:
        """Get current warning states and include warning counts."""
        warnings = self._last_warning_state.copy()
        # Ensure all expected keys exist with default False
        expected_keys = [
            'no_person_warning_active', 'multiple_people', 'phone_detected',
            'no_person', 'low_concentration', 'tab_switched',
            'excessive_noise', 'multiple_speakers'
        ]
        for key in expected_keys:
            if key not in warnings:
                warnings[key] = False
        # Add warning counts as metadata (can be used for display)
        warnings['_counts'] = self._warning_counts.copy()
        return warnings
    
    def get_warning_counts(self) -> dict:
        """Get warning counts for the session."""
        return self._warning_counts.copy()

    def set_tab_switch_status(self, hidden: bool) -> None:
        """Set tab switch status and log warning with snapshot if tab was switched."""
        prev_tab_switched = self._last_warning_state.get("tab_switched", False)
        self._last_warning_state["tab_switched"] = bool(hidden)
        
        # Log warning when tab is switched (becomes True)
        if hidden and not prev_tab_switched:
            # Get latest frame for snapshot (non-blocking)
            frame = None
            if self._frame_lock is not None:
                try:
                    if self._frame_lock.acquire(blocking=False):
                        try:
                            if self._latest_frame is not None:
                                frame = self._latest_frame.copy()
                        finally:
                            self._frame_lock.release()
                except:
                    pass
            
            if frame is not None:
                self._log_warning_with_snapshot_async('tab_switched', True, False, frame, rate_limit_seconds=3)

    def cleanup(self):
        """Clean up camera resources and return video path if recording was active."""
        print(f"🧹 Cleaning up simple camera for session {self.session_id}")
        video_path = None
        try:
            self._running = False
            # Stop video recording before cleanup
            video_path = self.stop_video_recording()
            
            # Join thread if exists
            t = getattr(self, '_detector_thread', None)
            if t and t.is_alive():
                t.join(timeout=1.5)
        except Exception as e:
            print(f"⚠️ Error during camera cleanup: {e}")
        if self.video:
            self.video.release()
        print(f"✅ Simple camera cleanup completed for session {self.session_id}")
        return video_path

    def _find_audio_file_for_session(self):
        """Attempt to locate the most recent audio file for this session."""
        try:
            from interview_app.models import InterviewSession
            session = InterviewSession.objects.get(id=self.session_id)
            session_key = session.session_key
        except Exception as e:
            print(f"⚠️ Could not resolve session key for audio lookup: {e}")
            session_key = None
        
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'interview_audio')
        if not os.path.isdir(audio_dir):
            return None
        
        prefixes = []
        if session_key:
            prefixes.append(session_key)
        prefixes.append(str(self.session_id))
        
        latest_file = None


class PyAudioAudioRecorder:
    """
    Backend audio recorder using PyAudio.
    Records audio synchronously with video recording for perfect synchronization.
    """
    def __init__(self, session_id, session_key=None):
        if not PYAudio_AVAILABLE:
            raise ImportError("PyAudio is required for backend audio recording. Install with: pip install pyaudio")
        
        self.session_id = session_id
        self.session_key = session_key
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_frames = []
        self.recording_start_timestamp = None
        self.recording_stop_timestamp = None
        
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1  # Mono
        self.RATE = 44100   # Sample rate
        
        # File paths
        self.audio_file_path = None
        
    def start_recording(self, synchronized_start_time=None):
        """Start recording audio. Returns the exact start timestamp for synchronization.
        
        Args:
            synchronized_start_time: Optional future timestamp to start at (for perfect sync with video).
                                    If provided, audio will wait until this exact time to start recording.
        """
        if self.is_recording:
            print(f"⚠️ Audio recording already active for session {self.session_id}")
            return getattr(self, 'recording_start_timestamp', None)
        
        try:
            import time
            
            # CRITICAL: If synchronized_start_time is provided, wait until that exact moment
            if synchronized_start_time:
                current_time = time.time()
                if current_time < synchronized_start_time:
                    wait_time = synchronized_start_time - current_time
                    print(f"🕐 Audio waiting {wait_time * 1000:.1f}ms until synchronized start time: {synchronized_start_time}")
                    time.sleep(wait_time)
                    print(f"✅ Reached synchronized start time - starting audio recording now")
                # CRITICAL: Use synchronized_start_time as authoritative timestamp (not current time after wait)
                # This ensures video and audio use the EXACT same timestamp for perfect synchronization
                self.recording_start_timestamp = synchronized_start_time
                print(f"🕐 Audio recording start timestamp (using synchronized time): {self.recording_start_timestamp}")
                print(f"   ✅ Video and audio using EXACT same timestamp - perfect synchronization!")
            else:
                # No synchronized time - use current time
                self.recording_start_timestamp = time.time()
                print(f"🕐 Audio recording start timestamp (no sync): {self.recording_start_timestamp}")
            
            # Open audio stream
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            self.is_recording = True
            self.audio_frames = []
            
            # Start recording thread
            self.recording_thread = threading.Thread(target=self._record_audio_thread)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            print(f"✅ PyAudio recording started for session {self.session_id}")
            return self.recording_start_timestamp
            
        except Exception as e:
            print(f"❌ Error starting PyAudio recording: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _record_audio_thread(self):
        """Thread function to continuously record audio frames."""
        try:
            while self.is_recording:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                self.audio_frames.append(data)
        except Exception as e:
            print(f"❌ Error in audio recording thread: {e}")
            import traceback
            traceback.print_exc()
    
    def stop_recording(self, synchronized_stop_time=None):
        """Stop recording and save audio file. Returns the exact stop timestamp.
        
        Args:
            synchronized_stop_time: Optional future timestamp to stop at (for perfect sync with video).
        """
        import time
        
        if not self.is_recording:
            print(f"⚠️ Audio recording not active for session {self.session_id}")
            return None
        
        # CRITICAL: If synchronized_stop_time is provided, wait until that exact moment
        if synchronized_stop_time:
            current_time = time.time()
            if current_time < synchronized_stop_time:
                wait_time = synchronized_stop_time - current_time
                print(f"🕐 Audio waiting {wait_time * 1000:.1f}ms until synchronized stop time: {synchronized_stop_time}")
                time.sleep(wait_time)
                print(f"✅ Reached synchronized stop time - stopping audio recording now")
            # CRITICAL: Use synchronized_stop_time as authoritative timestamp (not current time after wait)
            # This ensures video and audio stop at the EXACT same timestamp for perfect synchronization
            self.recording_stop_timestamp = synchronized_stop_time
            print(f"🕐 Audio recording stop timestamp (using synchronized time): {self.recording_stop_timestamp}")
            print(f"   ✅ Video and audio will stop at EXACT same timestamp - perfect synchronization!")
        else:
            # No synchronized stop time - use current time
            self.recording_stop_timestamp = time.time()
            print(f"🕐 Audio recording stop timestamp (no sync): {self.recording_stop_timestamp}")
        
        # Stop recording
        self.is_recording = False
        
        # Wait for recording thread to finish
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join(timeout=2.0)
        
        # Stop and close stream
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
        
        # Save audio to file
        try:
            # Create audio directory
            audio_dir = os.path.join(settings.MEDIA_ROOT, 'interview_audio')
            os.makedirs(audio_dir, exist_ok=True)
            
            # Generate filename
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            audio_filename = f"{self.session_id}_{timestamp}.wav"
            self.audio_file_path = os.path.join(audio_dir, audio_filename)
            
            # Save as WAV file
            wf = wave.open(self.audio_file_path, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.audio_frames))
            wf.close()
            
            # Return relative path
            relative_path = os.path.relpath(self.audio_file_path, settings.MEDIA_ROOT).replace('\\', '/')
            print(f"✅ Audio saved: {relative_path} ({len(self.audio_frames) * self.CHUNK / self.RATE:.2f}s)")
            
            return relative_path
            
        except Exception as e:
            print(f"❌ Error saving audio file: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def cleanup(self):
        """Clean up resources."""
        if self.is_recording:
            self.stop_recording()
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        
        try:
            self.audio.terminate()
        except:
            pass
        
        return self.audio_file_path
        latest_mtime = 0
        
        for filename in os.listdir(audio_dir):
            for prefix in prefixes:
                if filename.startswith(prefix):
                    path = os.path.join(audio_dir, filename)
                    try:
                        mtime = os.path.getmtime(path)
                        if mtime > latest_mtime:
                            latest_file = path
                            latest_mtime = mtime
                    except OSError:
                        continue
        
        if latest_file:
            print(f"🔎 Auto-detected audio file: {latest_file}")
        return latest_file
