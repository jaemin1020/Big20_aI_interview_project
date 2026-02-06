// AudioWorklet processor for Deepgram streaming
class DeepgramProcessor extends AudioWorkletProcessor {
  process(inputs, outputs, parameters) {
    const input = inputs[0];
    
    if (input && input.length > 0) {
      const channelData = input[0]; // Get first channel
      
      // Convert Float32Array to Int16Array (PCM)
      const buffer = new Int16Array(channelData.length);
      for (let i = 0; i < channelData.length; i++) {
        const s = Math.max(-1, Math.min(1, channelData[i]));
        buffer[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      
      // Send to main thread
      this.port.postMessage(buffer.buffer, [buffer.buffer]);
    }
    
    return true; // Keep processor alive
  }
}

registerProcessor('deepgram-processor', DeepgramProcessor);
