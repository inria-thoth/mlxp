import mlxp

# Create a reader object to access the results stored by the logger.
parent_log_dir = './logs/'
reader = mlxp.Reader(parent_log_dir)

# Displaying the number of runs accessible to the reader
print(len(reader))


# Displaying all fields accessible in the database.
print(reader.fields)


# Querying 

# Displaying searchable fields must start with info or config
print(reader.searchable)


# Searching using a query string
query = "info.status == 'COMPLETE' & config.model.num_units < 4"
results = reader.filter(query_string=query, result_format="pandas")

# Display the result as a pandas dataframe 
print(results)


# Returning an mlxp.DataFrame as a result
results = reader.filter(query_string=query)

# Display the result as a pandas dataframe
print(results)


# Access a particular column
print(results[0]['train.loss'])

# Access a particular column of the results 
art = results[0]['artifact.pickle.']
print(art)

# Loading an artifact
art['last_ckpt.pkl'].load()


# Inspect configurations that vary accross runs
print(results.diff())

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
def argmin(x):
	import numpy as np
	x = np.array(x)
	return x[:,-1]==np.min(x[:,-1])

group_keys = ['config.model.num_units','config.optimizer.lr']         
methods_keys = ['config.model.num_units']

grouped_res = results.groupby(group_keys)

best_results = grouped_res.aggregate((mean,'train.loss'))\
				   		.filter((argmin,'fmean.train.loss'), bygroups = methods_keys)


# Extracting the best results 
filtered_results = grouped_res.select(best_results.keys())\
						.aggregate((mean,'test.loss'))


print(filtered_results)
