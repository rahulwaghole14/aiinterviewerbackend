/**
 * Interview Audio Recorder
 * Records: Microphone audio only (candidate voice)
 * This is used alongside backend video recording
 */
class InterviewAudioRecorder {
    constructor(sessionKey) {
        this.sessionKey = sessionKey;
        this.mediaRecorder = null;
        this.microphoneStream = null;
        this.isRecording = false;
        this.audioChunks = [];
        this.recordingStartTime = null;
        this._uploadResolve = null; // Promise resolver for upload completion
    }
    
    /**
     * Start audio recording (microphone only - candidate voice)
     * Enhanced with Web Audio API filters for better quality
     */
    async startRecording(videoStartTimestamp = null) {
        if (this.isRecording) {
            console.warn('⚠️ Audio recording already in progress');
            return false;
        }
        
        try {
            console.log('🎙️ Starting audio recording (microphone only - candidate voice)...');
            
            // CRITICAL: Record exact start time at the VERY BEGINNING for synchronization
            // This timestamp will be used during merge to align audio and video
            // We record it BEFORE any async operations to ensure accuracy
            const audioStartTime = Date.now() / 1000; // Convert to seconds (Unix timestamp)
            this.recordingStartTime = Date.now();
            
            // If video timestamp provided, we want to start audio at the EXACT same time
            // Calculate the target start time based on video timestamp
            if (videoStartTimestamp) {
                const currentTime = Date.now() / 1000;
                const timeDiff = videoStartTimestamp - currentTime;
                
                console.log(`🕐 Video timestamp: ${videoStartTimestamp}`);
                console.log(`🕐 Current time: ${currentTime}`);
                console.log(`⏱️ Time difference: ${(timeDiff * 1000).toFixed(2)}ms`);
                
                // If video started in the past (normal case), use current time as audio start
                // If video timestamp is in the future (shouldn't happen), use video timestamp
                if (timeDiff > 0) {
                    // Video timestamp is in the future - use it as audio start time
                    this.audioStartTimestamp = videoStartTimestamp;
                    console.log(`🕐 Using video timestamp as audio start: ${videoStartTimestamp}`);
                } else {
                    // Video started in the past - use current time (audio starts now)
                    this.audioStartTimestamp = audioStartTime;
                    console.log(`🕐 Audio starting now at: ${audioStartTime} (video started ${Math.abs(timeDiff * 1000).toFixed(2)}ms ago)`);
                }
                
                // Store video timestamp for merge alignment
                this.videoStartTimestamp = videoStartTimestamp;
                console.log(`✅ Audio and video timestamps stored for merge synchronization`);
            } else {
                // No video timestamp - use current time
                this.audioStartTimestamp = audioStartTime;
                console.log(`⚠️ No video timestamp provided - audio will start independently at: ${audioStartTime}`);
            }
            
            // Get microphone stream with enhanced audio constraints
            console.log('🎤 Requesting microphone access with enhanced filters...');
            this.microphoneStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,      // Remove echo
                    noiseSuppression: true,      // Reduce background noise
                    autoGainControl: true,       // Normalize volume
                    sampleRate: 44100,           // High quality sample rate
                    channelCount: 1,             // Mono (sufficient for voice)
                    latency: 0.01                // Low latency
                }
            });
            console.log('✅ Microphone access granted');
            
            // Create AudioContext for advanced audio processing
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 44100
            });
            
            // Create source from microphone stream
            const source = this.audioContext.createMediaStreamSource(this.microphoneStream);
            
            // Create audio processing nodes for quality enhancement
            // 1. Dynamics Compressor - Normalize volume levels
            this.compressor = this.audioContext.createDynamicsCompressor();
            this.compressor.threshold.value = -24;      // Threshold in dB
            this.compressor.knee.value = 30;             // Knee width
            this.compressor.ratio.value = 12;           // Compression ratio
            this.compressor.attack.value = 0.003;       // Attack time (fast)
            this.compressor.release.value = 0.25;      // Release time
            
            // 2. High-pass filter - Remove low-frequency noise
            this.highPassFilter = this.audioContext.createBiquadFilter();
            this.highPassFilter.type = 'highpass';
            this.highPassFilter.frequency.value = 80;   // Cutoff frequency (removes rumble)
            this.highPassFilter.Q.value = 1;
            
            // 3. Low-pass filter - Remove high-frequency noise
            this.lowPassFilter = this.audioContext.createBiquadFilter();
            this.lowPassFilter.type = 'lowpass';
            this.lowPassFilter.frequency.value = 12000; // Cutoff frequency (keeps voice range)
            this.lowPassFilter.Q.value = 1;
            
            // 4. Gain node - Boost signal if needed
            this.gainNode = this.audioContext.createGain();
            this.gainNode.gain.value = 1.2;             // Slight boost (20%)
            
            // Connect audio processing chain: source -> highpass -> lowpass -> compressor -> gain -> destination
            source.connect(this.highPassFilter);
            this.highPassFilter.connect(this.lowPassFilter);
            this.lowPassFilter.connect(this.compressor);
            this.compressor.connect(this.gainNode);
            
            // Create MediaStreamDestination to capture processed audio
            this.processedDestination = this.audioContext.createMediaStreamDestination();
            this.gainNode.connect(this.processedDestination);
            
            // Create MediaRecorder with processed audio stream
            const options = {
                mimeType: 'audio/webm;codecs=opus',
                audioBitsPerSecond: 192000  // High quality bitrate
            };
            
            // Fallback to basic webm if opus not supported
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'audio/webm';
                console.log('⚠️ Opus not supported, using basic webm');
            }
            
            // Use processed audio stream for recording
            this.mediaRecorder = new MediaRecorder(this.processedDestination.stream, options);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    this.audioChunks.push(event.data);
                    console.log(`🎵 Audio chunk recorded: ${(event.data.size / 1024).toFixed(2)} KB`);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                console.log('🛑 Audio recording stopped, processing...');
                // Clean up audio context
                if (this.audioContext && this.audioContext.state !== 'closed') {
                    await this.audioContext.close();
                }
                await this.processRecording();
                // Note: processRecording will resolve _uploadResolve if it exists
            };
            
            this.mediaRecorder.onerror = (event) => {
                console.error('❌ MediaRecorder error:', event.error);
            };
            
            // CRITICAL: If we have a video timestamp, wait until that EXACT moment to start recording
            // This ensures both video and audio start at the EXACT same time (no trimming needed)
            const currentTime = Date.now() / 1000;
            
            if (videoStartTimestamp) {
                // Calculate time until synchronized start
                const timeUntilStart = videoStartTimestamp - currentTime;
                
                if (timeUntilStart > 0) {
                    // Future timestamp - wait until exact moment
                    console.log(`⏱️ Waiting ${(timeUntilStart * 1000).toFixed(1)}ms until synchronized start time...`);
                    console.log(`   Current time: ${currentTime}`);
                    console.log(`   Start time: ${videoStartTimestamp}`);
                    
                    // Wait until the exact synchronized start time
                    const waitMs = Math.max(0, timeUntilStart * 1000);
                    await new Promise(resolve => setTimeout(resolve, waitMs));
                    
                    // Verify we're at the right time (or very close)
                    const actualStartTime = Date.now() / 1000;
                    const timeDiff = Math.abs(actualStartTime - videoStartTimestamp);
                    console.log(`✅ Starting audio at synchronized time: ${actualStartTime}`);
                    console.log(`   Time difference: ${(timeDiff * 1000).toFixed(1)}ms (should be < 50ms)`);
                    
                    // Use the synchronized timestamp as authoritative start time
                    this.audioStartTimestamp = videoStartTimestamp;
                    console.log(`🕐 Audio and video using EXACT same start timestamp: ${videoStartTimestamp}`);
                    console.log(`   ✅ Perfect synchronization - no trimming needed!`);
                } else {
                    // Timestamp is in the past - use current time
                    this.audioStartTimestamp = currentTime;
                    console.log(`⚠️ Video timestamp is in the past, using current time: ${currentTime}`);
                }
                console.log(`🕐 MediaRecorder will start at: ${mediaRecorderStartTime}`);
                
                const syncDiff = Math.abs(mediaRecorderStartTime - videoStartTimestamp);
                console.log(`⏱️ Time difference between video start and audio MediaRecorder start: ${(syncDiff * 1000).toFixed(2)}ms`);
                
                if (syncDiff > 0.5) {
                    console.warn(`⚠️ WARNING: Audio MediaRecorder started ${(syncDiff * 1000).toFixed(2)}ms after video - will be corrected during merge`);
                } else {
                    console.log(`✅ Audio and video start times are well synchronized (< 500ms difference)`);
                }
            } else {
                // No video timestamp - use current time
                this.audioStartTimestamp = currentTime;
                console.log(`⚠️ No video timestamp - using current time: ${currentTime}`);
            }
            
            // Start recording with 10 second chunks
            // CRITICAL: Start MediaRecorder NOW (we already waited for synchronized time if needed)
            console.log('🎬 Starting MediaRecorder with enhanced audio filters...');
            this.mediaRecorder.start(10000);
            this.isRecording = true;
            
            // Verify synchronization
            const actualMediaRecorderStart = Date.now() / 1000;
            if (videoStartTimestamp) {
                const syncDiff = Math.abs(actualMediaRecorderStart - videoStartTimestamp);
                if (syncDiff < 0.1) {
                    console.log(`✅ Perfect synchronization! Audio started ${(syncDiff * 1000).toFixed(1)}ms from video start`);
                    console.log(`   ✅ No trimming needed - both started at exact same time!`);
                } else {
                    console.warn(`⚠️ Small sync difference: ${(syncDiff * 1000).toFixed(1)}ms (will be handled during merge)`);
                }
            }
            
            console.log('✅ Audio recording started successfully with enhanced filters');
            console.log('   - Echo cancellation: Enabled');
            console.log('   - Noise suppression: Enabled');
            console.log('   - Auto gain control: Enabled');
            console.log('   - High-pass filter: 80Hz');
            console.log('   - Low-pass filter: 12kHz');
            console.log('   - Dynamics compressor: Enabled');
            console.log('   - Gain boost: 20%');
            
            return true;
        } catch (error) {
            console.error('❌ Failed to start audio recording:', error);
            console.error('❌ Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            this.isRecording = false;
            return false;
        }
    }
    
    // TTS audio capture methods removed - recording microphone only (candidate voice)
    
    /**
     * Stop recording and upload audio
     * Returns a promise that resolves when upload is complete
     */
    async stopRecording(synchronizedStopTime = null) {
        // CRITICAL: If synchronized stop time is provided, wait until that exact moment
        if (synchronizedStopTime) {
            const currentTime = Date.now() / 1000;
            if (currentTime < synchronizedStopTime) {
                const waitTime = synchronizedStopTime - currentTime;
                console.log(`🕐 Waiting ${(waitTime * 1000).toFixed(1)}ms until synchronized stop time: ${synchronizedStopTime}`);
                await new Promise(resolve => setTimeout(resolve, waitTime * 1000));
                console.log(`✅ Reached synchronized stop time - stopping audio now`);
            }
        }
        
        // CRITICAL: Record audio stop timestamp AFTER synchronized wait
        const audioStopTimestamp = Date.now() / 1000;
        this.audioStopTimestamp = audioStopTimestamp;
        console.log(`🕐 Audio recording stop timestamp: ${audioStopTimestamp}`);
        
        // Even if not recording, check if there are chunks to process
        const hasChunks = this.audioChunks && this.audioChunks.length > 0;
        
        if (!this.isRecording && !hasChunks) {
            console.warn('⚠️ Audio recording not in progress and no chunks to process');
            // Still return stored path if available
            return { success: true, audioPath: window.uploadedAudioPath || null, audioStopTimestamp: audioStopTimestamp };
        }
        
        try {
            this.isRecording = false;
            
            // Create a promise that resolves when processing is complete
            const uploadPromise = new Promise((resolve) => {
                this._uploadResolve = resolve;
            });
            
            if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
                this.mediaRecorder.stop();
                console.log('🛑 Audio recording stopped, waiting for upload...');
            } else {
                // If MediaRecorder already stopped but we have chunks, process them
                if (hasChunks) {
                    console.log('📦 MediaRecorder already stopped, processing remaining chunks...');
                    await this.processRecording();
                }
                // Wait a bit for upload to complete
                await new Promise(resolve => setTimeout(resolve, 1000));
                // Check for stored path
                const storedPath = window.uploadedAudioPath || null;
                if (storedPath) {
                    return { success: true, audioPath: storedPath };
                }
                // If no stored path yet, wait for upload promise
                try {
                    const result = await Promise.race([
                        uploadPromise,
                        new Promise(resolve => setTimeout(() => resolve({ success: true, audioPath: window.uploadedAudioPath || null }), 5000))
                    ]);
                    return result;
                } catch (e) {
                    return { success: true, audioPath: window.uploadedAudioPath || null };
                }
            }
            
            // Wait for upload to complete (processRecording will resolve this)
            // Add timeout to prevent infinite waiting
            const result = await Promise.race([
                uploadPromise,
                new Promise(resolve => setTimeout(() => {
                    console.warn('⏱️ Upload timeout, checking stored path...');
                    resolve({ success: true, audioPath: window.uploadedAudioPath || null });
                }, 10000)) // 10 second timeout
            ]);
            
            // Stop all tracks after upload
            if (this.microphoneStream) {
                this.microphoneStream.getTracks().forEach(track => track.stop());
            }
            
            return result;
        } catch (error) {
            console.error('❌ Error stopping audio recording:', error);
            // Still try to return stored path if available
            return { success: true, audioPath: window.uploadedAudioPath || null };
        }
    }
    
    /**
     * Process and upload the recorded audio
     */
    async processRecording() {
        if (this.audioChunks.length === 0) {
            console.warn('⚠️ No audio chunks to process');
            return;
        }
        
        try {
            // Create blob from chunks
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            console.log(`📦 Audio blob created: ${(audioBlob.size / 1024 / 1024).toFixed(2)} MB`);
            
            // Upload audio file with timestamps for synchronization
            const formData = new FormData();
            formData.append('audio_file', audioBlob, `interview_audio_${this.sessionKey}.webm`);
            formData.append('session_key', this.sessionKey);
            
            // CRITICAL: Send timestamps for audio-video synchronization
            if (this.audioStartTimestamp) {
                formData.append('audio_start_timestamp', this.audioStartTimestamp.toString());
                console.log(`📤 Sending audio start timestamp: ${this.audioStartTimestamp}`);
            }
            if (this.videoStartTimestamp) {
                formData.append('video_start_timestamp', this.videoStartTimestamp.toString());
                console.log(`📤 Sending video start timestamp: ${this.videoStartTimestamp}`);
            }
            
            console.log('📤 Uploading audio file...');
            const response = await fetch('/ai/recording/upload_audio/', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Get audio path - check both audio_file_path and audio_path (backend might return either)
                const audioPath = result.audio_file_path || result.audio_path;
                
                if (!audioPath) {
                    console.error('❌ Audio uploaded but no path returned in response:', result);
                    if (this._uploadResolve) {
                        this._uploadResolve({ success: false, audioPath: null, error: 'No audio path in response' });
                    }
                    return;
                }
                
                console.log('✅ Audio uploaded successfully');
                console.log('📁 Audio file path:', audioPath);
                
                // Store audio path in multiple places to ensure it's accessible
                const targetWindow = window.parent !== window ? window.parent : window;
                
                // Store in parent window (portal.html) - this is the main location
                try {
                    targetWindow.uploadedAudioPath = audioPath;
                    console.log('✅ Audio path stored in parent window:', audioPath);
                } catch (e) {
                    console.warn('⚠️ Could not access parent window:', e);
                }
                
                // Store in current window as fallback
                window.uploadedAudioPath = audioPath;
                console.log('✅ Audio path stored in current window:', audioPath);
                
                // Also try to dispatch a custom event to notify portal.html
                try {
                    const event = new CustomEvent('audioUploaded', {
                        detail: { audioPath: audioPath, sessionKey: this.sessionKey }
                    });
                    targetWindow.dispatchEvent(event);
                    console.log('📢 Dispatched audioUploaded event');
                } catch (e) {
                    console.warn('⚠️ Could not dispatch event:', e);
                }
                
                console.log('📋 Audio path stored for session:', this.sessionKey);
                console.log('📋 Final stored path:', audioPath);
                
                // Resolve the upload promise with the audio path
                if (this._uploadResolve) {
                    this._uploadResolve({ success: true, audioPath: audioPath });
                    this._uploadResolve = null;
                }
                
                // The audio file path will be used by end_interview_session to merge with video
            } else {
                console.error('❌ Audio upload failed:', result.message);
                if (this._uploadResolve) {
                    this._uploadResolve({ success: false, audioPath: null, error: result.message });
                    this._uploadResolve = null;
                }
            }
        } catch (error) {
            console.error('❌ Error processing audio recording:', error);
            console.error('❌ Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            
            // Resolve with error if promise is waiting
            if (this._uploadResolve) {
                this._uploadResolve({ success: false, audioPath: null, error: error.message });
                this._uploadResolve = null;
            }
        }
    }
}

