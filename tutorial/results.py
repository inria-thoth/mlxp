import experimentalist as expy

parent_log_dir = './logs/'
reader = expy.Reader(parent_log_dir)


query = "config.optimizer.lr <= 1. & info.status == 'COMPLETE'"
results = reader.search(query_string=query)

print(results)