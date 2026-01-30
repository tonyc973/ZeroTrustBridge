import sys
import logging
from datetime import datetime
from llm_factory import LLMFactory
from llm_vault import LLMVault

# --- SETUP LOGGING ---
logging.basicConfig(
    filename='audit.log', 
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def log_event(event_type, content):
    """Writes to audit.log without printing to screen"""
    logging.info(f"[{event_type}] {content}")

def main():
    # 1. INIT
    print("🔌 Connecting to Local Guard (Mistral)...")
    try:
        local_client = LLMFactory.create_client("local")
        # Quick health check
        local_client.models.list()
    except Exception:
        print("❌ Error: Could not connect to llama-server at http://localhost:8080/v1")
        print("   Did you run: ./llama-server -m model.gguf --port 8080?")
        sys.exit(1)

    print("🔌 Connecting to Cloud Brain (OpenAI)...")
    cloud_client = LLMFactory.create_client("openai")

    vault = LLMVault(local_client)

    print("\n" + "="*50)
    print("🛡️  ZERO-TRUST BRIDGE v2.1 (INTERACTIVE)")
    print("   Type 'exit' or 'quit' to stop.")
    print("="*50 + "\n")

    system_instructions = """
    You are a Senior Developer.
    You will receive code with placeholders like <SECRET_x> or <IP_y>.
    Write working code using those EXACT placeholders.
    Do NOT ask for real values.
    """

    # 2. CHAT LOOP
    while True:
        try:
            user_input = input("👤 YOU: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            if not user_input.strip():
                continue

            # Log Raw Input (In a real app, you might NOT log this to be safe, 
            # but for this demo, we log it to prove it works)
            log_event("RAW_INPUT", user_input)

            # A. ENCRYPT
            print("   🔒 Scanning...", end="\r")
            safe_prompt = vault.encrypt(user_input)
            
            if safe_prompt != user_input:
                print(f"   🔒 Secured: {safe_prompt}")
                log_event("MASKED_PROMPT", safe_prompt)
            else:
                log_event("MASKED_PROMPT", "No secrets detected")

            # B. CLOUD
            print("   ☁️  Thinking...", end="\r")
            response = cloud_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": safe_prompt}
                ],
                temperature=0.7
            )
            cloud_output = response.choices[0].message.content
            log_event("CLOUD_RESPONSE", cloud_output)

            # C. DECRYPT
            final_output = vault.decrypt(cloud_output)
            log_event("DECRYPTED_OUTPUT", final_output)

            print(f"🤖 AI: {final_output}\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

    print("\n👋 Session Closed. Audit log saved to 'audit.log'.")

if __name__ == "__main__":
    main()