#!/usr/bin/env python
###############################################################################
# This software and supporting documentation are distributed by CEA/NeuroSpin,
# Batiment 145, 91191 Gif-sur-Yvette cedex, France. This software is governed
# by the CeCILL license version 2 under French law and abiding by the rules of
# distribution of free software. You can  use, modify and/or redistribute the
# software under the terms of the CeCILL license version 2 as circulated by
# CEA, CNRS and INRIA at the following URL "http://www.cecill.info".
###############################################################################

"""
This script does the following:
*
*

Main dependencies:
"""


# ----------------------------Imports------------------------------------------


# axon python API module
from __future__ import absolute_import
from brainvisa.processes import Signature
from brainvisa.processes import ReadDiskItem
from brainvisa.processes import WriteDiskItem
from brainvisa.processes import ValidationError

# soma module
from soma.path import find_in_path


def validation():
    """
    This function is executed at BrainVisa startup when the process is loaded.
    It checks some conditions for the process to be available.
    """
    if not find_in_path('AimsGyriTextureCleaningIsolatedVertices.py'):
        raise ValidationError(
            "Please make sure that constel module is installed.")


# ----------------------------Header-------------------------------------------


name = 'Cleaning Isolated Vertices'
userLevel = 2


signature = Signature(
    # inputs
    'gyri_texture', ReadDiskItem(
        'ROI Texture', 'Aims texture formats',
        requiredAttributes={"side": "both", "vertex_corr": "Yes"}),
    'mesh', ReadDiskItem(
        'White Mesh', 'Aims mesh formats',
        requiredAttributes={"side": "both", "vertex_corr": "Yes"}),

    # outputs
    'clean_gyri_texture', WriteDiskItem(
        'ROI Texture', 'Aims texture formats',
        requiredAttributes={"side": "both", "vertex_corr": "Yes"}),)


# ----------------------------Functions----------------------------------------


def initialization(self):
    """
    """

    self.linkParameters('mesh', 'gyri_texture')
    self.linkParameters('clean_gyri_texture', 'gyri_texture')


# ----------------------------Main Program-------------------------------------


def execution(self, context):
    """
    """

    context.pythonSystem('AimsGyriTextureCleaningIsolatedVertices.py',
                         self.gyri_texture,
                         self.mesh,
                         self.clean_gyri_texture)
