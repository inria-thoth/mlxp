import mlxp

# Create a reader object to access the results stored by the logger.
parent_log_dir = './logs/'
reader = mlxp.Reader(parent_log_dir)

# Displaying all fields accessible in the database.
print(reader.fields)


# Querying 

# Displaying searchable fields must start with info or config
print(reader.searchable)


# Searching using a query string
query = "info.status == 'COMPLETE' & config.optimizer.lr <= 100."
results = reader.filter(query_string=query, result_format="pandas")
print(results)


results = reader.filter(query_string=query)

print(results)
results.config_diff

# Access a particular column
print(results[0]['train.loss'])


# Inspect configurations that vary accross runs
print(results.config_diff())

# List of group keys.
group_keys = ['config.optimizer.lr']
    
# Grouping the results           
grouped_results = results.groupby(group_keys)
print(grouped_results)


# Creating the aggregation map 
def mean(x):
	import numpy as np
	x = np.array(x)
	return np.mean(x,axis=0)
agg_maps = (mean,('train.loss', 'train.epoch'))

# Aggregating the results
agg_results = grouped_results.aggregate(agg_maps)
print(agg_results)

# Finding the best performing hyper-parameters
def maximum(x):
	import numpy as np
	x = np.array(x)
	return x[:,-1]==np.max(x[:,-1])

group_keys = ['config.model.num_units','config.optimizer.lr']         
methods_keys = ['config.model.num_units']

best_keys = results.groupby(group_keys)\
			.aggregate((mean,'train.loss'),ungroup=True)\
			.filter((maximum,'fmean.train.loss'), bygroups = methods_keys)\
			.groupby(group_keys).keys()


# Extracting the best results 
filtered_results = results.groupby(group_keys)\
						.select(best_keys)\
						.aggregate((mean,'test.loss'),ungroup=True)\
						.groupby(methods_keys)



print(filtered_results)
