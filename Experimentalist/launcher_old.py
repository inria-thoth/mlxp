# class for submitting jobs to cluster
# take inspiration from : https://ai.facebook.com/blog/open-sourcing-submitit-a-lightweight-tool-for-slurm-cluster-computation/

import logging
import os
from stat import S_IREAD
import shutil
import subprocess

import hydra
from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig, ListConfig, OmegaConf
from datetime import datetime
from Experimentalist.logger import Logger

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def filter_fn(x):
    return not (x.startswith("launcher") or x.startswith("cluster"))


def handle_OAR(cfg: DictConfig, hydra_cfg: DictConfig, dst) -> str:
    """
    Output example:
    -----------------
    #!/usr/bin/zsh

    #OAR -l walltime=12:00:00
    #OAR -n mybigbeautifuljob
    #OAR -t besteffort
    #OAR -t idempotent
    #OAR -p gpumem>'20000'
    #OAR -p gpumodel='p100' #NOTE: last property takes priority
    #OAR -d /path/to/dir/
    #OAR -E /path/to/file.stderr
    #OAR -O /path/to/file.stdout

    source gpu_setVisibleDevices.sh

    conda activate $my_env

    python train.py $overrides
    """
    # Setup
    cmd = ""
    cluster = cfg.cluster
    launcher = cfg.launcher
    # Create OAR folder

    # now = datetime.now()
    # date = now.strftime("date_%d_%m_%Y_time_%H")
    # root = os.path.join(dst,cfg.logs.log_dir,cluster.engine,date,cfg.logs.log_name)
    # os.makedirs(root, exist_ok=True)
    # job_id = None
    # job_id, log_dir = _make_run_dir(job_id,root)

    _logger = Logger(cfg)
    job_id, log_dir = _logger.get_log_dir()

    #####################
    # Construct command #
    #####################

    # Shebang
    cmd += f"#!{cluster.shell.bin_path}\n"
    # Space
    cmd += "\n"
    # NOTE: use hours instead of walltime
    # Walltime
    cmd += f"{cluster.directive} -l core={launcher.cpus},walltime={launcher.hours}:00:00\n"
    if cluster.name:
        cmd += f"{cluster.directive} -p cluster='{cluster.name}'\n"
    # Remove overrides from launcher/cluster
    overrides = hydra_cfg.overrides.task
    # Job name
    filtered_args = list(filter(filter_fn, overrides))
    job_name = ",".join([a.split(".")[-1] for a in filtered_args])
    # Limit job_name length
    job_name = job_name[: min(50, len(job_name))]
    cmd += f"{cluster.directive} -n {launcher.cmd}|{job_name}\n"
    # Write exp id to file
    #with open("id", "w") as f:
    #    f.write(cfg.id)
    # Best effort
    # cmd += f"{cluster.directive} -c {cluster.name}\n"

    if launcher.besteffort:
        cmd += f"{cluster.directive} -t besteffort\n"
    # Idempotent (i.e. automatic restart)
    if launcher.idempotent:
        cmd += f"{cluster.directive} -t idempotent\n"
    # GPU memory property
    # NOTE gpumem is meant to be in Gb
    gpumem = f"{launcher.gpumem}000"
    if launcher.gpumem is not None:
        cmd += f"{cluster.directive} -p gpumem>{gpumem!r}\n"
    # GPU model property
    # NOTE: `gpumodel` takes priority over `gpumem` if both are defined
    if launcher.gpumodel is not None:
        if type(launcher.gpumodel) == ListConfig:
            cmd += f"{cluster.directive} -p "
            cmd += " or ".join([f"gpumodel={m!r}" for m in launcher.gpumodel])
            cmd += "\n"
        else:
            cmd += f"{cluster.directive} -p gpumodel={launcher.gpumodel!r}\n"
    # path to dir
    cmd += f"{cluster.directive} -d {hydra_cfg.runtime.cwd}\n"
    # Job stderr
    cwd = dst
    err_path = os.path.join(log_dir, "log.stderr")
    cmd += f"{cluster.directive} -E {err_path}\n"
    # Job stdout
    out_path = os.path.join(log_dir, "log.stdout")
    cmd += f"{cluster.directive} -O {out_path}\n"
    # Space
    cmd += "\n"
    cmd += 'echo "Host is `hostname`"\n'
    # Shell instance
    cmd += f"source {cluster.shell.config_path}\n"
    # Space
    cmd += "\n"
    # source gpu_setVisibleDevices.sh
    cmd += f"{cluster.cleanup}\n"
    # Space
    cmd += "\n"
    # conda environment
    cmd += f"conda activate {cluster.conda_env}\n"
    # Space
    cmd += "\n"
    # Change directory
    cmd += f"cd {dst}"
    # Space
    cmd += "\n"
    # Python command
    args = " ".join(filtered_args)
    now = datetime.now()
    date = now.strftime("%d/%m/%Y")
    time = now.strftime("%H:%M:%S")

    cmd += f"{launcher.app} {launcher.cmd} {args} system.date='{date}' system.time='{time}'"
    cmd += f" logs.log_id='{job_id}'"
    return cmd,log_dir


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


