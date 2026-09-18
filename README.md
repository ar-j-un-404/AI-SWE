# AI Software Engineer

An AI-powered software engineering agent that can analyze local codebases, understand relevant files, generate implementation plans, create and validate code patches, modify real project files, run tests, debug failures, review Git changes, create commits, and push updates to GitHub.

This is my first major AI project focused on building a practical software engineering agent rather than a simple chatbot.

## Overview

Traditional coding assistants mostly answer questions or generate isolated code snippets.

This project explores a different approach: an AI system that can work with an actual software repository and follow a structured software engineering workflow.

The system can inspect a repository, retrieve relevant code, create a plan, generate changes, validate them, apply them to real files, test the result, debug failures, and work with Git.

The workflow is designed to keep the human in control before important changes are applied.

## Current Workflow

Engineering Task  
→ Repository Scan  
→ Code Parsing  
→ Semantic + Lexical Retrieval  
→ Implementation Planning  
→ Human Approval  
→ Patch Generation  
→ Patch Validation  
→ Apply Changes  
→ Run Tests  
→ AI Debugging  
→ Git Diff Review  
→ Commit  
→ Push to GitHub  

## What the System Can Do

### Repository Analysis

- Scan a local Python repository
- Recursively discover source files
- Ignore unnecessary directories such as `.git`, `.venv`, `venv`, `__pycache__`, `node_modules`, and build directories
- Read source code
- Build repository context for AI agents

### Python Code Understanding

The project uses Python AST parsing to identify:

- Functions
- Classes
- Imports
- Module-level code
- Source locations
- Repository symbols

This gives the system more structure than treating the repository as plain text.

## Code Retrieval

The system retrieves code that is relevant to the engineering task using:

- Semantic similarity
- Lexical matching
- Filename relevance
- Symbol relevance
- Task-specific relevance

Sentence Transformers are used to create code embeddings.

This helps reduce the amount of repository code sent to the language model.

## Planning Agent

Before making changes, the planner creates a structured implementation plan containing:

- Summary
- Reasoning
- Files to modify
- Files to create
- Implementation steps
- Risks
- Tests to run

Example:

