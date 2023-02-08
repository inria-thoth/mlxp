# class for submitting jobs to cluster

import os
import subprocess
from hydra.core.hydra_config import HydraConfig
from datetime import datetime
import omegaconf
from omegaconf.errors import OmegaConfBaseException

OAR_config = {
    "directive": "#OAR",
    "cleanup_cmd": "",
    "subission_cmd": "oarsub -S",
}

SLURM_config = {
    "directive": "#SBATCH",
    "cleanup_cmd": "module purge",
    "subission_cmd": "sbatch",
}

class JobSubmissionError(Exception):
    """Raised when failed to submit a job using a scheduler"""
    pass


def submit_job(logger):
    cfg= logger.config
    work_dir, root_dir = create_working_dir(cfg)
    system = cfg.system
    cluster = cfg.cluster
    hydra_cfg = HydraConfig.get()
    overrides = hydra_cfg.overrides.task
    filtered_args = list(filter(filter_fn, overrides))
    args = " ".join(filtered_args)
    log_dir = logger.run_dir
    job_id = logger.run_id
    job_name = log_dir.split(os.sep)
    job_name = os.sep.join(job_name[-2:])
    cmd, subission_cmd = create_job_string(
        system, cluster, job_name, job_id, work_dir, root_dir, log_dir, args
    )
    print(cmd)
    job_path = save_job(cmd, log_dir)
    process_output, isJobSubmitted = _submit_job(job_path, subission_cmd)
    if isJobSubmitted:
        update_job_id(logger, cluster.engine, process_output)
        logger.log_config()


def update_job_id(logger, engine, process_output):
    if engine == "OAR":
        job_id = process_output.decode("utf-8").split("\n")[-2].split("=")[-1]

    omegaconf.OmegaConf.set_struct(logger.config, True)
    with omegaconf.open_dict(logger.config):
        logger.config.system.cluster_job_id = job_id
    omegaconf.OmegaConf.set_struct(logger.config, False)


def _submit_job(job_path, subission_cmd):
    chmod_cmd = f"chmod +x {job_path!r}"
    subprocess.check_call(chmod_cmd, shell=True)
    launch_cmd = f"{subission_cmd}  {job_path!r}"
    isJobSubmitted = False
    # Launch job over SSH
    try:
        process_output = subprocess.check_output(launch_cmd, shell=True)
        isJobSubmitted = True
        print(process_output)
        print("Job launched!")

    except subprocess.CalledProcessError as e:
        print(e.output)
        raise JobSubmissionError(f"Failed to launch the job! Might need to check the scheduler's command")
    return process_output, isJobSubmitted


def save_job(cmd_string, log_dir):
    job_path = os.path.join(log_dir, "script.sh")
    with open(job_path, "w") as f:
        f.write(cmd_string)
    return job_path


def create_job_string(
    system, cluster, job_name, job_id, work_dir, root_dir, log_dir, args
):
    err_path = os.path.join(log_dir, "log.stderr")
    out_path = os.path.join(log_dir, "log.stdout")
    cluster_config, make_cluster_command = get_cluster(cluster)
    cleanup_cmd = cluster_config["cleanup_cmd"]
    subission_cmd = cluster_config["subission_cmd"]
    cmd = script_header(system.shell_path)
    cmd += make_cluster_command(cluster, job_name, out_path, err_path)
    cmd += main_command(system, cleanup_cmd, work_dir, root_dir, args, job_id)
    return cmd, subission_cmd


def get_cluster(cluster):
    if cluster.engine == "OAR":
        cluster_config = OAR_config
        make_cluster_command = make_OAR_command
    elif cluster.engine == "SLURM":
        cluster_config = SLURM_config
        make_cluster_command = make_SLURM_command
    else:
        raise NotImplementedError
    if "cleanup_cmd" in cluster:
        cluster_config["cleanup_cmd"] = cluster.cleanup_cmd

    return cluster_config, make_cluster_command


def script_header(bin_path):
    return f"#!{bin_path}\n"


def main_command(system, cleanup_cmd, work_dir, root_dir, args, job_id):

    now = datetime.now()
    date = now.strftime("%d/%m/%Y")
    time = now.strftime("%H:%M:%S")
    values = ["", f"source {system.shell_config_path}", f"{cleanup_cmd}"]
    try:
        values += [f"{system.env}"]
    except OmegaConfBaseException:
        pass

    values += [
        f"cd {work_dir}",
        f"{system.app} {system.cmd} {args} ++system.date='{date}' \
            ++system.time='{time}'  ++logs.log_id={job_id}\
            ++logs.root_dir={root_dir} ",
    ]
    values = [f"{val}\n" for val in values]
    return "".join(values)


def make_OAR_command(job_scheduler, job_name, out_path, err_path):

    values = [
        f"-n {job_name}",
        f"-E {err_path}",
        f"-O {out_path}",
        #                f"-d {hydra_cfg.runtime.cwd}",
    ]
    values += job_scheduler.cmd

    directive = OAR_config["directive"]
    values = [f"{directive} {val}\n" for val in values]
    return "".join(values)


def make_SLURM_command(job_scheduler, job_name, out_path, err_path):

    values = [
        f"--job-name={job_name}",
        f"--output={out_path}",
        f"--error={err_path}",
        # f"--account={system.account}",
    ]

    values += job_scheduler.cmd

    directive = SLURM_config["directive"]
    values = [f"{directive} {val}\n" for val in values]
    return "".join(values)


def getGitRepo(isForceGitClean):
    import git

    repo = git.Repo(search_parent_directories=True)
    if repo.untracked_files:
        msg = "Untracked files"
        print("Warning: " +msg)

    if repo.is_dirty():
        msg = "Uncommited changes"
        if isForceGitClean:
            raise Exception(msg)
        else:
            print("Warning: "+msg)
    return repo


def create_working_dir(cfg):
    # creates a copy of the  current dir and returns its path

    src = os.getcwd()
    root_dir = os.path.abspath(cfg.logs.root_dir)
    work_dir = os.path.join(root_dir, cfg.logs.work_dir)
    repo = getGitRepo(cfg.system.isForceGitClean)
    repo_root = repo.git.rev_parse("--show-toplevel")
    relpath = os.path.relpath(src, repo_root)
    repo_name = repo.working_tree_dir.split("/")[-1]
    commit_hash = repo.head.object.hexsha
    target_name = os.path.join(repo_name, commit_hash)
    dst = os.path.join(work_dir, target_name)
    if not os.path.exists(dst):
        repo.clone(dst)
    return os.path.join(dst, relpath), root_dir


def ignorePath(paths):
    def ignoref(directory, contents):
        return (
            f
            for f in contents
            if os.path.abspath(os.path.join(directory, f)) in paths
            or f == "multirun.yaml"
        )

    return ignoref


def filter_fn(x):
    return "system.isBatchJob" not in x


def infer_qos(h):
    # affect qos based on hours asked
    if 0 <= h <= 2:
        return "qos_gpu-dev"
    elif h <= 20:
        return "qos_gpu-t3"
    elif h <= 100:
        return "qos_gpu-t4"
    else:
        raise ValueError(f"hours value cannot exceed 100, here: {h}")
