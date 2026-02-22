# agents/diagnosis_agent/llm_fallback.py

import os
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()


class LLMDiagnosticFallback:
    """
    LLM-powered diagnostic fallback using Groq API.
    Activates when rule-based diagnosis fails or has low confidence.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile" 
        
        if not self.api_key:
            print("[LLM] Warning: GROQ_API_KEY not set. LLM fallback disabled.")
            self.enabled = False
        else:
            self.enabled = True
            print("[LLM] LLM diagnostic fallback enabled with Groq")
    
    def should_use_llm(self, diagnoses: List[Dict], alert: Dict) -> bool:
        """
        Determine if LLM fallback should be used.
        
        Triggers when:
        - No diagnoses found
        - All diagnoses have low confidence (<0.6)
        - Alert type is unknown/complex
        - Multiple conflicting diagnoses
        """
        if not self.enabled:
            return False
        
        # Case 1: No diagnoses at all
        if not diagnoses:
            print("[LLM] Trigger: No diagnoses found")
            return True
        
        # Case 2: All low confidence
        max_confidence = max([d.get("confidence", 0) for d in diagnoses])
        if max_confidence < 0.6:
            print(f"[LLM] Trigger: Low confidence (max: {max_confidence:.2f})")
            return True
        
        # Case 3: Too many conflicting diagnoses with similar confidence
        if len(diagnoses) >= 3:
            confidences = [d.get("confidence", 0) for d in diagnoses[:3]]
            if max(confidences) - min(confidences) < 0.15:
                print("[LLM] Trigger: Conflicting diagnoses")
                return True
        
        # Case 4: Unknown alert type
        alert_type = alert.get("type", "")
        if alert_type in ["unknown", "anomaly", "unexpected"]:
            print("[LLM] Trigger: Unknown alert type")
            return True
        
        return False
    
    def diagnose_with_llm(self, 
                         alert: Dict, 
                         existing_diagnoses: List[Dict],
                         recent_alerts: List[Dict] = None,
                         metrics: List[Dict] = None,
                         logs: List[Dict] = None) -> Optional[Dict]:
        """
        Use LLM to diagnose the issue when rule-based system fails.
        
        Args:
            alert: The current alert
            existing_diagnoses: Previous diagnosis attempts
            recent_alerts: Recent alerts for context
            metrics: Recent metrics data
            logs: Recent log entries
            
        Returns:
            LLM-generated diagnosis or None if failed
        """
        if not self.enabled:
            return None
        
        print(f"[LLM] Consulting LLM for diagnosis...")
        
        # Build context for LLM
        context = self._build_context(
            alert, 
            existing_diagnoses, 
            recent_alerts, 
            metrics, 
            logs
        )
        
        # Create prompt
        prompt = self._create_diagnosis_prompt(context)
        
        # Call Groq API
        try:
            response = self._call_groq_api(prompt)
            
            if response:
                # Parse LLM response
                diagnosis = self._parse_llm_response(response, alert)
                print(f"[LLM] Diagnosis received: {diagnosis.get('root_cause')}")
                return diagnosis
            
        except Exception as e:
            print(f"[LLM] Error during LLM diagnosis: {e}")
            return None
    
    def _build_context(self, 
                      alert: Dict,
                      existing_diagnoses: List[Dict],
                      recent_alerts: List[Dict],
                      metrics: List[Dict],
                      logs: List[Dict]) -> Dict:
        """Build comprehensive context for LLM."""
        
        context = {
            "current_alert": alert,
            "timestamp": alert.get("timestamp"),
            "service": alert.get("service"),
            "alert_type": alert.get("type"),
        }
        
        # Add existing diagnosis attempts
        if existing_diagnoses:
            context["previous_diagnoses"] = [
                {
                    "root_cause": d.get("root_cause"),
                    "confidence": d.get("confidence"),
                    "category": d.get("category"),
                    "evidence": d.get("evidence", [])[:3]  # Top 3 pieces
                }
                for d in existing_diagnoses[:3]
            ]
        
        # Add recent alerts (last 5)
        if recent_alerts:
            context["recent_alerts"] = [
                {
                    "service": a.get("service"),
                    "type": a.get("type"),
                    "timestamp": a.get("timestamp")
                }
                for a in recent_alerts[-5:]
            ]
        
        # Add relevant metrics (last 5)
        if metrics:
            context["recent_metrics"] = [
                {
                    "service": m.get("service"),
                    "metric": m.get("metric"),
                    "value": m.get("value"),
                    "timestamp": m.get("timestamp")
                }
                for m in metrics[-5:]
            ]
        
        # Add relevant logs (last 3)
        if logs:
            context["recent_logs"] = [
                {
                    "message": log.get("message", "")[:200],  # Truncate
                    "timestamp": log.get("timestamp")
                }
                for log in logs[-3:]
            ]
        
        return context
    
    def _create_diagnosis_prompt(self, context: Dict) -> str:
        """Create a structured prompt for the LLM."""
        
        alert = context["current_alert"]
        
        prompt = f"""You are an expert DevOps diagnostic AI analyzing a production system alert.

