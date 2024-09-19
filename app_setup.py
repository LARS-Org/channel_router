"""
This script is used to automate the setup of the Python virtual environment, 
installation of Python requirements, and the application's deploy.
"""

import os
import subprocess
import sys


def _run_command(command, cwd=None, shell=False):
    """
    Run a shell command in the specified directory.

    :param command: The command to run.
    :param cwd: The directory to run the command in.
    :param shell: Whether to use a shell to run the command.
    """
    result = subprocess.run(command, shell=shell, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main():
    """
    Main function to parse command-line arguments and call the appropriate function.
    """
    # Get the current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct path to sibling directory
    common_project_dir = os.path.join(current_dir, "..", "aws-common")

    # check if script directory exists
    if not os.path.exists(common_project_dir):
        print(f"Script directory not found: {common_project_dir}")
        # call the git clone command
        parent_dir = os.path.join(current_dir, "..")
        _run_command(
            f"git clone https://github.com/LARS-Org/aws-common.git",
            cwd=parent_dir,
            shell=True,
        )
        print(f"Cloned the aws-common repository to {common_project_dir}")
    # script directory exists, update it
    # call the git pull command to ensure the latest version
    _run_command("git fetch --quiet", cwd=common_project_dir, shell=True)
    _run_command("git pull --quiet", cwd=common_project_dir, shell=True)

    # calling the execute script passing the sys.argv
    script_path = os.path.join(common_project_dir, "app_scripts")
    script_path = os.path.join(script_path, "app_setup_execution.py")
    # convert the sys.argv to a string
    sys_argv = " ".join(sys.argv[1:])  # remove the first argument.
    # add the current_dir as an argument
    sys_argv = f"{sys_argv} --current_dir {current_dir}"

    # _run_command(f"python3.11 {script_path} {sys_argv}", cwd=current_dir, shell=False)
    _run_command(f"python3.11 {script_path} {sys_argv}", shell=True)


if __name__ == "__main__":
    main()
