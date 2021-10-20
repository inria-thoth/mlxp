



import json
import os



def load_dict_from_json(json_file_name):
    out_dict = {}
    with open(json_file_name) as f:
        for line in f:
            cur_dict = json.loads(line)
            keys = cur_dict.keys()
            for key in keys:
                if key in out_dict:
                    out_dict[key].append(cur_dict[key])
                else:
                    out_dict[key] = [cur_dict[key]]
    return out_dict

def _make_run_dir(_id, root):
    os.makedirs(root, exist_ok=True)
    log_dir = None
    if _id is None:
        fail_count = 0
        #_id = self._maximum_existing_run_id() + 1
        while log_dir is None:
            try:
                _id = _maximum_existing_run_id(root) + 1
                log_dir = _make_dir(_id, root)
            except FileExistsError:  # Catch race conditions
                sleep(random())
                if fail_count < 1000:
                    fail_count += 1
                else:  # expect that something else went wrong
                    raise
    else:
        log_dir = os.path.join(root, str(_id))
        os.mkdir(log_dir)
    return _id, log_dir
def _maximum_existing_run_id(root):
    dir_nrs = [
        int(d)
        for d in os.listdir(root)
        if os.path.isdir(os.path.join(root, d)) and d.isdigit()
    ]
    if dir_nrs:
        return max(dir_nrs)
    else:
        return 0
def _make_dir( _id, root):
    log_dir = os.path.join(root, str(_id))
    os.mkdir(log_dir)
    return log_dir  # set only if mkdir is successful


