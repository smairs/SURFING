import glob
import re
import os
import logging
logging.basicConfig(level=logging.INFO)
logging.root.setLevel(logging.INFO)
from starlink import wrapper,kappa,convert
wrapper.change_starpath('/star')

def DR_setup(datescans):
    '''
    Setup directory tree for reduced products and make sure raw data exists in the proper format

    datescans: A list of datescan strings in the format ['YYYYMMDD_SS','YYYYMMDD_SS'...], where SS = Scan Number
    '''
    for datescan in datescans:

        # Make sure we have raw data in the proper format!
        try:
            os.listdir('raw/{}/{}/*sdf'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5)))
        except FileNotFoundError:
            print('Oh no! There is no raw data available in a directory called: \nraw/{}/{}/\n'\
                    'Please create and/or populate this directory with the raw SDF files'\
                    'you intend to reduce.'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5)))

        # Make Output Directories
        if not os.path.exists('reduced'):
            os.system('mkdir reduced')
        if not os.path.exists('reduced/{}'.format(datescan.split('_')[0])):
            os.system('mkdir reduced/{}'.format(datescan.split('_')[0]))
        if not os.path.exists('reduced/{}/{}'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))):
            os.system('mkdir reduced/{}/{}'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5)))



def reduce_combined_p0_p1(datescans,recipe,parfile=''):
    '''
    Reduce the P0 and P1 data together using Starlink's pywrapper.
    Clean up the results into organised directories.
    Save the path information for the log, image, and data files to a summary text document.


    datescans: A list of datescan strings in the format ['YYYYMMDD_SS','YYYYMMDD_SS'...], where SS = Scan Number
    recipe   : The ORACDR recipe to run. e.g. 'REDUCE_SCIENCE_NARROWLINE'
    parfile  : The configuration/parameter file to pass to ORACDR. This file must reflect the recipe chosen.
               See: https://www.eaobservatory.org/jcmt/science/reductionanalysis-tutorials/heterodyne-instrument-data-reduction-tutorial-2/
               An empty string ('') assumes the default parameters for the chosen recipe
    '''

    #####
    # Ensure the raw data exists and then construct the appropriate reduced product directories
    # for all datescans
    DR_setup(datescans)
    #####

    #####
    # Run the data reduction and save the output information
    #####
    outputs = []

    # Loop over each input observation
    for datescan in datescans:
    
        # Define raw and out paths -- the existence of these paths are checked by DR_setup, above
        rawpath    = 'raw/{}/{}/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))
        outpath    = 'reduced/{}/{}'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))
    
        # Collect raw files into list 
        raw_files = sorted(list(glob.glob(os.path.join(rawpath,'*sdf'))))
    
        # Run ORACDR
        print('\nNow running ORACDR for: {}...'.format(datescan))
        if parfile != '':
            output = wrapper.oracdr('ACSIS',loop='file',dataout=outpath,recipe=recipe,rawfiles=raw_files,recpars=parfile,verbose=True,debug=True)
        else:
            output = wrapper.oracdr('ACSIS',loop='file',dataout=outpath,recipe=recipe,rawfiles=raw_files,verbose=True,debug=True)

        # Save the output (paths to log, image, data files and other information)
        outputs.append(output)

        # Clean up the output. The python wrapper creates a temporary directory beginning with ORACworking* (given by output.outdir)
        # to store the files -- we want to move the files to our directory tree and remove the temporary directory.
        os.system('mv {}/* {}/'.format(output.outdir,outpath))
        os.system('rm -rf {}'.format(output.outdir))
        os.system('mkdir {}/logfiles; mv {}/*log* {}/logfiles'.format(outpath,outpath,outpath))
        os.system('mkdir {}/imagefiles; mv {}/*png {}/imagefiles'.format(outpath,outpath,outpath))

    #####
    # Next, we will create a summary file that gives an overview of the locations of the data products 
    #####
    summaryfile = open('Summary.txt','w')
    print('\n#####\n#####\nSummary:\n')
    for datescan,output in zip(datescans,outputs):
        #Save the Summary to a file
        summaryfile.write('~~~{}~~~\n#######\n'.format(datescan))
        summaryfile.write('\nThe run log for {} can be found here {}'.format(datescan,re.sub('ORACworking\w+/','logfiles',output.runlog)))
        summaryfile.write('\n\nThe datafiles are listed below:\n')
        summaryfile.write(re.sub('ORACworking\w+/','','\n'.join(output.datafiles)))
        summaryfile.write('\n\nThe image files are listed below:\n')
        summaryfile.write(re.sub('ORACworking\w+/','','\n'.join(output.imagefiles)))
        summaryfile.write('\n\nThe additional logs are listed below:\n')
        summaryfile.write(re.sub('ORACworking\w+/','','\n'.join(output.logfiles)))
        summaryfile.write('\n')
    
        #Print the summary to the screen
        print('~~~{}~~~\n#######\n'.format(datescan))
        print('The run log for {} can be found here {}'.format(datescan,output.runlog))
        print('\nThe datafiles are listed below:')
        print(re.sub('ORACworking\w+/','','\n'.join(output.datafiles)))
        print('\nThe image files are listed below:')
        print(re.sub('ORACworking\w+/','','\n'.join(output.imagefiles)))
        print('\nThe additional logs are listed below:')
        print(re.sub('ORACworking\w+/','','\n'.join(output.logfiles)))
        print('')
    
    # Close the file    
    summaryfile.close()
    print('\nThis summary is available here: Summary.txt\n')


