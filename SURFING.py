# Import Necessary Modules
from SURFING.reduce import reduce_combined_p0_p1,reduce_individual_p0_p1
from SURFING.postprocess import moment0_residuals,coadd_results,convert_to_fits

#-------------------------------------------------------------------------------------------
#####
# User Defined Parameters
#####

# The region associated with the supplied datescans
region      = 'SERPENS_SOUTH'

# The list of datescans you want to reduce in one batch
# (Observations will be reduced individually, then co-added afterwards)
datescans   = ['20220307_73']

# The parameter file to offer ORACDR. A blank string assumes all default parameters
parfile     = "config/SURFING.ini"

# The ORACDR recipe. For SURFING, it is appropirate to use "REDUCE_SCIENCE_NARROWLINE"
recipe      = 'REDUCE_SCIENCE_NARROWLINE'

# A Key-Value paring of the Molecules associated with each subband. For SURFING:
# C18O Signal = Subband 1. The Image band is subband 4.
# 13CO Signal = Subband 2. The Image band is subband 5.
# 12CO Signal = Subband 3. The Image band is subband 6.
# This can be confirmed in the Het Setup of the JCMTOT.
mol_subband = {'C18O':1,'13CO':2,'CO':3}

#-------------------------------------------------------------------------------------------

###########################################
###########################################
# Begin Main Code
###########################################
###########################################

#####
# Begin the reduction! Start with the combined P0 and P1 reduction
#####
print('Reducing P0 and P1 together...')
reduce_combined_p0_p1(datescans,recipe,parfile=parfile)

#####
# Now, reduce P0 and P1 individually to see if we have an issue with an individual detector (QA testing)
#####
print('\nReducing P0 and P1 separately...')
reduce_individual_p0_p1(datescans,recipe,parfile=parfile)

#####
# Now, make P1-P0 subtraction maps for Moment 0 to assess residual for structure
# In a perfect world, this would produce a blank map, but sometimes artifacts/sensitivity differences
# can lead to different signals from the two detectors (P0 and P1)
#####

print('\nSubtracting P0 Moment 0 maps from P1 Moment 0 maps...')
moment0_residuals(datescans,mol_subband)

#####
# Produce final co-add including the new observations
#####
print('\nCo-adding the results with the main files...')
coadd_results(datescans,mol_subband,region)

#####
# Convert SDF to FITS for convenience
#####
print('\nConverting SDF files to FITS for "non-Starlink" people ;p...')
convert_to_fits(datescans)

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

