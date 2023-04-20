import mlxpy as expy
from mlxpy.data_structures.contrib.aggregation_maps import AvgStd


parent_log_dir = './logs/'
reader = expy.Reader(parent_log_dir)


query = "info.status == 'COMPLETE'"
results = reader.search(query_string=query)

print(results)



## Groupby

group_keys = ['config.optimizer.lr']
              
grouped_results = results.groupBy(group_keys)

agg_maps = [AvgStd('train.loss'),AvgStd('train.epoch')]

agg_results = grouped_results.aggregate(agg_maps)

print(agg_results)
print(results)

