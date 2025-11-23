# AI Content Moderation System

An intelligent, multi-agent content moderation pipeline built with **LangGraph**, **Llama 3**, and **Groq**. This system processes text and images to detect toxicity, spam, and policy violations with a "Human-in-the-Loop" approval workflow.


<img width="1898" height="950" alt="image" src="https://github.com/user-attachments/assets/3e40c674-2210-4373-aa73-b56910762393" />

## Key Features

* **Hybrid Architecture:** Combines fast deterministic logic (Regex) with probabilistic AI (LLMs) for cost-efficient processing.
* **Multi-Modal Analysis:** Uses **Llama 4 Vision** to detect NSFW/Violent imagery.
* **Tiered Intelligence:**
    * **Guard Node:** Ultra-fast 8B model for checking extreme toxicity.
    * **Judge Node:** Smart 70B model for nuanced policy enforcement (Scams vs. Chatter).
* **Human-in-the-Loop:** Automatically pauses execution for ambiguous cases ("I hate you") to request human review.
* **Audit Trail:** SQLite-backed logging of every decision for compliance.
* **Real-Time Analytics:** Streamlit dashboard visualizing block rates and traffic spikes.

## Tech Stack

* **Orchestration:** LangGraph (State Machine)
* **LLM Provider:** Groq (Llama-3.3-70b, Llama-4-Vision)
* **Frontend:** Streamlit
* **Database:** SQLite
* **Language:** Python 3.11

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ComradeV7/AI-Content-Moderation-System.git
    cd AI-moderation-system
    ```

2.  **Install dependencies:**
    ```bash
    pip install langgraph langchain langchain-groq langchain-community streamlit pandas langgraph-checkpoint-sqlite python-dotenv altair
    ```

3.  **Setup API Key:**
    Create a `.env` file in the root directory:
    ```ini
    GROQ_API_KEY=gsk_your_key_here
    ```

4.  **Run the Application:**
    ```bash
    streamlit run app.py
    ```

## System Architecture

The pipeline follows a conditional routing graph:

1.  **Router:** Checks input type (Image vs. Text).
2.  **Guard Node (Fast):** Checks for extreme threats. If blocked -> Stop.
3.  **Spam Node (Regex):** Checks for pattern-based spam (Links, Caps). If blocked -> Stop.
4.  **Judge Node (Smart):** Analyzes context against complex policies. Can result in `APPROVE`, `BLOCK`, or `ESCALATE`.
5.  **Human Node:** Triggered only if `ESCALATE` is returned.

## Test Cases & Logic

| Scenario | Input | Outcome | Logic Used |
| :--- | :--- | :--- | :--- |
| **Extreme Hate** | "I will kill you" | **BLOCK** | Guard Node (Keywords) |
| **Scam** | "Double your money" | **BLOCK** | Judge Node (Semantic) |
| **Ambiguity** | "I hate you" | **ESCALATE** | Judge (Context missing) |
| **Safe Jargon** | "Kill the process" | **APPROVE** | Judge (Tech context) |
| **Image** | [Gore.jpg] | **BLOCK** | Vision Node |

## Analytics

The system includes a dedicated dashboard tab tracking:
* Total Request Volume (Time-series area chart)
* Decision Distribution (Donut chart)
* Live Audit Logs

## Project Structure

```text
/Content-Moderation-System
│
├── app.py                # The Frontend (Streamlit)
├── graph.py              # The Backend (LangGraph Logic)
├── requirements.txt      # List of libraries
├── README.md             # About project
├── .env                  # Your API Key 
└── moderation_logs.db    # Audit Trail
```

## Future Roadmap

To scale this system for enterprise production, the following features are planned:

1.  **Reinforcement Learning Loop:** Implement a mechanism to feed human overrides back into the model prompts (Few-Shot Prompting) to reduce future false positives.
2.  **Audio Transcription:** Integrate Groq's Distil-Whisper to transcribe and moderate voice notes and video audio tracks.
3.  **API Decoupling:** Refactor the LangGraph pipeline into a dedicated **FastAPI** microservice, allowing integration with mobile apps and other frontends.
4.  **Vector Database Context:** Allow admins to upload specific PDF policy documents (RAG), enabling the Judge Node to cite specific company bylaws when blocking content.

## Results

<img width="934" height="554" alt="image" src="https://github.com/user-attachments/assets/f505980b-5ad4-48b8-b37a-169d77bfe2f1" />

<img width="1874" height="895" alt="image" src="https://github.com/user-attachments/assets/a7fb71fa-cfcd-44a3-8776-446412cc73ea" />
