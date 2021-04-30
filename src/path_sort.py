import subprocess 
import hail as hl 

# if the path is accessible, return 'True' if not return 'False'
def path_works(path):
    if subprocess.call(['gsutil', 'ls', path]) == 0:
        return(True)
    else:
        return(False)

# go line by line in the file and sort w/c paths are accessible and w/c are not, then save them into separate files
with open("/Users/myohanne/Desktop/Broad/tj/exomecov/data/cram_paths.txt", "r") as input_file, open('/Users/myohanne/Desktop/Broad/tj/exomecov/data/access_paths.txt', 'w') as output_access, open('/Users/myohanne/Desktop/Broad/tj/exomecov/data/no_access_paths.txt', 'w') as output_no_access:
    for path in input_file:
        path = path.replace('"', '').strip() # formating 
        if path_works(path):
            output_access.write(f'{path}\n')
        else:
            output_no_access.write(f'{path}\n')
