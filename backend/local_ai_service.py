#!/usr/bin/env python3
"""
Local AI Service for SoulBridge AI
Provides free local AI responses using Hugging Face Transformers
"""
import os
import logging
import threading
import time
from typing import Optional, Dict, Any
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class LocalAIService:
    """Local AI service using Hugging Face Transformers"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_name = "microsoft/DialoGPT-large"  # Better quality responses
        self.is_initialized = False
        self.initialization_lock = threading.Lock()
        self.max_length = 150
        self.temperature = 0.7
        
        # Performance tracking
        self.request_count = 0
        self.total_response_time = 0.0
        self.last_cleanup = time.time()
        
    def initialize(self) -> bool:
        """Initialize the local AI model lazily"""
        if self.is_initialized:
            return True
            
        with self.initialization_lock:
            if self.is_initialized:  # Double-check after acquiring lock
                return True
                
            try:
                logger.info("Initializing local AI model...")
                logger.info(f"Loading model: {self.model_name}")
                
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                # Check if CUDA is available
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Using device: {device}")
                
                # Load tokenizer and model
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    device_map="auto" if device == "cuda" else None,
                    low_cpu_mem_usage=True
                )
                
                if device == "cpu":
                    self.model = self.model.to(device)
                
                # Add padding token if it doesn't exist
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                self.is_initialized = True
                logger.info("Local AI model initialized successfully!")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize local AI model: {e}")
                self.model = None
                self.tokenizer = None
                self.is_initialized = False
                return False
    
    def generate_response(self, message: str, character: str = "Blayzo", context: str = "") -> Dict[str, Any]:
        """Generate AI response using local model"""
        start_time = time.time()
        
        try:
            # Initialize model if needed
            if not self.initialize():
                return {
                    "success": False,
                    "response": f"Hello! I'm {character}, your AI companion. I'm currently loading my local AI system. Please try again in a moment!",
                    "error": "Model initialization failed",
                    "response_time": time.time() - start_time
                }
            
            # Clean up memory periodically
            if time.time() - self.last_cleanup > 3600:  # Every hour
                self._cleanup_memory()
            
            # Format the input for DialoGPT (it works better with direct conversation format)
            # DialoGPT is trained on conversational data, so we keep it simple
            input_text = f"Human: {message}\nAI:"
            
            # Tokenize input
            inputs = self.tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
            
            if inputs.shape[1] == 0:
                raise ValueError("Empty input after tokenization")
            
            # Move to same device as model
            if hasattr(self.model, 'device'):
                inputs = inputs.to(self.model.device)
            
            # Import torch at runtime to ensure it's available
            import torch
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=self.max_length,
                    temperature=self.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    attention_mask=torch.ones_like(inputs),
                    repetition_penalty=1.1,
                    length_penalty=1.0,
                    early_stopping=True
                )
            
            # Decode response
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the AI's response (after "AI:")
            if "AI:" in generated_text:
                response = generated_text.split("AI:")[-1].strip()
            else:
                response = generated_text[len(input_text):].strip()
            
            # Clean up the response
            response = self._clean_response(response, character)
            
            # Update performance tracking
            response_time = time.time() - start_time
            self.request_count += 1
            self.total_response_time += response_time
            
            logger.info(f"Local AI response generated in {response_time:.2f}s")
            
            return {
                "success": True,
                "response": response,
                "model": self.model_name,
                "response_time": response_time,
                "character": character
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Local AI generation error: {e}")
            
            # Provide graceful fallback
            fallback_responses = [
                f"Hello! I'm {character}, your AI companion. I understand you said something about '{message[:50]}...'. I'm here to help and support you!",
                f"Hi there! I'm {character} from SoulBridge AI. I'm experiencing some technical difficulties, but I'm still here to chat with you!",
                f"Hey! {character} here. I'm having a moment of digital contemplation, but I'm ready to listen and help however I can!"
            ]
            
            import random
            fallback_response = random.choice(fallback_responses)
            
            return {
                "success": False,
                "response": fallback_response,
                "error": str(e),
                "response_time": response_time,
                "character": character,
                "fallback": True
            }
    
    def _clean_response(self, response: str, character: str) -> str:
        """Clean and format the AI response"""
        if not response:
            return f"Hello! I'm {character}, and I'm here to help you today. What's on your mind?"
        
        # Remove redundant character names and prompts
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip lines that look like prompts or system messages
            if line.startswith(('User:', 'System:', 'Human:', character + ':')):
                continue
                
            # Remove character name from beginning if it's there
            if line.startswith(character):
                line = line[len(character):].lstrip(':').strip()
            
            # Skip empty or very short lines
            if len(line) > 3:
                cleaned_lines.append(line)
        
        # Join lines and truncate if too long
        cleaned_response = ' '.join(cleaned_lines)
        
        if len(cleaned_response) > 300:
            cleaned_response = cleaned_response[:297] + "..."
        
        # Ensure we have a response
        if not cleaned_response or len(cleaned_response) < 10:
            cleaned_response = f"I'm {character}, and I'm here to support you! How can I help you today?"
        
        return cleaned_response
    
    def _cleanup_memory(self):
        """Clean up memory and cache"""
        try:
            import torch
            import gc
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            gc.collect()
            self.last_cleanup = time.time()
            logger.info("Memory cleanup completed")
            
        except Exception as e:
            logger.warning(f"Memory cleanup failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_response_time = (self.total_response_time / self.request_count) if self.request_count > 0 else 0
        
        return {
            "model_name": self.model_name,
            "is_initialized": self.is_initialized,
            "request_count": self.request_count,
            "avg_response_time": avg_response_time,
            "last_cleanup": datetime.fromtimestamp(self.last_cleanup).isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the local AI service is healthy"""
        try:
            if not self.is_initialized:
                return {"status": "not_initialized", "healthy": False}
            
            # Quick test generation
            test_response = self.generate_response("Hello", "TestBot")
            
            return {
                "status": "healthy" if test_response["success"] else "degraded",
                "healthy": test_response["success"],
                "response_time": test_response.get("response_time", 0),
                "last_test": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
                "last_test": datetime.now().isoformat()
            }


# Global instance
_local_ai_instance = None
_instance_lock = threading.Lock()

def get_local_ai_service() -> LocalAIService:
    """Get the global LocalAI service instance (singleton)"""
    global _local_ai_instance
    
    with _instance_lock:
        if _local_ai_instance is None:
            _local_ai_instance = LocalAIService()
        return _local_ai_instance


# Quick test function
if __name__ == "__main__":
    # Test the local AI service
    print("Testing Local AI Service...")
    
    ai_service = get_local_ai_service()
    
    # Test response generation
    test_message = "Hello, I'm feeling a bit stressed today."
    result = ai_service.generate_response(test_message, "Blayzo")
    
    print(f"Test Result:")
    print(f"Success: {result['success']}")
    print(f"Response: {result['response']}")
    print(f"Time: {result['response_time']:.2f}s")
    
    if not result['success']:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Show stats
    stats = ai_service.get_stats()
    print(f"Stats: {stats}")