def reduce_individual_p0_p1(datescans,recipe,parfile=''): 
    '''
    Reduce the P0 and P1 data individually using Starlink's pywrapper.
    Clean up the results into organised directories.
    Save the path information for the log, image, and data files to a summary text document.
    This will be used mainly for QA testing.

    datescans: A list of datescan strings in the format ['YYYYMMDD_SS','YYYYMMDD_SS'...], where SS = Scan Number
    recipe   : The ORACDR recipe to run. e.g. 'REDUCE_SCIENCE_NARROWLINE'
    parfile  : The configuration/parameter file to pass to ORACDR. This file must reflect the recipe chosen.
               See: https://www.eaobservatory.org/jcmt/science/reductionanalysis-tutorials/heterodyne-instrument-data-reduction-tutorial-2/
               An empty string ('') assumes the default parameters for the chosen recipe
    '''

    #####
    # Ensure the raw data exists and then construct the appropriate reduced product directories
    # for all datescans
    DR_setup(datescans)
    #####

    for eachpol in ['P0','P1']:
    
        print('\n\t{}...'.format(eachpol))

        #####
        # Define "bad" receptors that will be ignored. 
        # Format: N = Namakanui, U|W|A =Uu|Aweoweo|Alaihi, 0|1 = Polarisation, U|L = Upper or Lower sideband  
        #####
        if eachpol == 'P0':
            BRlist = ['NU1L','NU1U','NW1L','NW1U','NA1L','NA1U']
        elif eachpol == 'P1':
            BRlist = ['NU0L','NU0U','NW0L','NW0U','NA0L','NA0U']
        
        #####
        # Loop over each datescan and apply the lists of receptors to ignore such that we have individual P0 and P1 observations
        #####
        for datescan in datescans:

            # Define raw and out paths --  the existence of these initial paths are checked by DR_setup, above, the we add directories P0 and P1
            rawpath    = 'raw/{}/{}'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))
            if not os.path.exists('reduced/{}/{}/{}/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5),eachpol)):
                os.system('mkdir reduced/{}/{}/{}/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5),eachpol))
            outpath    = 'reduced/{}/{}/{}'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5),eachpol)
        
            # Collect raw files into list 
            raw_files = glob.glob(os.path.join(rawpath,'*sdf'))
        
            # Run ORACDR with the "bad_receptors" option to ignore one of the detectors
            print('\nNow running ORACDR for: {}...'.format(datescan))
            if parfile != '':
                output = wrapper.oracdr('ACSIS',loop='file',dataout=outpath,recipe=recipe,rawfiles=raw_files,recpars=parfile,calib='bad_receptors={}'.format(':'.join(BRlist)),verbose=True,debug=True)
            else:
                output = wrapper.oracdr('ACSIS',loop='file',dataout=outpath,recipe=recipe,rawfiles=raw_files,calib='bad_receptors={}'.format(':'.join(BRlist)),verbose=True,debug=True)

            #####
            # Clean up the output. The python wrapper creates a temporary directory beginning with ORACworking* (given by output.outdir)
            # to store the files -- we want to move the files to our directory tree and remove the temporary directory.
            #####
            os.system('mv {}/* {}'.format(output.outdir,outpath))
            os.system('rm -rf {}'.format(output.outdir))
            os.system('mkdir {}/logfiles; mv {}/*log* {}/logfiles'.format(outpath,outpath,outpath))
            os.system('mkdir {}/imagefiles; mv {}/*png {}/imagefiles'.format(outpath,outpath,outpath))

