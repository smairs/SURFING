import glob
import re
import os
import logging
logging.basicConfig(level=logging.INFO)
logging.root.setLevel(logging.INFO)
from starlink import wrapper,kappa,convert
wrapper.change_starpath('/star')

def moment0_residuals(datescans,mol_subband):
    '''
    ORACDR has produced moment 0 maps (*integ.sdf) for each molecule and datescan.
    This code grabs those "integ.sdf" files and organises them by P0 and P1, performs subtractions.
    then organises the results for by-eye QA testing.

    datescans  : A list of datescan strings in the format ['YYYYMMDD_SS','YYYYMMDD_SS'...], where SS = Scan Number
    mol_subband: A Key-Value paring of the Molecules associated with each subband. For SURFING:
                 C18O Signal = Subband 1. The Image band is subband 4.
                 13CO Signal = Subband 2. The Image band is subband 5.
                 12CO Signal = Subband 3. The Image band is subband 6.
                 This can be confirmed in the Het Setup of the JCMTOT.
    '''

    #####
    # Loop over datescans
    #####
    for datescan in datescans:
        
        # Collect the individual P0 and P1 Moment 0 maps
        P0_mom0 = glob.glob('reduced/{}/{}/{}/g*integ.sdf'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5),'P0'))
        P1_mom0 = glob.glob('reduced/{}/{}/{}/g*integ.sdf'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5),'P1'))

        # Make the directory to store the residuals
        if not os.path.exists('reduced/{}/{}/Moment0_residuals/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))):
            os.system('mkdir reduced/{}/{}/Moment0_residuals/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5)))

        # Define the directory to store the residuals 
        outsub  = 'reduced/{}/{}/Moment0_residuals/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))   
     
        # Perform the subtraction by molecule
        for eachmol in mol_subband:
            thissubband = mol_subband[eachmol]

            # Define the name = include molecule information
            outsub = outsub+'{}_P1_minus_P0_integ.sdf'.format(eachmol)
    
            # Define empty strings to ensure that we have matching P0 and P1 Moment 0 maps, or we can't perform subtraction!
            P0_coadd_thismol = ''
            P1_coadd_thismol = ''
    
            for P0file in P0_mom0:
                if P0file.endswith('{}_integ.sdf'.format(thissubband)):
                    P0_coadd_thismol = P0file
        
            for P1file in P1_mom0:
                if P1file.endswith('{}_integ.sdf'.format(thissubband)):
                    P1_coadd_thismol = P1file
   
            # If we have matching P0 and P1 moment 0 maps, perform the subtraction!
            if P0_coadd_thismol != '':
                if P1_coadd_thismol != '':
                    kappa.sub(P1_coadd_thismol,P0_coadd_thismol,outsub)

def coadd_results(datescans,mol_subband,region):
    '''
    Produce coadds including new results. If no coadd exists yet, create one. If there is a coadd from previous observations,
    add these new observations to that main file.

    datescans  : A list of datescan strings in the format ['YYYYMMDD_SS','YYYYMMDD_SS'...], where SS = Scan Number
    mol_subband: A Key-Value paring of the Molecules associated with each subband. For SURFING:
                 C18O Signal = Subband 1. The Image band is subband 4.
                 13CO Signal = Subband 2. The Image band is subband 5.
                 12CO Signal = Subband 3. The Image band is subband 6.
                 This can be confirmed in the Het Setup of the JCMTOT.
    region     : The region you are working on -- MUST MATCH CURRENT CO-ADD NAME FOR PROPER AVERAGING e.g. SERPENS_SOUTH
    '''
    # Perform co-adds by molecule
    for eachmol in mol_subband:

        # Define an empty list to populate with all the ga*reduced0*.sdf cubes for this molecule by date and scan
        reduced_files = []
        for datescan in datescans:

            # This directory was created and populated in previous steps found in SURFING.reduce
            reducedpath = 'reduced/{}/{}/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))
            reduced_files = reduced_files+list(glob.glob(reducedpath+'ga*_{}_reduced0*.sdf'.format(mol_subband[eachmol])))

        #####
        # We will first co-add all new observations together, then co-add the result with the existing, main co-added file.
        #####

        # Create a name for the co-add of the new observations and store it in a temporary directory
        coadd_out = 'coadd_temp/{}_{}_temp_coadd.sdf'.format(region,eachmol)
        if not os.path.exists('coadd_temp/'):
            os.system('mkdir coadd_temp/')

        # Check to see if we have more than one new observation to co-add together for this molecule!
        if len(reduced_files)>1:
            kappa.wcsmosaic(reduced_files,out=coadd_out,ref=reduced_files[0])

        # In the case that we are only reducing one observation - we don't need to co-add it with itself!
        elif len(reduced_files)==1:
            os.system('cp {} {}'.format(reduced_files[0],coadd_out))
    
        else:
            try:
                print(reduced_files[1])
            except IndexError:
                print('Oh no! There are no ga*_{}_reduced0*.sdf files to co-add! It appears that there is no new {} data in '\
                        'the listed datescans!'.format(mol_subband[eachmol],eachmol))

        # Make sure that the official co-add exists. If it doesn't - move the new co-added observations to
        # the main "coadds" directory and that will become the official co-add.
        if not os.path.exists('coadds'):
            os.system('mkdir coadds')
        if not os.path.exists('coadds/{}_{}_coadd.sdf'.format(region,eachmol)):
            os.system('cp {} coadds/{}_{}_coadd.sdf'.format(coadd_out,region,eachmol))
        else:
            # Perform the coadd
            kappa.wcsmosaic([coadd_out,'coadds/{}_{}_coadd.sdf'.format(region,eachmol)],out='coadds/{}_{}_coadd_new.sdf'.format(region,eachmol),ref='coadds/{}_{}_coadd.sdf'.format(region,eachmol))
            # Remove the old coadd
            os.system('rm -f coadds/{}_{}_coadd.sdf'.format(region,eachmol))
            # Rename the new coadd to be the official version
            os.system('mv coadds/{}_{}_coadd_new.sdf coadds/{}_{}_coadd.sdf'.format(region,eachmol,region,eachmol))

        # Remove temp directory
        os.system('rm -rf coadd_temp/')

        # Create a new FITS copy of the coadd
        if os.path.exists('coadds/{}_{}_coadd.fits'.format(region,eachmol)):
            os.system('rm -f coadds/{}_{}_coadd.fits'.format(region,eachmol))
        # Convert SDF to fits
        convert.ndf2fits('coadds/{}_{}_coadd.sdf'.format(region,eachmol),'coadds/{}_{}_coadd.fits'.format(region,eachmol))

def convert_to_fits(datescans):
    '''
    Convert all reduced sdf fils to fits

    datescans  : A list of datescan strings in the format ['YYYYMMDD_SS','YYYYMMDD_SS'...], where SS = Scan Number
    '''

    # Loop over all new observations
    for datescan in datescans:
        # Gather combined P0 and P1 results
        sdf_files_1 = sorted(list(glob.glob('reduced/{}/{}/*sdf'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5)))))

        # Gather individual P0 and P1 results
        sdf_files_2 = sorted(list(glob.glob('reduced/{}/{}/*/*sdf'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5)))))

        # Concatenate the lists into one
        all_sdf_files = sdf_files_1+sdf_files_2

        # Loop through all sdf files and perform conversion to fits
        for i,eachsdf in enumerate(all_sdf_files):
            print('\tFile {} of {}...'.format(i+1,len(all_sdf_files)))
            convert.ndf2fits(eachsdf,eachsdf.replace('.sdf','.fits'))

