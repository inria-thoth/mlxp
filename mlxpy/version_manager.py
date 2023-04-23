import os
import abc
from omegaconf import OmegaConf
import omegaconf
import subprocess
import yaml
from typing import Any, Dict

from mlxpy._internal.interactive_mode import bcolors, printc, inputc

class VersionManager(abc.ABC):
    """
    An abstract class whose children allow custumizing the working directory of the run.
    
    """

    def __init__(self):

        self._interactive_mode = False
        self._vm_choices_file = ""
        self._existing_choices = False
        self.vm_choices = {}

    def _handle_interactive_mode(self, mode:bool, 
                                 vm_choices_file: './vm_choices.yaml')->None:
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
    def get_info(self)->Dict[str, Any]:
        """
            Returns a dictionary containing 
            information about the version used for the run.

            :return: Dictionary containing 
            information about the version used for the run.

            :rtype: Dict[str, Any]         
        """

        pass


    @abc.abstractmethod
    def make_working_directory(self)->str:
        """
            Returns a path to the target working directory from which 
            jobs submitted to a cluster in batch mode will be executed.     
            
            :rtype: str
            :return: A path to the target working directory
            
        """

        pass 



class GitVM(VersionManager):
    """
    GitVM creates a copy of the current directory 
    based on the latest commit, if it doesn't exist already, 
    then sets the working directory to this copy. 
    This class allows separting development code from 
    code deployed in a cluster. 
    It also allows recovering exactly the code used for a given run.
    
    .. py:attribute:: parent_target_work_dir
        :type: str 

        The target parent directory of 
        the new working directory returned by the version manager

    .. py:attribute:: compute_requirements
        :type: bool 

        When set to true, the version manager stores a list of requirements and their version.
    
    """

    def __init__(self,
                parent_target_work_dir: str,
                compute_requirements: bool):
        super().__init__()

        self.parent_target_work_dir = os.path.abspath(parent_target_work_dir)
        self.compute_requirements = compute_requirements
        self.dst = None 
        self.commit_hash = None
        self.repo_path = None
        self.work_dir = os.getcwd()
        self.requirements = ["UNKNOWN"]

        
        

    def get_info(self)->Dict[str, Any]:
        """
            Returns a dictionary containing 
            information about the version used for the run:
                - requirements: the dependencies of the code and their versions. Empty if no requirements file was found.
                - commit_hash: The hash of the latest commit.
                - repo_path: Path to the repository.  
            :return: Dictionary containing 
            information about the version used for the run.

            :rtype: Dict[str, Any]         
        """
        return {"requirements": self.requirements,
                        "commit_hash":self.commit_hash,
                        "repo_path": self.repo_path
                        }
                        
    def make_working_directory(self)->str:
        
        """     
        This function creates and returns a target working directory. 
        Depending on the user's choice, the returned directory is either: 
            - The current working directory.
            - A directory under self.parent_target_work_dir/repo_name/latest_commit_hash. 
            In this case, a copy of the code based on the latest git commit is created and used to run the experiment. 

        :rtype: str
        :return: A path to the target working directory
        """
        
        repo = self._getGitRepo()
        repo_root = repo.git.rev_parse("--show-toplevel")
        relpath = os.path.relpath(os.getcwd(), repo_root)
        self.repo_path = repo.working_tree_dir
        repo_name = self.repo_path .split("/")[-1]
        self.commit_hash = repo.head.object.hexsha
        target_name = os.path.join(repo_name, self.commit_hash)
        parent_work_dir = self.parent_target_work_dir
        self.dst = os.path.join(parent_work_dir, target_name)

        self._handle_cloning(repo, relpath)
        self._save_vm_choice()
        
        return self.work_dir
    
        



    def _clone_repo(self,repo):
        if not os.path.isdir(self.dst):
            printc(bcolors.OKBLUE, f"Creating a copy of the repository at {self.dst}")
            repo.clone(self.dst)
            if self.compute_requirements:
                self._make_requirements_file()
        else:
            if not self._existing_choices:
                printc(bcolors.OKBLUE,f"Found a copy of the repository with commit-hash: {self.commit_hash}")
                printc(bcolors.OKBLUE,f"Run will be executed from {self.dst}")
        
    def _handle_cloning(self, repo, relpath):
        while True:                
            if self._interactive_mode:
                if self._existing_choices:
                    choice = self.vm_choices['cloning']
                else: 
                    printc(bcolors.OKGREEN,f"Where would you like to run your code from? (a/b):")
                    if os.path.isdir(self.dst):
                        print(f"{bcolors.OKGREEN} a {bcolors.ENDC}: Execute code from an existing copy of the repository based on the latest commit.")
                        print(f"The copy is located in: {self.dst}")
                    else:
                        print(f"{bcolors.OKGREEN}a{bcolors.ENDC}: Create a copy of the repository based on the latest commit and execute code from there.")
                        print(f"The copy will be created in: {self.dst}")
                    print(f"{bcolors.OKGREEN}b{bcolors.ENDC}: Execute code from the main repository")
                    choice = input(f"{bcolors.OKGREEN}Please enter you answer (a/b):{bcolors.ENDC}")
                    self.vm_choices['cloning'] = choice
                
                if choice=='a':
                    self._clone_repo(repo)
                    self._set_requirements()
                    self.work_dir = os.path.join(self.dst, relpath)
                    break 
                elif choice=='b':
                    if not self._existing_choices:
                        printc(bcolors.OKBLUE,f"Run will be executed from the current repository {self.dst}")
                    break
                else:
                    printc(bcolors.OKBLUE,f"Invalid choice. Please try again. (a/b)")
            else:
                self._clone_repo(repo)
                self._set_requirements()
                self.work_dir = os.path.join(self.dst, relpath)
                break

    def _handle_commit_state(self, repo):
        ignore_msg = "Ingoring uncommitted changes!\n"
        ignore_msg+=bcolors.FAIL + "Warning:" +bcolors.ENDC+"Uncommitted changes will not be taken into account during execution of the jobs!\n"
        ignore_msg+= bcolors.FAIL + "Warning:" +bcolors.ENDC+ "Jobs will be executed from the latest commit"

        while True:
            if self._interactive_mode:
                if self._existing_choices:
                    break
                if repo.is_dirty():    
                    printc(bcolors.OKBLUE,f"There are uncommitted changes in the repository:")
                    _disp_uncommited_files(repo)
                    printc(bcolors.OKGREEN,f"How would you like to handle uncommitted changes? (a/b/c)")
                    print(f"{bcolors.OKGREEN}a{bcolors.ENDC}: Create a new automatic commit before launching jobs.")
                    print(f"{bcolors.OKGREEN}b{bcolors.ENDC}: Check again for uncommitted changes (assuming you manually committed them). ")
                    print(f"{bcolors.OKGREEN}c{bcolors.ENDC}: Ignore uncommitted changes.")
                    choice = input(f"{bcolors.OKGREEN}[Uncommitted changes]: Please enter your choice (a/b/c): {bcolors.ENDC}")
                    if choice == 'a':
                        printc(bcolors.OKBLUE,f"Commiting changes....")
                        output_msg = repo.git.commit("-a", "-m", "mlxpy: Automatically committing all changes")
                        printc(bcolors.OKBLUE, output_msg)
                        
                        if not repo.is_dirty():
                            printc(bcolors.OKBLUE,f"No more uncommitted changes!")
                            break
                    elif choice == 'b':
                        printc(bcolors.OKBLUE,f"Checking again for uncommitted changes...")
                        pass
                    elif choice == 'c':
                        if repo.is_dirty():
                            print(ignore_msg)
                        else:
                            printc(bcolors.OKBLUE,f"No more uncommitted changes found!")
                        break

                    else:
                        printc(bcolors.OKBLUE,f"Invalid choice. Please try again. (a/b/c)")
                else:
                    printc(bcolors.OKBLUE,f"No uncommitted changes!")
                    break
            else:
                print(ignore_msg)
                break             
        
    def _handle_untracked_files(self,repo):
        ignore_msg =bcolors.FAIL + "Warning:" +bcolors.ENDC+ "There are untracked files! \n"
        ignore_msg +=bcolors.FAIL + "Warning:" +bcolors.ENDC+ "Untracked files will not be accessible during execution of the jobs!"


        while True:
            if self._interactive_mode:
                if self._existing_choices:
                    break
                status = repo.git.status()
                print(status)
                if repo.untracked_files:
                    printc(bcolors.OKBLUE,f"There are untracked files in the repository:")
                    _disp_untracked_files(repo)
                    printc(bcolors.OKGREEN,f"How would you like to handle untracked files? (a/b/c)")
                    print(f"{bcolors.OKGREEN}a{bcolors.ENDC}: Add untracked files directly from here?")
                    print(f"{bcolors.OKGREEN}b{bcolors.ENDC}: Check again for untrakced files (assuming you manually added them).")
                    print(f"{bcolors.OKGREEN}c{bcolors.ENDC}: Ignore untracked files.")
                    choice = input(f"{bcolors.OKGREEN}[Untracked files]: Please enter your choice (a/b/c):{bcolors.ENDC}")
                    if choice=='a':
                        print("Untracked files:")
                        _disp_untracked_files(repo)
                        printc(bcolors.OKGREEN,f"Please select files to be tracked (comma-separated, hit Enter to skip):")
                        
                        files_input = input()

                        # If user input is not empty
                        if files_input:
                            # Split user input by commas
                            files_to_add = files_input.split(",")

                            # Add selected files
                            for file in files_to_add:
                                repo.git.add(file.strip())
                            # Commit the changes
                            #repo.index.commit("mlxpy: Committing selected files ")
                            if not repo.untracked_files:
                                break
                        else:
                            printc(bcolors.OKBLUE,f"No files added. Skipping...")
                            print(ignore_msg)
                            break
                    elif choice=='b':
                        printc(bcolors.OKBLUE,f"Checking again for untracked files...")
                        pass
                    elif choice=='c':
                        if repo.untracked_files:
                            print(ignore_msg)
                        else:
                            printc(bcolors.OKBLUE,f"No more untracked files!")
                            printc(bcolors.OKBLUE,f"Continuing checks ...")
                        break
                    else:
                        printc(bcolors.OKBLUE,f"Invalid choice. Please try again. (a/b/c)")

                else:
                    printc(bcolors.OKBLUE,f"No untracked files!")
                    printc(bcolors.OKBLUE,f"Continuing checks ...")
                    break
            else: 
                print(ignore_msg)
                break 


    def _make_requirements_file(self):

        printc(bcolors.OKBLUE,f"No requirements file found")
        printc(bcolors.OKBLUE,f"Generating it using pipreqs")
        # Create a new updated requirement file.
        reqs_cmd = f"pipreqs --force {self.dst}" 
        subprocess.check_call(reqs_cmd, shell=True)


    def _set_requirements(self):
        fname = os.path.join(self.dst, 'requirements.txt')
        

        if os.path.exists(fname) or not self.compute_requirements:
            pass
        else:
            self._make_requirements_file()

        if os.path.exists(fname):
            with open(fname, 'r') as file:
            # Read the contents of the file
                contents = file.read()
                # Split the contents into lines
                lines = contents.splitlines()
                # Create a list of package names
                package_list = []
                # Iterate through the lines and append each line (package name) to the list
                for line in lines:
                    package_list.append(line)
            self.requirements =  package_list

        


    def _getGitRepo(self):

        import git
        try:
            repo = git.Repo(search_parent_directories=True)
        except git.exc.InvalidGitRepositoryError:
            msg = os.getcwd() +  ". To use the GitVM, the code must belong to a git repository!"
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
        print("\033[91m" + file_name + "\033[0m")

def _disp_untracked_files(repo):
    import subprocess
    command = ["git", "ls-files", "--others", "--directory", "--exclude-standard", "--no-empty-directory"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    untracked_files_and_folders = [u.decode().strip() for u in process.stdout]

    for name in untracked_files_and_folders:
        print("\033[91m" + name + "\033[0m")


def _disp_untracked_files(repo):
    from git.compat import defenc
    status = repo.git.status( porcelain=True, untracked_files=False, as_process=True)

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
        printc(bcolors.FAIL,name )




