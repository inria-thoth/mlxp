import os
import experimentalist as expy
import seaborn as sns


def make_plot_dicts(methods,key_name):
    
    labels = {m: key_name +' ' +m  for m in methods}
    colors = sns.color_palette("colorblind", n_colors=len(methods), desat=.7)
    sns.palplot(colors)
    color_dict_index = {m:i for i,m in enumerate(methods)}
    color_dict = {key:colors[value] for key,value in color_dict_index.items()}
    linestyles = {m:'-' for m in methods}
    return color_dict,labels,linestyles, colors


log_name = 'test'
out_dir = 'data/outputs'
reader = expy.Reader(os.path.join(out_dir,log_name), reload=True)

query = 'metadata.max_iter == 100'
        
out = reader.search(query)


out 

out.add([expy.maps.Last("metrics.loss")
          ])



group_keys = [['metadata.optimizer.name']]
aggmaps = [expy.maps.AggMin("metadata.metrics.loss_last")]

list_config_dicts = out.groupBy(group_keys).agg(aggmaps).toConfigCollection()['metadata.metrics.loss_last_aggmin']

aggmaps = [expy.maps.AggAvgStd("metrics.loss")
        ,"metrics.iteration"]

list_config_dicts.add(aggmaps)



values_list = ["metrics.loss_avg",
            "metrics.iteration",
            "group_keys_val",
            "group_keys"]
gen_list = list_config_dicts.get(values_list)
methods = ['-'.join(data['group_keys_val']) for data in gen_list]
key_name = gen_list[0]['group_keys']+':'
color_dict, labels_dict, linestyles_dict,colors = make_plot_dicts(methods,key_name)


print(color_dict)











