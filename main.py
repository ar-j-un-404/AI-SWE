from pathlib import Path

import streamlit as st

from repository.scanner import scan_repository
from repository.parser import build_symbol_index

from retrieval.chunking import create_chunks
from retrieval.embeddings import embed_chunks
from retrieval.retriever import retrieve_relevant_chunks

from agents.planner import create_plan
from agents.coder import generate_changes

from tools.file_editor import apply_patches
from tools.executor import run_tests, tests_passed

st.set_page_config(
    page_title="AI Software Engineer",
    page_icon="⚙️",
    layout="wide"
)

DEFAULT_STATE = {
    "repo_path": "",
    "task": "",
    "repo_files": None,
    "symbols": None,
    "chunks": None,
    "embeddings": None,
    "relevant_chunks": None,
    "plan": None,
    "patches": None,
    "applied_changes": None,
    "changes_applied": False,
    "test_results": None,
}


for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = value

def reset_task_state():

    st.session_state.relevant_chunks = None
    st.session_state.plan = None
    st.session_state.patches = None
    st.session_state.applied_changes = None
    st.session_state.changes_applied = False
    st.session_state.test_results = None


def refresh_repository():

    repo_path = Path(
        st.session_state.repo_path
    ).resolve()

    files = scan_repository(
        repo_path
    )

    symbols = build_symbol_index(
        files
    )

    chunks = create_chunks(
        files
    )

    embeddings = embed_chunks(
        chunks
    )

    st.session_state.repo_files = files
    st.session_state.symbols = symbols
    st.session_state.chunks = chunks
    st.session_state.embeddings = embeddings


def get_test_commands():

    if not st.session_state.plan:

        return [
            "python -m compileall ."
        ]

    commands = st.session_state.plan.get(
        "tests_to_run",
        []
    )

    if not commands:

        return [
            "python -m compileall ."
        ]

    return commands

st.title(
    "AI Software Engineer"
)

st.write(
    "Analyze repositories, create implementation plans, "
    "generate patches, edit real files, and run tests."
)

st.divider()

st.header(
    "1. Repository"
)

repo_input = st.text_input(
    "Local repository path",
    value=st.session_state.repo_path,
    placeholder=(
        r"C:\Users\ARJUN\OneDrive\Documents\project\comparator"
    )
)


col_scan, col_refresh = st.columns(
    [1, 1]
)


with col_scan:

    scan_button = st.button(
        "Scan Repository",
        type="primary",
        use_container_width=True
    )


with col_refresh:

    refresh_button = st.button(
        "Refresh Repository",
        use_container_width=True,
        disabled=(
            st.session_state.repo_files
            is None
        )
    )



if scan_button:

    if not repo_input.strip():

        st.warning(
            "Enter a repository path."
        )

    else:

        try:

            repo_path = Path(
                repo_input
            ).resolve()

            if not repo_path.exists():

                st.error(
                    "Repository does not exist."
                )

            elif not repo_path.is_dir():

                st.error(
                    "The path is not a directory."
                )

            else:

                st.session_state.repo_path = str(
                    repo_path
                )

                with st.spinner(
                    "Scanning repository..."
                ):

                    refresh_repository()

                reset_task_state()

                st.success(
                    "Repository scanned successfully."
                )

        except Exception as error:

            st.exception(
                error
            )

if refresh_button:

    try:

        with st.spinner(
            "Refreshing repository index..."
        ):

            refresh_repository()

        st.success(
            "Repository refreshed."
        )

    except Exception as error:

        st.exception(
            error
        )

if st.session_state.repo_files is not None:

    st.subheader(
        "Repository Information"
    )

    col1, col2, col3 = st.columns(
        3
    )

    with col1:

        st.metric(
            "Python Files",
            len(
                st.session_state.repo_files
            )
        )

    with col2:

        st.metric(
            "Code Chunks",
            len(
                st.session_state.chunks
            )
        )

    with col3:

        st.metric(
            "Repository",
            Path(
                st.session_state.repo_path
            ).name
        )


    with st.expander(
        "Repository Files"
    ):

        for file_data in (
            st.session_state.repo_files
        ):

            st.code(
                file_data["path"]
            )


