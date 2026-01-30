# 🛡️ Zero-Trust AI Bridge

> **Generative AI Security Layer CLI**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![OpenAI](https://img.shields.io/badge/OpenAI-API-green?style=for-the-badge&logo=openai)
![Llama.cpp](https://img.shields.io/badge/Backend-Llama.cpp-orange?style=for-the-badge)

**Zero-Trust Bridge** enables organizations to utilize state-of-the-art Cloud LLMs (GPT-4o, Claude 3.5) on highly sensitive data without ever exposing PII or trade secrets to the provider.

It implements a **Split-Plane Architecture**:
1.  **Local Control Plane:** A local Mistral 7B model scans inputs for semantic secrets (Project Names, PII, Keys).
2.  **Cloud Reasoning Plane:** The sanitized, tokenized request is processed by the superior reasoning model.
3.  **Local Re-Assembly:** The bridge intercepts the response and cryptographically restores the secrets.

---

## 🏗 System Architecture

The system uses a "Masquerade" pattern to decouple semantic understanding from logical reasoning.

```mermaid
graph LR
    subgraph Local Machine
        direction TB
        User[User Input]
        Vault["Vault LLM (Mistral 7B)"]
        Glossary[("Secret Map")]
    end

    subgraph Cloud["☁️ Untrusted Public Cloud"]
        GPT["Reasoning Model (GPT-4o)"]
    end

    User -->|1. Raw Data| Vault
    Vault -->|2. Extract Secrets| Glossary
    Vault -->|3. Masked Prompt| GPT
    GPT -->|4. Logic Solution| Vault
    Vault <-->|5. Restore Values| Glossary
    Vault -->|6. Safe Output| User

    style Vault fill:#d5f5e3,stroke:#2ecc71
    style GPT fill:#fadbd8,stroke:#e74c3c


```


## 🛠️ Quick Start

### 1. Prerequisites
* Python 3.10+
* `llama-server` (from [llama.cpp](https://github.com/ggerganov/llama.cpp))
* A GGUF Model (e.g., Mistral-7B-Instruct-v0.3)

### 2. Start the Local Security Guard and create .env file
This runs the local model that scans for secrets. You must keep this terminal window open.
```bash
/path/to/llama-server -m Mistral-7B-Instruct.gguf --port 8080 -c 4096

# OPENAI_API_KEY=sk-your-key-here in your root file .env
```

### 3. Run 
```bash
pip install -r requirements.txt
python bridge.py
```


