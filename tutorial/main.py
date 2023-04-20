import mlxpy as expy
import torch
 

from core_app import DataLoader, OneHiddenLayer

def set_seeds(seed):
    import torch
    torch.manual_seed(seed)

@expy.launch(config_path='./configs',
             seeding_function=set_seeds)

def train(ctx: expy.Context)->None:


    cfg = ctx.config
    logger = ctx.logger


    try:
        checkpoint = logger.load_checkpoint(log_name= 'last_ckpt')
        num_epoch = cfg.num_epoch - checkpoint['epoch']-1
        model = checkpoint['model']
    except:
        num_epoch = cfg.num_epoch
        model = OneHiddenLayer(d_int=cfg.data.d_int, 
                        n_units = cfg.model.num_units)

    model = model.to(cfg.data.device)
    optimizer = torch.optim.SGD(model.parameters(), 
                          lr=cfg.optimizer.lr)
    dataloader = DataLoader(cfg.data.d_int,
                            cfg.data.device)         

    for epoch in range(num_epoch):

        for data in dataloader:
            x,y = data
            pred = model(x)
            train_err = torch.mean((pred-y)**2)
            train_err.backward()
            optimizer.step()
        
        logger.log_metrics({'loss': train_err.item(),
                            'epoch': epoch}, log_name='train')
        
        logger.log_checkpoint({'model': model,
                               'epoch':epoch}, log_name='last_ckpt' )



if __name__ == "__main__":
    train()







