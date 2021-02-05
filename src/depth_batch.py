import hailtop.batch as hb

#function to run depth 
def depth(cram, bed, label):
	j = b.new_job(name=f'depth-{label}') #define job
	#use publically available Docker image that contains samtools  
	j.image('hailgenetics/genetics:0.2.37')
	g.cpu(4)
	#run samtools depth and save it to a tmp file
	j.command(f'''samtools depth -b {bed} {cram} > {j.ofile}''')
	return j

# def merge(results):
# 	g.command(f'''
# 		python3 -c "
# 		import hail as hl
# 		ht = hl.import_table({results}, impute=True)
# 		ht.write('')
# 		"
# 	''')

if __name__ == '__main__':
	backend = hb.ServiceBackend(billing_project='daly-neale-sczmeta', bucket='MY_BUCKET') #set up backend 

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
		label = os.path.splitext(os.path.basename(path))[0]
		cram = b.read_input(path) #input cram file
		j = depth(cram, bed, label) #run depth 
		results.append(j.ofile)
		# see what happens, but comment out after when you work on the merge command
		b.write_output(j.ofile, 'gs://imary116/{label}.tsv') #write the output file in a google cloud bucket 

	# merge command
	# j = merge(cram, bed)
	# b.write_output(j.ofile, 'gs://imary116/test-output.tsv')

	b.run(open=True, wait=False) #run batch 

	backend.close() 





