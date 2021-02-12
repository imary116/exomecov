import hailtop.batch as hb
import os 

#function to run depth 
def depth(b, cram, bed, label):
	j = b.new_job(name=f'depth-{label}') #define job and label it as "depth-<file_name>"
	#use publically available Docker image that contains samtools  
	j.image('hailgenetics/genetics:0.2.37')
	j.cpu(4)
	#run samtools depth and save it to a tmp file
	j.command(f'''samtools depth -b {bed} {cram} > {j.ofile}''')
	return j

#function to merge the results together 
def merge(b, results):
	k = b.new_job(name='merge_results')
	if results:   
		k.command(f''' 
		python3 -c " \
		import hail as hl \
		{k.ofile} = hl.import_table({results}, impute=True) "
		''')
		return k
		

if __name__ == '__main__':
	backend = hb.ServiceBackend(billing_project='daly-neale-sczmeta', bucket='gs://imary116') #set up backend 

	b = hb.Batch(backend=backend, name='coverage') #define batch

	#read in the bed file that has the coverage regions for each chr
	bed = b.read_input('gs://imary116/coverage_region.bed')
	
	#paths to the cram files on google cloud 
	cram_file_paths = [
		'gs://imary116/JP-RIK-C-00070.cram',
		'gs://imary116/JP-RIK-C-00071.cram']
	
	#run depth function on each cram file
	results = []
	for path in cram_file_paths:
		label = os.path.splitext(os.path.basename(path))[0] #only get the file name (without path and ext) 
		cram = b.read_input(path) #input cram file
		j = depth(b, cram, bed, label) #run depth 
		results.append(j.ofile)
		# see what happens, but comment out after when you work on the merge command
		#b.write_output(j.ofile, 'gs://imary116/{label}.tsv') #write the output file in a google cloud bucket 

	# merge command
	m = merge(b, results)
	b.write_output(m.ofile, 'gs://imary116/total_output.tsv')

	b.run(open=True, wait=False) #run batch 

	backend.close() 





