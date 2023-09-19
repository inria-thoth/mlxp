import mlxp
import torch
#import numpy
from core_app import DataLoader, OneHiddenLayer, train_epoch

def set_seeds(seed):
    import torch
    torch.manual_seed(seed)




@mlxp.launch(config_path='configs',
             seeding_function=set_seeds)

def train(ctx: mlxp.Context)->None:


    cfg = ctx.config
    logger = ctx.logger


    try:
        checkpoint = logger.load_checkpoint(log_name= 'last_ckpt')
        start_epoch = checkpoint['epoch']+1
        model = checkpoint['model']
    except:
        start_epoch = 0
        model = OneHiddenLayer(d_int=cfg.data.d_int, 
                        n_units = cfg.model.num_units)

    model = model.to(cfg.data.device)
    optimizer = torch.optim.SGD(model.parameters(), 
                          lr=cfg.optimizer.lr)
    dataloader = DataLoader(cfg.data.d_int,
                            cfg.data.device)         

    print(f"Starting from epoch: {start_epoch}")
    for epoch in range(start_epoch, cfg.num_epoch):

        train_err = train_epoch(dataloader,
                                model,
                                optimizer)

        logger.log_metrics({'loss': train_err.item(),
                            'epoch': epoch}, log_name='train')
        
        logger.log_checkpoint({'model': model,
                               'epoch':epoch}, log_name='last_ckpt' )

    print(f"Completed training with a learning rate of {cfg.optimizer.lr}")

    assert True


if __name__ == "__main__":
    
    train()










