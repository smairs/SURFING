import glob
import re
import os
import logging
logging.basicConfig(level=logging.INFO)
logging.root.setLevel(logging.INFO)
from starlink import wrapper,kappa,convert
wrapper.change_starpath('/star')

## User Defined Parameters
region      = 'SERPENS_SOUTH'
datescans   = ['20220307_73']
parfile     = "config/SURFING.ini"
recipe      = 'REDUCE_SCIENCE_NARROWLINE'
mol_subband = {'C18O':1,'13CO':2,'CO':3}

outputs = []
for datescan in datescans:

    # Make output directory
    os.system('mkdir reduced/{}'.format(datescan.split('_')[0]))
    os.system('mkdir reduced/{}/{}'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5)))

    # Populate raw and out paths
    rawpath    = 'raw/{}/{}/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))
    outpath    = 'reduced/{}/{}'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))

    # Collect raw files into list 
    raw_files = glob.glob(os.path.join(rawpath,'*sdf'))

    # Run ORACDR
    print('\nNow running ORACDR for: {}...'.format(datescan))
    output = wrapper.oracdr('ACSIS',loop='file',dataout=outpath,recipe=recipe,rawfiles=raw_files,recpars=parfile,verbose=True,debug=True)
    outputs.append(output)
    os.system('mv {}/* {}/'.format(output.outdir,outpath))
    os.system('rm -r {}'.format(output.outdir))

summaryfile = open('Summary.txt','w')
print('\n#####\n#####\nSummary:\n')
for datescan,output in zip(datescans,outputs):
    #Save the Summary to a file
    summaryfile.write('~~~{}~~~\n#######\n'.format(datescan))
    summaryfile.write('The run log for {} can be found here {}'.format(datescan,output.runlog))
    summaryfile.write('\nThe datafiles are listed below:')
    summaryfile.write(re.sub('ORACworking\w+/','','\n'.join(output.datafiles)))
    summaryfile.write('\nThe image files are listed below:')
    summaryfile.write(re.sub('ORACworking\w+/','','\n'.join(output.imagefiles)))
    summaryfile.write('\nThe additional logs are listed below:')
    summaryfile.write(re.sub('ORACworking\w+/','','\n'.join(output.logfiles)))
    summaryfile.write('')

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

print('\nThis summary is available here: Summary.txt\n')

print('\nNow constructing P0 and P1 separately...')
# Now creating P0 and P1 reductions individually along with their residual Moment 0 maps

for eachpol in ['P0','P1']:
    
    print('\n\t{}...'.format(eachpol))

    # Define "bad" receptors. N = Namakanui, U|W|A =Uu|Aweoweo|Alaihi, 0|1 = Polarisation, U|L = Upper or Lower sideband  
    if eachpol == 'P0':
        BRlist = ['NU1L','NU1U','NW1L','NW1U','NA1L','NA1U']
    elif eachpol == 'P1':
        BRlist = ['NU0L','NU0U','NW0L','NW0U','NA0L','NA0U']
    
    for datescan in datescans:

        # Populate raw and out paths
        rawpath    = 'raw/{}/{}'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))
        if not os.path.exists('reduced/{}/{}/{}/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5),eachpol)):
            os.system('mkdir reduced/{}/{}/{}/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5),eachpol))
        outpath    = 'reduced/{}/{}/{}'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5),eachpol)
    
        # Collect raw files into list 
        raw_files = glob.glob(os.path.join(rawpath,'*sdf'))
    
        # Run ORACDR
        print('\nNow running ORACDR for: {}...'.format(datescan))
        output = wrapper.oracdr('ACSIS',loop='file',dataout=outpath,recipe=recipe,rawfiles=raw_files,recpars=parfile,calib='bad_receptors={}'.format(':'.join(BRlist)),verbose=True,debug=True)
        os.system('mv {}/* {}'.format(output.outdir,outpath))
        os.system('rm -r {}'.format(output.outdir))
        os.system('mkdir {}/logfiles; mv {}/*log* {}/logfiles'.format(outpath,outpath,outpath))
        os.system('mkdir {}/imagefiles; mv {}/*png {}/imagefiles'.format(outpath,outpath,outpath))


