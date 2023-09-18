import mlxp
import shutil


def read_outputs():

	# Create a reader object to access the results stored by the logger.
	parent_log_dir = './test_examples/logs'
	reader = mlxp.Reader(parent_log_dir)

	# Displaying all fields accessible in the database.
	print(reader.fields)


	# Querying 

	# Displaying searchable fields must start with info or config
	print(reader.searchable)


	# Searching using a query string
	query = "info.status in ['COMPLETE', 'RUNNING'] & config.optimizer.lr >= 0.1"
	results = reader.filter(query_string=query, result_format="pandas")

	print(results)


	results = reader.filter(query_string=query)

	print(results)

	# Access a particular column
	print(results[0]['train.epoch'])

	# List of group keys.
	group_keys = ['config.optimizer.lr']
	    
	# Grouping the results           
	grouped_results = results.groupBy(group_keys)


	print(grouped_results)

	# Creating the aggregation maps 
	from mlxp.data_structures.contrib.aggregation_maps import AvgStd
	agg_maps = [AvgStd('train.epoch')]

	agg_results = grouped_results.aggregate(agg_maps)

	print(agg_results)
	try:
		shutil.rmtree(parent_log_dir)
	except:
		pass
if __name__ == "__main__":
    
    read_outputs()



