/**
 * Comprehensive Interview Video Recorder
 * Records: Camera video, Microphone audio, and TTS question audio
 */
class InterviewVideoRecorder {
    constructor(sessionKey) {
        this.sessionKey = sessionKey;
        this.mediaRecorder = null;
        this.videoStream = null;
        this.audioStream = null;
        this.ttsAudioContext = null;
        this.ttsSource = null;
        this.ttsDestination = null;
        this.mixedAudioContext = null;
        this.mixedAudioDestination = null;
        this.isRecording = false;
        this.videoChunks = [];
        this.recordingStartTime = null;
        this.questionTimestamps = [];
    }
    
    /**
     * Start comprehensive video recording
     * Captures: Camera video, Microphone audio, TTS audio
     */
    async startRecording() {
        if (this.isRecording) {
            console.warn('⚠️ Recording already in progress');
            return false;
        }
        
        try {
            console.log('🎥 Starting comprehensive video recording...');
            console.log('📊 Pre-recording check:', {
                hasVideoRecorder: !!this,
                sessionKey: this.sessionKey,
                isRecording: this.isRecording
            });
            this.recordingStartTime = Date.now();
            
            // Step 1: Try to get camera and microphone streams
            // First, try to reuse existing video stream from proctoring system
            let userMediaStream = null;
            let videoTrack = null;
            let audioTrack = null;
            
            // Try to get stream from existing video elements (proctoring feed)
            const videoElements = document.querySelectorAll('video');
            for (const videoEl of videoElements) {
                if (videoEl.srcObject && videoEl.srcObject instanceof MediaStream) {
                    const existingStream = videoEl.srcObject;
                    const existingVideoTrack = existingStream.getVideoTracks()[0];
                    if (existingVideoTrack && existingVideoTrack.readyState === 'live') {
                        console.log('✅ Found existing video stream from proctoring system, cloning track...');
                        // Clone the video track to avoid conflicts
                        videoTrack = existingVideoTrack;
                        break;
                    }
                }
            }
            
            // If no existing video track, try getUserMedia with retry logic
            if (!videoTrack) {
                console.log('📹 Requesting camera and microphone access...');
                let retries = 3;
                let delay = 1000; // Start with 1 second delay
                
                while (retries > 0 && !userMediaStream) {
                    try {
                        userMediaStream = await navigator.mediaDevices.getUserMedia({
                            video: {
                                width: { ideal: 1280 },
                                height: { ideal: 720 },
                                frameRate: { ideal: 30 }
                            },
                            audio: {
                                echoCancellation: true,
                                noiseSuppression: true,
                                autoGainControl: true
                            }
                        });
                        videoTrack = userMediaStream.getVideoTracks()[0];
                        audioTrack = userMediaStream.getAudioTracks()[0];
                        break;
                    } catch (error) {
                        if (error.name === 'NotReadableError' && error.message.includes('Device in use')) {
                            retries--;
                            if (retries > 0) {
                                console.log(`⚠️ Camera in use, retrying in ${delay}ms... (${retries} retries left)`);
                                await new Promise(resolve => setTimeout(resolve, delay));
                                delay *= 2; // Exponential backoff
                            } else {
                                throw error;
                            }
                        } else {
                            throw error;
                        }
                    }
                }
            } else {
                // We have a video track from existing stream, but still need audio
                console.log('📹 Requesting microphone access only...');
                try {
                    const audioStream = await navigator.mediaDevices.getUserMedia({
                        video: false,
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        }
                    });
                    audioTrack = audioStream.getAudioTracks()[0];
                } catch (error) {
                    console.warn('⚠️ Could not get microphone, continuing without audio:', error);
                }
            }
            
            if (!videoTrack) {
                throw new Error('No video track available');
            }
            
            console.log('✅ Camera access granted');
            console.log('📊 Media stream tracks:', {
                videoTrack: !!videoTrack,
                audioTrack: !!audioTrack,
                videoTrackState: videoTrack?.readyState,
                audioTrackState: audioTrack?.readyState
            });
            
            this.videoStream = videoTrack;
            this.audioStream = audioTrack;
            
            if (!this.audioStream) {
                console.warn('⚠️ No audio track available, recording video only');
            }
            
            console.log('✅ Video and audio tracks extracted');
            
            // Step 2: Set up Web Audio API to capture TTS audio (non-blocking)
            let ttsSetupSuccess = false;
            try {
                await this.setupTTSAudioCapture();
                ttsSetupSuccess = true;
            } catch (error) {
                console.warn('⚠️ TTS setup failed, continuing without TTS capture:', error);
            }
            
            // Step 3: Create mixed audio stream (microphone + TTS if available)
            let mixedStream;
            try {
                if (this.audioStream) {
                    mixedStream = await this.createMixedAudioStream();
                } else {
                    // No microphone, try TTS only
                    console.log('⚠️ No microphone available, attempting TTS-only audio...');
                    mixedStream = await this.createMixedAudioStream();
                }
            } catch (error) {
                console.warn('⚠️ Mixed audio stream creation failed:', error);
                // Fallback to microphone-only stream if available
                if (this.audioStream) {
                    mixedStream = new MediaStream([this.audioStream]);
                } else {
                    // No audio at all - create empty audio stream or skip audio
                    console.warn('⚠️ No audio tracks available, recording video only');
                    mixedStream = new MediaStream([]);
                }
            }
            
            // Step 4: Combine video and mixed audio
            const combinedStream = new MediaStream([
                this.videoStream
            ]);
            
            // Add audio tracks if available
            const audioTracks = mixedStream.getAudioTracks();
            if (audioTracks.length > 0) {
                audioTracks.forEach(track => combinedStream.addTrack(track));
            } else {
                console.warn('⚠️ No audio tracks to add to combined stream');
            }
            
            console.log('📊 Combined stream tracks:', {
                video: combinedStream.getVideoTracks().length,
                audio: combinedStream.getAudioTracks().length,
                ttsEnabled: ttsSetupSuccess
            });
            
            // Step 5: Create MediaRecorder with optimal settings
            const options = {
                mimeType: 'video/webm;codecs=vp9,opus',
                videoBitsPerSecond: 2500000, // 2.5 Mbps
                audioBitsPerSecond: 192000    // 192 kbps for better quality
            };
            
            // Fallback to vp8 if vp9 not supported
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'video/webm;codecs=vp8,opus';
                console.log('⚠️ VP9 not supported, using VP8');
            }
            
