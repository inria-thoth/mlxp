


from hashfs import HashFS
from tinydb import TinyDB
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware, ConcurrencyMiddleware

def get_db_file_manager(root_dir):

    #fs = HashFS(os.path.join(root_dir, "hashfs"), depth=3, width=2, algorithm="md5")

    db = TinyDB(os.path.join(root_dir, "metadata.json"), storage==ConcurrencyMiddleware(CachingMiddleware(JSONStorage)))
    return db
class Saver(object):
    __init__(self, root = "./runs_db", overwrite=None):
        #from .tinydb_hashfs_bases import get_db_file_manager
        root_dir = os.path.abspath(root)
        os.makedirs(root_dir, exist_ok=True)
        db = get_db_file_manager(root_dir)
        self.db = db
        self.runs = db.table("runs")
        self.fs = fs
        self.overwrite = overwrite
        self.run_entry = {}
        self.db_run_id = None
        self.root = root_dir
        
        self.samples_dir = None
        self.checkpoint_dir = None
        self.arrays_dir = None

    def save_config(self,config):
        # config contains only experiment parameters
        # host_info:  slurm id, hostname, gpu , etc
        # meta : run_id, starting time, slum id

        self.db_run_id = None
        host_config = self.get_host_config()
        self.run_entry = config

        """Insert or update the current run entry."""
        if self.db_run_id:
            self.runs.update(self.run_entry, eids=[self.db_run_id])
        else:
            db_run_id = self.runs.insert(self.run_entry)
            self.db_run_id = db_run_id
        self.make_dirs()
        self.log_file()
    def save_data(self,metrics_dict, arrays_dict = None ,index=0):
        if dic_arrays is not None:
            fname = os.path_join(self.root, self.db_run_id, 'arrays', f'arrays_{str(index).zfill(3)}')
            np.savez(fname, **arrays_dict)
            metrics_dict['index'] = index
            metrics_dict['path_arrays'] = fname
        file_name = os.path.join(self.root, self.db_run_id, f'metrics')
        with open(file_name+'.json','a') as f:
            json.dump(metrics_dict,f)
            f.write(os.linesep)
    def save_checkpoint(self, state_dict, epoch, tag, best=False, model_type='torch'):
            path = os.path.join(self.root,self.db_run_id, 'checkpoints', tag+'_'+str({epoch})+'.pth')
            if model=='torch':
                torch.save(state_dict, path)
                print(f'Saved model parameters to {path}')

    def log_file(self):
        if self.log_to_file:
            log_file = open(os.path.join(self.root,self.db_run_id, f'log.txt'), 'w', buffering=1)
            sys.stdout = log_file
            sys.stderr = log_file

    def make_dirs(self):
        os.makedirs(self.root, exist_ok=True)
        self.arrays_dir = os.path_join(self.root, self.db_run_id, 'arrays')
        os.makedirs(arrays_dir, exist_ok=True)
        self.checkpoint_dir = os.path_join(self.root, self.db_run_id, 'checkpoints')
        os.makedirs(checkpoint_dir, exist_ok=True)
        self.samples_dir = os.path_join(self.root, self.db_run_id, 'samples')
        os.makedirs(samples_dir, exist_ok=True)
class Reader(object):
    __init__(self,root):
        root_dir = os.path.abspath(root)
        if not os.path.exists(root_dir):
            raise IOError("Path does not exist: %s" % root)

        self.db = get_db_file_manager(root_dir)
        self.runs = db.table("runs")


    def search(self, *args, **kwargs):
        """Wrapper to TinyDB's search function."""
        return self.runs.search(*args, **kwargs)


