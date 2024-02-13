import atexit
import os
import signal
import sys
import tempfile

import yaml

from mlxp.scheduler import Schedulers_dict

scheduler_env_var = "MLXP_SCHEDULER"


def process_bash_script(bash_script_name):
    shebang = ""
    scheduler = {"option_cmd": [], "env_cmd": [], "name": "NoScheduler", "shell_path": ""}

    with open(bash_script_name, "r") as script_file:
        for line in script_file:
            line = line.strip()

            if not line:
                continue

            if line.startswith("#!"):
                shebang = line[2:]
                scheduler["shell_path"] = shebang
                continue  # Skip shebang line

            elif line.startswith("#"):
                # Assuming scheduler instructions are comments starting with '#'
                splitted_line = line.split(" ")

                if len(splitted_line) > 1:
                    directive = splitted_line[0]
                    option_cmd = " ".join(splitted_line[1:])
                    if directive in Schedulers_dict:
                        scheduler["name"] = Schedulers_dict[directive]["name"]
                        scheduler["option_cmd"].append(option_cmd)

            elif not skip_cmd(line):
                scheduler["env_cmd"].append(line)
                continue

    if scheduler["name"] == "NoScheduler":
        print("Warning: No valid scheduler syntax were found")
        print("Valid scheduler")

    configs = {"scheduler": scheduler, "use_scheduler": True}
    return configs, shebang


def skip_cmd(line):
    lower_line = line.lower()
    if lower_line.startswith("python ") or lower_line.startswith("python3 "):
        return True
    else:
        if (" python " in lower_line) or (" python3 " in lower_line):
            return True

    # Skip assignment
    split_eq = line.split("=")
    if len(split_eq) > 1:
        return True
    if line.startswith("cd") or line.startswith("#"):
        return True

    return False


def handle_launch_cmd(bash_cmd, bash_script_name):
    if sys.platform.startswith("win"):
        # Windows
        if bash_script_name.endswith(".sh"):
            command = f"{bash_cmd}  {bash_script_name}"
        elif bash_script_name.endswith(".ps1"):
            command = f"powershell -File {bash_script_name}"
        else:
            command = f"{bash_script_name}"
    else:
        # Assume non-Windows (Unix-like)
        command = f"{bash_cmd}  {bash_script_name}"
    return command


def run_python_script(bash_cmd, bash_script_name, scheduler_file_name):
    cmd = handle_launch_cmd(bash_cmd, bash_script_name)
    envs = os.environ
    envs[scheduler_env_var] = f"{scheduler_file_name}"
    code = os.spawnvpe(os.P_WAIT, bash_cmd, cmd.split(), envs)
    if code == 127:
        sys.stderr.write("{0}: command not found\n".format(bash_cmd))
    else:
        print(code)

    # print(process_output)


def mlxpsub():
    """A function for submitting a script to a job scheduler. 
    Usage: mlxpsub <script.sh>
    
    The 'script.sh' must contain the scheduler's options defining 
    the resource allocation for each individual job.
    Below is an example of 'script.sh'

    :example:

    .. code-block:: console

        #!/bin/bash

        #OAR -l core=1, walltime=6:00:00
        #OAR -t besteffort
        #OAR -t idempotent
        #OAR -p gpumem>'16000'

        python main.py  optimizer.lr=10.,1.,0.1 seed=1,2,3,4
        python main.py  model.num_units=100,200 seed=1,2,3,4

    The command assumes the script contains at least a python command of the form:
    python <python_file_name.py> options_1=A,B,C option_2=X,Y
    where <python_file_name.py> is a python file that uses MLXP for launching. 
    
    MLXP creates a script for each job corresponding to an option setting.
    Each script is located in a directory of the form parent_log_dir/log_id, 
    where log_id is automatically assigned by MLXP for each job. 

    Here is an example of the first created script in 'logs/1/script.sh'
    
    :example:

    .. code-block:: console

        #!/bin/bash
        #OAR -n logs/1
        #OAR -E /root/logs/1/log.stderr
        #OAR -O /root/logs/1/log.stdout
        #OAR -l core=1, walltime=6:00:00
        #OAR -t besteffort
        #OAR -t idempotent
        #OAR -p gpumem>'16000'
    
        cd /root/workdir/
        python main.py  optimizer.lr=10. seed=1
    
    As you can see, MLXP automatically assigns values for 
    the job's name, stdout and stderr file paths, 
    so there is no need to specify those in the original script 'script.sh'.
    These scripts contain the same scheduler's options 
    as in 'script.sh' and a single python command using one specific option setting: optimizer.lr=10. seed=1
    Additionally, MLXP pre-processes the python command to extract its working directory 
    and set it explicitly in the newly created script before the python command. 

    .. note:: 
        It is also possible to have other commands in the 'script.sh', 
        for instance to activate an environment: (conda activate my_env). 
        These commands will be copied from  'script.sh' to  the new created script 
        and placed before the python command. Variable assignments and directory changes
        will be systematically ignored.
    """

    if len(sys.argv) != 2:
        print("Usage: mlxpsub <script.sh>")
        sys.exit(1)

    root = os.getcwd()
    bash_script_name = sys.argv[1]
    script_path = os.path.join(root, bash_script_name)

    scheduler, shebang = process_bash_script(script_path)
    with tempfile.NamedTemporaryFile() as temporary_file:
        yaml.dump(scheduler, temporary_file, encoding=("utf-8"))
        scheduler_file_name = temporary_file.name
        run_python_script(shebang, bash_script_name, scheduler_file_name)


def main():
    mlxpsub()


if __name__ == "__main__":
    main()