            this.mediaRecorder = new MediaRecorder(combinedStream, options);
            this.videoChunks = [];
            
            // Handle data available (chunks)
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    this.videoChunks.push(event.data);
                    console.log(`📹 Video chunk recorded: ${(event.data.size / 1024).toFixed(2)} KB`);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                console.log('🛑 Video recording stopped, processing...');
                await this.processRecording();
            };
            
            this.mediaRecorder.onerror = (event) => {
                console.error('❌ MediaRecorder error:', event.error);
            };
            
            // Start recording with 10 second chunks for better reliability
            console.log('🎬 Starting MediaRecorder...');
            this.mediaRecorder.start(10000);
            this.isRecording = true;
            
            console.log('✅ Comprehensive video recording started');
            console.log('📊 Recording state:', {
                isRecording: this.isRecording,
                mediaRecorderState: this.mediaRecorder.state,
                videoTracks: combinedStream.getVideoTracks().length,
                audioTracks: combinedStream.getAudioTracks().length,
                mimeType: options.mimeType,
                sessionKey: this.sessionKey
            });
            
            // Verify recording is actually active
            setTimeout(() => {
                if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                    console.log('✅ MediaRecorder confirmed in recording state');
                } else {
                    console.warn('⚠️ MediaRecorder state check:', {
                        state: this.mediaRecorder?.state,
                        isRecording: this.isRecording
                    });
                }
            }, 1000);
            
            return true;
        } catch (error) {
            console.error('❌ Failed to start video recording:', error);
            console.error('❌ Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            // Fallback: Try recording without TTS audio capture
            console.log('🔄 Attempting fallback recording (camera + microphone only)...');
            return await this.startRecordingFallback();
        }
    }
    
    /**
     * Set up Web Audio API to capture TTS audio from audio elements
     */
    async setupTTSAudioCapture() {
        try {
            // Create audio context for TTS capture
            this.ttsAudioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.ttsDestination = this.ttsAudioContext.createMediaStreamDestination();
            
            console.log('✅ TTS AudioContext created');
            
            // Hook into audio elements to capture TTS
            this.hookAudioElements();
            
            console.log('✅ TTS audio capture setup complete');
        } catch (error) {
            console.warn('⚠️ Could not set up TTS audio capture:', error);
            console.warn('⚠️ TTS capture error details:', {
                name: error.name,
                message: error.message
            });
            // Don't throw - continue without TTS capture
        }
    }
    
    /**
     * Hook into audio elements to capture TTS playback
     */
    hookAudioElements() {
        // Find all audio elements that might play TTS
        const audioElements = document.querySelectorAll('audio');
        
        audioElements.forEach((audioEl, index) => {
            // Create a MediaElementAudioSourceNode to capture audio element output
            try {
                if (!audioEl.captured) {
                    const source = this.ttsAudioContext.createMediaElementSource(audioEl);
                    source.connect(this.ttsDestination);
                    audioEl.captured = true;
                    console.log(`✅ Hooked into audio element ${index} for TTS capture`);
                }
            } catch (error) {
                console.warn(`⚠️ Could not hook into audio element ${index}:`, error);
                // If error is due to audio element already being connected, that's okay
                if (error.name !== 'InvalidStateError') {
                    console.warn(`   Error details:`, error);
                }
            }
        });
        
        // Also hook into global currentAudio if it exists (used in portal.html)
        if (typeof currentAudio !== 'undefined' && currentAudio && !currentAudio.captured) {
            try {
                const source = this.ttsAudioContext.createMediaElementSource(currentAudio);
                source.connect(this.ttsDestination);
                currentAudio.captured = true;
                console.log('✅ Hooked into global currentAudio element for TTS capture');
            } catch (error) {
                console.warn('⚠️ Could not hook into currentAudio:', error);
            }
        }
        
        // Also monitor for dynamically created audio elements
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeName === 'AUDIO' || (node.querySelector && node.querySelector('audio'))) {
                        const newAudio = node.nodeName === 'AUDIO' ? node : node.querySelector('audio');
                        if (newAudio && !newAudio.captured) {
                            try {
                                const source = this.ttsAudioContext.createMediaElementSource(newAudio);
                                source.connect(this.ttsDestination);
                                newAudio.captured = true;
                                console.log('✅ Hooked into dynamically created audio element');
                            } catch (error) {
                                console.warn('⚠️ Could not hook into new audio element:', error);
                            }
                        }
                    }
                });
            });
        });
        
        observer.observe(document.body, { childList: true, subtree: true });
        this.audioObserver = observer;
    }
    
    /**
     * Create mixed audio stream combining microphone and TTS
     */
    async createMixedAudioStream() {
        try {
            // Create audio context for mixing
            this.mixedAudioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.mixedAudioDestination = this.mixedAudioContext.createMediaStreamDestination();
            
            console.log('✅ Mixed audio context created');
            
            // Get microphone audio source
            const micStream = new MediaStream([this.audioStream]);
            const micSource = this.mixedAudioContext.createMediaStreamSource(micStream);
            
            console.log('✅ Microphone source connected');
            
            // Get TTS audio source (if available)
            let ttsSource = null;
            if (this.ttsDestination && this.ttsDestination.stream) {
                try {
                    const ttsTracks = this.ttsDestination.stream.getAudioTracks();
                    if (ttsTracks.length > 0) {
                        ttsSource = this.mixedAudioContext.createMediaStreamSource(
                            this.ttsDestination.stream
                        );
                        console.log('✅ TTS source connected');
                    } else {
                        console.log('⚠️ TTS destination stream has no audio tracks');
                    }
                } catch (error) {
                    console.warn('⚠️ Could not create TTS audio source:', error);
                }
            } else {
                console.log('⚠️ TTS destination not available, recording microphone only');
            }
            
            // Create gain nodes for volume control
            const micGain = this.mixedAudioContext.createGain();
            const ttsGain = this.mixedAudioContext.createGain();
            
            // Set gain levels (microphone: 1.0, TTS: 0.8 to avoid overpowering)
            micGain.gain.value = 1.0;
            ttsGain.gain.value = 0.8;
            
            // Connect sources to gain nodes
            micSource.connect(micGain);
            if (ttsSource) {
                ttsSource.connect(ttsGain);
            }
            
            // Connect gain nodes to destination
            micGain.connect(this.mixedAudioDestination);
            if (ttsSource) {
                ttsGain.connect(this.mixedAudioDestination);
            }
            
            const finalTracks = this.mixedAudioDestination.stream.getAudioTracks();
            console.log(`✅ Mixed audio stream created with ${finalTracks.length} audio track(s)`);
            return this.mixedAudioDestination.stream;
        } catch (error) {
            console.error('❌ Failed to create mixed audio stream:', error);
            console.error('❌ Mixing error details:', {
                name: error.name,
                message: error.message
            });
            // Fallback: Use only microphone
            console.log('🔄 Using microphone-only stream as fallback');
            return new MediaStream([this.audioStream]);
        }
    }
    
    /**
     * Fallback recording without TTS capture (microphone + camera only)
     */
    async startRecordingFallback() {
        try {
            console.log('🔄 Starting fallback recording (camera + microphone only)...');
            
            // Clean up any existing streams
            if (this.videoStream && this.videoStream.getTracks) {
                this.videoStream.getTracks().forEach(track => track.stop());
            }
            if (this.audioStream && this.audioStream.stop) {
                this.audioStream.stop();
            }
            
            // Try to reuse existing video stream first
            let videoTrack = null;
            let audioTrack = null;
            
            const videoElements = document.querySelectorAll('video');
            for (const videoEl of videoElements) {
                if (videoEl.srcObject && videoEl.srcObject instanceof MediaStream) {
                    const existingStream = videoEl.srcObject;
                    const existingVideoTrack = existingStream.getVideoTracks()[0];
                    if (existingVideoTrack && existingVideoTrack.readyState === 'live') {
                        console.log('✅ Found existing video stream for fallback, reusing...');
                        videoTrack = existingVideoTrack;
                        break;
                    }
                }
            }
            
            // If no existing video, try getUserMedia with retry
            if (!videoTrack) {
                let retries = 3;
                let delay = 2000; // Start with 2 second delay for fallback
                
                while (retries > 0) {
                    try {
                        const tempStream = await navigator.mediaDevices.getUserMedia({
                            video: {
                                width: { ideal: 1280 },
                                height: { ideal: 720 },
                                frameRate: { ideal: 30 }
                            },
                            audio: {
                                echoCancellation: true,
                                noiseSuppression: true,
                                autoGainControl: true
                            }
                        });
                        videoTrack = tempStream.getVideoTracks()[0];
                        audioTrack = tempStream.getAudioTracks()[0];
                        break;
                    } catch (error) {
                        if (error.name === 'NotReadableError' && error.message.includes('Device in use')) {
                            retries--;
                            if (retries > 0) {
                                console.log(`⚠️ Camera in use (fallback), retrying in ${delay}ms... (${retries} retries left)`);
                                await new Promise(resolve => setTimeout(resolve, delay));
                                delay *= 2;
                            } else {
                                throw error;
                            }
                        } else {
                            throw error;
                        }
                    }
                }
            } else {
                // We have video track, get audio separately
                try {
                    const audioStream = await navigator.mediaDevices.getUserMedia({
                        video: false,
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        }
                    });
                    audioTrack = audioStream.getAudioTracks()[0];
                } catch (error) {
                    console.warn('⚠️ Could not get microphone for fallback:', error);
                }
            }
            
            if (!videoTrack) {
                throw new Error('No video track available for fallback recording');
            }
            
            const userMediaStream = new MediaStream();
            userMediaStream.addTrack(videoTrack);
            if (audioTrack) {
                userMediaStream.addTrack(audioTrack);
            }
            
            console.log('✅ Got media stream for fallback recording');
            console.log('📊 Stream tracks:', {
                video: userMediaStream.getVideoTracks().length,
                audio: userMediaStream.getAudioTracks().length,
                videoTrackState: videoTrack?.readyState,
                audioTrackState: audioTrack?.readyState
            });
            
            const options = {
                mimeType: 'video/webm;codecs=vp9,opus',
                videoBitsPerSecond: 2500000,
                audioBitsPerSecond: 192000
            };
            
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'video/webm;codecs=vp8,opus';
                console.log('⚠️ VP9 not supported, using VP8 for fallback');
            }
            
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                // Last resort: try basic webm
                options.mimeType = 'video/webm';
                console.log('⚠️ VP8 not supported, using basic webm');
            }
            
            this.mediaRecorder = new MediaRecorder(userMediaStream, options);
            this.videoChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    this.videoChunks.push(event.data);
                    console.log(`📹 Fallback video chunk: ${(event.data.size / 1024).toFixed(2)} KB`);
                }
            };
            
            this.mediaRecorder.onstop = async () => {
                console.log('🛑 Fallback recording stopped');
                await this.processRecording();
            };
            
            this.mediaRecorder.onerror = (event) => {
                console.error('❌ Fallback MediaRecorder error:', event.error);
            };
            
            // Start recording with 10 second chunks
            this.mediaRecorder.start(10000);
            this.isRecording = true;
            this.videoStream = userMediaStream;
            this.audioStream = userMediaStream.getAudioTracks()[0];
            
            console.log('✅ Fallback recording started successfully');
            console.log('📊 Recording state:', {
                isRecording: this.isRecording,
                state: this.mediaRecorder.state,
                mimeType: options.mimeType
            });
            return true;
        } catch (error) {
            console.error('❌ Fallback recording failed:', error);
            console.error('❌ Fallback error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            this.isRecording = false;
            return false;
        }
    }
    
    /**
     * Record when a question is asked (for metadata)
     */
    recordQuestion(questionIndex, questionText, questionType) {
        const timestamp = Date.now() - (this.recordingStartTime || Date.now());
        this.questionTimestamps.push({
            index: questionIndex,
            timestamp: timestamp,
            text: questionText,
            type: questionType
        });
        console.log(`📝 Recorded question ${questionIndex}: ${questionType} at ${timestamp}ms`);
    }
    
    /**
     * Stop recording
     */
    async stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) {
            console.warn('⚠️ No recording in progress');
            return;
        }
        
        console.log('🛑 Stopping video recording...');
        this.mediaRecorder.stop();
        this.isRecording = false;
        
        // Stop all tracks
        if (this.videoStream) {
            if (this.videoStream.getTracks) {
                this.videoStream.getTracks().forEach(track => track.stop());
            } else if (this.videoStream.stop) {
                this.videoStream.stop();
            }
        }
        
        if (this.audioStream) {
            this.audioStream.stop();
        }
        
        // Clean up audio contexts
        if (this.mixedAudioContext) {
            await this.mixedAudioContext.close();
        }
        if (this.ttsAudioContext) {
            await this.ttsAudioContext.close();
        }
        
        // Stop audio observer
        if (this.audioObserver) {
            this.audioObserver.disconnect();
        }
    }
    
    /**
     * Process and upload the recorded video
     */
    async processRecording() {
        try {
            console.log('🔄 Processing video recording...');
            
            if (this.videoChunks.length === 0) {
                console.warn('⚠️ No video chunks recorded');
                return;
            }
            
            // Combine all chunks into a single blob
            const videoBlob = new Blob(this.videoChunks, { type: 'video/webm' });
            const fileSizeMB = (videoBlob.size / 1024 / 1024).toFixed(2);
            console.log(`📦 Total video size: ${fileSizeMB} MB`);
            
            // Upload video with metadata
            const formData = new FormData();
            formData.append('session_key', this.sessionKey);
            formData.append('video', videoBlob, `interview_${this.sessionKey}.webm`);
            formData.append('question_timestamps', JSON.stringify(this.questionTimestamps));
            formData.append('duration', Date.now() - (this.recordingStartTime || Date.now()));
            
            console.log('📤 Uploading video...');
            const response = await fetch('/ai/recording/upload_video/', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('✅ Video uploaded successfully:', result);
            
            return result;
        } catch (error) {
            console.error('❌ Error processing video recording:', error);
            throw error;
        }
    }
}

