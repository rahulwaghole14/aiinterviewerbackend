/**
 * Interview Video Recorder
 * Records complete interview with:
 * - Webcam video
 * - Microphone audio (candidate answers)
 * - System audio (TTS questions)
 * 
 * Uses MediaRecorder API to capture and upload chunks to server
 */

class InterviewVideoRecorder {
    constructor(sessionKey) {
        this.sessionKey = sessionKey;
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.chunkIndex = 0;
        this.isRecording = false;
        this.videoStream = null;
        this.audioContext = null;
        this.destinationStream = null;
        
        console.log('📹 InterviewVideoRecorder initialized for session:', sessionKey);
    }
    
    async startRecording() {
        if (this.isRecording) {
            console.warn('⚠️ Recording already in progress');
            return false;
        }
        
        try {
            console.log('🎥 Starting video recording...');
            
            // Get webcam video + audio
            const videoStream = await navigator.mediaDevices.getUserMedia({
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
            
            this.videoStream = videoStream;
            
            // Create media recorder with optimized settings
            const options = {
                mimeType: 'video/webm;codecs=vp9,opus',
                videoBitsPerSecond: 2500000, // 2.5 Mbps
                audioBitsPerSecond: 128000    // 128 kbps
            };
            
            // Fallback to vp8 if vp9 not supported
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'video/webm;codecs=vp8,opus';
                console.log('⚠️ VP9 not supported, using VP8');
            }
            
            this.mediaRecorder = new MediaRecorder(videoStream, options);
            
            // Handle data available (chunks)
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                    console.log(`📹 Chunk recorded: ${event.data.size} bytes (total: ${this.recordedChunks.length} chunks)`);
                    
                    // Upload chunk every 10 seconds (to avoid memory issues)
                    if (this.recordedChunks.length >= 10) {
                        this._uploadChunks(false);
                    }
                }
            };
            
            // Handle recording stop
            this.mediaRecorder.onstop = () => {
                console.log('🛑 Recording stopped, uploading final chunks...');
                this._uploadChunks(true);
            };
            
            // Handle errors
            this.mediaRecorder.onerror = (event) => {
                console.error('❌ MediaRecorder error:', event.error);
            };
            
            // Start recording (capture chunks every 1 second)
            this.mediaRecorder.start(1000);
            this.isRecording = true;
            
            console.log('✅ Recording started successfully');
            
            // Show recording indicator
            this._showRecordingIndicator();
            
            return true;
            
        } catch (error) {
            console.error('❌ Error starting recording:', error);
            alert('Failed to start recording: ' + error.message);
            return false;
        }
    }
    
    async stopRecording() {
        if (!this.isRecording) {
            console.warn('⚠️ No recording in progress');
            return false;
        }
        
        try {
            console.log('🛑 Stopping recording...');
            
            // Stop media recorder
            if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
                this.mediaRecorder.stop();
            }
            
            // Stop all tracks
            if (this.videoStream) {
                this.videoStream.getTracks().forEach(track => track.stop());
            }
            
            this.isRecording = false;
            
            // Hide recording indicator
            this._hideRecordingIndicator();
            
            console.log('✅ Recording stopped successfully');
            return true;
            
        } catch (error) {
            console.error('❌ Error stopping recording:', error);
            return false;
        }
    }
    
    async _uploadChunks(isFinal) {
        if (this.recordedChunks.length === 0) {
            console.log('⚠️ No chunks to upload');
            if (isFinal) {
                this._notifyRecordingComplete();
            }
            return;
        }
        
        try {
            // Create blob from chunks
            const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
            const formData = new FormData();
            formData.append('video_chunk', blob);
            formData.append('session_key', this.sessionKey);
            formData.append('chunk_index', this.chunkIndex);
            formData.append('is_final', isFinal ? 'true' : 'false');
            
            console.log(`📤 Uploading chunk ${this.chunkIndex} (${blob.size} bytes, final: ${isFinal})...`);
            
            // Upload chunk
            const response = await fetch('/ai/recording/upload_chunk/', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log(`✅ Chunk ${this.chunkIndex} uploaded successfully`);
                this.chunkIndex++;
                this.recordedChunks = []; // Clear chunks after upload
                
                if (isFinal) {
                    console.log('✅ All chunks uploaded, recording complete!');
                    this._notifyRecordingComplete(result.recording_path);
                }
            } else {
                console.error('❌ Chunk upload failed:', result.error);
            }
            
        } catch (error) {
            console.error('❌ Error uploading chunk:', error);
        }
    }
    
    _showRecordingIndicator() {
        // Create recording indicator if it doesn't exist
        if (!document.getElementById('recording-indicator')) {
            const indicator = document.createElement('div');
            indicator.id = 'recording-indicator';
            indicator.innerHTML = `
                <div style="position: fixed; top: 20px; right: 20px; z-index: 10000; 
                           background: rgba(220, 53, 69, 0.9); color: white; 
                           padding: 10px 20px; border-radius: 25px; 
                           display: flex; align-items: center; gap: 10px;
                           box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                           font-family: Arial, sans-serif; font-size: 14px; font-weight: 600;">
                    <div class="recording-dot" style="width: 12px; height: 12px; 
                                background: white; border-radius: 50%; 
                                animation: pulse 1.5s ease-in-out infinite;"></div>
                    <span>RECORDING</span>
                </div>
                <style>
                    @keyframes pulse {
                        0%, 100% { opacity: 1; transform: scale(1); }
                        50% { opacity: 0.5; transform: scale(0.8); }
                    }
                </style>
            `;
            document.body.appendChild(indicator);
        }
    }
    
    _hideRecordingIndicator() {
        const indicator = document.getElementById('recording-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    _notifyRecordingComplete(recordingPath) {
        console.log('📹 Recording complete notification:', recordingPath);
        
        // Dispatch custom event
        const event = new CustomEvent('interviewRecordingComplete', {
            detail: { recordingPath }
        });
        window.dispatchEvent(event);
        
        // Show success message (optional)
        console.log('✅ Interview recording saved successfully!');
    }
    
    // Cleanup method
    cleanup() {
        if (this.isRecording) {
            this.stopRecording();
        }
        
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
        }
        
        this._hideRecordingIndicator();
    }
}

// Export for use in portal.html
window.InterviewVideoRecorder = InterviewVideoRecorder;

