FROM hailgenetics/genetics:0.2.37

LABEL maintainer "Tarjinder Singh <tsingh@broadinstitute.org>"
LABEL version "0.1.0"
LABEL date "2021-03-18"

RUN apt-get update \
    && apt-get install -y wget \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN ( mkdir -p /fasta )
COPY Homo_sapiens_assembly38.fasta /fasta
COPY Homo_sapiens_assembly38.fasta.fai /fasta

ENV REF_PATH=/fasta/Homo_sapiens_assembly38.fasta

RUN ( mkdir -p /htslib \
    && cd /htslib \
    && wget https://github.com/samtools/htslib/releases/download/1.12/htslib-1.12.tar.bz2 \
    && tar -xf htslib-1.12.tar.bz2 \
    && cd htslib-1.12 \
    && ./configure \
    && make \
    && make install )

ENV LD_LIBRARY_PATH=/htslib/htslib-1.12/

RUN curl https://nim-lang.org/choosenim/init.sh -sSf | sh -s -- -y

ENV PATH=/root/.nimble/bin:$PATH

RUN ( mkdir -p /mosdepth \
    && cd /mosdepth \
    && wget https://github.com/brentp/mosdepth/archive/v0.3.1.tar.gz \
    && tar xfvz v0.3.1.tar.gz \
    && cd mosdepth-0.3.1 \
    && nimble install -y \
    && ln -s mosdepth /usr/local/bin )
