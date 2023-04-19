    import experimentalist as expy
    from core_app import DataLoader, Network, Optimizer, Loss

    @expy.launch(config_path='./configs')
    def train(ctx: expy.Context)->None:

        cfg = ctx.config
        logger = ctx.logger

        try:
            checkpoint = logger.load_checkpoint()
            num_epoch = cfg.num_epoch - checkpoint['epoch']-1
            model = checkpoint['model']
        except:
            num_epoch = cfg.num_epoch
            model = Network(n_layers = cfg.model.num_layers)


        optimizer = Optimizer(lr = cfg.optimizer.lr)

        dataloader = DataLoader()
        loss = Loss()
         

        for epoch in range(num_epoch):

            for data in dataloader:
                x,y = data
                pred = model(x)
                train_err = loss(pred, y)
                logger.log_metrics({'train_loss': train_err.item()})

            logger.log_checkpoint({'model': model,
                                   'epoch':epoch} )



    if __name__ == "__main__":
        train()







