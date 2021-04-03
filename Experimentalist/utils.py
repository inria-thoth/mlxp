



def make_all_dirs(root, datasets, models,methods):
    all_paths = [] 
    for d in datasets:
        for m in models:
            for method in methods:
                all_paths.append(os.path.join(root, d, m, method))
    return all_paths


def get_status(reason):
    if reason.startswith('('):
        return 'Queued'
    elif reason.startswith('gpu'):
        return 'Running'
def get_slurm_jobs(query=''):
    out = os.popen('squeue ' + query ).read() 
    lines = out.splitlines()
    reader = csv.reader(lines, delimiter=' ')
    out = [ [row[11], row[-1]] for row in reader]
    out = out[1:]
    job_id = [int(a[0]) for a in out]
    status = [get_status(a[1]) for a in out]
    return job_id, status



def get_time_index(x):
    Slurm_id = x.split('_')[1].split('.')[0]
    if not Slurm_id=='':
        Slurm_id = int(Slurm_id)
    else:
        Slurm_id = -1
    return Slurm_id
def get_slurm_index(x):
    #import pdb
    #pdb.set_trace()
    Slurm_id = x.split('_')[-1].split('.')[0]
    if not Slurm_id=='':
        Slurm_id = int(Slurm_id)
    else:
        Slurm_id = -1
    return Slurm_id


def get_slurm_status(epoch, file_name, jobs_ids,status, Total_epochs = 1990):
    if epoch >= Total_epochs:
        return 'Done'
    else:
        slurm_id = get_slurm_index(file_name)
        if slurm_id in jobs_ids:
            return 'Running'
        else:
            if slurm_id==-1:
                return 'Unknown'
            else:
                return 'Failed'

def find_last_file_from_path(path):
    if os.path.exists(path):
        files = [file for file in os.listdir(path) if file.startswith('samples')]
        
        if len(files)==0:
            print('No samples files in directory', path)
            return None
    
        else:
            files.sort(key=lambda x:  get_time_index(x) )
            files = [os.path.join(path,file) for file in files]
            return files[-1]
    else:
        return None

def find_file_from_dic(path, dico_paths):
    if os.path.exists(path):
        splits = path.split('/')
        key = splits[-3]+'_'+splits[-2]+'_'+splits[-1]
        try:
            file = dico_paths[key]
            return os.path.join(path,file)
        except:
            return None
    else:
        return None

    
    
    
    
def find_best_file_from_path(path):
    path_splits = path.split('/')
    if os.path.exists(path):
        files = [os.path.join(path,file) for file in os.listdir(path) if file.startswith('samples')]
        
        if len(files)==0:
            print('No samples files in directory', path)
            return None
    
        else:
            best_file = files[0]
            best_val = 1000000
            for file in files:
                data = extract_result_from_path(file)
                if path_splits[-2].startswith('are'):
                    val = get_min_val(data, 'valid_nkale')
                else:
                    val = get_min_val(data, 'valid_nll')
                if val < best_val and np.isfinite(val):
                    best_val = val
                    best_file = file
            return best_file
    else:
        return None
    
def extract_result_from_path(path):
    try:
        filename = 'stats_seed_0.json'
        full_path = os.path.join(path, filename)
        return load_dictionary(full_path)
    except:
        pass
def get_min_val(out_dic, key):
    try:
        
        return np.array(out_dic[key]).min()
    except:
        return np.nan

def get_min_val_from_ind(out_dic, key_val,key_ind, max_ind=1989):
    try:
        idx = np.argmin(np.array(out_dic[key_ind])[:max_ind])
        return out_dic[key_val][idx]
    except:
        return np.nan    
    

def get_epoch(out_dic):
    try:
        return out_dic['epoch'][-1]
    except:
        return np.nan
def find_files_from_slurm(path,jobs_ids):
    if os.path.exists(path):
        #aa = [get_slurm_index(file) for file in os.listdir(path) if file.startswith('samples')]
        #bb = [file for file in os.listdir(path) if file.startswith('samples')]
        #print(aa)
        #print(bb)
        files = [os.path.join(path, file) for file in os.listdir(path) if file.startswith('samples') and get_slurm_index(file) in jobs_ids]
        return files
    
def make_data_frame(all_paths, option = 'last'):
    res = {'dataset':[],
          'model':[],
          'method':[],
          'test_nll':[],
          'epoch':[],
          'path':[],
          'Slurm_status':[],}
    jobs_ids, status = get_slurm_jobs()
    for path in all_paths:
        if option=='last':
            files = [find_last_file_from_path(path)]
        elif option=='best':
            files = [find_best_file_from_path(path)]
        elif option=='dico':
            files = [find_file_from_dic(path, dico_paths)]
        elif option =='slurm':
            files = find_files_from_slurm(path,jobs_ids)
        #print(jobs_ids)
        try:
            for file in files:
                #print(file)
                data = extract_result_from_path(file)
                path_splits = path.split('/')
                #val = get_min_val(data, 'test_nll')
                if data is not None:
                    res['method'].append( path_splits[-1])
                    res['model'].append(path_splits[-2])
                    res['dataset'].append(path_splits[-3])
                    res['epoch'].append(get_epoch(data))
                    res['path'].append(file.split('/')[-1])
                    if path_splits[-2].startswith('are'):
                        res['test_nll'].append(get_min_val_from_ind(data, 'test_nkale_dist', 'valid_nkale_dist'))
                    else:
                        res['test_nll'].append(get_min_val_from_ind(data, 'test_nll', 'valid_nll'))
                    res['Slurm_status'].append(get_slurm_status(get_epoch(data),file.split('/')[-1],jobs_ids,status))
                #print(res)
        except:
            pass
    return pd.DataFrame(res), res

import collections

def flatten(d, parent_key='', sep='/'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def gather_metadata(root):
    all_dirs = [d for d in os.listdir(root) if os.path.isdir(d)  ]
    with TinyDB(os.path.join(root, "metadata.json"), storage=JSONStorage) as db: 
        runs = db.table("runs")
        if len(runs)>0:
            cur_id = db.all()[-1]._id
        all_dirs = [os.path.join(root,d) for d in all_dirs if int(d)> cur_id ]
        for d in all_dirs:
            cur_id  = json.loads( os.path.join(d,'metadata.json'))
            runs.insert(cur_id)

def safe_metadata(root):
    try:
        gather_metadata(root)
    except:
        os.remove(os.path.join(root,"metadata.json"))
        gather_metadata(root)
    

















