from pathlib import Path

import streamlit as st

from repository.scanner import scan_repository
from repository.parser import build_symbol_index

from retrieval.chunking import create_chunks
from retrieval.embeddings import embed_chunks
from retrieval.retriever import retrieve_relevant_chunks

from agents.planner import create_plan
from agents.coder import generate_changes
from agents.debugger import debug_failure

from tools.file_editor import (
    apply_patches,
    rollback_changes,
)

from tools.executor import (
    run_tests,
    tests_passed,
)

from tools.git_tools import (
    get_git_status,
    get_git_diff,
    create_commit,
    is_git_repository,
    push_current_branch,
)


st.set_page_config(
    page_title="AI Software Engineer",
    page_icon="⚙️",
    layout="wide",
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
    "applied_changes": [],
    "changes_applied": False,
    "test_results": None,
    "debug_result": None,
    "debug_patches": None,
    "git_diff": None,
    "no_changes_required": False,
    "commit_created": False,
}


for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.sidebar.subheader("AI SWE Test")
st.sidebar.write("Git push workflow working")

def reset_task_state():
    st.session_state.relevant_chunks = None
    st.session_state.plan = None
    st.session_state.patches = None
    st.session_state.applied_changes = []
    st.session_state.changes_applied = False
    st.session_state.test_results = None
    st.session_state.debug_result = None
    st.session_state.debug_patches = None
    st.session_state.git_diff = None
    st.session_state.no_changes_required = False
    st.session_state.commit_created = False


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


def show_patch(
    patch,
    title,
):
    action = patch.get(
        "action",
        "unknown",
    )

    path = patch.get(
        "path",
        "unknown",
    )

    with st.expander(
        f"{title}: {path} [{action.upper()}]",
        expanded=True,
    ):
        if action == "modify":
            st.markdown(
                "#### Existing Code"
            )

            st.code(
                patch.get(
                    "find",
                    "",
                ),
                language="python",
            )

            st.markdown(
                "#### Replacement"
            )

            st.code(
                patch.get(
                    "replace",
                    "",
                ),
                language="python",
            )

        elif action == "create":
            st.markdown(
                "#### New File"
            )

            st.code(
                patch.get(
                    "content",
                    "",
                ),
                language="python",
            )


def show_test_results(
    results,
):
    for index, result in enumerate(
        results,
        start=1,
    ):
        command = result.get(
            "command",
            "Unknown command",
        )

        returncode = result.get(
            "returncode"
        )

        skipped = result.get(
            "skipped",
            False,
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
            expanded=True,
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
                    f"Test failed with exit code {returncode}."
                )

            stdout = result.get(
                "stdout",
                "",
            )

            stderr = result.get(
                "stderr",
                "",
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


st.title(
    "AI Software Engineer"
)

st.write(
    "Analyze repositories, plan code changes, generate patches, "
    "edit real files, run tests, debug failures, review Git changes, "
    "commit work, and push changes to GitHub."
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
    ),
)

col_scan, col_refresh = st.columns(
    2
)

with col_scan:
    scan_button = st.button(
        "Scan Repository",
        type="primary",
        use_container_width=True,
    )

