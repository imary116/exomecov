import hailtop.batch as hb

#function to run depth 
def depth(cram, bed):
	j = b.new_job(name=cram) #define job

	#use publically available Docker image that contains samtools  
	j.image('hailgenetics/genetics:0.2.37')

	#run samtools depth and save it to a tmp file
	j.command(f'''samtools depth -b {bed} {cram} > {j.ofile}''')
	
	return j

if __name__ == '__main__':
	backend = hb.ServiceBackend(billing_project='myohanne-trial', bucket='MY_BUCKET') #set up backend 

	b = hb.Batch(backend=backend, name='coverage') #define batch

	#read in the bed file that has the coverage regions for each chr
	bed = b.read_input('gs://imary116/coverage_region.bed')
	
	#paths to the cram files on google cloud 
	cram_file_paths = [
		'gs://imary116/JP-RIK-C-00070.cram',
		'gs://imary116/JP-RIK-C-00071.cram']

	#results = []
	
	#run depth function on each cram file 
	for path in cram_file_paths:
		cram = b.read_input(path) #input cram file
		j = depth(cram, bed) #run depth 
		#results.append(j.ofile)
		b.write_output(j.ofile, 'gs://imary116') #write the output file in a google cloud bucket 

	b.run(open=True, wait=False) #run batch 

	backend.close() 





