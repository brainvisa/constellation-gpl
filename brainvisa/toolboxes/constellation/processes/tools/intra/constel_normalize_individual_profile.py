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
* this process executes the command 'constelRemoveInternalConnections.py'.

Main dependencies: Axon python API, Soma-base, constel

Author: sandrine.lefranc@cea.fr
"""

#----------------------------Imports-------------------------------------------


# python modules
import sys

# Axon python API module
from brainvisa.processes import Signature, Boolean, ReadDiskItem, String, \
    WriteDiskItem, ValidationError

# soma-base module
from soma.path import find_in_path

# constel module
try:
    from constel.lib.utils.files import select_ROI_number
except:
    pass


def validation():
    """This function is executed at BrainVisa startup when the process is
    loaded. It checks some conditions for the process to be available.
    """
    try:
        import constel
    except:
        raise ValidationError(
            "Please make sure that constel module is installed.")


#----------------------------Header--------------------------------------------


name = "Mean Individual Profile Normalization"
userLevel = 2

signature = Signature(
    # --inputs--
    "mean_individual_profile", ReadDiskItem(
        "Connectivity Profile Texture", "Aims texture formats",
        requiredAttributes={"normed": "No",
                            "thresholded": "No",
                            "averaged": "No",
                            "intersubject": "No"}),
    "ROIs_segmentation", ReadDiskItem("ROI Texture", "Aims texture formats",
                                 requiredAttributes={"side": "both",
                                                     "vertex_corr": "Yes"}),
    "ROIs_nomenclature", ReadDiskItem("Nomenclature ROIs File", "Text File"),
    "ROI", String(),

    # --outputs--
    "normed_individual_profile", WriteDiskItem(
        "Connectivity Profile Texture", "Aims texture formats",
        requiredAttributes={"normed": "Yes",
                            "thresholded": "Yes",
                            "averaged": "No",
                            "intersubject": "No"}),
    "keep_internal_connections", Boolean(),
)


#----------------------------Functions-----------------------------------------


def initialization(self):
    """Provides default values and link of parameters
    """
    # default value
    self.keep_internal_connections = False
    self.ROIs_nomenclature = self.signature["ROIs_nomenclature"].findValue({})

    def link_matrix2ROI(self, dummy):
        """Define the attribut 'gyrus' from fibertracts pattern for the
        signature 'ROI'.
        """
        if self.mean_individual_profile is not None:
            s = str(self.mean_individual_profile.get("gyrus"))
            name = self.signature["ROI"].findValue(s)
        return name

    # link of parameters for autocompletion
    self.linkParameters("ROI", "mean_individual_profile", link_matrix2ROI)
    self.linkParameters(
        "normed_individual_profile", "mean_individual_profile")


#----------------------------Main program--------------------------------------


def execution(self, context):
    """
    STEP 1/2: Remove internals connections of patch.
    STEP 2/2: The profile is normalized.
    """
    # selects the ROI label corresponding to ROI name
    ROIlabel = select_ROI_number(self.ROIs_nomenclature.fullPath(), self.ROI)
    
    if not self.keep_internal_connections:
        arg = "-q"
    else:
        arg = "-c"

    context.system(sys.executable,
                   find_in_path("constelRemoveInternalConnections.py"),
                   ROIlabel,
                   self.mean_individual_profile,
                   self.ROIs_segmentation,
                   self.normed_individual_profile,
                   arg)