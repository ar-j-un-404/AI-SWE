AI Software Engineer
An AI-powered software engineering agent that can analyze local codebases, retrieve relevant code, create implementation plans, generate and validate patches, modify real files, run tests, debug failures, review Git changes, create commits, and push updates to GitHub.

This is my first major AI project, focused on building a practical software engineering agent rather than a simple chatbot.

Overview
Traditional coding assistants mostly answer questions or generate isolated snippets. This project explores a more complete workflow where an AI system works with a real repository and follows a controlled engineering process.

The system can inspect a repository, understand relevant code, plan changes, generate patches, validate them, apply them to real files, test the result, debug failures, and work with Git.

Workflow
Engineering Task
      ↓
Repository Scan
      ↓
Code Parsing
      ↓
Semantic + Lexical Retrieval
      ↓
Implementation Planning
      ↓
Human Approval
      ↓
Patch Generation
      ↓
Patch Validation
      ↓
Apply Changes
      ↓
Run Tests
      ↓
AI Debugging
      ↓
Git Diff Review
      ↓
Commit
      ↓
Push to GitHub
Features
Scan local Python repositories

Parse functions, classes, imports, and module-level code using Python AST

Retrieve relevant code using semantic and lexical search

Generate structured implementation plans

Identify files to modify or create

Generate patch-based code changes

Validate patches before applying them

Reject invalid, duplicate, unauthorized, or placeholder file changes

Create backups before modifying files

Apply changes to real project files

Run safe terminating tests and syntax checks

Analyze failed tests with an AI debugger

Generate and apply repair patches after approval

Show Git status and Git diff

Create Git commits

Push commits to GitHub

Use multiple OpenRouter coding models

Fall back to local Ollama when cloud models are unavailable or rate-limited

Manage the workflow through a Streamlit interface

Repository Analysis
The repository scanner recursively discovers source files while ignoring directories such as:

.git

.venv

venv

__pycache__

node_modules

build directories

The parser uses Python AST to identify repository symbols and source structure.

Code Retrieval
The retrieval system combines:

semantic similarity

lexical matching

filename relevance

symbol relevance

task-specific relevance

Sentence Transformers are used to generate embeddings, helping the system send only relevant code to the language model.

Planning Agent
Before modifying any code, the planner returns a structured plan similar to:

{
  "summary": "Add authentication to the Streamlit application",
  "reasoning": "The main interface should only be available after successful login.",
  "files_to_modify": ["app.py"],
  "files_to_create": ["auth.py"],
  "steps": [
    "Create authentication logic",
    "Integrate authentication into the main application",
    "Add logout support"
  ],
  "risks": [
    "Incorrect Streamlit session state handling"
  ],
  "tests_to_run": [
    "python -m compileall ."
  ]
}
The user can review and approve the plan before code generation continues.

Patch-Based Editing
Instead of allowing the model to rewrite arbitrary files, the system uses patches.

Modify an existing file:

<PATCH>
<PATH>app.py</PATH>
<FIND>
existing code
</FIND>
<REPLACE>
updated code
</REPLACE>
</PATCH>
Create a new file:

<PATCH>
<PATH>auth.py</PATH>
<CONTENT>
complete file content
</CONTENT>
</PATCH>
Patch Validation
Generated patches can be rejected when:

a MODIFY target does not exist

a CREATE target already exists

the file was not authorized by the planner

a FIND block cannot be located

a FIND block matches multiple places

FIND and REPLACE are identical

the patch is empty

the model invents placeholder filenames

patch tags are malformed

This validation layer helps keep the model from modifying arbitrary files.

Safe File Editing
Before modifying an existing file, the system creates a backup. The editor supports:

file modification

file creation

directory creation

backups

rollback

Automated Testing
The executor can run safe terminating commands such as:

python -m py_compile app.py
python -m compileall .
Persistent commands such as streamlit run app.py are not treated as tests because they do not terminate automatically.

AI Debugger
When tests fail, the debugger receives the engineering task, test output, error output, and repository context. It can then:

analyze the failure

identify a likely root cause

generate repair patches

apply repairs after approval

re-run tests

Git and GitHub Integration
The system supports:

detecting Git repositories

Git status

Git diff

staging changes

commit creation

branch detection

remote detection

