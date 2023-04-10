import os
import abc



class WDManager(abc.ABC):
    """
    An abstract class whose children allow custumizing the working directory of the run.
    
    """


    @abc.abstractmethod
    def make_working_directory(self)->str:
        """
            Returns a path to the target working directory from which 
            jobs submitted to a cluster in batch mode will be executed.     
            
            :rtype: str
            :return: A path to the target working directory
            
        """

        pass 



class LastGitCommitWD(WDManager):
    """
    LastGitCommitWD creates a copy of the current directory 
    based on the latest commit, if it doesn't exist already, 
    then sets the working directory to this copy. 
    This class allows separting development code from 
    code deployed in a cluster. 
    It also allows recovering exactly the code used for a given run.
    
    .. py:attribute:: parent_target_work_dir
        :type: str 

        The target parent directory of the new working directory.

    .. py:attribute:: forceTracking
        :type: bool 

        When set to true, throws an error if there 
        are untracked files in the git repo of the current working directory 

    .. py:attribute:: forceCommit
        :type: bool 

        When set to true, throws an error if there 
        are uncommited changes in the git repo of the current working directory 
    
    """

    def __init__(self,
                parent_target_work_dir: str,
                forceTracking: bool, 
                forceCommit: bool):
        self.parent_target_work_dir = parent_target_work_dir
        self.forceCommit = forceCommit
        self.forceTracking = forceTracking
    def make_working_directory(self)->str:
        
        """     
        This function creates and returns a target working directory under self.parent_target_work_dir
        and containing a copy of the code used to run the experiment based on the latest git commit. 

        :rtype: str
        :return: A path to the target working directory
        :raises UncommitedChangesError: if there are uncommited changes in the git repository 
            containing the current working directory.
        :raises UntrackedFilesError: if there are untracked files in the git repository 
            containing the current working directory.
        """
        repo = self._getGitRepo()
        repo_root = repo.git.rev_parse("--show-toplevel")
        relpath = os.path.relpath(os.getcwd(), repo_root)
        repo_name = repo.working_tree_dir.split("/")[-1]
        commit_hash = repo.head.object.hexsha
        target_name = os.path.join(repo_name, commit_hash)
        parent_work_dir = self.parent_target_work_dir
        dst = os.path.join(parent_work_dir, target_name)
        if not os.path.exists(dst):
            repo.clone(dst)
        work_dir = os.path.join(dst, relpath)
        return work_dir


    def _getGitRepo(self):

        import git
        try:
            repo = git.Repo(search_parent_directories=True)
        except git.exc.InvalidGitRepositoryError:
            raise git.exc.InvalidGitRepositoryError(os.getcwd()) 

        if repo.untracked_files:
            msg = "There are untracked files."
            if self.forceTracking:
                error_msg = msg  + "\n" + "Make sure all files in the repo are either tracked or ignored by git!"
                raise UntrackedFilesError(error_msg)
            else:
                print("Warning: " +msg)

        if repo.is_dirty():
            msg = "There are uncommited changes"
            if self.forceCommit:
                error_msg = error_msg = msg  + "\n" + "Make sure all changes are commited!"
                raise UncommitedChangesError(error_msg)
            else:
                msg = msg + "\n" + "Using code from last commit!"
                print("Warning: "+msg)
        return repo

class CWD(WDManager):
    """
    CWD keeps the default working directory of the run.
    
    """

    def make_working_directory(self)->str:
        """
            Returns the current working directory.     
            
            :rtype: str
            :return: A path to the target working directory
            
        """

        return os.getcwd()


class UncommitedChangesError(Exception):
    """
    Raised when there are uncommited changes in the git repository 
    containing the current working directory
    """
    pass

class UntrackedFilesError(Exception):
    """Raised when there are untracked files in the git repository 
    containing the current working directory
    """
    pass



