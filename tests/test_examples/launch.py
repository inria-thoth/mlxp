import mlxp
import numpy as np

def set_seeds(seed):
    np.random.seed(seed)




@mlxp.launch(config_path='./configs',
             seeding_function=set_seeds)

def main(ctx: mlxp.Context)->None:


    cfg = ctx.config
    logger = ctx.logger

    for epoch in range(cfg.num_epoch):



        logger.log_metrics({'loss': np.random.rand(),
                            'epoch':epoch}, log_name='train')
        logger.log_metrics({'loss': np.random.rand(),
                            'epoch':epoch}, log_name='test')
        
        logger.log_checkpoint({'data': np.array([cfg.data.d_int])}, log_name='last_ckpt' )


if __name__ == "__main__":
    
    main()










