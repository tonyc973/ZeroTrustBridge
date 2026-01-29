from llm_factory import LLMFactory
from llm_vault import LLMVault

# --- CONFIGURATION ---
# 1. LOCAL: Used for Security Scanning (Mistral running on llama-server)
LOCAL_CLIENT = LLMFactory.create_client("local")

# 2. CLOUD: Used for Complex Reasoning (GPT-4o)
# Change this to "local" if you want to run everything offline!
CLOUD_CLIENT = LLMFactory.create_client("openai")

def main():
    # Initialize the Vault with the local client
    # Note: 'mistral' is just a label here, llama-server uses whatever model you loaded
    vault = LLMVault(LOCAL_CLIENT, model_name="mistral")

    print("\n🛡️  Zero-Trust Bridge v2 (No-Magic Edition) Initialized")
    print("-------------------------------------------------------")

    # SIMULATED INPUT
    user_input = """
    I'm debugging a legacy app.
    The database is at 10.50.22.19 (Project: 'Titan-DB').
    The admin user is 'admin_corp' and the hash is 'x88-99-aa-bb'.
    Write a Python script to connect to this.
    """

    print(f"\n📝 RAW INPUT:\n{user_input.strip()}")

    # 1. ENCRYPT (Local)
    safe_prompt = vault.encrypt(user_input)
    
    if safe_prompt != user_input:
        print(f"\n🔒 MASKED PROMPT (Sending to Cloud):\n{safe_prompt.strip()}")
    else:
        print("\n⚠️ No secrets detected.")

    # 2. REASON (Cloud)
    print("\n☁️  Sending to GPT-4o...")
    
    system_instructions = """
    You are a Senior Developer.
    You will receive code with placeholders like <SECRET_x>.
    Write working code using those EXACT placeholders.
    Do not ask for the real values.
    """

    try:
        response = CLOUD_CLIENT.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": safe_prompt}
            ],
            temperature=0.7
        )
        cloud_output = response.choices[0].message.content
    except Exception as e:
        print(f"❌ Cloud Error: {e}")
        return

    # 3. DECRYPT (Local)
    print("\n🔓 DECRYPTING RESPONSE...")
    final_output = vault.decrypt(cloud_output)

    print("\n✅ FINAL RESTORED CODE:")
    print("="*40)
    print(final_output)
    print("="*40)

if __name__ == "__main__":
    main()
