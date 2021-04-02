import hailtop.batch as hb
import os


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

# function to merge the region results together and annotate with sample name column
def merge_regions(b, results_region, labels):
    j = b.new_job(name='merge_regions')
    j.image('hailgenetics/hail:0.2.37')
    j.cpu(4)
    if results_region:
        j.command(f'''
python3 -c "
import hail as hl
from functools import reduce

ht_list = []   

for p, l in zip(results_region, labels):
    ht = hl.import_table(p, impute=True, no_header=True, force_bgz = True) 
    ht = ht.annotate(label = l) 
    ht_list.append(ht) 

ht = reduce(lambda x, y: x.union(y), ht_list) 

ht.export('{j.ofile}')"
''')
        return j

# function to merge the threshold results together and annotate with sample name column
def merge_thresholds(b, results_threshold, labels):
    j = b.new_job(name='merge_thresholds')
    j.image('hailgenetics/hail:0.2.37')
    j.cpu(4)
    if results_threshold:
        j.command(f'''
python3 -c "
import hail as hl
from functools import reduce

ht_list = [] # to hold a list of hail tables after label annotation  

# for each hail table and corresponding label 
for p, l in zip(results_threshold, labels):
    ht = hl.import_table(p, impute=True, no_header=True, force_bgz = True) # import in and unzip 
    ht = ht.annotate(label = l) # add a label column field so that later on when the tables are merged, we can keep track of which sample a table came from
    ht_list.append(ht) # add hail table to the list 

ht = reduce(lambda x, y: x.union(y), ht_list) # combine the hail tables into one big one 

ht.export('{j.ofile}')"
''')
        return j

if __name__ == '__main__':
    backend = hb.ServiceBackend(billing_project='daly-neale-sczmeta', bucket='imary116')  # set up backend

    b = hb.Batch(backend=backend, name='calculating depth and merging')  # define batch

    # read in the bed file that has the coverage regions for each chr
    bed = b.read_input('gs://imary116/coverage_region.bed')

    # paths to the cram files
    # cram_file_paths = [
    #     'gs://imary116/JP-RIK-C-00070.cram',
    #     'gs://imary116/JP-RIK-C-00071.cram']

    cram_file_paths = [
        'gs://fc-7a86ab95-f5c5-4ac1-976b-e57dbc601eb1/sc_global_japan_rik_Huang_Yoshikawa_schizophrenia_exome/RP-1855/Exome/JP-RIK-C-00070/v1/JP-RIK-C-00070.cram',
        'gs://fc-7a86ab95-f5c5-4ac1-976b-e57dbc601eb1/sc_global_japan_rik_Huang_Yoshikawa_schizophrenia_exome/RP-1855/Exome/JP-RIK-C-00071/v1/JP-RIK-C-00071.cram']

    # empty lists
    results_region = []  # for the regions depth function output
    results_threshold = [] # for the threshold depth function output
    labels = [] # for corresponding sample names

    for path in cram_file_paths:
        # only get the file name - without path (removed by os.path.basename) and '.cram' ext (removed by os.path.splitext)
        label = os.path.splitext(os.path.basename(path))[0]  # ex output: JP-RIK-C-00070
        labels.append(label)

        # read in cram and corresponding crai files
        cram = b.read_input_group(
            cram=path,
            crai=f'{path}.crai')

        # run depth function
        j = depth(b, cram, bed, label)

        # append depth function output to lists
        results_region.append(j.ofile['regions.bed.gz'])
        results_threshold.append(j.ofile['thresholds.bed.gz'])
        #OR results_threshold.append(j.ofile.threshold.bed.gz)

        # write the output files of the depth function for each sample in a google cloud bucket (prior to merging the outputs)
        #b.write_output(j.ofile, f'gs://imary116/data/mosdepth-coverage/{label}')


    # merging
    mr = merge_regions(b, results_region, labels)
    b.write_output(mr.ofile, 'gs://imary116/data/test-coverage/allsamples_region.tsv')

    mt = merge_thresholds(b, results_threshold, labels)
    b.write_output(mt.ofile, 'gs://imary116/data/test-coverage/allsamples_threshold.tsv')

    b.run(open=True, wait=False)  # run batch

    backend.close()






