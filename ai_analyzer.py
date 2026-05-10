"""
AI-powered analysis module using Google Gemini API
"""
import google.generativeai as genai
from typing import Dict, List, Optional
import json
import config


class AIAnalyzer:
    """Uses Gemini AI for intelligent frame analysis and object detection"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.GEMINI_API_KEY
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
        
        self.generation_config = {
            "temperature": config.GEMINI_TEMPERATURE,
            "max_output_tokens": config.GEMINI_MAX_TOKENS,
        }
    
    def analyze_frame(self, frame_description: str, telemetry: Dict) -> Dict:
        """Analyze frame using AI to extract detailed insights"""
        prompt = f"""
You are a security analyst AI analyzing drone surveillance footage.

Frame Description: {frame_description}
Location: {telemetry.get('location', 'unknown')}
Timestamp: {telemetry.get('timestamp', 'unknown')}
Altitude: {telemetry.get('altitude', 0)}m

Extract and return a JSON object with:
1. "objects_detected": List of objects with type, description, and confidence
2. "activity_type": Classification (normal/suspicious/alert)
3. "security_level": Risk level (low/medium/high/critical)
4. "detailed_analysis": Brief security assessment
5. "recommendations": List of recommended actions

Return ONLY valid JSON, no markdown or explanation.
"""
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            result = self._parse_json_response(response.text)
            return result
        except Exception as e:
            # Fallback to rule-based analysis
            return self._fallback_analysis(frame_description, telemetry)
    
    def detect_objects(self, description: str) -> List[Dict]:
        """Extract objects from frame description using AI"""
        prompt = f"""
Analyze this security camera description and extract all objects:
"{description}"

Return a JSON array of objects, each with:
- "type": object type (person/vehicle/animal/other)
- "details": specific details (color, model, actions)
- "confidence": confidence score (0-1)

Return ONLY valid JSON array, no markdown.
"""
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            objects = self._parse_json_response(response.text)
            return objects if isinstance(objects, list) else []
        except:
            return []
    
    def generate_alert_description(self, frame_data: Dict, alert_type: str) -> str:
        """Generate human-readable alert description using AI"""
        prompt = f"""
Generate a concise security alert message.

Alert Type: {alert_type}
Frame Description: {frame_data.get('description', '')}
Location: {frame_data.get('location', 'unknown')}
Time: {frame_data.get('timestamp', 'unknown')}

Create a single-sentence alert that security personnel can quickly understand.
Return only the alert message, no explanation.
"""
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text.strip()
        except:
            return f"{alert_type.replace('_', ' ').title()} detected at {frame_data.get('location', 'unknown')}"
    
    def summarize_video_session(self, frames: List[Dict]) -> str:
        """Generate summary of entire video session"""
        if not frames:
            return "No frames processed."
        
        summary_data = {
            "total_frames": len(frames),
            "time_span": f"{frames[0]['timestamp']} to {frames[-1]['timestamp']}",
            "sample_descriptions": [f['description'] for f in frames[:5]]
        }
        
        prompt = f"""
Summarize this drone security monitoring session:

Total Frames: {summary_data['total_frames']}
Time Period: {summary_data['time_span']}
Sample Events: {', '.join(summary_data['sample_descriptions'])}

Provide a 2-3 sentence executive summary highlighting key activities and any security concerns.
"""
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text.strip()
        except:
            return f"Processed {len(frames)} frames from {summary_data['time_span']}"
    
    def answer_query(self, query: str, context: List[Dict]) -> str:
        """Answer questions about the surveillance data"""
        context_summary = "\n".join([
            f"Frame {i+1}: {frame.get('description', '')}"
            for i, frame in enumerate(context[:10])
        ])
        
        prompt = f"""
You are analyzing drone security footage. Answer this question based on the context:

Question: {query}

Context (recent frames):
{context_summary}

Provide a concise, factual answer.
"""
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text.strip()
        except Exception as e:
            return f"Unable to answer query: {str(e)}"
    
    def _parse_json_response(self, text: str) -> Dict:
        """Parse JSON from AI response, handling markdown formatting"""
        # Remove markdown code blocks if present
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text.strip())
    
    def _fallback_analysis(self, description: str, telemetry: Dict) -> Dict:
        """Rule-based fallback when AI fails"""
        description_lower = description.lower()
        
        # Determine activity type
        if any(word in description_lower for word in ["loitering", "running", "suspicious", "unusual"]):
            activity_type = "suspicious"
            security_level = "high"
        elif any(word in description_lower for word in ["gathering", "circling", "carrying"]):
            activity_type = "alert"
            security_level = "medium"
        else:
            activity_type = "normal"
            security_level = "low"
        
        return {
            "objects_detected": [],
            "activity_type": activity_type,
            "security_level": security_level,
            "detailed_analysis": f"Detected: {description}",
            "recommendations": ["Monitor situation"] if security_level != "low" else []
        }