with col_refresh:
    refresh_button = st.button(
        "Refresh Repository",
        use_container_width=True,
        disabled=(
            st.session_state.repo_files
            is None
        ),
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
                st.session_state.repo_path = (
                    str(repo_path)
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
            "Refreshing repository..."
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
            ),
        )

    with col2:
        st.metric(
            "Code Chunks",
            len(
                st.session_state.chunks
            ),
        )

    with col3:
        st.metric(
            "Repository",
            Path(
                st.session_state.repo_path
            ).name,
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
        "Describe the engineering task",
        value=st.session_state.task,
        height=280,
        placeholder=(
            "Examples:\n\n"
            "Add a login page to this Streamlit application.\n\n"
            "Verify whether Recent Activity is implemented.\n\n"
            "Fix this traceback..."
        ),
    )

    analyze_button = st.button(
        "Analyze Task",
        type="primary",
        use_container_width=True,
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
                st.session_state.applied_changes = []
                st.session_state.changes_applied = False
                st.session_state.test_results = None
                st.session_state.debug_result = None
                st.session_state.debug_patches = None
                st.session_state.git_diff = None
                st.session_state.no_changes_required = False
                st.session_state.commit_created = False

                with st.spinner(
                    "Searching repository..."
                ):
                    relevant_chunks = (
                        retrieve_relevant_chunks(
                            st.session_state.task,
                            st.session_state.chunks,
                            st.session_state.embeddings,
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
        score = chunk.get(
            "retrieval_score",
            chunk.get(
                "similarity",
                0,
            ),
        )

        title = (
            f"{chunk['path']} → "
            f"{chunk['symbol']} "
            f"({score:.3f})"
        )

        with st.expander(
            title
        ):
            st.code(
                chunk.get(
                    "content",
                    "",
                ),
                language="python",
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
            use_container_width=True,
        )

        if generate_plan_button:
            try:
                with st.spinner(
                    "Creating implementation plan..."
                ):
                    plan = create_plan(
                        st.session_state.task,
                        st.session_state.relevant_chunks,
                        st.session_state.symbols,
                    )

                st.session_state.plan = (
                    plan
                )

                if not plan.get(
                    "files_to_modify",
                    [],
                ) and not plan.get(
                    "files_to_create",
                    [],
                ):
                    st.session_state.no_changes_required = True

                else:
                    st.session_state.no_changes_required = False

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
            "",
        )
    )

    st.subheader(
        "Reasoning"
    )

    st.write(
        plan.get(
            "reasoning",
            "",
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
            [],
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
            [],
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

    steps = plan.get(
        "steps",
        [],
    )

    if steps:
        for index, step in enumerate(
            steps,
            start=1,
        ):
            st.write(
                f"{index}. {step}"
            )

    st.markdown(
        "### Risks"
    )

    risks = plan.get(
        "risks",
        [],
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

    for command in get_test_commands():
        st.code(
            command
        )


                                                              
                        
                                                              

if (
    st.session_state.plan
    and st.session_state.no_changes_required
):
    st.divider()

    st.header(
        "5. Verification Result"
    )

    st.success(
        "The planner determined that no source-code "
        "changes are required."
    )

    verification_test_button = st.button(
        "Run Verification Tests",
        type="primary",
        use_container_width=True,
    )

    if verification_test_button:
        try:
            repo_path = Path(
                st.session_state.repo_path
            ).resolve()

            with st.spinner(
                "Running verification tests..."
            ):
                results = run_tests(
                    repo_path,
                    get_test_commands(),
                )

            st.session_state.test_results = (
                results
            )

        except Exception as error:
            st.exception(
                error
            )


                                                              
                     
                                                              

if (
    st.session_state.plan
    and not st.session_state.no_changes_required
    and st.session_state.patches is None
):
    st.divider()

    st.header(
        "5. Generate Code Changes"
    )

    approve_plan = st.checkbox(
        "I approve this implementation plan",
        key="approve_plan",
    )

    generate_patches_button = st.button(
        "Generate Code Changes",
        type="primary",
        disabled=not approve_plan,
        use_container_width=True,
    )

    if generate_patches_button:
        try:
            files_to_modify = (
                st.session_state.plan.get(
                    "files_to_modify",
                    [],
                )
            )

            files_to_create = (
                st.session_state.plan.get(
                    "files_to_create",
                    [],
                )
            )

            if (
                not files_to_modify
                and not files_to_create
            ):
                st.session_state.no_changes_required = True

                st.info(
                    "No code changes are required."
                )

            else:
                with st.spinner(
                    "Generating repository patches..."
                ):
                    result = generate_changes(
                        st.session_state.task,
                        st.session_state.plan,
                        st.session_state.repo_files,
                    )

                patches = result.get(
                    "patches",
                    [],
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
            st.error(
                "Code generation failed."
            )

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
        start=1,
    ):
        show_patch(
            patch,
            f"Patch {index}",
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
        "This action modifies the real files "
        "inside the selected repository."
    )

    approve_changes = st.checkbox(
        "I approve these code changes",
        key="approve_changes",
    )

    apply_button = st.button(
        "Apply Changes to Repository",
        type="primary",
        disabled=not approve_changes,
        use_container_width=True,
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
                    st.session_state.patches,
                )

            st.session_state.applied_changes.extend(
                applied_changes
            )

            st.session_state.changes_applied = True
            st.session_state.test_results = None
            st.session_state.debug_result = None
            st.session_state.debug_patches = None
            st.session_state.git_diff = None
            st.session_state.commit_created = False

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


                                                              
          
                                                              

if st.session_state.changes_applied:
    st.divider()

    st.header(
        "8. Run Tests"
    )

    test_commands = get_test_commands()

    st.write(
        "Commands that will run:"
    )

    for command in test_commands:
        st.code(
            command
        )

    run_tests_button = st.button(
        "Run Tests",
        type="primary",
        use_container_width=True,
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
                    test_commands,
                )

            st.session_state.test_results = (
                results
            )

            st.session_state.debug_result = None
            st.session_state.debug_patches = None

        except Exception as error:
            st.exception(
                error
            )


if st.session_state.test_results is not None:
    st.divider()

    st.header(
        "Test Results"
    )

    show_test_results(
        st.session_state.test_results
    )

    if tests_passed(
        st.session_state.test_results
    ):
        st.success(
            "All executable tests passed."
        )

    else:
        st.error(
            "One or more tests failed."
        )


                                                              
             
                                                              

if (
    st.session_state.test_results is not None
    and not tests_passed(
        st.session_state.test_results
    )
    and st.session_state.changes_applied
):
    st.divider()

    st.header(
        "9. AI Debugger"
    )

    st.error(
        "Tests failed. The debugger can inspect "
        "the failure and generate repair patches."
    )

    debug_button = st.button(
        "Debug Failure",
        type="primary",
        use_container_width=True,
    )

    if debug_button:
        try:
            with st.spinner(
                "Investigating failure..."
            ):
                refresh_repository()

                result = debug_failure(
                    st.session_state.task,
                    st.session_state.test_results,
                    st.session_state.repo_files,
                )

            st.session_state.debug_result = (
                result
            )

            st.session_state.debug_patches = (
                result.get(
                    "patches",
                    [],
                )
            )

            if not st.session_state.debug_patches:
                st.warning(
                    "The debugger did not generate a repair patch."
                )

        except Exception as error:
            st.exception(
                error
            )


if st.session_state.debug_result:
    st.subheader(
        "Root Cause"
    )

    st.write(
        st.session_state.debug_result.get(
            "root_cause",
            "Unknown",
        )
    )


if st.session_state.debug_patches:
    st.subheader(
        "Proposed Repair"
    )

    for index, patch in enumerate(
        st.session_state.debug_patches,
        start=1,
    ):
        show_patch(
            patch,
            f"Repair {index}",
        )

    approve_debug = st.checkbox(
        "I approve this repair patch",
        key="approve_debug",
    )

    apply_debug_button = st.button(
        "Apply Repair and Re-run Tests",
        type="primary",
        disabled=not approve_debug,
        use_container_width=True,
    )

    if apply_debug_button:
        try:
            repo_path = Path(
                st.session_state.repo_path
            ).resolve()

            with st.spinner(
                "Applying repair..."
            ):
                applied = apply_patches(
                    repo_path,
                    st.session_state.debug_patches,
                )

            st.session_state.applied_changes.extend(
                applied
            )

            refresh_repository()

            with st.spinner(
                "Re-running tests..."
            ):
                st.session_state.test_results = (
                    run_tests(
                        repo_path,
                        get_test_commands(),
                    )
                )

            st.session_state.debug_result = None
            st.session_state.debug_patches = None
            st.session_state.git_diff = None
            st.session_state.commit_created = False

            st.rerun()

        except Exception as error:
            st.exception(
                error
            )



if (
    st.session_state.changes_applied
    or st.session_state.no_changes_required
):
    st.divider()

    st.header(
        "10. Git Review"
    )

    repo_path = Path(
        st.session_state.repo_path
    ).resolve()

    try:
        if is_git_repository(
            repo_path
        ):
            col_status, col_diff = st.columns(
                2
            )

            with col_status:
                if st.button(
                    "Git Status",
                    use_container_width=True,
                ):
                    status = get_git_status(
                        repo_path
                    )

                    if status.strip():
                        st.code(
                            status
                        )
                    else:
                        st.success(
                            "Working tree is clean."
                        )

            with col_diff:
                if st.button(
                    "Show Git Diff",
                    use_container_width=True,
                ):
                    diff = get_git_diff(
                        repo_path
                    )

                    st.session_state.git_diff = (
                        diff
                    )

            if st.session_state.git_diff:
                st.subheader(
                    "Git Diff"
                )

                st.code(
                    st.session_state.git_diff,
                    language="diff",
                )

            elif (
                st.session_state.git_diff == ""
            ):
                st.info(
                    "There are no uncommitted Git changes."
                )


           
            if (
                st.session_state.applied_changes
                and not st.session_state.commit_created
            ):
                st.subheader(
                    "Rollback"
                )

                st.warning(
                    "Rollback restores files changed "
                    "during this AI task."
                )

                approve_rollback = st.checkbox(
                    "I want to rollback these AI changes",
                    key="approve_rollback",
                )

                if st.button(
                    "Rollback Changes",
                    disabled=not approve_rollback,
                    use_container_width=True,
                ):
                    try:
                        rollback_changes(
                            repo_path,
                            st.session_state.applied_changes,
                        )

                        st.session_state.applied_changes = []
                        st.session_state.changes_applied = False
                        st.session_state.patches = None
                        st.session_state.test_results = None
                        st.session_state.debug_result = None
                        st.session_state.debug_patches = None
                        st.session_state.git_diff = None
                        st.session_state.commit_created = False

                        refresh_repository()

                        st.success(
                            "Changes rolled back."
                        )

                        st.rerun()

                    except Exception as error:
                        st.exception(
                            error
                        )


                                                                  
                    
                                                                  

            if (
                st.session_state.changes_applied
                and not st.session_state.commit_created
            ):
                st.subheader(
                    "Create Git Commit"
                )

                if (
                    st.session_state.test_results is None
                ):
                    st.warning(
                        "Tests have not been run yet."
                    )

                elif not tests_passed(
                    st.session_state.test_results
                ):
                    st.error(
                        "Tests are failing. "
                        "Fix them before committing."
                    )

                commit_message = st.text_input(
                    "Commit message",
                    placeholder=(
                        "Add login page"
                    ),
                )

                approve_commit = st.checkbox(
                    "I approve creating this Git commit",
                    key="approve_commit",
                )

                tests_ok = (
                    st.session_state.test_results
                    is not None
                    and tests_passed(
                        st.session_state.test_results
                    )
                )

                commit_button = st.button(
                    "Create Commit",
                    type="primary",
                    disabled=(
                        not approve_commit
                        or not commit_message.strip()
                        or not tests_ok
                    ),
                    use_container_width=True,
                )

                if commit_button:
                    try:
                        result = create_commit(
                            repo_path,
                            commit_message.strip(),
                        )

                        if result["success"]:
                            st.session_state.commit_created = True
                            st.session_state.git_diff = None

                            st.success(
                                result["message"]
                            )

                            st.rerun()

                        else:
                            st.error(
                                result["message"]
                            )

                    except Exception as error:
                        st.exception(
                            error
                        )


                                                                  
                  
                                                                  

            if st.session_state.commit_created:
                st.subheader(
                    "Push to GitHub"
                )

                st.success(
                    "The local Git commit was created successfully."
                )

                st.write(
                    "The AI Software Engineer can now push "
                    "the current branch to the repository's "
                    "configured `origin` remote."
                )

                st.warning(
                    "Your computer must already be authenticated "
                    "with GitHub for `git push` to work."
                )

                approve_push = st.checkbox(
                    "I approve pushing this commit to GitHub",
                    key="approve_push",
                )

                push_button = st.button(
                    "Push to GitHub",
                    type="primary",
                    disabled=not approve_push,
                    use_container_width=True,
                )

                if push_button:
                    try:
                        with st.spinner(
                            "Pushing commit to GitHub..."
                        ):
                            result = push_current_branch(
                                repo_path
                            )

                        if result["success"]:
                            st.success(
                                "Push completed successfully."
                            )

                            if result.get(
                                "message"
                            ):
                                st.code(
                                    result["message"]
                                )

                        else:
                            st.error(
                                "Git push failed."
                            )

                            st.code(
                                result.get(
                                    "message",
                                    "Unknown Git push error.",
                                )
                            )

                    except Exception as error:
                        st.exception(
                            error
                        )

        else:
            st.info(
                "This repository is not initialized with Git."
            )

    except Exception as error:
        st.exception(
            error
        )


                                                              
              
                                                              

st.divider()

st.header(
    "Agent Status"
)

status_col1, status_col2, status_col3, status_col4, status_col5 = (
    st.columns(
        5
    )
)

with status_col1:
    st.metric(
        "Repository",
        (
            "Loaded"
            if st.session_state.repo_files
            else "Not Loaded"
        ),
    )

with status_col2:
    st.metric(
        "Plan",
        (
            "Ready"
            if st.session_state.plan
            else "Not Ready"
        ),
    )

with status_col3:
    if st.session_state.no_changes_required:
        change_status = "Not Required"

    elif st.session_state.changes_applied:
        change_status = "Applied"

    elif st.session_state.patches:
        change_status = "Ready"

    else:
        change_status = "Not Ready"

    st.metric(
        "Changes",
        change_status,
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
        test_status,
    )

with status_col5:
    st.metric(
        "Git Commit",
        (
            "Created"
            if st.session_state.commit_created
            else "Not Created"
        ),
    )