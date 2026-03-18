from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from langsmith import traceable
import re
class Guardrails:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        # Whitelist of terms that should NEVER be masked (ITSM & Specialist titles)
        self.allow_list = [
            "L1", "L2", "L3", "RCA", "Specialist", "Support", "Incident", "Technical",
            "P1", "P2", "P3", "P4", "Critical", "High", "Medium", "Low",
            "hours", "minutes", "days", "weeks", "months", "approx", "approximately"
        ]
        # Conversational time words are commonly detected as DATE_TIME by Presidio.
        # They are not user-identifying PII and should remain visible.
        self.safe_datetime_terms = {
            "today", "tomorrow", "yesterday", "now",
            "morning", "afternoon", "evening", "night",
        }
        self.safe_datetime_pattern = re.compile(
            r"^(this|today|tomorrow|yesterday|tonight)\s+(morning|afternoon|evening|night)$|^(today|tomorrow|yesterday|tonight)$",
            re.IGNORECASE
        )

    @traceable(run_type="tool", name="mask_pii_guardrail", project_name="IT-Incident-Assistant")
    def mask_pii(self, text: str) -> str:
        if not text:
            return text
        
        # Analyze for PII
        results = self.analyzer.analyze(text=text, language='en')
        
        # Filter results to ignore whitelisted terms and priority/duration patterns
        filtered_results = []
        for res in results:
            val = text[res.start:res.end].strip()
            val_lower = val.lower()

            # 0. Do not mask generic DATE_TIME terms/phrases
            # Examples: "today", "this morning", "tonight"
            if getattr(res, "entity_type", "") == "DATE_TIME":
                if val_lower in self.safe_datetime_terms:
                    continue
                if self.safe_datetime_pattern.match(val_lower):
                    continue
            
            # 1. Check direct whitelist
            if val_lower in [item.lower() for item in self.allow_list]:
                continue
                
            # 2. Check for priority patterns (e.g., P1, P2) or durations (e.g., 4 to 6 hours)
            # If the span contains a whitelisted word, it's likely a false positive duration or title
            if any(word.lower() in val_lower for word in self.allow_list):
                continue
                
            # 3. Specific check for priority codes at the start of a span
            if re.match(r'^[Pp][1-4](\b|$)', val):
                continue
                
            # 4. Whitelist Incident ID patterns (e.g., IM0024032, INC0024032)
            # These are essential for traceability and are NOT PII.
            if re.match(r'^(IM|INC)\d+(\b|$)', val):
                continue

            filtered_results.append(res)
        
        # Anonymize only the remaining PII
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=filtered_results,
            operators={"DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"})}
        )
        
        output_text = anonymized_result.text
        
        # 5. Apply partial masking to any remaining Incident IDs (Middle Ground)
        # Example: IM0024032 -> IM0024***
        def partial_mask_id(match):
            full_id = match.group(0)
            if len(full_id) > 5:
                return full_id[:-3] + "***"
            return full_id
            
        output_text = re.sub(r'\b(IM|INC)\d+\b', partial_mask_id, output_text)
        
        return output_text

guardrails = Guardrails()
