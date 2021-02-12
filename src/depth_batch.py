import hailtop.batch as hb
import os 

#function to run depth 
def depth(b, cram, bed, label):
	j = b.new_job(name=f'depth-{label}') #define job and label it as "depth-<file_name>"
	#use publically available Docker image that contains samtools  
	j.image('hailgenetics/genetics:0.2.37')
	j.cpu(4)
	#run samtools depth and save it to a tmp file
	j.command(f'''samtools depth -b {bed} {cram.cram} > {j.ofile}''')
	return j

#function to merge the results together 
def merge(b, results):
	k = b.new_job(name='merge_results')
	if results:   
		k.command(f''' 
python3 -c "
import hail as hl
ht = hl.import_table({results}, impute=True)
ht.export('{k.ofile}')"
''')
		return k

if __name__ == '__main__':
	backend = hb.ServiceBackend(billing_project='daly-neale-sczmeta', bucket='imary116') #set up backend 

	b = hb.Batch(backend=backend, name='coverage') #define batch

	#read in the bed file that has the coverage regions for each chr
	bed = b.read_input('gs://imary116/coverage_region.bed')
	
	#paths to the cram files on google cloud 
	root = 'gs://fc-7a86ab95-f5c5-4ac1-976b-e57dbc601eb1/sc_global_japan_rik_Huang_Yoshikawa_schizophrenia_exome/RP-1855/Exome'
	subpath = '**/**/*.cram'
	cram_file_paths = subprocess.check_output(['gsutil', 'ls', f'{root}/{subpath}']).decode().split('\n')
	cram_file_paths = cram_file_paths[0:3]

	cram_file_paths = [
		'gs://imary116/JP-RIK-C-00070.cram',
		'gs://imary116/JP-RIK-C-00071.cram']
	
	#run depth function on each cram file
	results = []
	for path in cram_file_paths:
		label = os.path.splitext(os.path.basename(path))[0] #only get the file name (without path and ext) 
		root = os.path.splitext(path)[0]
		# read in multiple inputs
		cram = b.read_input_group(
			cram=f'{root}.cram',
			crai=f'{root}.crai')
		# cram = b.read_input(path) #input cram file
		j = depth(b, cram, bed, label) #run depth 
		results.append(j.ofile)
		# see what happens, but comment out after when you work on the merge command
		b.write_output(j.ofile, f'gs://imary116/data/test-coverage/{label}.tsv') #write the output file in a google cloud bucket 

	# merge command
	m = merge(b, results)
	b.write_output(m.ofile, 'gs://imary116/data/test-coverage/total_output.tsv')

	b.run(open=True, wait=False) #run batch 

	backend.close() 




