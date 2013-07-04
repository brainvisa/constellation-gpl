from brainvisa.processes import *

def validation():
  try:
    import constel
  except:
    raise ValidationError( 'constellation module is not here.' )

name = 'Brainvisa Constellation Inter Pipeline'
userLevel = 2

signature = Signature(
    'study_name', String(),
    'texture_in', String(),
   'texture_out', String(),
   'patch_label', Integer(),
         'group', ReadDiskItem('Group definition', 'XML' ),
  'average_mesh', ReadDiskItem( 'BothAverageBrainWhite', 'BrainVISA mesh formats' ),
  'gyri_texture', ListOf( ReadDiskItem( 'BothResampledGyri', 'Aims texture formats' ) ),
)

def linkGroup( self, param1 ):
  print 'linkGroup', param1
  print 'self:', self
  eNode = self.executionNode()
  for node in eNode.children():
    print node.name()
    if node.name() == 'Parallel Node':
      node.addChild( 'N%d' % len(list(node.children())), ProcessExecutionNode( 'createReducedConnectivityMatrixOnRangeOfSubjects',
                  optional = 1) )
      print 'added. Nb nodes:', len(list(node.children()))

def initialization( self ):

  self.addLink( None, 'group', self.linkGroup )

  eNode = SerialExecutionNode( self.name, parameterized=self )

  ## 01 Surface With Enough Connections Creation InterSubjects
  eNode.addChild( 'meanProfileInter',
                  ProcessExecutionNode( 'surfaceWithEnoughConnectionsCreation',
                  optional = 1 ) )

  eNode.addDoubleLink( 'meanProfileInter.study_name',
                       'study_name' )

  eNode.addDoubleLink( 'meanProfileInter.texture_in',
                       'texture_in' )

  eNode.addDoubleLink( 'meanProfileInter.texture_out',
                       'texture_out' )                     

  eNode.addDoubleLink( 'meanProfileInter.patch_label',
                       'patch_label' )

  eNode.addDoubleLink( 'meanProfileInter.group',
                       'group' )

  ## 02 Combine All Subjects Mean Conectivity Profile
  eNode.addChild( 'combineMeanInter',
                  ProcessExecutionNode( 'createConnectivityProfileOnRangeOfSubjects',
                  optional = 1 ) )

  eNode.addDoubleLink( 'combineMeanInter.study_name',
                       'study_name' )

  eNode.addDoubleLink( 'combineMeanInter.texture_in',
                       'texture_in' )

  eNode.addDoubleLink( 'combineMeanInter.texture_out',
                       'texture_out' )

  eNode.addDoubleLink( 'combineMeanInter.patch_label',
                       'patch_label' )

  eNode.addDoubleLink( 'combineMeanInter.group',
                       'group' )

  ## 03 Thresholding Average Mean Connectivity Profile
  eNode.addChild( 'meanInter',
                  ProcessExecutionNode( 'removeInternalConnectionsOnRangeOfSubjects',
                  optional = 1 ) )

  eNode.addDoubleLink( 'meanInter.mask',
                       'meanProfileInter.mask' )

  eNode.addDoubleLink( 'meanInter.connectivity_profile_group',
                       'combineMeanInter.connectivity_profile_group' )

  ## 04 Watershed On Normed Smoothed InterSubjects
  eNode.addChild( 'watershedInter',
                  ProcessExecutionNode( 'filteringWatershedOnRangeOfSubjects',
                  optional = 1 ) )

  eNode.addDoubleLink( 'watershedInter.average_mesh',
                       'average_mesh' )

  eNode.addDoubleLink( 'watershedInter.normed_thresholded_mean_connectivity_profile',
                       'meanInter.norm_thresholded_mean_connectivity_profile' )

  ## 05 Connectivity Matrix to Watershed Bassins InterSubjects
  eNode.addChild( 'connMatrixBasinInter',
                  ProcessExecutionNode( 'createReducedConnectivityMatrixOnRangeOfSubjects',
                  optional = 1 ) )

  eNode.addDoubleLink( 'connMatrixBasinInter.study_name',
                       'study_name' )

  eNode.addDoubleLink( 'connMatrixBasinInter.texture_in',
                       'texture_in' )

  eNode.addDoubleLink( 'connMatrixBasinInter.texture_out',
                       'texture_out' )

  eNode.addDoubleLink( 'connMatrixBasinInter.patch_label',
                       'patch_label' )

  eNode.addDoubleLink( 'connMatrixBasinInter.group',
                       'group' )

  eNode.addDoubleLink( 'connMatrixBasinInter.average_mesh',
                       'average_mesh' )

  eNode.addDoubleLink( 'connMatrixBasinInter.gyri_segmentation',
                       'gyri_texture' )

  eNode.addDoubleLink( 'connMatrixBasinInter.filtered_watershed',
                       'watershedInter.filtered_watershed' )

  ## 06 Clustering InterSubjects
  eNode.addChild( 'clusteringInter',
                  ProcessExecutionNode( 'clusteringInterSubjects',
                  optional = 1 ) )

  eNode.addDoubleLink( 'clusteringInter.study_name',
                       'study_name' )

  eNode.addDoubleLink( 'clusteringInter.texture_in',
                       'texture_in' )

  eNode.addDoubleLink( 'clusteringInter.texture_out',
                       'texture_out' )

  eNode.addDoubleLink( 'clusteringInter.patch_label',
                       'patch_label' )

  eNode.addDoubleLink( 'clusteringInter.group',
                       'group' )

  #eNode.addDoubleLink( 'clusteringInter.patch_label',
                       #'patch_label' )

  eNode.addDoubleLink( 'clusteringInter.average_mesh',
                       'average_mesh' )
  eNode.addDoubleLink( 'clusteringInter.gyri_segmentation',
                       'connMatrixBasinInter.gyri_segmentation' )
  eNode.addDoubleLink( 'clusteringInter.individual_reduced_matrix',
                       'connMatrixBasinInter.connectivity_matrix_reduced' )

  self.setExecutionNode( eNode )