FROM hailgenetics/genetics:0.2.37

COPY cache/ /tmp/fasta/
RUN /samtools/samtools-1.9/misc/seq_cache_populate.pl -root /samtools-cache /tmp/fasta/Homo_sapiens_assembly38.fasta

ENV REF_PATH /samtools-cache/%2s/%2s/%s:http://www.ebi.ac.uk/ena/cram/md5/%s
ENV REF_CACHE /samtools-cache/%2s/%2s/%s

RUN rm -r /tmp/fasta/