pushing the current branch to GitHub

The user can review the final diff before committing and pushing.

Model Fallbacks
The project supports multiple coding models through OpenRouter. If a model fails because of rate limits, empty responses, API errors, or timeouts, the system can try another model.

When cloud models are unavailable, the system can fall back to a local Ollama model.

Current local fallback:

qwen3:4b
Streamlit Interface
The interface provides controls for:

repository selection

repository scanning

engineering task input

relevant code inspection

plan generation

plan approval

patch generation

patch review

applying changes

running tests

debugging failures

Git review

rollback

commit creation

GitHub push

Project Structure
AI-SWE/
│
├── app.py
├── main.py
├── config.py
├── llm.py
├── requirements.txt
├── .gitignore
│
├── repository/
│   ├── scanner.py
│   └── parser.py
│
├── retrieval/
│   ├── chunking.py
│   ├── embeddings.py
│   └── retriever.py
│
├── agents/
│   ├── planner.py
│   ├── coder.py
│   └── debugger.py
│
├── tools/
│   ├── file_editor.py
│   ├── executor.py
│   └── git_tools.py
│
├── backups/
└── workspace/
Technologies Used
Python

Streamlit

Python AST

Sentence Transformers

Semantic Search

Lexical Search

Cosine Similarity

OpenRouter

Ollama

Qwen3

Git

GitHub

Installation
Clone the repository:

git clone https://github.com/ar-j-un-404/AI-SWE.git
cd AI-SWE
Create a virtual environment:

python -m venv .venv
Activate it on Windows:

.venv\Scripts\activate
Install dependencies:

python -m pip install -r requirements.txt
OpenRouter Setup
Create a .env file in the project root:

OPENROUTER_API_KEY=your_api_key_here
Do not commit .env.

Recommended .gitignore entries:

.env
.venv/
__pycache__/
Ollama Setup
Install Ollama and pull the local model:

ollama pull qwen3:4b
Test it with:

ollama run qwen3:4b
Run the Application
python -m streamlit run app.py
Then open the local Streamlit URL shown in the terminal.

Example Task
Add a login page to this Streamlit application.

Requirements:
- unauthenticated users should see the login page
- block the main application before login
- store authentication state using Streamlit session state
- add logout support
- preserve existing functionality
- do not add unnecessary dependencies
- run safe terminating tests
The system will analyze the repository, retrieve relevant code, create a plan, wait for approval, generate and validate patches, apply approved changes, run tests, debug failures if necessary, and show the final Git diff.

Reliability Problems Explored
Building this project involved handling issues that appear in real AI coding agents, including:

malformed JSON

Markdown surrounding structured output

invalid patches

hallucinated file paths

unauthorized modifications

duplicate file creation

incorrect FIND blocks

multiple matching code blocks

rate limits

daily API quotas

model timeouts

empty responses

local model performance

test execution safety

Streamlit state management

Safety Design
READ freely
PLAN freely
EDIT only after approval
RUN controlled commands
COMMIT only after approval
PUSH only after approval
The goal is to keep the user in control while still allowing the agent to perform meaningful engineering work.

Current Limitations
Mainly optimized for Python repositories

Patch generation still depends on LLM output quality

Local models can be slow on limited hardware

Retrieval can miss important dependencies

Runtime UI behavior is harder to verify than syntax

Complex multi-file refactoring is still experimental

GitHub authentication must already be configured locally

Planned Improvements
AST-aware editing

dependency graph analysis

package and import validation

automatic test discovery

stronger post-change verification

runtime error capture

better debugger retrieval

transactional file editing

safer rollback across repeated edits

repository dependency awareness

task history

agent memory

multi-step autonomous execution

automatic GitHub repository creation

automatic repository cloning

support for more programming languages

Why I Built This
I wanted to move beyond projects where an LLM only generates text. This project helped me explore how an AI agent can interact with real source code, repository structures, retrieval systems, validation layers, tests, debugging workflows, and version control.

The focus is not only code generation, but building a controlled software engineering workflow around the language model.

Status
Under active development.

Repository
https://github.com/ar-j-un-404/AI-SWE

Author
Arjun
B.Tech Computer Science and Engineering student exploring AI, machine learning, AI agents, RAG, software engineering, and developer tools.