def handle_SLURM(cfg: DictConfig, hydra_cfg: DictConfig, dst) -> str:
    """"""
    # Setup
    cmd = ""
    cluster = cfg.cluster
    launcher = cfg.launcher
    # Create SLURM folder
    #os.makedirs(os.path.join(os.path.abspath(cfg.logs.log_dir),cluster.engine), exist_ok=True)
    # now = datetime.now()
    # date = now.strftime("date_%d_%m_%Y_time_%H")
    # root = os.path.join(dst,cfg.logs.log_dir,cluster.engine,date,cfg.logs.log_name)
    # os.makedirs(root, exist_ok=True)
    # job_id = None
    # job_id, log_dir = _make_run_dir(job_id,root)
    # Copy config file when job is created
    #shutil.copy2(".hydra/config.yaml", "config.yaml")

    _logger = Logger(cfg)
    job_id, log_dir = _logger.get_log_dir()

    # Shebang
    cmd += f"#!{cluster.shell.bin_path}\n"
    # Space
    cmd += "\n"
    # Remove overrides from launcher/cluster
    overrides = hydra_cfg.overrides.task
    # Job name
    filtered_args = list(filter(filter_fn, overrides))
    job_name = ",".join([a.split(".")[-1] for a in filtered_args])
    cmd += f"{cluster.directive} --job-name={launcher.cmd}|{job_name}\n"
    # Write exp id to file
    #with open("id", "w") as f:
    #   f.write(cfg.id)
    # Check if partition
    if launcher.partition is not None:
        cmd += f"{cluster.directive} --partition={launcher.partition}\n"
    # ntasks
    if launcher.ntasks is not None:
        cmd += f"{cluster.directive} --ntasks={launcher.ntasks}\n"
    # gres
    cmd += f"{cluster.directive} --gres={launcher.gres}\n"
    # cpus-per-task
    cmd += f"{cluster.directive} --cpus-per-task={launcher.cpus_per_task}\n"
    # nodes
    if launcher.nodes is not None:
        cmd += f"{cluster.directive} --nodes={launcher.nodes}\n"
    # ntasks-per-nodes
    if launcher.ntasks_per_node is not None:
        cmd += f"{cluster.directive} --ntasks-per-node={launcher.ntasks_per_node}\n"
    # C
    if launcher.C is not None:
        cmd += f"{cluster.directive} -C {launcher.C}\n"
    # hint
    cmd += f"{cluster.directive} --hint={launcher.hint}\n"
    # change time processing (only consider hours)
    # time
    hours = launcher.hours
    cmd += f"{cluster.directive} --time={hours}:00:00\n"
    # output
    cwd = dst
    out_path = os.path.join(log_dir, "log.stdout")
    cmd += f"{cluster.directive} --output={out_path}\n"
    # error
    err_path = os.path.join(log_dir, "log.stderr")
    cmd += f"{cluster.directive} --error={err_path}\n"
    # infer QoS based on hours value
    # QoS
    qos = infer_qos(hours)
    cmd += f"{cluster.directive} --qos={qos}\n"
    # account
    cmd += f"{cluster.directive} --account={cluster.account}"
    # Space
    cmd += "\n"
    # Module purge
    cmd += f"{cluster.cleanup}\n"
    # Space
    cmd += "\n"
    # source conda shell
    #cmd += f". {cluster.conda_path}"
    # Space
    #cmd += "\n"
    # conda activate
    cmd += f"conda activate {cluster.conda_env}"
    # Space
    cmd += "\n"
    # Change directory
    cmd += f"cd {dst}"
    # Space
    cmd += "\n"
    # Code execution
    args = " ".join(filtered_args)
    # Script path

    now = datetime.now()
    date = now.strftime("%d/%m/%Y")
    time = now.strftime("%H:%M:%S")

    cmd += f"srun {launcher.app} -u {launcher.cmd} {args} system.date={date} system.time={time}"
    cmd += f" logs.log_id='{job_id}'"
    return cmd,log_dir


def create(cfg: DictConfig) -> None:
    dst = create_working_dir(cfg)
    logger.debug(cfg)
    cluster = cfg.cluster
    # Some assertions on possible combinations
    launcher = cfg.launcher
    assert (
        launcher.name in cluster.launchers
    ), f"{launcher.name} not in {cluster.launchers}"
    # Get Hydra config
    hydra_cfg = HydraConfig.get()
    # Construct command
    if cluster.engine == "OAR":
        cmd,log_dir = handle_OAR(cfg, hydra_cfg, dst)
    elif cluster.engine == "SLURM":
        cmd,log_dir = handle_SLURM(cfg, hydra_cfg, dst)
    print(cmd)
    logger.info(f"Selected cluster: {cluster.engine}")
    logger.info(
        f"Using {cluster.shell.bin_path!r} for shebang,"
        f" {cluster.directive!r} as directive"
    )
    logger.debug(cmd)

    # Get path to script

    sh_path = os.path.join(log_dir, launcher.filename)

    # Write down .sh file
    with open(sh_path, "w") as f:
        f.write(cmd)

    # Make file executable
    chmod_cmd = f"chmod +x {sh_path!r}"
    subprocess.check_call(chmod_cmd, shell=True)
    # Connect to frontal node and invoke launch command
    #if cluster.node is not None:
    #    launch_cmd = f'ssh {cluster.node} "{cluster.cmd} {sh_path!r}"'
    #else:
    launch_cmd = f"{cluster.cmd} {sh_path!r}"
    logger.debug(launch_cmd)
    # Launch job over SSH
    subprocess.check_call(launch_cmd, shell=True)
    

    logging.info(f"Job launched!")

def create_working_dir(cfg: DictConfig):
    # creates a copy of the  current dir and returns its path
    src = os.getcwd()
    dirname, filename= os.path.split(src)
    now = datetime.now()
    date = now.strftime("date_%d_%m_%Y")
    time = now.strftime("time_%H_%M")
    target_name = '.'+date+'_'+time
    dst = os.path.join(dirname,filename,'data','workdirs',filename,target_name)
    if not os.path.exists(dst):
        shutil.copytree(src, dst, symlinks=True, ignore=None)
    #permission_dir(dst)
    os.chdir(dst)
    return dst




