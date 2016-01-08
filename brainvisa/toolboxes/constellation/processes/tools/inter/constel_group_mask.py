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
* defines a Brainvisa process
    - the parameters of a process (Signature),
    - the parameters initialization
    - the linked parameters
* this process executes the command 'constelConnectivityProfileOverlapMask'

Main dependencies: Axon python API, Soma-base, constel

Author: sandrine.lefranc@cea.fr
"""

#----------------------------Imports-------------------------------------------


# python system module
import os
import sys

# axon python API module
from brainvisa.processes import Signature, ListOf, ReadDiskItem, String, \
    WriteDiskItem, ValidationError

# soma-base module
from soma.path import find_in_path


def validation():
    """This function is executed at BrainVisa startup when the process is
    loaded. It checks some conditions for the process to be available.
    """
    if not find_in_path("constelConnectivityProfileOverlapMask.py"):
        raise ValidationError(
            "Please make sure that constel module is installed.")


#----------------------------Header--------------------------------------------


name = "Group Connectivity Mask"
userLevel = 2

signature = Signature(
    # inputs
    "mean_individual_profiles", ListOf(
        ReadDiskItem("Connectivity Profile Texture", "Aims texture formats",
                     requiredAttributes={"normed": "No",
                                         "thresholded": "No",
                                         "averaged": "No",
                                         "intersubject": "No"})),
    "subjects_group", ReadDiskItem("Group definition", "XML"),
    "new_study_name", String(),

    # outputs
    "group_mask", WriteDiskItem(
        "Mask Texture", "Aims texture formats"), )


#----------------------------Functions-----------------------------------------


def initialization(self):
    """Provides link of parameters"""

    # optional value
    self.setOptional("new_study_name")

    # link of parameters
    def link_mask(self, dummy):
        """Function of link between mask and group parameters."""
        if self.subjects_group and self.mean_individual_profiles:
            atts = dict(self.mean_individual_profiles[0].hierarchyAttributes())
            atts["group_of_subjects"] = os.path.basename(
                os.path.dirname(self.subjects_group.fullPath()))
            if self.new_study_name:
                atts["texture"] = self.new_study_name
            else:
                atts["texture"] = \
                    self.mean_individual_profiles[0].get("texture")
            return self.signature["group_mask"].findValue(atts)

    # link of parameters for autocompletion
    self.linkParameters("group_mask", ("mean_individual_profiles", "subjects_group", "new_study_name"),
                        link_mask)


#----------------------------Main program--------------------------------------


def execution(self, context):
    # execute the command
    context.system(sys.executable,
                   find_in_path("constelConnectivityProfileOverlapMask.py"),
                   self.mean_individual_profiles,
                   self.group_mask)