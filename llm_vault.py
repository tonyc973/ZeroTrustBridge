import json
import uuid
import re
from datetime import datetime

class LLMVault:
    def __init__(self, local_client, model_name="mistral"):
        self.client = local_client
        self.model = model_name
        self._secret_map = {}   # Real -> Alias
        self._reverse_map = {}  # Alias -> Real
        
        # 1. REGEX PATTERNS (The Fast Layer)
        # Catches obvious rigid formats instantly.
        self.regex_patterns = {
            "IP": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "API_KEY": r'(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16})',
        }

    def _get_alias(self, real_value, label="SECRET"):
        if real_value not in self._secret_map:
            token_id = str(uuid.uuid4())[:4]
            alias = f"<{label}_{token_id}>"
            self._secret_map[real_value] = alias
            self._reverse_map[alias] = real_value
        return self._secret_map[real_value]

    def _scan_llm(self, text):
        """Uses the Local LLM to find semantic secrets (Project names, etc)."""
        system_prompt = """
        You are a Data Loss Prevention system.
        Extract ALL confidential information from the text.
        
        Target:
        1. Internal Project Names (e.g. 'Project Obsidian', 'Falcon-9', 'Titan-DB')
        2. Names of People
        3. Passwords or Hashes
        
        Output ONLY a JSON object: {"secrets": ["string1", "string2"]}
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("secrets", [])
        except Exception:
            return []

    def encrypt(self, text):
        sanitized_text = text
        found_secrets = set()

        # PHASE 1: REGEX (Fast & Deterministic)
        for label, pattern in self.regex_patterns.items():
            matches = re.findall(pattern, text)
            for m in matches:
                # Store the secret and the specific label (IP, EMAIL)
                found_secrets.add((m, label))

        # PHASE 2: LLM (Smart & Contextual)
        llm_findings = self._scan_llm(text)
        for s in llm_findings:
            if isinstance(s, str) and len(s) > 2:
                found_secrets.add((s, "SECRET"))

        # PHASE 3: REPLACE
        # Sort by length (descending) to avoid partial replacement issues
        # e.g. replacing "Project X" before "Project X V2"
        sorted_secrets = sorted(list(found_secrets), key=lambda x: len(x[0]), reverse=True)

        for secret, label in sorted_secrets:
            # Skip common false positives
            if secret.lower() in ["the", "error", "connect", "fail", "true", "false"]: continue
            
            alias = self._get_alias(secret, label)
            sanitized_text = sanitized_text.replace(secret, alias)
            
        return sanitized_text

    def decrypt(self, text):
        restored_text = text
        for alias, real_value in self._reverse_map.items():
            restored_text = restored_text.replace(alias, real_value)
        return restored_text