import json
import uuid
import re

class LLMVault:
    def __init__(self, local_client, model_name="mistral"):
        self.client = local_client
        self.model = model_name
        self._secret_map = {}   # Real -> Alias
        self._reverse_map = {}  # Alias -> Real

    def _get_alias(self, real_value):
        if real_value not in self._secret_map:
            token_id = str(uuid.uuid4())[:4]
            alias = f"<SECRET_{token_id}>"
            self._secret_map[real_value] = alias
            self._reverse_map[alias] = real_value
        return self._secret_map[real_value]

    def scan_for_secrets(self, text):
        """
        Uses the Local LLM to analyze text and extract sensitive substrings.
        """
        system_prompt = """
        You are a Data Loss Prevention (DLP) system.
        Analyze the user's text and extract ALL confidential information.
        
        Categories to detect:
        1. PII (Names, Emails, Phones)
        2. Infrastructure (IP addresses, Hostnames, Internal URLs)
        3. Secrets (API Keys, Tokens, Passwords)
        4. Internal Project Names (e.g. 'Project Obsidian', 'Falcon-9')

        Output ONLY a JSON object with a single key "secrets" containing a list of strings.
        Example: {"secrets": ["192.168.1.1", "sk-12345", "John Doe"]}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.0, # Deterministic behavior
                response_format={"type": "json_object"} # Forces valid JSON
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            return data.get("secrets", [])
            
        except Exception as e:
            print(f"⚠️ Vault Scan Error: {e}")
            return []

    def encrypt(self, text):
        """Scans and replaces secrets with placeholders."""
        print("   (Vault is scanning...)")
        secrets = self.scan_for_secrets(text)
        
        sanitized_text = text
        for secret in secrets:
            if not isinstance(secret, str) or len(secret) < 2: continue
            
            # Simple allowlist to prevent over-masking common words
            if secret.lower() in ["the", "error", "connect", "fail", "retry"]: continue
            
            alias = self._get_alias(secret)
            sanitized_text = sanitized_text.replace(secret, alias)
            
        return sanitized_text

    def decrypt(self, text):
        """Restores the real values."""
        restored_text = text
        for alias, real_value in self._reverse_map.items():
            restored_text = restored_text.replace(alias, real_value)
        return restored_text