if st.session_state.repo_files is not None:

    st.divider()

    st.header(
        "2. Engineering Task"
    )

    task_input = st.text_area(
        "Describe the task or paste a complete error traceback",
        value=st.session_state.task,
        height=250,
        placeholder=(
            "Example:\n\n"
            "Fix the current Streamlit authentication crash.\n\n"
            "Error:\n"
            "StreamlitWidgetAlreadyInstantiatedError...\n\n"
            "Inspect auth.py and ui.py and preserve "
            "the existing login/logout behavior."
        )
    )


    analyze_button = st.button(
        "Analyze Task",
        type="primary",
        use_container_width=True
    )


    if analyze_button:

        if not task_input.strip():

            st.warning(
                "Enter a task first."
            )

        else:

            try:

                st.session_state.task = (
                    task_input.strip()
                )

                st.session_state.plan = None
                st.session_state.patches = None
                st.session_state.applied_changes = None
                st.session_state.changes_applied = False
                st.session_state.test_results = None

                with st.spinner(
                    "Searching for relevant code..."
                ):

                    relevant_chunks = (
                        retrieve_relevant_chunks(
                            st.session_state.task,
                            st.session_state.chunks,
                            st.session_state.embeddings
                        )
                    )

                st.session_state.relevant_chunks = (
                    relevant_chunks
                )

                st.success(
                    "Repository analysis completed."
                )

            except Exception as error:

                st.exception(
                    error
                )


if st.session_state.relevant_chunks:

    st.divider()

    st.header(
        "3. Relevant Code"
    )

    for chunk in (
        st.session_state.relevant_chunks
    ):

        similarity = chunk.get(
            "similarity",
            0
        )

        title = (
            f"{chunk['path']} → "
            f"{chunk['symbol']} "
            f"({similarity:.3f})"
        )

        with st.expander(
            title
        ):

            st.code(
                chunk.get(
                    "content",
                    ""
                ),
                language="python"
            )

if st.session_state.relevant_chunks:

    st.divider()

    st.header(
        "4. Implementation Plan"
    )


    if st.session_state.plan is None:

        generate_plan_button = st.button(
            "Generate Plan",
            type="primary",
            use_container_width=True
        )


        if generate_plan_button:

            try:

                with st.spinner(
                    "AI is creating the implementation plan..."
                ):

                    plan = create_plan(
                        st.session_state.task,
                        st.session_state.relevant_chunks,
                        st.session_state.symbols
                    )

                st.session_state.plan = plan

                st.success(
                    "Plan generated."
                )

            except Exception as error:

                st.exception(
                    error
                )



if st.session_state.plan:

    plan = st.session_state.plan


    st.subheader(
        "Summary"
    )

    st.write(
        plan.get(
            "summary",
            ""
        )
    )


    st.subheader(
        "Reasoning"
    )

    st.write(
        plan.get(
            "reasoning",
            ""
        )
    )


    col_modify, col_create = st.columns(
        2
    )


    with col_modify:

        st.markdown(
            "### Files to Modify"
        )

        files_to_modify = plan.get(
            "files_to_modify",
            []
        )

        if files_to_modify:

            for path in files_to_modify:

                st.code(
                    path
                )

        else:

            st.write(
                "None"
            )


    with col_create:

        st.markdown(
            "### Files to Create"
        )

        files_to_create = plan.get(
            "files_to_create",
            []
        )

        if files_to_create:

            for path in files_to_create:

                st.code(
                    path
                )

        else:

            st.write(
                "None"
            )


    st.markdown(
        "### Steps"
    )

    for index, step in enumerate(
        plan.get(
            "steps",
            []
        ),
        start=1
    ):

        st.write(
            f"{index}. {step}"
        )


    st.markdown(
        "### Risks"
    )

    risks = plan.get(
        "risks",
        []
    )

    if risks:

        for risk in risks:

            st.write(
                f"- {risk}"
            )

    else:

        st.write(
            "No major risks identified."
        )


    st.markdown(
        "### Planned Tests"
    )

    test_commands = get_test_commands()

    for command in test_commands:

        st.code(
            command
        )


if (
    st.session_state.plan
    and st.session_state.patches is None
):

    st.divider()

    st.header(
        "5. Generate Code Changes"
    )


    approve_plan = st.checkbox(
        "I approve this implementation plan",
        key="approve_plan"
    )


    generate_patches_button = st.button(
        "Generate Code Changes",
        type="primary",
        disabled=not approve_plan,
        use_container_width=True
    )


    if generate_patches_button:

        try:

            with st.spinner(
                "AI is generating repository patches..."
            ):

                result = generate_changes(
                    st.session_state.task,
                    st.session_state.plan,
                    st.session_state.repo_files
                )

            patches = result.get(
                "patches",
                []
            )


            if not patches:

                st.error(
                    "The coder generated no valid patches."
                )

            else:

                st.session_state.patches = (
                    patches
                )

                st.success(
                    f"{len(patches)} valid patch(es) generated."
                )

        except Exception as error:

            st.exception(
                error
            )


if st.session_state.patches:

    st.divider()

    st.header(
        "6. Proposed Changes"
    )


    for index, patch in enumerate(
        st.session_state.patches,
        start=1
    ):

        action = patch.get(
            "action",
            "unknown"
        )

        path = patch.get(
            "path",
            "unknown"
        )


        with st.expander(
            f"Patch {index}: {path} [{action.upper()}]",
            expanded=True
        ):

            if action == "modify":

                st.markdown(
                    "#### Existing Code"
                )

                st.code(
                    patch.get(
                        "find",
                        ""
                    ),
                    language="python"
                )


                st.markdown(
                    "#### Replacement"
                )

                st.code(
                    patch.get(
                        "replace",
                        ""
                    ),
                    language="python"
                )


            elif action == "create":

                st.markdown(
                    "#### New File"
                )

                st.code(
                    patch.get(
                        "content",
                        ""
                    ),
                    language="python"
                )

