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
* this process executes the command 'constelNormProfile'

Main dependencies: Axon python API, Soma-base, constel

Author: sandrine.lefranc@cea.fr
"""

#----------------------------Imports-------------------------------------------


# python system module
import os
import sys

# Axon python API module
from brainvisa.processes import Signature, ListOf, ReadDiskItem, String, \
    WriteDiskItem, ValidationError

# soma-base module
from soma.path import find_in_path


#----------------------------Functions-----------------------------------------


# Plot constel module
def validation():
    """This function is executed at BrainVisa startup when the process is
    loaded. It checks some conditions for the process to be available.
    """
    if not find_in_path("constelNormProfile.py"):
        raise ValidationError(
            "Please make sure that constel module is installed.")

name = "Mask and Normalize Group Profile"
userLevel = 2

# Argument declaration
signature = Signature(
    "group_mask", ReadDiskItem("Mask Texture", "Aims texture formats"),
    "group_profile", ReadDiskItem(
        "Connectivity Profile Texture", "Aims texture formats",
        requiredAttributes={"normed":"No",
                            "thresholded":"No",
                            "averaged":"Yes",
                            "intersubject":"Yes"}),
    "thresholded_group_profile", WriteDiskItem(
        "Connectivity Profile Texture", "Aims texture formats",
        requiredAttributes={"normed":"No",
                            "thresholded":"Yes",
                            "averaged":"Yes",
                            "intersubject":"Yes"}),
    "normed_group_profile", WriteDiskItem(
        "Connectivity Profile Texture", "Aims texture formats",
        requiredAttributes={"normed":"Yes",
                            "thresholded":"Yes",
                            "averaged":"Yes",
                            "intersubject":"Yes"}),)


def initialization(self):
    """Provides default values and link of parameters"""

    def link_profiles(self, dummy):
        """
        """
        if self.group_profile is not None:
            atts = dict()
            atts["_database"] = self.group_profile.get("_database")
            atts["center"] = self.group_profile.get("center")
            atts["group_of_subjects"] = self.group_profile.get(
                "group_of_subjects")
            atts["texture"] = self.group_profile.get("texture")
            atts["study"] = self.group_profile.get("study")
            atts["smoothing"] = self.group_profile.get("smoothing")
            atts["gyrus"] = self.group_profile.get("gyrus")
            atts['acquisition'] = ''
            atts['analysis'] = ''
            atts['tracking_session'] = ''
            atts["intersubject"] = "Yes"
            atts["averaged"] = "Yes"
            atts["normed"] = "No"
            atts["thresholded"] = "Yes"
            return self.signature["thresholded_group_profile"].findValue(atts)

    def link_gprofiles(self, dummy):
        """
        """
        if self.thresholded_group_profile is not None:
            atts = dict()
            atts["_database"] = self.thresholded_group_profile.get("_database")
            atts["center"] = self.thresholded_group_profile.get("center")
            atts["group_of_subjects"] = self.thresholded_group_profile.get("group_of_subjects")
            atts["texture"] = self.thresholded_group_profile.get("texture")
            atts["study"] = self.thresholded_group_profile.get("study")
            atts["smoothing"] = self.thresholded_group_profile.get("smoothing")
            atts["gyrus"] = self.thresholded_group_profile.get("gyrus")
            atts['acquisition'] = ''
            atts['analysis'] = ''
            atts['tracking_session'] = ''
            atts["intersubject"] = "Yes"
            atts["averaged"] = "Yes"
            atts["normed"] = "Yes"
            atts["thresholded"] = "Yes"
            return self.signature["normed_group_profile"].findValue(atts)

    self.linkParameters("group_profile", "group_mask")
    self.linkParameters(
        "thresholded_group_profile",
        "group_profile", link_profiles)
    self.linkParameters(
        "normed_group_profile",
        "thresholded_group_profile", link_gprofiles)


#----------------------------Main program--------------------------------------


def execution(self, context):
    """
    """
    context.system(sys.executable,
                   find_in_path("constelNormProfile.py"),
                   self.group_mask,
                   self.group_profile,
                   self.normed_group_profile)