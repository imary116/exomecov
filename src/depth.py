import hailtop.batch as hb

#backend = hb.ServiceBackend(billing_project='myohanne-trial', bucket='fc-7a86ab95-f5c5-4ac1-976b-e57dbc601eb1/sc_global_japan_rik_Huang_Yoshikawa_schizophrenia_exome/RP-1855/Exome/JP-RIK-C-00070/v1')

#b = hb.Batch(backend=backend, name='coverage')
b = hb.Batch(name='depth')

j = b.new_job(name='j1')

j.command('samtools depth -H -b ~/Desktop/Broad/tj/exomecov/data/coverage_region.bed -f ~/Desktop/Broad/tj/exomecov/data/cram_file_paths -o ~/Desktop/Broad/tj/exomecov/output/local_output')

b.run()





