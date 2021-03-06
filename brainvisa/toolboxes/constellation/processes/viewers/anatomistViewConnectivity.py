###############################################################################
# This software and supporting documentation are distributed by CEA/NeuroSpin,
# Batiment 145, 91191 Gif-sur-Yvette cedex, France. This software is governed
# by the CeCILL license version 2 under French law and abiding by the rules of
# distribution of free software. You can  use, modify and/or redistribute the
# software under the terms of the CeCILL license version 2 as circulated by
# CEA, CNRS and INRIA at the following URL "http://www.cecill.info".
###############################################################################

from __future__ import print_function

# Axon python API module
from __future__ import absolute_import
from brainvisa.processes import Signature, ReadDiskItem, Integer, Boolean,\
    mainThreadActions


def validation(self):
    try:
        from brainvisa import anatomist as ana
    except ImportError:
        raise ValidationError(_t_("Anatomist not available"))
    ana.validation()


name = 'Anatomist view connectivity'
userLevel = 2

signature = Signature(
    'bundles', ReadDiskItem(
        'Fascicles bundles', 'Aims readable bundles formats'),
    'dw_to_t1', ReadDiskItem(
        'Transform T2 Diffusion MR to Raw T1 MRI', 'Transformation matrix'),
    'white_mesh', ReadDiskItem(
        'White Mesh', 'anatomist mesh formats',
        requiredAttributes={"side": "both",
                            "vertex_corr": "Yes",
                            "averaged": "No"}),
    'clustering_texture', ReadDiskItem(
        'Connectivity ROI Texture', 'anatomist texture formats'),
    'cluster_number', Integer(),
    'max_number_of_fibers', Integer(),
    'clustering_texture_timestep', Integer(),
    'inflated_mesh', Boolean(),
)


def initialization(self):
    """
    """

    def link_mesh(self, dummy):
        if self.bundles is not None:
            atts = ['center', 'subject']
            datts = dict([(att, self.bundles.get(att)) for att in atts
                          if self.bundles.get(att) is not None])
            datts['inflated'] = 'Yes'
            yes_no = ['Yes', 'No']
            datts['inflated'] = yes_no[1 - int(self.inflated_mesh)]
            print('link_mesh, datts:', datts)
            res = self.signature['white_mesh'].findValue(datts)
            if res is None:
                datts['inflated'] = yes_no[int(self.inflated_mesh)]
                print('try other mesh:', datts)
                res = self.signature['white_mesh'].findValue(datts)
            print('res:', res)
            return res

    self.inflated_mesh = True
    self.linkParameters('bundles', 'clustering_texture')
    self.linkParameters('dw_to_t1', 'bundles')
    self.linkParameters('white_mesh', ['bundles', 'inflated_mesh'], link_mesh)
    self.max_number_of_fibers = 10000
    self.clustering_texture_timestep = 0


def loadFilteredBundles(self, bundles_name):
    '''Fake bundles reading: just creates an empty graph with the file name
    in it, which will be used (and actually read) by the fusion.
    Also counts fibers.
    '''
    from soma import aims
    from soma.minf import api as minf
    from brainvisa import anatomist

    maxFibers = self.max_number_of_fibers
    nfibers = 0
    if maxFibers != 0:
        binfo = minf.readMinf(bundles_name)[0]
        if 'curves_count' in binfo:
            nfibers = binfo['curves_count']
        elif 'fibers_count' in binfo:
            nfibers = binfo['fibers_count']
        else:
            nfibers = 500000  # arbitrary...
    graph = aims.Graph('RoiArg')
    graph['fibers_count'] = nfibers
    a = anatomist.Anatomist()
    ag = a.toAObject(graph)
    ag.setFileName(bundles_name)
    return ag


def execution_mainthread(self, context):
    """
    """
    from brainvisa import anatomist

    # instance of Anatomist
    a = anatomist.Anatomist()

    # load objects
    mesh = a.loadObject(self.white_mesh)
    clusters = a.loadObject(self.clustering_texture)
    # wat = a.loadObject(self.watershed)

    # filtering fiber tracts
    clusters.attributed()['time_step'] \
        = self.clustering_texture_timestep
    bundles = self.loadFilteredBundles(self.bundles.fullPath())
    totalfibers = bundles.graph()['fibers_count']
    if totalfibers != 0:
        fibers_proportion_filter \
            = float(self.max_number_of_fibers) / totalfibers
    else:
        fibers_proportion_filter = 1.
    bundles.graph()['fibers_proportion_filter'] = fibers_proportion_filter

    # load a transformation
    r = a.createReferential()
    mr = mesh.referential
    bundles.assignReferential(r)
    mesh.assignReferential(mr)
    a.loadTransformation(self.dw_to_t1.fullPath(), r, mr)

    # change palette
    palette = a.getPalette("freesurfer_gyri")
    clusters.setPalette(palette, minVal=0, maxVal=20, absoluteMode=True)

    # view object
    win = a.createWindow('3D')

    # fusion T1, mesh, texture and bundles
    fusionned = [mesh, clusters, bundles]
    connectivity = a.fusionObjects(
                        fusionned,
                        method='FusionBundlesSplitByCorticalROIsMethod')

    if connectivity is None:
        raise ValueError('could not fusion objects')

    # adds objects in windows:
    win.addObjects(connectivity)

    # get the Aims graph
    graph = a.toAimsObject(connectivity)
    a.execute('SetMaterial',
              objects=[connectivity],
              diffuse=[0.5, 0., 1., 0.2])

    # list of builtin patches/clusters colors
    # TODO: this has to move to a more flexible nomenclature
    patches = {'1': [1., 0.3, 0.3, 1.], '2': [0.3, 0.8, 0.3, 1.],
               '3': [0.3, 0.3, 0.8, 1.], '4': [0.8, 0.8, 0.3, 1.],
               '5': [0.8, 0.3, 0.8, 1.], '6': [0.3, 0.8, 0.8, 1.]}
    patches[self.cluster_number] = [0.4, 0.6, 1., 1.]
    basins = {'17': [0., 0., 1., 0.35], '14': [1., 0., 0., 0.35],
              '15': [0., 1., 0., 0.35]}

    basincolor = [0.9, 0.9, 0.9, 1.]
    all_regions = list(patches.keys()) + list(basins.keys())
    for v in graph.vertices():
        if v['name'] in all_regions:
            if v['name'] in patches:
                a.execute('SetMaterial', objects=[v['ana_object']],
                          diffuse=patches[v['name']],
                          selectable_mode='always_selectable')
                for edge in v.edges():
                    if edge.vertices()[0]['name'] in basins \
                            or edge.vertices()[1]['name'] in basins:
                        if edge.vertices()[0]['name'] in basins:
                            color = basins[edge.vertices()[0]['name']]
                        else:
                            color = basins[edge.vertices()[1]['name']]
                        edgeobj = edge['ana_object']
                        a.execute('SetMaterial',
                                  objects=[edgeobj],
                                  diffuse=color)
                        win.addObjects(edgeobj)
            else:
                a.execute('SetMaterial',
                          objects=[v['ana_object']],
                          diffuse=basincolor,
                          selectable_mode='always_selectable')
        else:
            a.execute('SetMaterial',
                      objects=[v['ana_object']],
                      selectable_mode='always_selectable')

    win.setControl('SelectControl')
    sel_action = win.view().controlSwitch().getAction('SelectionAction')
    sel_action.mode = sel_action.mode_intersection
    return [win, connectivity] + fusionned


def execution(self, context):
    """
    """

    return mainThreadActions().call(self.execution_mainthread, context)
