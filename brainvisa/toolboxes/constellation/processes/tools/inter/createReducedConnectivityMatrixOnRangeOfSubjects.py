# -*- coding: utf-8 -*-
from brainvisa.processes import *
from soma.path import find_in_path
from brainvisa.group_utils import Subject
from soma.minf.api import registerClass, readMinf
from soma.functiontools import partial

def validation():
  if not find_in_path( 'constelConnectionDensityTexture' ):
    raise ValidationError( 'constellation module is not here.' )

name = '05 - Connectivity Matrix Reduced'
userLevel = 2

signature = Signature(
                'study_name', String(),
                'texture_in', String(),
               'texture_out', String(),
               'patch_label', Integer(),
                     'group', ReadDiskItem('Group definition', 'XML' ),
        'filtered_watershed', ReadDiskItem( 'Averaged Filtered Watershed', 'Aims texture formats' ),
  'individual_matrix_sparse', ListOf( ReadDiskItem( 'Gyrus Connectivity Matrix', 'Matrix sparse' ) ),
              'average_mesh', ReadDiskItem( 'BothAverageBrainWhite', 'BrainVISA mesh formats' ),
         'gyri_segmentation', ListOf( ReadDiskItem( 'BothResampledGyri', 'Aims texture formats' ) ),
              'vertex_index', ListOf( ReadDiskItem( 'Vertex Index', 'Text file' ) ),
  'connectivity_matrix_reduced', ListOf( WriteDiskItem( 'Group Reduced Connectivity Matrix', 'GIS image' ) ),
)


def afterChildAddedCallback( self, parent, key, child ):
  # Set default values
  child.removeLink( 'filtered_watershed', 'connectivity_matrix_full' )
  child.removeLink( 'connectivity_matrix_reduced', 'filtered_watershed' )
  child.removeLink( 'vertex_index', 'connectivity_matrix_full' )

  child.signature[ 'filtered_watershed' ] \
    = parent.signature[ 'filtered_watershed' ]
  child.signature[ 'white_mesh' ] = parent.signature[ 'average_mesh' ]

  child.patch_label = parent.patch_label
  child.filtered_watershed = parent.filtered_watershed
  child.white_mesh = parent.average_mesh

  ## Add link between eNode.ListOf_Input_3dImage and pNode.Input_3dImage
  parent.addLink( key + '.filtered_watershed', 'filtered_watershed' )
  parent.addLink( key + '.patch_label', 'patch_label' )
  parent.addLink( key + '.white_mesh', 'average_mesh' )


def beforeChildRemovedCallback( self, parent, key, child ):
  parent.removeLink( key + '.filtered_watershed', 'filtered_watershed' )
  parent.removeLink( key + '.patch_label', 'patch_label' )
  parent.removeLink( key + '.white_mesh', 'average_mesh' )


def initialization ( self ):
  def linkIndividualProfiles( self, dummy ):
    if self.group is not None:
      registerClass('minf_2.0', Subject, 'Subject')
      groupOfSubjects = readMinf(self.group.fullPath())
      profiles = []
      for subject in groupOfSubjects:
        study = self.study_name
        texture = self.texture_in
        gyrus = 'G' + str(self.patch_label)
        profiles.append( WriteDiskItem( 'Gyrus Connectivity Matrix', 'Matrix sparse' ).findValue( { 'study': study, 'texture': texture, 'gyrus': gyrus }, subject.attributes() ) )
      return profiles
  def linkProfiles( self, dummy ):
    if self.individual_matrix_sparse and self.group is not None:
      profiles = []
      for p in self.individual_matrix_sparse:
        if p is None:
          continue
        atts = dict( self.group.hierarchyAttributes() )
        atts[ 'study' ] = p.get( 'study' )
        atts[ 'texture' ] = self.texture_out
        atts[ 'gyrus' ] = p.get( 'gyrus' )
        atts[ 'subject' ] = p.get( 'subject' )
        profiles.append( WriteDiskItem( 'Group Reduced Connectivity Matrix', 'GIS image' ).findValue( atts ) )
      return profiles
  def linkWatershed( self, dummy ):
    if self.group is not None and self.patch_label and self.texture_out \
        and self.study_name:
      atts = self.group.hierarchyAttributes()
      atts[ 'texture' ] = self.texture_out
      atts[ 'gyrus' ] = 'G' + str(self.patch_label)
      atts[ 'study' ] = self.study_name
      #print 'atts:', atts
      return ReadDiskItem( 'Averaged Filtered Watershed', 'Aims texture formats' ).findValue( atts )

  self.linkParameters( 'individual_matrix_sparse', ( 'group', 'study_name', 'texture_in', 'patch_label' ), linkIndividualProfiles )
  self.linkParameters( 'filtered_watershed', ( 'group', 'patch_label', 'texture_out', 'study_name' ), linkWatershed )
  self.linkParameters( 'connectivity_matrix_reduced', ( 'group','individual_matrix_sparse', 'texture_out') , linkProfiles )
  self.linkParameters( 'vertex_index', 'individual_matrix_sparse')
  self.signature['individual_matrix_sparse'].userLevel = 2

  eNode = ParallelExecutionNode( 'Reduced_connectivity_matrix',
                                 parameterized = self,
                                 possibleChildrenProcesses = [ 'createReducedConnectivityMatrix' ],
                                 notify = True )
  self.setExecutionNode( eNode )

  # Add callback to warn about child add and remove
  eNode.afterChildAdded.add(\
    ExecutionNode.MethodCallbackProxy( self.afterChildAddedCallback ) )
  eNode.beforeChildRemoved.add(\
    ExecutionNode.MethodCallbackProxy( self.beforeChildRemovedCallback ) )
  #eNode.afterChildRemoved.add(\
    #ExecutionNode.MethodCallbackProxy( self.afterChildRemovedCallback ) )

  # Add links to refresh child nodes when main lists are modified
  eNode.addLink( None,
                 'individual_matrix_sparse',
                 partial( brainvisa.processes.mapValuesToChildrenParameters,
                          eNode,
                          eNode,
                          'connectivity_matrix_full',
                          'individual_matrix_sparse',
                          defaultProcess = 'createReducedConnectivityMatrix',
                          name='createReducedConnectivityMatrix' ) )

  eNode.addLink( None,
                 'connectivity_matrix_reduced',
                 partial( brainvisa.processes.mapValuesToChildrenParameters,
                          eNode,
                          eNode,
                          'connectivity_matrix_reduced',
                          'connectivity_matrix_reduced',
                          defaultProcess = 'createReducedConnectivityMatrix',
                          name='createReducedConnectivityMatrix' ) )

  eNode.addLink( None,
                 'vertex_index',
                 partial( brainvisa.processes.mapValuesToChildrenParameters,
                          eNode,
                          eNode,
                          'vertex_index',
                          'vertex_index',
                          defaultProcess = 'createReducedConnectivityMatrix',
                          name='createReducedConnectivityMatrix' ) )

  eNode.addLink( None,
                 'gyri_segmentation',
                 partial( brainvisa.processes.mapValuesToChildrenParameters,
                          eNode,
                          eNode,
                          'gyri_segmentation',
                          'gyri_segmentation',
                          defaultProcess = 'createReducedConnectivityMatrix',
                          name='createReducedConnectivityMatrix' ) )

