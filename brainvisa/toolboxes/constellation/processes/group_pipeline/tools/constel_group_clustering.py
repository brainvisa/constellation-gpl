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
    - the signature of the inputs/ouputs,
    - the initialization (by default) of the inputs,
    - the interlinkages between inputs/outputs.
* executes the commands 'constel_calculate_group_matrix' and
  'constel_inter_subject_clustering'.

Main dependencies: Axon python API, Soma-base, constel
"""

# ---------------------------Imports-------------------------------------------

# python module
from __future__ import absolute_import
import os

# axon python API modules
from brainvisa.processes import Signature
from brainvisa.processes import ReadDiskItem
from brainvisa.processes import WriteDiskItem
from brainvisa.processes import ValidationError
from brainvisa.processes import ListOf
from brainvisa.processes import Choice
from brainvisa.processes import String
from brainvisa.processes import Integer

# soma-base module
from soma.path import find_in_path


def validation():
    """This function is executed at BrainVisa startup when the process is
    loaded. It checks some conditions for the process to be available.
    """
    if not find_in_path("constel_inter_subject_clustering.py"):
        raise ValidationError(
            "Please make sure that constel module is installed.")
    try:
        from constel.lib.utils.filetools import select_ROI_number
    except ImportError:
        raise ValidationError(
            "Please make sure that constel module is installed.")

# ---------------------------Header--------------------------------------------


name = "Clustering From Reduced Group Matrix"
userLevel = 2

signature = Signature(
    "regions_nomenclature", ReadDiskItem(
        "Nomenclature ROIs File", "Text File", section="Nomenclature"),

    "method", Choice(
        ("averaged approach", "avg"),
        ("concatenated approach", "concat"),
        section="Study parameters"),
    "region", String(section="Study parameters"),

    # inputs
    "subjects_group", ReadDiskItem(
        "Group definition", "XML", section="Group inputs"),
    "intersubject_reduced_matrices", ListOf(ReadDiskItem(
        "Connectivity Matrix", "Aims matrix formats",
        requiredAttributes={"ends_labelled": "all",
                            "reduced": "yes",
                            "intersubject": "yes",
                            "individual": "yes"}),
        section="Group inputs"),

    "average_mesh", ReadDiskItem(
        "White Mesh", "BrainVISA mesh formats",
        requiredAttributes={"side": "both",
                            "vertex_corr": "Yes",
                            "averaged": "Yes"},
        section="Freesurfer data"),
    "regions_parcellation", ListOf(ReadDiskItem(
        "ROI Texture", "Aims texture formats",
        requiredAttributes={"side": "both",
                            "vertex_corr": "Yes"}),
        section="Freesurfer data"),

    "nb_clusters", Integer(section="Options"),

    # outputs
    "reduced_group_matrix", WriteDiskItem(
        "Connectivity Matrix", "Gis image",
        requiredAttributes={"ends_labelled": "all",
                            "reduced": "yes",
                            "intersubject": "yes",
                            "individual": "no"},
        section="Clustering"),
    "ROI_clustering", ListOf(WriteDiskItem(
        "Connectivity ROI Texture", "Aims texture formats",
        requiredAttributes={"roi_autodetect": "no",
                            "roi_filtered": "no",
                            "intersubject": "yes",
                            "step_time": "yes",
                            "measure": "no"}),
        section="Clustering"),
)


# ---------------------------Functions-----------------------------------------


def initialization(self):
    """Provides default values and link of parameters"""

    # default value
    self.nb_clusters = 12
    self.regions_nomenclature = self.signature[
        "regions_nomenclature"].findValue(
        {"atlasname": "desikan_freesurfer"})

    def link_matrix2label(self, dummy):
        """Define the attribut 'gyrus' from fibertracts pattern for the
        signature 'region'.
        """
        if self.intersubject_reduced_matrices:
            s = self.intersubject_reduced_matrices[0].get("gyrus")
            name = self.signature["region"].findValue(s)
            return name

    def link_matrices(self, dummy):
        """Function of link between the reduced connectivity matrices and
        the group matrix
        """
        if self.subjects_group and self.intersubject_reduced_matrices:
            atts = dict(
                self.intersubject_reduced_matrices[0].hierarchyAttributes())
            for att_name in [
                    "name_serie", "tracking_session",
                    "_declared_attributes_location", "analysis", "_ontology",
                    "acquisition", "subject", "sid"]:
                if att_name in atts:
                    del atts[att_name]
            atts['individual'] = 'no'
            atts["group_of_subjects"] = os.path.basename(
                os.path.dirname(self.subjects_group.fullPath()))
            if self.method == "avg":
                atts["method"] = "avg"
            else:
                atts["method"] = "concat"
            return self.signature["reduced_group_matrix"].findValue(atts)

    def link_clustering(self, dummy):
        """function of link between clustering time and individual reduced
        connectivity matrices
        """
        if self.subjects_group and self.intersubject_reduced_matrices:
            if self.method == "avg":
                atts = dict(
                    self.intersubject_reduced_matrices[0].hierarchyAttributes()
                )
                atts["sid"] = "avgSubject"
                atts["method"] = "avg"
                atts["step_time"] = "yes"
                atts["roi_autodetect"] = "no"
                atts["measure"] = "no"
                atts["roi_filtered"] = "no"
                for att in ("tracking_session", "individual", "reduced",
                            "ends_labelled", "analysis", "name_serie"):
                    if att in atts:
                        del atts[att]
                # bug in axon ? 2 DI with same filename, and differing
                # attributes for tracking_session, analysis, acquisition...
                atts['tracking_session'] = ''
                filename = self.signature[
                    "ROI_clustering"].contentType.findValue(atts)
                return [filename]
            else:
                profiles = []
                for matrix in self.intersubject_reduced_matrices:
                    atts = dict(matrix.hierarchyAttributes())
                    atts["method"] = "concat"
                    atts["step_time"] = "yes"
                    atts["roi_autodetect"] = "no"
                    atts["measure"] = "no"
                    atts["roi_filtered"] = "no"
                    for att in ("tracking_session", "individual", "reduced",
                                "ends_labelled", "analysis", "name_serie",
                                "acquisition"):
                        if att in atts:
                            del atts[att]
                    profile = self.signature[
                        'ROI_clustering'].contentType.findValue(atts)
                    if profile is not None:
                        profiles.append(profile)
                return profiles

    # link of parameters for autocompletion
    self.linkParameters(
        "region", "intersubject_reduced_matrices", link_matrix2label)
    self.linkParameters(
        "reduced_group_matrix",
        ("subjects_group", "intersubject_reduced_matrices", "method"),
        link_matrices)
    self.linkParameters(
        "ROI_clustering",
        ("subjects_group", "intersubject_reduced_matrices", "method"),
        link_clustering)


# ---------------------------Main program--------------------------------------


def execution(self, context):
    """Compute the clustering of the ROI.

    Execute 'constel_inter_subject_clustering' and
    'constel_calculate_group_matrix'.

    The gyrus vertices connectivity profiles of all the subjects are
    concatenated into a big matrix. The clustering is performed with the
    classical kmedoids algorithm and the Euclidean distance between profiles
    as dissimilarity measure.
    """
    from constel.lib.utils.filetools import select_ROI_number

    # selects the label number corresponding to label name
    label_number = select_ROI_number(
        self.regions_nomenclature.fullPath(), self.region)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Compute the group matrix
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    # Declare the constel command
    args = ["constel_calculate_group_matrix.py"]

    # Define the arguments
    for x in self.intersubject_reduced_matrices:
        args += ["-m", x]
    args += ["-o", self.reduced_group_matrix, "-s", self.method]

    # Execute the command
    context.pythonSystem(*args)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    # Compute the clustering of the group matrix
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

    # Declare the constel command
    cmd_args = ["constel_inter_subject_clustering.py"]

    # Define the arguments
    for t in self.ROI_clustering:
        cmd_args += ["-p", t]
    for y in self.regions_parcellation:
        cmd_args += ["-t", y]
    cmd_args += ["-m", self.average_mesh,
                 "-l", str(label_number),
                 "-s", self.method,
                 "-g", self.reduced_group_matrix,
                 "-a", self.nb_clusters]

    # Execute the command
    context.pythonSystem(*cmd_args)