{
  "summary": "Add authentication to the Streamlit application",
  "reasoning": "The main interface should only be available after successful login.",
  "files_to_modify": [
    "app.py"
  ],
  "files_to_create": [
    "auth.py"
  ],
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

## Human Approval

The system does not immediately modify files after generating a plan.

The user can review:

- Implementation summary
- Reasoning
- Files to modify
- Files to create
- Implementation steps
- Risks
- Planned tests

The user explicitly approves the plan before code generation continues.

## Patch-Based Code Editing

Instead of allowing the model to rewrite arbitrary files, the system uses a patch-based editing protocol.

Example:

<PATCH>
<PATH>app.py</PATH>
<FIND>
existing code
</FIND>
<REPLACE>
updated code
</REPLACE>
</PATCH>

For new files:

<PATCH>
<PATH>auth.py</PATH>
<CONTENT>
complete file content
</CONTENT>
</PATCH>

This gives the application more control over what the language model is allowed to modify.

## Patch Validation

Generated patches are validated before they reach the file editor.

The system can reject patches when:

- The requested file does not exist for a MODIFY operation
- A CREATE patch targets an existing file
- The target path was not approved by the planner
- The FIND block cannot be found
- The FIND block matches multiple locations
- The replacement is identical to the original code
- The patch is empty
- The model generates placeholder filenames
- Malformed patch tags are returned

The coder can retry generation when the previous response is invalid.

## Safe File Editing

Before modifying an existing file, the system creates a backup.

The file editor supports:

- File modification
- New file creation
- Directory creation
- Backups
- Rollback

## Automated Testing

After changes are applied, the system can execute safe terminating test commands.

Examples:

python -m py_compile app.py

python -m compileall .

The executor avoids persistent commands such as:

streamlit run app.py

because those commands would not terminate automatically.

## AI Debugger

If tests fail, the AI debugger receives:

- The original engineering task
- Test command
- Standard output
- Error output
- Repository context

The debugger can then:

- Analyze the failure
- Identify a possible root cause
- Generate repair patches
- Apply fixes after approval
- Re-run tests

## Git Integration

The system includes Git tooling for repository review and version control.

Supported operations include:

- Checking whether the folder is a Git repository
- Git status
- Git diff
- Staging changes
- Creating commits
- Detecting the current branch
- Detecting configured remotes
- Pushing the current branch to GitHub

The user can review the Git diff before creating a commit.

## GitHub Push

After a successful commit, the system can push the current branch to the configured `origin` remote.

Workflow:

Tests Passed  
→ Git Diff  
→ Commit Approval  
→ Create Commit  
→ Push Approval  
→ Push to GitHub  

Git authentication must already be configured on the local machine.

## Multiple LLM Fallbacks

The project supports multiple coding models through OpenRouter.

If one model fails because of:

- Rate limits
- Empty responses
- API errors
- Timeouts

the system can try another model.

It also supports a local Ollama fallback.

Workflow:

OpenRouter Model  
→ OpenRouter Fallback  
→ Another Coding Model  
→ Local Ollama  

## Local Ollama Support

When cloud models are unavailable or the OpenRouter free quota is exhausted, the system can fall back to a local model.

Current local model:

qwen3:4b

Advantages of local fallback:

- Works without cloud model availability
- No provider request limits
- Code remains on the local machine
- Useful for development and experimentation

Local models may be slower depending on the available hardware.

## Streamlit Interface

The project includes a Streamlit interface for controlling the complete engineering workflow.

The interface includes:

- Repository path input
- Repository scanning
- Repository statistics
- Engineering task input
- Relevant code display
- Implementation plan
- Plan approval
- Generated patch review
- Patch approval
- File modification
- Test execution
- Test results
- AI debugging
- Git status
- Git diff
- Rollback
- Commit creation
- GitHub push

## Project Structure

AI-SWE/
├── app.py
├── main.py
├── config.py
├── llm.py
├── requirements.txt
├── .gitignore
├── repository/
│   ├── scanner.py
│   └── parser.py
├── retrieval/
│   ├── chunking.py
│   ├── embeddings.py
│   └── retriever.py
├── agents/
│   ├── planner.py
│   ├── coder.py
│   └── debugger.py
├── tools/
│   ├── file_editor.py
│   ├── executor.py
│   └── git_tools.py
├── backups/
└── workspace/

## Technologies Used

### Core

- Python
- Streamlit

### AI / NLP

- Sentence Transformers
- OpenRouter
- Ollama
- Qwen3

### Retrieval

- Semantic Search
- Lexical Search
- Cosine Similarity

### Code Analysis

- Python AST

### Software Engineering

- Patch-based editing
- Automated testing
- Debugging
- Git
- GitHub

## Installation

Clone the repository:

git clone https://github.com/ar-j-un-404/AI-SWE.git

Move into the project:

cd AI-SWE

Create a virtual environment:

python -m venv .venv

Activate it on Windows:

.venv\Scripts\activate

Install dependencies:

python -m pip install -r requirements.txt

## OpenRouter Setup

Create a `.env` file in the project root:

OPENROUTER_API_KEY=your_api_key_here

Do not commit the `.env` file.

Make sure `.gitignore` contains:

.env
.venv/
__pycache__/

## Ollama Setup

Install Ollama and download the local model:

ollama pull qwen3:4b

Check the model:

ollama run qwen3:4b

The AI Software Engineer can use Ollama when cloud models are unavailable.

## Running the Application

Start the Streamlit interface:

python -m streamlit run app.py

Then open the local Streamlit URL shown in the terminal.

## Example Task

Add a login page to this Streamlit application.

Requirements:

- Unauthenticated users should see the login page
- Block the main application before login
- Store authentication state using Streamlit session state
- Add logout support
- Preserve existing functionality
- Do not add unnecessary dependencies
- Run safe terminating tests

The system will:

1. Scan the repository
2. Retrieve relevant code
3. Create a plan
4. Wait for approval
5. Generate patches
6. Validate the patches
7. Apply approved changes
8. Run tests
9. Debug failures if necessary
10. Show the Git diff

## Reliability Problems Explored

Building this project involved dealing with several problems that appear in real AI coding agents.

Examples include:

- Malformed JSON from language models
- Markdown surrounding structured output
- Invalid patches
- Incomplete model responses
- Hallucinated filenames
- Unauthorized file modifications
- Duplicate file creation
- Incorrect FIND blocks
- Multiple matching code blocks
- Rate limiting
- Daily API quotas
- Model timeouts
- Empty responses
- Local model performance
- Test execution safety
- Streamlit state management

Handling these failures became an important part of the architecture.

## Safety Design

The project follows several basic safety principles:

READ freely  
PLAN freely  
EDIT only after approval  
RUN controlled commands  
COMMIT only after approval  
PUSH only after approval  

The goal is to avoid giving an AI model unrestricted access to the repository or shell.

## Current Limitations

The project is still under development.

Current limitations include:

- Mainly optimized for Python repositories
- Patch generation depends on LLM output quality
- Local Ollama models can be slow
- Retrieval can miss important dependencies
- Debugger context can still become large
- Runtime web application behavior is harder to verify than syntax
- GitHub authentication must already be configured
- Complex multi-file refactoring is still experimental

## Planned Improvements

Future improvements include:

- AST-aware code editing
- Dependency graph analysis
- Import and package dependency validation
- Automatic test discovery
- Stronger post-change verification
- Better runtime error capture
- Improved debugger retrieval
- Transactional file editing
- Safer rollback across multiple modifications
- Repository dependency awareness
- Task history
- Agent memory
- Multi-step autonomous execution
- Tool selection between coder, debugger, Git, and other agents
- GitHub repository creation
- Automatic repository cloning
- Support for more programming languages

## Why I Built This

I wanted to move beyond building applications where an LLM only generates text.

This project helped me understand how an AI agent can interact with:

- Real source code
- Repository structures
- Retrieval systems
- Validation layers
- Testing tools
- Debugging workflows
- Version control

The focus is not just code generation, but building a controlled engineering workflow around the language model.

## Status

The project is currently under active development.

New reliability improvements and engineering capabilities are being added as the system is tested on real repositories.

## Repository

GitHub:

https://github.com/ar-j-un-404/AI-SWE

## Author

Arjun

B.Tech Computer Science and Engineering student exploring:

- Artificial Intelligence
- Machine Learning
- AI Agents
- Retrieval-Augmented Generation
- Software Engineering
- Developer Tools
