import hailtop.batch as hb
import os
import hail as hl
from collections import defaultdict


# function to run mosdepth
def depth(b: hb.batch.Batch, cram: hb.resource.ResourceGroup, bed: hb.resource.ResourceFile, label: str = None):
    j = b.new_job(name=f'depth-{label}')  # define job and label it as "depth-<file_name>"
    j.image('gcr.io/daly-neale-sczmeta/mosdepth') # use publicly available Docker image that contains mosdepth
    j.cpu(4) # update CPU size
    j.storage('10G') # update storage
    # the command written below produces 7 outputs and since we don't want all of them, we specify which outputs here - 'regions' and 'thresholds' bed files
    j.declare_resource_group(ofile={
        'regions.bed.gz': '{root}.regions.bed.gz',
        'thresholds.bed.gz': '{root}.thresholds.bed.gz'
    })
    j.command(f'''mosdepth -n -b {bed} -T 1,10,20 {j.ofile} {cram.cram}''') # run mosdepth on the .cram file and save it to a tmp file j.ofile
    return j



# function to merge the results produced from the depth function and annotate them with sample names (makes use of hail query)
def merge(b, results, labels, job_label: str):
    j = b.new_job(name=f'merge-{job_label}')
    j.image('hailgenetics/hail:0.2.37')
    j.cpu(4)
    if results:
        delimiter = "', '" # for formatting purposes
        j.command(f'''
python3 -c "
import hail as hl
from functools import reduce

ht_list = [] # to hold a list of hail tables after label annotation

# format inputs for hail batch purposes 
paths = ['{delimiter.join(results)}']
names = ['{delimiter.join(labels)}']

# for each output of the depth function (in our case region.bed.gz and thresholds.bed.gz of each sample) and their corresponding sample labels 
for p, n in zip(paths, names):
    # the regions bed file has no header while the threshold bed file has one so for import_table, the options are slightly different 
    if '{job_label}' == 'region': 
        ht = hl.import_table(p, impute=True, no_header=True, force_bgz = True) # import in as hail table and unzip - no header  
    else:
        ht = hl.import_table(p, impute=True, force_bgz = True) # import in as a hail table and unzip - with a header 
    
    ht = ht.annotate(sample = n) # add a sample column field using the sample lables so that later on when the tables are merged, we can keep track of which sample a table came from
    ht_list.append(ht) # add hail table to the list 

ht = reduce(lambda x, y: x.union(y), ht_list) # combine the hail tables in the list into one big one 
ht.write('{j.ofile}')"  # write it out 
''')
        return j


if __name__ == '__main__':
    backend = hb.ServiceBackend(billing_project='daly-neale-sczmeta', bucket='imary116')  # set up backend

    # empty lists
    pdo_list = []
    path_list = []
    with hl.hadoop_open('gs://imary116/second_run/data/pdo25_crampath_sampleID.tsv') as cram_file_paths:
        cram_file_paths.readline()  # skip the header
        for row in cram_file_paths:
            row = row.strip()  # remove space at end of each row
            pdo, path, sample_id = row.split('\t')  # for each row, split the three column values into three variables
            pdo_list.append(pdo)
            path_list.append(path)

    # missing key will always be a list and if a key already exists, then it will just be appended to
    file_dict = defaultdict(list)
    for pdo, path in zip(pdo_list, path_list):
        file_dict[pdo].append(path) # dictionary looks something like: {'pdo_1' : [sample1_path, sample2_path], 'pdo_2' : [sample3_path, sample4_path, sample5_path] ... }

    if (len(file_dict) == len(set(pdo_list))): # for sanity check - 25 pdos in total

        for key in file_dict.keys(): # for each pdo
            b = hb.Batch(backend=backend, name=f'{key} - coverage and merging')  # define batch

            # read in the bed file that has the coverage regions for each chr
            bed = b.read_input('gs://imary116/second_run/data/grch38_gencode-regions_2017-11-07_gencode-cds-regions-p8-grch38.bed')

            # more empty lists
            results_region = []  # for the regions depth function output
            results_threshold = []  # for the threshold depth function output
            labels = []  # for corresponding sample names

            for path in file_dict[key]: # get the paths for all randomly selected samples that are under that pdo and do the following
                #path = path.strip().strip('""')  # preprocess path
                label = os.path.splitext(os.path.basename(path))[0]  # only get the file name - without path (removed by os.path.basename) and '.cram' ext (removed by os.path.splitext) ex output: JP-RIK-C-00070
                labels.append(label)  # add sample label to the list

                # read in cram and corresponding crai files
                cram = b.read_input_group(
                    cram=path,
                    crai=f'{path}.crai')

                # run depth function
                j = depth(b, cram, bed, label)

                # append depth function outputs to their corresponding lists
                results_region.append(j.ofile['regions.bed.gz'])
                results_threshold.append(j.ofile['thresholds.bed.gz'])

                # to write the output files of the depth function for each sample in a google cloud bucket (prior to merging the outputs)
                #b.write_output(j.ofile, f'gs://imary116/data/mosdepth-coverage/{label}')

                # merging and saving the outputs as hail tables
            mr = merge(b, results_region, labels, 'region')
            b.write_output(mr.ofile, f'gs://imary116/second_run/output/region/{key}_region.ht')

            mt = merge(b, results_threshold, labels, 'threshold')
            b.write_output(mt.ofile, f'gs://imary116/second_run/output/threshold/{key}_threshold.ht')

            b.run(open=True, wait=False)  # run batch

    backend.close()






