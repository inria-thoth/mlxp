import experimentalist as expy


@expy.launch(config_name="config.yaml", config_path="./configs")
def main(logger):

    for i in range(cfg.max_iter):
        metrics = {"loss": i * cfg.system.seed, "iteration": i}
        logger.log_metric(metrics, tag="")


if __name__ == "__main__":
    main()
