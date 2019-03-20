workflow PairedRnaSeqAndDgeWorkflow {
    Array[File] r1_files
    Array[File] r2_files
    File sample_annotations
    Array[String] base_conditions
    Array[String] experimental_conditions
    String genome
    File star_index_path
    File gtf
    File bed_annotations
    String output_zip_name
    String git_repo_url
    String git_commit_hash


    Array[Pair[File, File]] fastq_pairs = zip(r1_files, r2_files)
    scatter(item in fastq_pairs){

        call assert_valid_fastq {
            input:
                r1_file = item.left,
                r2_file = item.right
        }
    }

    call assert_valid_annotations{
        input:
            r1_files = r1_files,
            r2_files = r2_files,
            sample_annotations = sample_annotations,
            base_conditions = base_conditions,
            experimental_conditions = experimental_conditions
    }
}

task assert_valid_fastq {

    File r1_file
    File r2_file

    command <<<
        python3 /opt/software/precheck/check_fastq -r1 ${r1_file} -r2 ${r2_file}
    >>>
}

task assert_valid_annotations {

    Array[String] r1_files
    Array[String] r2_files
    File sample_annotations
    Array[String] base_conditions
    Array[String] experimental_conditions

    command <<<
        python3 /opt/software/precheck/perform_precheck.py \
            -a ${sample_annotations} \
            -r1 ${sep=" " r1_files} \
            -r2 ${sep=" " r2_files} \
            -x ${sep=" " base_conditions} \
            -y ${sep=" " experimental_conditions}
    >>>
}