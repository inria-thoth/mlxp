# class for submitting jobs to cluster

import os
import shutil
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


def submit_job(cfg, logger):
    work_dir = create_working_dir()
    # logger.debug(cfg)
    system = cfg.system
    cluster = cfg.cluster
    hydra_cfg = HydraConfig.get()
    overrides = hydra_cfg.overrides.task
    filtered_args = list(filter(filter_fn, overrides))
    args = " ".join(filtered_args)
    job_id, log_dir = logger.get_log_dir()
    job_name = log_dir.split(os.sep)
    job_name = os.sep.join(job_name[-2:])
    cmd, subission_cmd = create_job_string(
        system, cluster, job_name, job_id, work_dir, log_dir, args
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
    # Launch job over SSH
    subprocess.check_call(launch_cmd, shell=True)
    isJobSubmitted = False
    try:
        process_output = subprocess.check_output(launch_cmd, shell=True)
        isJobSubmitted = True
        print("Job launched!")
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise
    return process_output, isJobSubmitted


def save_job(cmd_string, log_dir):
    job_path = os.path.join(log_dir, "script.sh")
    with open(job_path, "w") as f:
        f.write(cmd_string)
    return job_path


def create_job_string(system, cluster, job_name, job_id, work_dir, log_dir, args):
    err_path = os.path.join(log_dir, "log.stderr")
    out_path = os.path.join(log_dir, "log.stdout")
    cluster_config, make_cluster_command = get_cluster(cluster)
    cleanup_cmd = cluster_config["cleanup_cmd"]
    subission_cmd = cluster_config["subission_cmd"]
    cmd = script_header(system.shell_path)
    cmd += make_cluster_command(cluster, job_name, out_path, err_path)
    cmd += main_command(system, cleanup_cmd, work_dir, args, job_id)
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


def main_command(system, cleanup_cmd, work_dir, args, job_id):

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
            ++system.time='{time}'  ++logs.log_id={job_id}",
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


def create_working_dir():
    # creates a copy of the  current dir and returns its path
    src = os.getcwd()
    dirname, filename = os.path.split(src)
    now = datetime.now()
    date = now.strftime("date_%d_%m_%Y")
    time = now.strftime("time_%H_%M")
    target_name = "." + date + "_" + time
    dst = os.path.join(dirname, filename, "data", "workdirs", filename, target_name)
    if not os.path.exists(dst):
        shutil.copytree(src, dst, symlinks=True, ignore=None)
    # permission_dir(dst)
    os.chdir(dst)
    return dst


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