print('\nSubtracting P0 Moment 0 maps from P1 Moment 0 maps...')
for datescan in datescans:
    
    P0_mom0 = glob.glob('reduced/{}/{}/{}/g*integ.sdf'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5),'P0'))
    P1_mom0 = glob.glob('reduced/{}/{}/{}/g*integ.sdf'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5),'P1'))

    if not os.path.exists('reduced/{}/{}/Moment0_residuals/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))):
        os.system('mkdir reduced/{}/{}/Moment0_residuals/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5)))

    outsub  = 'reduced/{}/{}/Moment0_residuals/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))   
 
    for eachmol in mol_subband:
        thissubband = mol_subband[eachmol]
        outsub = outsub+'{}_P1_minus_P0_integ.sdf'.format(eachmol)

        P0_coadd_thismol = ''
        P1_coadd_thismol = ''

        for P0file in P0_mom0:
            if P0file.endswith('{}_integ.sdf'.format(thissubband)):
                P0_coadd_thismol = P0file
    
        for P1file in P1_mom0:
            if P1file.endswith('{}_integ.sdf'.format(thissubband)):
                P1_coadd_thismol = P1file

        if P0_coadd_thismol != '':
            if P1_coadd_thismol != '':
                kappa.sub(P1_coadd_thismol,P0_coadd_thismol,outsub)    

print('\nConverting SDF files to FITS for "non-Starlink" people ;p...')
for datescan in datescans:

    sdf_files_1 = sorted(list(glob.glob('reduced/{}/{}/*sdf'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5)))))
    sdf_files_2 = sorted(list(glob.glob('reduced/{}/{}/*/*sdf'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5)))))
    all_sdf_files = sdf_files_1+sdf_files_2
    for i,eachsdf in enumerate(all_sdf_files):
        print('\tFile {} of {}...'.format(i+1,len(all_sdf_files)))
        convert.ndf2fits(eachsdf,eachsdf.replace('.sdf','.fits'))

print('\nCo-adding the results with the main files...')
for eachmol in mol_subband:
    reduced_files = []
    for datescan in datescans:
        reducedpath = 'reduced/{}/{}/'.format(datescan.split('_')[0],datescan.split('_')[-1].zfill(5))
        reduced_files = reduced_files+list(glob.glob(reducedpath+'ga*_{}_reduced001.sdf'.format(mol_subband[eachmol])))
    coadd_out = 'coadd_temp/{}_{}_temp_coadd.sdf'.format(region,eachmol)
    if not os.path.exists('coadd_temp/'):
        os.system('mkdir coadd_temp/')
    kappa.wcsmosaic(reduced_files,out=coadd_out,ref=reduced_files[0])

    if not os.path.exists('coadds'):
        os.system('mkdir coadds')
        os.system('mv {} coadds/{}_{}_coadd.sdf'.format(coadd_out,region,eachmol))
    else:
        kappa.wcsmosaic([coadd_out,'coadds/{}_{}_coadd.sdf'.format(region,eachmol)],out='coadds/{}_{}_coadd_new.sdf'.format(region,eachmol),ref='coadds/{}_{}_coadd.sdf'.format(region,eachmol))
        os.system('rm coadds/{}_{}_coadd.sdf'.format(region,eachmol))
        os.system('mv coadds/{}_{}_coadd_new.sdf coadds/{}_{}_coadd.sdf'.format(region,eachmol,region,eachmol))

    if os.path.exists('coadds/{}_{}_coadd.fits'.format(region,eachmol)):
        os.system('rm coadds/{}_{}_coadd.fits'.format(region,eachmol))
    convert.ndf2fits('coadds/{}_{}_coadd.sdf'.format(region,eachmol),'coadds/{}_{}_coadd.fits'.format(region,eachmol))
        

print('\n\n######################')
print('              ___            ___')
print('             /   \          /   \\')
print('             \_   \        /  __/')
print('              _\   \      /  /__')
print('              \___  \____/   __/')
print('                  \_       _/')
print('                    | @ @  \_')
print('                    |        ')
print('                  _/     /\  ')
print('                 /o)  (o/\ \_')
print('Done!            \_____/ /   ')
print('Thanks, eh?!       \____/    ')
print('')
print('######################\n')