CURRENT ALERT:
- Service: {alert.get('service')}
- Type: {alert.get('type')}
- Timestamp: {alert.get('timestamp')}
- Message: {alert.get('message', 'N/A')}
"""
        
        # Add metric info if available
        if alert.get('metric'):
            prompt += f"- Metric: {alert.get('metric')} = {alert.get('value')}"
            if alert.get('zscore'):
                prompt += f" (z-score: {alert.get('zscore'):.2f})"
            prompt += "\n"
        
        # Add previous diagnosis attempts
        if context.get('previous_diagnoses'):
            prompt += "\nPREVIOUS DIAGNOSIS ATTEMPTS (low confidence):\n"
            for i, diag in enumerate(context['previous_diagnoses'], 1):
                prompt += f"{i}. Root Cause: {diag['root_cause']} "
                prompt += f"(confidence: {diag['confidence']:.2f})\n"
                if diag.get('evidence'):
                    prompt += f"   Evidence: {', '.join(diag['evidence'][:2])}\n"
        
        # Add recent context
        if context.get('recent_alerts'):
            prompt += "\nRECENT ALERTS:\n"
            for alert_item in context['recent_alerts']:
                prompt += f"- {alert_item['service']}: {alert_item['type']} at {alert_item['timestamp']}\n"
        
        if context.get('recent_metrics'):
            prompt += "\nRECENT METRICS:\n"
            for metric in context['recent_metrics'][:3]:
                prompt += f"- {metric['service']}.{metric['metric']}: {metric['value']}\n"
        
        if context.get('recent_logs'):
            prompt += "\nRECENT LOGS:\n"
            for log in context['recent_logs']:
                prompt += f"- {log['message'][:150]}...\n"
        
        prompt += """
TASK:
Analyze this alert and provide a diagnostic assessment. Consider:
1. What is the most likely root cause?
2. Is this a direct service failure or a dependency issue?
3. What evidence supports your diagnosis?
4. What remediation actions would you recommend?
5. What is your confidence level (0.0-1.0)?

Respond ONLY with a JSON object in this exact format:
{
  "root_cause": "service_name",
  "category": "service_degradation|dependency_failure|cascading_failure|resource_exhaustion|configuration_error",
  "confidence": 0.85,
  "reasoning": "Brief explanation of your diagnosis",
  "evidence": ["evidence point 1", "evidence point 2"],
  "recommended_actions": [
    {"action": "action_name", "risk": "low|medium|high", "description": "what this does"}
  ],
  "additional_checks": ["what else to investigate"]
}

Think step by step, but respond with ONLY the JSON object, no other text.
"""
        
        return prompt
    
    def _call_groq_api(self, prompt: str) -> Optional[str]:
        """Call Groq API with the diagnosis prompt."""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert DevOps diagnostic AI. You analyze system alerts and provide structured diagnoses in JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Lower temperature for more deterministic output
            "max_tokens": 1000,
            "response_format": {"type": "json_object"}  # Force JSON response
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            return content
            
        except requests.exceptions.RequestException as e:
            print(f"[LLM] API request failed: {e}")
            return None
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"[LLM] Failed to parse API response: {e}")
            return None
    
    def _parse_llm_response(self, response: str, alert: Dict) -> Dict:
        """Parse LLM JSON response into diagnosis format."""
        
        try:
            llm_diagnosis = json.loads(response)
            
            # Ensure all required fields exist
            diagnosis = {
                "root_cause": llm_diagnosis.get("root_cause", "unknown"),
                "category": llm_diagnosis.get("category", "unknown"),
                "confidence": float(llm_diagnosis.get("confidence", 0.7)),
                "source": "llm_fallback",
                "model": self.model,
                "evidence": llm_diagnosis.get("evidence", []),
                "recommended_actions": llm_diagnosis.get("recommended_actions", []),
                "reasoning": llm_diagnosis.get("reasoning", ""),
                "additional_checks": llm_diagnosis.get("additional_checks", []),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Ensure actions have proper format
            if not diagnosis["recommended_actions"]:
                diagnosis["recommended_actions"] = [{
                    "action": f"investigate_{diagnosis['root_cause']}",
                    "risk": "low",
                    "description": f"Manual investigation of {diagnosis['root_cause']}"
                }]
            
            return diagnosis
            
        except json.JSONDecodeError as e:
            print(f"[LLM] Failed to parse LLM response as JSON: {e}")
            
            # Fallback: create basic diagnosis
            return {
                "root_cause": alert.get("service", "unknown"),
                "category": "unknown",
                "confidence": 0.5,
                "source": "llm_fallback_error",
                "evidence": ["LLM analysis failed to parse"],
                "recommended_actions": [{
                    "action": "manual_investigation",
                    "risk": "low",
                    "description": "Requires manual investigation"
                }],
                "reasoning": "LLM response could not be parsed",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_explanation(self, diagnosis: Dict, alert: Dict) -> str:
        """
        Get a human-readable explanation of the diagnosis from LLM.
        Useful for logging and notifications.
        """
        if not self.enabled:
            return "LLM explanations disabled"
        
        prompt = f"""Explain this diagnosis in 2-3 sentences for a DevOps engineer:

Alert: {alert.get('service')} - {alert.get('type')}
Root Cause: {diagnosis.get('root_cause')}
Confidence: {diagnosis.get('confidence')}
Evidence: {', '.join(diagnosis.get('evidence', []))}

Provide a clear, actionable explanation."""

        try:
            response = self._call_groq_api(prompt)
            if response:
                data = json.loads(response)
                return data.get("explanation", "No explanation available")
        except:
            pass
        
        return f"The system identified {diagnosis['root_cause']} as the likely root cause."


# Global instance
llm_fallback = LLMDiagnosticFallback()


# Convenience function
def diagnose_with_llm(alert: Dict, 
                     existing_diagnoses: List[Dict],
                     **kwargs) -> Optional[Dict]:
    """
    Quick access to LLM diagnosis.
    
    Usage:
        diagnosis = diagnose_with_llm(alert, existing_diagnoses)
    """
    return llm_fallback.diagnose_with_llm(alert, existing_diagnoses, **kwargs)