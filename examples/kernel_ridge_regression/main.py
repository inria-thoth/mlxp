import experimentalist as expy


@expy.launch(config_name="config.yaml", config_path="./configs")
def main(logger):
    cfg = logger.config_dict
    for i in range(cfg.max_iter):
        metrics = {"loss": i * cfg.system.seed, "iteration": i}
        logger.log_metric(metrics, file_name="metrics")
        print(metrics)

if __name__ == "__main__":
    main()