if (
    st.session_state.patches
    and not st.session_state.changes_applied
):

    st.divider()

    st.header(
        "7. Apply Changes"
    )

    st.warning(
        "This action will modify the actual files "
        "inside the selected repository."
    )


    approve_changes = st.checkbox(
        "I approve these code changes",
        key="approve_changes"
    )


    apply_button = st.button(
        "Apply Changes to Repository",
        type="primary",
        disabled=not approve_changes,
        use_container_width=True
    )


    if apply_button:

        try:

            repo_path = Path(
                st.session_state.repo_path
            ).resolve()


            with st.spinner(
                "Applying patches..."
            ):

                applied_changes = apply_patches(
                    repo_path,
                    st.session_state.patches
                )


            st.session_state.applied_changes = (
                applied_changes
            )

            st.session_state.changes_applied = True

            st.session_state.test_results = None


            # Refresh the repository so the agent
            # sees its own modifications.
            with st.spinner(
                "Refreshing repository..."
            ):

                refresh_repository()


            st.success(
                f"Changes applied successfully. "
                f"{len(applied_changes)} change(s) applied."
            )

        except Exception as error:

            st.exception(
                error
            )


# ============================================================
# STEP 8 — RUN TESTS
# ============================================================

if st.session_state.changes_applied:

    st.divider()

    st.header(
        "8. Run Tests"
    )


    test_commands = get_test_commands()


    st.write(
        "The following commands will be executed:"
    )


    for command in test_commands:

        st.code(
            command
        )


    run_tests_button = st.button(
        "Run Tests",
        type="primary",
        use_container_width=True
    )


    if run_tests_button:

        try:

            repo_path = Path(
                st.session_state.repo_path
            ).resolve()


            with st.spinner(
                "Running repository tests..."
            ):

                results = run_tests(
                    repo_path,
                    test_commands
                )


            st.session_state.test_results = (
                results
            )


        except Exception as error:

            st.exception(
                error
            )


if st.session_state.test_results is not None:

    st.divider()

    st.header(
        "9. Test Results"
    )


    test_results = (
        st.session_state.test_results
    )


    for index, result in enumerate(
        test_results,
        start=1
    ):

        command = result.get(
            "command",
            "Unknown command"
        )

        returncode = result.get(
            "returncode"
        )

        skipped = result.get(
            "skipped",
            False
        )

        reason = result.get(
            "reason"
        )


        if skipped:

            status = "SKIPPED"

        elif returncode == 0:

            status = "PASSED"

        else:

            status = "FAILED"


        with st.expander(
            f"Test {index}: {command} [{status}]",
            expanded=True
        ):

            if skipped:

                st.warning(
                    f"Skipped: {reason}"
                )


            elif returncode == 0:

                st.success(
                    "Test passed."
                )


            else:

                st.error(
                    f"Test failed with exit code "
                    f"{returncode}."
                )


            stdout = result.get(
                "stdout",
                ""
            )

            stderr = result.get(
                "stderr",
                ""
            )


            if stdout:

                st.markdown(
                    "#### Standard Output"
                )

                st.code(
                    stdout
                )


            if stderr:

                st.markdown(
                    "#### Error Output"
                )

                st.code(
                    stderr
                )


    if tests_passed(
        test_results
    ):

        st.success(
            "All executable tests passed."
        )


    else:

        st.error(
            "One or more tests failed."
        )

        st.info(
            "The next upgrade will send these failures "
            "directly to the debugger agent so it can "
            "generate a repair patch."
        )


st.divider()

st.header(
    "Agent Status"
)


status_col1, status_col2, status_col3, status_col4 = (
    st.columns(
        4
    )
)


with status_col1:

    st.metric(
        "Repository",
        "Loaded"
        if st.session_state.repo_files
        else "Not Loaded"
    )


with status_col2:

    st.metric(
        "Plan",
        "Ready"
        if st.session_state.plan
        else "Not Ready"
    )


with status_col3:

    st.metric(
        "Changes",
        "Applied"
        if st.session_state.changes_applied
        else (
            "Ready"
            if st.session_state.patches
            else "Not Ready"
        )
    )


with status_col4:

    if st.session_state.test_results is None:

        test_status = "Not Run"

    elif tests_passed(
        st.session_state.test_results
    ):

        test_status = "Passed"

    else:

        test_status = "Failed"


    st.metric(
        "Tests",
        test_status
    )
