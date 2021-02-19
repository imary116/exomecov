import hailtop.batch as hb
import os 

#function to merge the results together
def merge(b, results):
	j = b.new_job(name='merge_results')
	j.image('hailgenetics/hail:0.2.37')
	j.cpu(4)
	if results:
		j.command(f'''
python3 -c "
import hail as hl
ht = hl.import_table({results}, impute=True)
ht.export('{j.ofile}')"
''')
		return j

if __name__ == '__main__':
	backend = hb.ServiceBackend(billing_project='daly-neale-sczmeta', bucket='imary116') #set up backend 

	b = hb.Batch(backend=backend, name='merge') #define batch

	results = [
		'gs://imary116/data/test-coverage/JP-RIK-C-00070.tsv',
		'gs://imary116/data/test-coverage/JP-RIK-C-00071.tsv']

	# merge command - took 4 min to run
	m = merge(b, results)
	b.write_output(m.ofile, 'gs://imary116/data/test-coverage/total_output70-71.tsv')

	b.run(open=True, wait=False) #run batch 

	backend.close() 

