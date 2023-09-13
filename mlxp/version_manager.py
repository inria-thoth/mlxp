"""The version manager allows to keep track of changes to the code and to automatically
generate a deployment version of the code based on the latest git commit."""

import abc
import os
import subprocess
from typing import Any, Dict

import yaml

from mlxp._internal._interactive_mode import _bcolors, _printc


class VersionManager(abc.ABC):
    """An abstract class whose children allow custumizing the working directory of the
    run."""

    def __init__(self):

        self._interactive_mode = False
        self._vm_choices_file = ""
        self._existing_choices = False
        self.vm_choices = {}

    def _handle_interactive_mode(self, mode: bool, vm_choices_file: str = "./vm_choices.yaml") -> None:
        self._interactive_mode = mode
        self._vm_choices_file = vm_choices_file
        if os.path.isfile(self._vm_choices_file):
            with open(self._vm_choices_file, "r") as file:
                self.vm_choices = yaml.safe_load(file)
                self._existing_choices = True

    def _save_vm_choice(self):
        if self._interactive_mode:
            if not os.path.isfile(self._vm_choices_file):
                with open(self._vm_choices_file, "w") as f:
                    yaml.dump(self.vm_choices, f)

    @abc.abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Return a dictionary containing information about the version used for the
        run.

        :return: Dictionary containing information about the version used for the run.
        :rtype: Dict[str, Any]
        """
        pass

    @abc.abstractmethod
    def make_working_directory(self) -> str:
        """Return a path to the target working directory from which jobs submitted to a
        cluster in batch mode will be executed.

        :rtype: str
        :return: A path to the target working directory
        """
        pass


class GitVM(VersionManager):
    """GitVM allows separting development code from code deployed in a cluster and
    allows to recover exactly the code used for a given run.

    GitVM creates a copy of the current directory based on the latest commit,
    if it doesn't exist already, then sets the working directory to this copy.

    .. py:attribute:: parent_work_dir
        :type: str

        The target parent directory of
        the new working directory returned by the version manager

    .. py:attribute:: compute_requirements
        :type: bool

        When set to true, the version manager stores a list of requirements and their version.
    """

    def __init__(self, parent_work_dir: str, compute_requirements: bool):
        super().__init__()

        self.parent_work_dir = os.path.abspath(parent_work_dir)
        self.compute_requirements = compute_requirements
        self.dst = None
        self.commit_hash = None
        self.repo_path = None
        self.work_dir = os.getcwd()
        self.requirements = ["UNKNOWN"]

    def get_info(self) -> Dict[str, Any]:
        """Return a dictionary containing information about the version used for the
        run.

        The following information is returned:
        - requirements: the dependencies of the code and their versions. Empty if no requirements file was found.
        - commit_hash: The hash of the latest commit.
        - repo_path: Path to the repository.

        :return: Dictionary containing
        information about the version used for the run.
        :rtype: Dict[str, Any]
        """
        return {
            "requirements": self.requirements,
            "commit_hash": self.commit_hash,
            "repo_path": self.repo_path,
        }

    def make_working_directory(self) -> str:
        """Create and return a target working directory.

        Depending on the user's choice, the returned directory is either:

        - The current working directory.
        - A directory under self.parent_work_dir/repo_name/latest_commit_hash.
        In this case, a copy of the code based on the latest git commit is created and used to run the experiment.

        :rtype: str
        :return: A path to the target working directory
        """
        repo = self._getGitRepo()
        repo_root = repo.git.rev_parse("--show-toplevel")
        relpath = os.path.relpath(os.getcwd(), repo_root)
        self.repo_path = repo.working_tree_dir
        repo_name = self.repo_path.split("/")[-1]
        self.commit_hash = repo.head.object.hexsha
        target_name = os.path.join(repo_name, self.commit_hash)
        parent_work_dir = self.parent_work_dir
        self.dst = os.path.join(parent_work_dir, target_name)

        self._handle_cloning(repo, relpath)
        self._save_vm_choice()

        return self.work_dir

    def _clone_repo(self, repo):
        if not os.path.isdir(self.dst):
            _printc(_bcolors.OKBLUE, f"Creating a copy of the repository at {self.dst}")
            repo.clone(self.dst)
            if self.compute_requirements:
                self._make_requirements_file()
        else:
            if not self._existing_choices:
                _printc(
                    _bcolors.OKBLUE, f"Found a copy of the repository with commit-hash: {self.commit_hash}",
                )
                _printc(_bcolors.OKBLUE, f"Run will be executed from {self.dst}")

    def _handle_cloning(self, repo, relpath):
        while True:
            if self._interactive_mode:
                if self._existing_choices:
                    choice = self.vm_choices["cloning"]
                else:
                    _printc(
                        _bcolors.OKGREEN, "Where would you like to run your code from? (a/b):",
                    )
                    if os.path.isdir(self.dst):
                        print(
                            f"{_bcolors.OKGREEN} a {_bcolors.ENDC}: Execute code from an existing copy of the repository based on the latest commit."
                        )
                        print(f"The copy is located in: {self.dst}")
                    else:
                        print(
                            f"{_bcolors.OKGREEN}a{_bcolors.ENDC}: Create a copy of the repository based on the latest commit and execute code from there."
                        )
                        print(f"The copy will be created in: {self.dst}")
                    print(f"{_bcolors.OKGREEN}b{_bcolors.ENDC}: Execute code from the main repository")
                    choice = input(f"{_bcolors.OKGREEN}Please enter you answer (a/b):{_bcolors.ENDC}")
                    self.vm_choices["cloning"] = choice

                if choice == "a":
                    self._clone_repo(repo)
                    self._set_requirements()
                    self.work_dir = os.path.join(self.dst, relpath)
                    break
                elif choice == "b":
                    if not self._existing_choices:
                        _printc(
                            _bcolors.OKBLUE, f"Run will be executed from the current repository {self.dst}",
                        )
                    break
                else:
                    _printc(_bcolors.OKBLUE, "Invalid choice. Please try again. (a/b)")
            else:
                self._clone_repo(repo)
                self._set_requirements()
                self.work_dir = os.path.join(self.dst, relpath)
                break

    def _handle_commit_state(self, repo):
        ignore_msg = "Ingoring uncommitted changes!\n"
        ignore_msg += (
            _bcolors.FAIL
            + "Warning:"
            + _bcolors.ENDC
            + "Uncommitted changes will not be taken into account during execution of the jobs!\n"
        )
        ignore_msg += (
            _bcolors.FAIL + "Warning:" + _bcolors.ENDC + "Jobs will be executed from the latest commit"
        )

        while True:
            if self._interactive_mode:
                if self._existing_choices:
                    break
                if repo.is_dirty():
                    _printc(
                        _bcolors.OKBLUE, "There are uncommitted changes in the repository:",
                    )
                    _disp_uncommited_files(repo)
                    _printc(
                        _bcolors.OKGREEN, "How would you like to handle uncommitted changes? (a/b/c)",
                    )
                    print(
                        f"{_bcolors.OKGREEN}a{_bcolors.ENDC}: Create a new automatic commit before launching jobs."
                    )
                    print(
                        f"{_bcolors.OKGREEN}b{_bcolors.ENDC}: Check again for uncommitted changes (assuming you manually committed them). "
                    )
                    print(f"{_bcolors.OKGREEN}c{_bcolors.ENDC}: Ignore uncommitted changes.")
                    choice = input(
                        f"{_bcolors.OKGREEN}[Uncommitted changes]: Please enter your choice (a/b/c): {_bcolors.ENDC}"
                    )
                    if choice == "a":
                        _printc(_bcolors.OKBLUE, "Commiting changes....")
                        output_msg = repo.git.commit("-a", "-m", "mlxp: Automatically committing all changes")
                        _printc(_bcolors.OKBLUE, output_msg)

                        if not repo.is_dirty():
                            _printc(_bcolors.OKBLUE, "No more uncommitted changes!")
                            break
                    elif choice == "b":
                        _printc(_bcolors.OKBLUE, "Checking again for uncommitted changes...")
                        pass
                    elif choice == "c":
                        if repo.is_dirty():
                            print(ignore_msg)
                        else:
                            _printc(_bcolors.OKBLUE, "No more uncommitted changes found!")
                        break

                    else:
                        _printc(_bcolors.OKBLUE, "Invalid choice. Please try again. (a/b/c)")
                else:
                    _printc(_bcolors.OKBLUE, "No uncommitted changes!")
                    break
            else:
                print(ignore_msg)
                break

    def _handle_untracked_files(self, repo):
        ignore_msg = _bcolors.FAIL + "Warning:" + _bcolors.ENDC + "There are untracked files! \n"
        ignore_msg += (
            _bcolors.FAIL
            + "Warning:"
            + _bcolors.ENDC
            + "Untracked files will not be accessible during execution of the jobs!"
        )

        while True:
            if self._interactive_mode:
                if self._existing_choices:
                    break
                status = repo.git.status()
                print(status)
                if repo.untracked_files:
                    _printc(_bcolors.OKBLUE, "There are untracked files in the repository:")
                    _disp_untracked_files(repo)
                    _printc(
                        _bcolors.OKGREEN, "How would you like to handle untracked files? (a/b/c)",
                    )
                    print(f"{_bcolors.OKGREEN}a{_bcolors.ENDC}: Add untracked files directly from here?")
                    print(
                        f"{_bcolors.OKGREEN}b{_bcolors.ENDC}: Check again for untrakced files (assuming you manually added them)."
                    )
                    print(f"{_bcolors.OKGREEN}c{_bcolors.ENDC}: Ignore untracked files.")
                    choice = input(
                        f"{_bcolors.OKGREEN}[Untracked files]: Please enter your choice (a/b/c):{_bcolors.ENDC}"
                    )
                    if choice == "a":
                        print("Untracked files:")
                        _disp_untracked_files(repo)
                        _printc(
                            _bcolors.OKGREEN,
                            "Please select files to be tracked (comma-separated, hit Enter to skip):",
                        )

                        files_input = input()

                        # If user input is not empty
                        if files_input:
                            # Split user input by commas
                            files_to_add = files_input.split(",")

                            # Add selected files
                            for file in files_to_add:
                                repo.git.add(file.strip())
                            # Commit the changes
                            # repo.index.commit("mlxp: Committing selected files ")
                            if not repo.untracked_files:
                                break
                        else:
                            _printc(_bcolors.OKBLUE, "No files added. Skipping...")
                            print(ignore_msg)
                            break
                    elif choice == "b":
                        _printc(_bcolors.OKBLUE, "Checking again for untracked files...")
                        pass
                    elif choice == "c":
                        if repo.untracked_files:
                            print(ignore_msg)
                        else:
                            _printc(_bcolors.OKBLUE, "No more untracked files!")
                            _printc(_bcolors.OKBLUE, "Continuing checks ...")
                        break
                    else:
                        _printc(_bcolors.OKBLUE, "Invalid choice. Please try again. (a/b/c)")

                else:
                    _printc(_bcolors.OKBLUE, "No untracked files!")
                    _printc(_bcolors.OKBLUE, "Continuing checks ...")
                    break
            else:
                print(ignore_msg)
                break

    def _make_requirements_file(self):

        _printc(_bcolors.OKBLUE, "No requirements file found")
        _printc(_bcolors.OKBLUE, "Generating it using pipreqs")
        # Create a new updated requirement file.
        reqs_cmd = f"pipreqs --force {self.dst}"
        subprocess.check_call(reqs_cmd, shell=True)

    def _set_requirements(self):
        fname = os.path.join(self.dst, "requirements.txt")

        if os.path.exists(fname) or not self.compute_requirements:
            pass
        else:
            self._make_requirements_file()

        if os.path.exists(fname):
            with open(fname, "r") as file:
                # Read the contents of the file
                contents = file.read()
                # Split the contents into lines
                lines = contents.splitlines()
                # Create a list of package names
                package_list = []
                # Iterate through the lines and append each line (package name) to the
                # list
                for line in lines:
                    package_list.append(line)
            self.requirements = package_list

    def _getGitRepo(self):

        import git

        try:
            repo = git.Repo(search_parent_directories=True)
        except git.exc.InvalidGitRepositoryError:
            msg = os.getcwd() + ". To use the GitVM, the code must belong to a git repository!"
            raise git.exc.InvalidGitRepositoryError(msg)

        self._handle_untracked_files(repo)
        self._handle_commit_state(repo)
        return repo


def _disp_uncommited_files(repo):
    unstaged_files = repo.index.diff(None)
    staged_files = repo.index.diff("HEAD", staged=True)
    all_files = unstaged_files + staged_files
    for change in all_files:
        file_name = change.a_path
        _printc(_bcolors.FAIL, file_name)


def _disp_untracked_files(repo):
    from git.compat import defenc

    status = repo.git.status(porcelain=True, untracked_files=False, as_process=True)

    prefix = "?? "
    untracked_files = []
    for line in status.stdout:
        line = line.decode(defenc)
        if not line.startswith(prefix):
            continue
        filename = line[len(prefix) :].rstrip("\n")
        # Special characters are escaped
        if filename[0] == filename[-1] == '"':
            filename = filename[1:-1]
            # WHATEVER ... it's a mess, but works for me
            filename = filename.encode("ascii").decode("unicode_escape").encode("latin1").decode(defenc)
        untracked_files.append(filename)

    for name in untracked_files:
        _printc(_bcolors.FAIL, name)
