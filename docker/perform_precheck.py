import argparse
import sys
import os

R1 = 'r1_files'
R2 = 'r2_files'
BASE = 'base'
EXP = 'experimental'
ANNOTATIONS = 'annotations'
SAMPLE = 'sample'
CONDITION = 'condition'
COL_NAMES = [SAMPLE, CONDITION]
MIN_SAMPLES_PER_GROUP = 2

def read_annotations(annotation_filepath):
    '''
    Tries to parse the annotation file.  If it cannot, issue return some sensible
    message
    '''
    generic_problem_message = '''A problem occurred when trying to parse your annotation 
        file, which was inferred to be in %s format.  
        Please ensure it follows our expected formatting.'''
    file_extension = annotation_filepath.split('.')[-1].lower()
    if file_extension == 'tsv':
        try:
            df = pd.read_csv(annotation_filepath, header=None, sep='\t', names=COL_NAMES)
        except Exception as ex:
            return (None, [generic_problem_message % 'tab-delimited'])
    elif file_extension == 'csv':
        try:
            df = pd.read_csv(annotation_filepath, header=None, sep=',', names=COL_NAMES)
        except Exception as ex:
            return (None, [generic_problem_message % 'comma-separated'])
    elif ((file_extension == 'xlsx') or (file_extension == 'xls')):    
        try:
            df = pd.read_excel(annotation_filepath, header=None, names=COL_NAMES)
        except Exception as ex:
            return (None, [generic_problem_message % 'MS Excel'])

    # now that we have successfully parsed something.  
    if df.shape[1] != 2:
        return (None, 
                ['The file extension of the annotation file was %s, but the' 
                ' file reader parsed %d columns.  Please check your annotation file.' % (file_extension, df.shape[1])])
    return (df, [])

    

def get_commandline_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', required=True, dest=ANNOTATIONS)
    parser.add_argument('-r1', required=True, dest=R1, nargs='+')
    parser.add_argument('-r2', required=True, dest=R2, nargs='+')
    parser.add_argument('-x', required=True, dest=BASE, nargs='+')
    parser.add_argument('-y', required=True, dest=EXP, nargs='+')

    args = parser.parse_args()
    return vars(args)


if __name__ == '__main__':
    arg_dict = get_commandline_args()

    # collect the error strings into a list, which we will eventually dump to stderr
    err_list = []

    # put all the fastq into a list:
    all_fastq = []
    all_fastq.extend(arg_dict[R1])
    all_fastq.extend(arg_dict[R2])

    # infer the names of the samples from the fastq:
    suffix = '_RX.fastq.gz'
    sample_set = [os.path.basename(x)[-len(suffix):] for x in all_fastq]

    # check that the contrasts make sense:
    base_conditions = arg_dict[BASE]
    experimental_conditions = arg_dict[EXP]
    condition_set = set(base_conditions).union(experimental_conditions)
    contrast_pairs = list(zip(base_conditions, experimental_conditions))
    # check for repeated contrast.  Not strictly a problem, but could make difficulty for naming
    if len(set(contrast_pairs)) < len(contrast_pairs):
        err_list.append('There were repeated contrasts, which can cause an issue with naming of files.  Please remove.')
    
    # check for contrast with same group (e.g. A vs A)
    for pair in contrast_pairs:
        if len(set(pair)) == 1:
            err_list.append('The contrast of %s versus itself is not valid.  Please remove.' % pair[0])
    

    # check that annotations are in a known/readable format:
    annotations_df, errors = read_annotations(arg_dict[ANNOTATIONS])
    err_list.extend(errors)

    if annotations_df:
        # check that all the fastq are annotated, but ONLY if we were able to parse a dataframe
        # from the annotation file
        suffix = '_RX.fastq.gz'
        sample_set_from_fq = set([os.path.basename(x)[-len(suffix):].lower() for x in all_fastq])
        sample_set_from_annotations = set([x.lower() for x in df[SAMPLE].tolist()])
        diff_set = sample_set_from_fq.difference(sample_set_from_annotations)
        if len(diff_set) > 0:
            err_list.append('Some of your fastq files did not have annotations.  '
            'Samples with the following names were not found in your annotation file: %s' % ', '.join(diff_set))
        else:
            # all samples were annotated.  Check that each contrast group has at least two samples.  
            for group_id, sub_df in df.groupby(CONDITION):
                if sub_df.shape[1] < MIN_SAMPLES_PER_GROUP:
                    err_list.append('Group %s did not have the required minimum of %d replicates' % (group_id, MIN_SAMPLES_PER_GROUP))

    if len(err_list) > 0:
        sys.stderr.write('\n'.join(err_list))
        sys.exit(1) # need this to trigger Cromwell to fail
        