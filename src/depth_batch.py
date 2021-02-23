import hailtop.batch as hb
import os 

#function to run depth 
def depth(b, cram, bed, label):
	j = b.new_job(name=f'depth-{label}') #define job and label it as "depth-<file_name>"
	#use publically available Docker image that contains samtools  
	j.image('gcr.io/daly-neale-sczmeta/genetics-cram')
	j.cpu(4)
	#run samtools depth on the .cram file and save it to a tmp file
	j.command(f'''samtools depth -b {bed} {cram.cram} > {j.ofile}''')
	return j

#function to merge the results together 
def merge(b, results):
	j = b.new_job(name='merge_results')
	j.image('hailgenetics/hail:0.2.37')
	j.cpu(4)
	if results:
		j.command(f'''
python3 -c "
import hail as hl
ht = hl.import_table(["{"\", \"".join(results)}"], impute=True)
ht.export('{j.ofile}')"
''')
		return j

if __name__ == '__main__':
	backend = hb.ServiceBackend(billing_project='daly-neale-sczmeta', bucket='imary116') #set up backend 

	b = hb.Batch(backend=backend, name='coverage') #define batch

	#read in the bed file that has the coverage regions for each chr
	bed = b.read_input('gs://imary116/coverage_region.bed')
	
	#set up paths to the cram files on google cloud
	###root = 'gs://fc-7a86ab95-f5c5-4ac1-976b-e57dbc601eb1/sc_global_japan_rik_Huang_Yoshikawa_schizophrenia_exome/RP-1855/Exome'
	###subpath = '**/**/*.cram'

	#subprocess.check_output() runs what is inside () as if it was being run in the terminal, decode() sets up the output for split() on a new line
	# returns a list of file paths: ex. ['gs://.../JP-RIK-C-00070.cram', 'gs://.../JP-RIK-C-00071.cram', ... ]
	###cram_file_paths = subprocess.check_output(['gsutil', 'ls', f'{root}/{subpath}']).decode().split('\n')


	###cram_file_paths = cram_file_paths[0:3] # the first three file paths in the list

	cram_file_paths = [
		'gs://imary116/JP-RIK-C-00070.cram',
		'gs://imary116/JP-RIK-C-00071.cram']
	
	#run depth function on each cram file
	results = [] #empty lists for the depth function outputs
	for path in cram_file_paths:

		# only get the file name - without path (removed by os.path.basename) and '.cram' ext (removed by os.path.splitext)
		label = os.path.splitext(os.path.basename(path))[0] # ex output: JP-RIK-C-00070
		##root = os.path.splitext(path)[0] #obtain path with file name (without the '.cram' extension) - ex output: 'gs://... /JP-RIK-C-00070'


		# read in multiple inputs (need both the .cram and .crai (index) files for samtools depth to run faster)
		# cram = b.read_input_group(
		# 	cram=f'{root}.cram',
		# 	crai=f'{root}.crai')
		cram = b.read_input_group(
			cram=path,
			crai=f'{path}.crai')

		# cram = b.read_input(path) #input cram file
		j = depth(b, cram, bed, label) #run depth function
		results.append(j.ofile) #append outputs to the list 'results'

		# see what happens, but comment out after when you work on the merge command - took an hour to run
		#b.write_output(j.ofile, f'gs://imary116/data/test-coverage/{label}.tsv') #write the output file in a google cloud bucket

	# merge command
	m = merge(b, results)
	b.write_output(m.ofile, 'gs://imary116/data/test-coverage/total_output.tsv')

	b.run(open=True, wait=False) #run batch 

	backend.close() 




