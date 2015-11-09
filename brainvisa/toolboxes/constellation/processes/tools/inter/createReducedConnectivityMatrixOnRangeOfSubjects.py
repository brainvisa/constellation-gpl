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

Author: Sandrine Lefranc, 2015
"""


#----------------------------Imports-------------------------------------------

# python module
import os

# Axon python API module
from brainvisa.processes import Signature, ValidationError, ReadDiskItem, \
    WriteDiskItem, String, ListOf, ParallelExecutionNode, ExecutionNode, \
    mapValuesToChildrenParameters
from brainvisa.group_utils import Subject

# Soma-base modules
from soma.path import find_in_path
from soma.minf.api import registerClass, readMinf
from soma.functiontools import partial
try:
    from constel.lib.utils.files import read_file
except:
    pass


def validation():
    """This function is executed at BrainVisa startup when the process is
    loaded. It checks some conditions for the process to be available.
    """
    if not find_in_path("constelConnectionDensityTexture"):
        raise ValidationError(
            "Please make sure that constel module is installed.")


#----------------------------Header--------------------------------------------


name = "Reduced Intersubject Matrices From Filtered Reduced Group Profile"
userLevel = 2

signature = Signature(
    # --inputs--
    "filtered_reduced_group_profile", ReadDiskItem(
        "Connectivity ROI Texture", "Aims texture formats",
        requiredAttributes={"roi_autodetect": "Yes",
                            "roi_filtered": "Yes",
                            "averaged": "Yes",
                            "intersubject": "Yes",
                            "step_time": "No"}),
    "subjects_group", ReadDiskItem("Group definition", "XML"),
    "study_name", String(),
    "ROIs_nomenclature", ReadDiskItem("Nomenclature ROIs File", "Text File"),
    "ROI", String(),
    "complete_individual_matrices", ListOf(ReadDiskItem(
        "Connectivity Matrix", "Sparse Matrix",
        requiredAttributes={"ends_labelled": "mixed",
                            "reduced": "No",
                            "dense": "No",
                            "intersubject": "No"})),
    "average_mesh", ReadDiskItem(
        "White Mesh", "Aims mesh formats",
        requiredAttributes={"side": "both",
                            "vertex_corr": "Yes",
                            "averaged": "Yes"}),
    "ROIs_segmentation", ListOf(ReadDiskItem(
        "ROI Texture", "Aims texture formats",
        requiredAttributes={"side": "both",
                            "vertex_corr": "Yes"})),

    # --outputs--
    "intersubject_reduced_matrices", ListOf(WriteDiskItem(
        "Connectivity Matrix", "Aims matrix formats",
        requiredAttributes={"ends_labelled": "mixed",
                            "reduced": "Yes",
                            "dense": "No",
                            "intersubject": "Yes"})))


#----------------------------Functions-----------------------------------------


def afterChildAddedCallback(self, parent, key, child):
    # Set default values
    child.removeLink(
        "filtered_reduced_individual_profile", "complete_individual_matrix")
    child.removeLink(
        "reduced_individual_matrix", "filtered_reduced_individual_profile")
    child.removeLink("ROI", "complete_individual_matrix")

    child.signature["filtered_reduced_individual_profile"] = parent.signature[
        "filtered_reduced_group_profile"]
    child.signature["white_mesh"] = parent.signature["average_mesh"]
    child.signature["reduced_individual_matrix"] = \
        parent.signature["intersubject_reduced_matrices"].contentType

    child.filtered_reduced_individual_profile = parent.filtered_reduced_group_profile
    child.white_mesh = parent.average_mesh
    child.ROIs_nomenclature = parent.ROIs_nomenclature
    child.ROI = parent.ROI

    # Add link between eNode.ListOf_Input_3dImage and pNode.Input_3dImage
    parent.addDoubleLink(key + ".filtered_reduced_individual_profile", "filtered_reduced_group_profile")
    parent.addDoubleLink(key + ".white_mesh", "average_mesh")
    parent.addDoubleLink(key + ".ROIs_nomenclature", "ROIs_nomenclature")
    parent.addDoubleLink(key + ".ROI", "ROI")


def beforeChildRemovedCallback(self, parent, key, child):
    parent.removeDoubleLink(key + ".filtered_reduced_individual_profile", "filtered_reduced_group_profile")
    parent.removeDoubleLink(key + ".white_mesh", "average_mesh")
    parent.removeDoubleLink(key + ".ROIs_nomenclature", "ROIs_nomenclature")
    parent.removeDoubleLink(key + ".ROI", "ROI")


def initialization(self):
    """Provides default values and link of parameters.
    """

    self.ROIs_nomenclature = self.signature["ROIs_nomenclature"].findValue(
        {"atlasname": "desikan_freesurfer"})

    def link_watershed(self, dummy):
        """Function of link between the filtered watershed and the
        complete matrices.
        """
        if self.filtered_reduced_group_profile and self.subjects_group \
                and self.study_name:
            registerClass("minf_2.0", Subject, "Subject")
            groupOfSubjects = readMinf(self.subjects_group.fullPath())
            matrices = []
            for subject in groupOfSubjects:
                atts = dict()
                atts["_database"] = self.filtered_reduced_group_profile.get("_database")
                atts["center"] = self.filtered_reduced_group_profile.get("center")
                atts["texture"] = self.study_name
                atts["study"] = self.filtered_reduced_group_profile.get("study")
                atts["gyrus"] = self.filtered_reduced_group_profile.get("gyrus")
                atts["smoothing"] = self.filtered_reduced_group_profile.get("smoothing")
                atts["ends_labelled"] = "mixed",
                atts["reduced"] = "No",
                atts["dense"] = "No",
                atts["intersubject"] = "No"
                matrix = self.signature[
                    "complete_individual_matrices"].contentType.findValue(
                    atts, subject.attributes())
                if matrix is not None:
                    matrices.append(matrix)
            return matrices

    def link_matrices(self, dummy):
        """Function of link between the complete matrices and
        the reduced matrices.
        """
        if self.subjects_group and self.complete_individual_matrices and \
                self.filtered_reduced_group_profile:
            matrices = []
            registerClass("minf_2.0", Subject, "Subject")
            groupOfSubjects = readMinf(self.subjects_group.fullPath())
            for subject in groupOfSubjects:
                atts = dict()
                atts["_database"] = self.complete_individual_matrices[0].get(
                    "_database")
                atts["center"] = self.complete_individual_matrices[0].get(
                    "center")
                atts["texture"] = self.study_name
                atts["study"] = self.complete_individual_matrices[0].get(
                    "study")
                atts["gyrus"] = self.complete_individual_matrices[0].get(
                    "gyrus")
                atts["smoothing"] = self.complete_individual_matrices[0].get(
                    "smoothing")
                atts["group_of_subjects"] = os.path.basename(
                    os.path.dirname(self.subjects_group.fullPath()))
                atts["texture"] = self.filtered_reduced_group_profile.get("texture")
                atts["ends_labelled"] = "mixed",
                atts["reduced"] = "Yes",
                atts["dense"] = "No",
                atts["intersubject"] = "Yes"
                matrix = self.signature[
                    "intersubject_reduced_matrices"].contentType.findValue(
                    atts, subject.attributes())
                if matrix is not None:
                    matrices.append(matrix)
            return matrices

    def link_roi(self, dummy):
        if self.filtered_reduced_group_profile is not None:
            s = str(self.filtered_reduced_group_profile.get("gyrus"))
            return s


    # link of parameters for autocompletion
    self.linkParameters("ROI", "filtered_reduced_group_profile", link_roi)
    self.linkParameters(
        "complete_individual_matrices",
        ("filtered_reduced_group_profile", "subjects_group", "study_name"),
        link_watershed)
    self.linkParameters(
        "intersubject_reduced_matrices",
        ("complete_individual_matrices", "subjects_group", "filtered_reduced_group_profile"),
        link_matrices)

    # define the main node of the pipeline
    eNode = ParallelExecutionNode(
        "Reduced_connectivity_matrix", parameterized=self,
        possibleChildrenProcesses=["createReducedConnectivityMatrix"],
        notify=True)
    self.setExecutionNode(eNode)

    # Add callback to warn about child add and remove
    eNode.afterChildAdded.add(
        ExecutionNode.MethodCallbackProxy(self.afterChildAddedCallback))
    eNode.beforeChildRemoved.add(
        ExecutionNode.MethodCallbackProxy(self.beforeChildRemovedCallback))

    # Add links to refresh child nodes when main lists are modified
    eNode.addLink(
        None, "complete_individual_matrices",
        partial(mapValuesToChildrenParameters, eNode,
                eNode, "complete_individual_matrix",
                "complete_individual_matrices",
                defaultProcess="createReducedConnectivityMatrix",
                name="createReducedConnectivityMatrix"))

    eNode.addLink(
        None, "intersubject_reduced_matrices",
        partial(mapValuesToChildrenParameters, eNode,
                eNode, "reduced_individual_matrix",
                "intersubject_reduced_matrices",
                defaultProcess="createReducedConnectivityMatrix",
                name="createReducedConnectivityMatrix"))

    eNode.addLink(
        None, "ROIs_segmentation",
        partial(mapValuesToChildrenParameters, eNode,
                eNode, "ROIs_segmentation",
                "ROIs_segmentation",
                defaultProcess="createReducedConnectivityMatrix",
                name="createReducedConnectivityMatrix"))
