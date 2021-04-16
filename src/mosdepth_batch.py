import hailtop.batch as hb
import os
import hail as hl


# function to run mosdepth
def depth(b: hb.batch.Batch, cram: hb.resource.ResourceGroup, bed: hb.resource.ResourceFile, label: str = None):
    j = b.new_job(name=f'depth-{label}')  # define job and label it as "depth-<file_name>"
    j.image('gcr.io/daly-neale-sczmeta/mosdepth') # use publicly available Docker image that contains mosdepth
    j.cpu(4)
    # the command written below produces 7 outputs and since we don't want all of them, we specify which outputs here - 'regions' and 'thresholds' bed files
    j.declare_resource_group(ofile={
        'regions.bed.gz': '{root}.regions.bed.gz',
        'thresholds.bed.gz': '{root}.thresholds.bed.gz'
    })
    j.command(f'''mosdepth -n -b {bed} -T 1,10,20 {j.ofile} {cram.cram}''') # run mosdepth on the .cram file and save it to a tmp file
    return j

# function to merge results and annotate with sample names
def merge(b, results, labels, job_label: str):
    j = b.new_job(name=f'merge-{job_label}')
    j.image('hailgenetics/hail:0.2.37')
    j.cpu(4)
    if results:
        delimiter = "', '"
        j.command(f'''
python3 -c "
import hail as hl
from functools import reduce

ht_list = [] # to hold a list of hail tables after label annotation

# format inputs for hail batch purposes 
paths = ['{delimiter.join(results)}']
names = ['{delimiter.join(labels)}']

# for each hail table and corresponding label 
for p, n in zip(paths, names):
    # the regions bed file has no header while the threshold bed file has one so for import, the options are slightly different 
    if '{job_label}' == 'region': 
        ht = hl.import_table(p, impute=True, no_header=True, force_bgz = True) # import in and unzip - no header  
    else:
        ht = hl.import_table(p, impute=True, force_bgz = True) # import in and unzip - with a header 
    
    ht = ht.annotate(sample = n) # add a sample column field so that later on when the tables are merged, we can keep track of which sample a table came from
    ht_list.append(ht) # add hail table to the list 

ht = reduce(lambda x, y: x.union(y), ht_list) # combine the hail tables into one big one 
ht.write('{j.ofile}')"  
''')
        return j

if __name__ == '__main__':
    backend = hb.ServiceBackend(billing_project='daly-neale-sczmeta', bucket='imary116')  # set up backend

    b = hb.Batch(backend=backend, name='calculating coverage and merging')  # define batch

    # read in the bed file that has the coverage regions for each chr
    bed = b.read_input('gs://imary116/coverage_region.bed')

    # empty lists
    results_region = []  # for the regions depth function output
    results_threshold = [] # for the threshold depth function output
    labels = [] # for corresponding sample names

    with hl.hadoop_open('gs://imary116/sampled_78.txt') as cram_file_paths:  # file with paths to 78 randomly selected cram files
        for path in cram_file_paths:
            path = path.strip().strip('""') # preprocess path
            label = os.path.splitext(os.path.basename(path))[0]  # only get the file name - without path (removed by os.path.basename) and '.cram' ext (removed by os.path.splitext) ex output: JP-RIK-C-00070
            labels.append(label) # add sample label to the list

            # read in cram and corresponding crai files
            cram = b.read_input_group(
                cram=path,
                crai=f'{path}.crai')

            # run depth function
            j = depth(b, cram, bed, label)

            # append depth function output to lists
            results_region.append(j.ofile['regions.bed.gz'])
            results_threshold.append(j.ofile['thresholds.bed.gz'])

            # to write the output files of the depth function for each sample in a google cloud bucket (prior to merging the outputs)
            #b.write_output(j.ofile, f'gs://imary116/data/mosdepth-coverage/{label}')


    # merging
    mr = merge(b, results_region, labels, 'region')
    b.write_output(mr.ofile, 'gs://imary116/data/coverage/78_random_samples_region.ht') #change to ht

    mt = merge(b, results_threshold, labels, 'threshold')
    b.write_output(mt.ofile, 'gs://imary116/data/coverage/78_random_samples_threshold.ht')

    b.run(open=True, wait=False)  # run batch

    backend.close()






