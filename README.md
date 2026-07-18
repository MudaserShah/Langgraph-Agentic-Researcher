# 🧠 LangGraph Agentic Researcher

An autonomous AI research assistant built with **LangGraph** that performs multi-step research by planning tasks, gathering information, reasoning over collected data, and generating structured reports.

This project demonstrates how to build an **agentic AI system** capable of autonomous decision-making and iterative workflows instead of simple prompt-response interactions.

---

## ✨ Features

- 🤖 Autonomous AI research workflow
- 🧠 Multi-step reasoning with LangGraph
- 🔍 Web search and information gathering
- 📄 Automatic report generation
- 🔁 Stateful graph execution
- 📚 Modular agent architecture
- ⚡ Extensible workflow design
- 🔒 Environment variable support

---

## 🏗️ Project Architecture

```text
                 User Query
                      │
                      ▼
             Research Planner Agent
                      │
                      ▼
              Web Search Agent
                      │
                      ▼
             Information Analyzer
                      │
                      ▼
             Report Generator Agent
                      │
                      ▼
                Final Response
```

---

## 🛠️ Tech Stack

- Python 3.11+
- LangGraph
- LangChain
- OpenAI GPT Models
- Tavily Search API
- Pydantic
- python-dotenv

---

## 📂 Project Structure

```text
Langgraph-Agentic-Researcher/
│
├── app/
│   ├── agents/
│   ├── graphs/
│   ├── tools/
│   ├── prompts/
│   ├── utils/
│   └── main.py
│
├── frontend-next/
│
├── .env.example
├── requirements.txt
├── README.md
└── LICENSE
```

---

## 🚀 Installation

Clone the repository

```bash
git clone https://github.com/MudaserShah/Langgraph-Agentic-Researcher.git

cd Langgraph-Agentic-Researcher
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate the environment

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

---

## ▶️ Run the Project

```bash
python app/main.py
```

or

```bash
python main.py
```

(depending on your project structure)

---

## 💡 Example

### Input

```text
Research the future of AI Agents in Healthcare.
```

### Output

```text
✔ Research Plan

✔ Information Collected

✔ Key Findings

✔ Summary

✔ References
```

---

## 📸 Screenshots

> Add screenshots of your application here.

```
assets/
    home.png
    workflow.png
```

---

## 🎯 Learning Objectives

This project demonstrates:

- Agentic AI Systems
- LangGraph Workflows
- State Management
- LLM Orchestration
- Tool Calling
- Multi-Step Reasoning
- Research Automation

---

## 📚 Future Improvements

- Memory Support
- RAG Integration
- Multi-Agent Collaboration
- PDF Report Export
- Streamlit Dashboard
- Next.js Frontend
- Human-in-the-loop Approval
- Citation Generation

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create your feature branch

```bash
git checkout -b feature/new-feature
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push the branch

```bash
git push origin feature/new-feature
```

5. Open a Pull Request

---

## ⭐ Support

If you found this project useful, please consider giving it a ⭐ on GitHub.

---

## 👨‍💻 Author

**Syed Mudaser Shah**

- GitHub: https://github.com/MudaserShah
- LinkedIn: *(Add your LinkedIn URL)*

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgements

- LangGraph
- LangChain
- OpenAI
- Tavily
- Python Community
