import hailtop.batch as hb
import os


# function to run mosdepth
def depth(b: hb.batch.Batch, cram: hb.resource.ResourceGroup, bed: hb.resource.ResourceFile, label: str = None):
    j = b.new_job(name=f'depth-{label}')  # define job and label it as "depth-<file_name>"
    # use publically available Docker image that contains mosdepth
    j.image('gcr.io/daly-neale-sczmeta/mosdepth')
    j.cpu(4)
    # the command written below produces 7 outputs and since we don't want all of them, we specify which outputs here - 'regions' and 'thresholds' bed files
    j.declare_resource_group(ofile={
        'regions.bed.gz': '{root}.regions.bed.gz',
        'thresholds.bed.gz': '{root}.thresholds.bed.gz',
    })
    # run mosdepth on the .cram file and save it to a tmp file
    j.command(f'''mosdepth -n -b {bed} -T 1,10,20 {j.ofile} {cram.cram}''')
    return j

# function to merge the results together
def merge(b, results, labels):
    j = b.new_job(name='merge_results')
    j.image('hailgenetics/hail:0.2.37')
    j.cpu(4)
    if results:
        delimiter = "', '"
        j.command(f'''
python3 -c "
import hail as hl
from functools import reduce

ht_list = []
paths = ['{delimiter.join(results)}']
labels = ['{delimiter.join(labels)}']

for p, l in zip(paths, labels):
    ht = hl.import_table(p, impute=True, no_header=True)
    ht = ht.annotate(label = l)
    ht_list.append(ht)

ht = reduce(lambda x, y: x.union(y), ht_list)

ht.export('{j.ofile}')"
''')
        return j

if __name__ == '__main__':
    backend = hb.ServiceBackend(billing_project='daly-neale-sczmeta', bucket='imary116')  # set up backend

    b = hb.Batch(backend=backend, name='calculating depth')  # define batch

    # read in the bed file that has the coverage regions for each chr
    bed = b.read_input('gs://imary116/coverage_region.bed')

    # paths to the cram files
    cram_file_paths = [
        'gs://imary116/JP-RIK-C-00070.cram',
        'gs://imary116/JP-RIK-C-00071.cram']

    # run depth function on each cram file
    results_region = []  # empty lists for the depth function outputs
    results_threshold = []
    labels = []

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
        results_region.append(j.ofile.region.bed.gz)  # append outputs to the list 'results'
        results_threshold.append(j.ofile['threshold.bed.gz'])  # append outputs to the list 'results'

        # see what happens, but comment out after when you work on the merge command - took 2 min to run on the two cram files
        b.write_output(j.ofile, f'gs://imary116/data/mosdepth-coverage/{label}') #write the output files for each sample in a google cloud bucket (without merging the outputs)

    # merge command
    m = merge(b, results_region, labels)
    # b.write_output(m.ofile, 'gs://imary116/data/test-coverage/allsamples.region.tsv')

    b.run(open=True, wait=False)  # run batch

    backend.close()






