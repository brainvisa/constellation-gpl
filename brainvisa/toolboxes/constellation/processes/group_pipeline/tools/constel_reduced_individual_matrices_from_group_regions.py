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
*defines a Brainvisa process
    - the parameters of a process (Signature),
    - the parameters initialization
    - the linked parameters
*

Main dependencies: axon python API, soma, constel
"""


# ---------------------------Imports-------------------------------------------


# Axon python API module
from __future__ import absolute_import
from brainvisa.processes import Signature, ValidationError, ReadDiskItem, \
    WriteDiskItem, String, ListOf, ParallelExecutionNode, ExecutionNode, \
    mapValuesToChildrenParameters, Boolean, OpenChoice, Choice
from brainvisa.group_utils import Subject

# Soma-base modules
from soma.path import find_in_path
from soma.minf.api import registerClass, readMinf
from soma.functiontools import partial


def validation():
    """This function is executed at BrainVisa startup when the process is
    loaded. It checks some conditions for the process to be available.
    """
    try:
        from constel.lib.utils.filetools import read_nomenclature_file
    except ImportError:
        raise ValidationError(
            "Please make sure that constel module is installed.")
    if not find_in_path("constelConnectionDensityTexture"):
        raise ValidationError(
            "Please make sure that constel module is installed.")


# ---------------------------Header--------------------------------------------


name = "Reduced Individual Matrices From Group Regions"
userLevel = 2

signature = Signature(
    "regions_nomenclature", ReadDiskItem(
        "Nomenclature ROIs File", "Text File", section="Nomenclature"),

    "study_name", String(section="Study parameters"),
    "region", OpenChoice(section="Study parameters"),

    # inputs
    "subjects_group", ReadDiskItem("Group definition", "XML",
                                   section="Group inputs"),
    "complete_individual_matrices", ListOf(ReadDiskItem(
        "Connectivity Matrix", "Sparse Matrix",
        requiredAttributes={"ends_labelled": "all",
                            "reduced": "no",
                            "intersubject": "no",
                            "individual": "yes"}),
        section="Group inputs"),

    "filtered_reduced_group_profile", ReadDiskItem(
        "Connectivity ROI Texture", "Aims texture formats",
        requiredAttributes={"roi_autodetect": "yes",
                            "roi_filtered": "yes",
                            "intersubject": "yes",
                            "step_time": "no",
                            "measure": "no"},
        section="Watershed"),

    "average_mesh", ReadDiskItem(
        "White Mesh", "Aims mesh formats",
        requiredAttributes={"side": "both",
                            "vertex_corr": "Yes",
                            "averaged": "Yes"},
        section="Freesurfer data"),
    "regions_parcellation", ListOf(ReadDiskItem(
        "ROI Texture", "Aims texture formats",
        requiredAttributes={"side": "both",
                            "vertex_corr": "Yes"}),
        section="Freesurfer data"),

    "normalize", Boolean(section="Options"),
    "erase_smoothed_matrix", Boolean(section="Options"),

    # outputs
    "intersubject_reduced_matrices", ListOf(WriteDiskItem(
        "Connectivity Matrix", "Aims matrix formats",
        requiredAttributes={"ends_labelled": "all",
                            "reduced": "yes",
                            "intersubject": "yes",
                            "individual": "yes"},
        section="Reduced matrix"),
        section="Output matrices"),
)


# ---------------------------Functions-----------------------------------------


def afterChildAddedCallback(self, parent, key, child):
    """
    """

    # Remove a link added with addLink() function.
    child.removeLink("filtered_reduced_individual_profile",
                     "complete_matrix_smoothed")
    child.removeLink("region",
                     "complete_matrix_smoothed")
    child.removeLink("reduced_individual_matrix",
                     "filtered_reduced_individual_profile")

    # Define the parent signatures.
    child.signature["filtered_reduced_individual_profile"] = parent.signature[
        "filtered_reduced_group_profile"]
    child.signature["individual_white_mesh"] = parent.signature["average_mesh"]
    child.signature["reduced_individual_matrix"] = parent.signature[
        "intersubject_reduced_matrices"].contentType

    child.filtered_reduced_individual_profile = \
        parent.filtered_reduced_group_profile
    child.individual_white_mesh = parent.average_mesh
    child.regions_nomenclature = parent.regions_nomenclature
    child.region = parent.region
    child.normalize = parent.normalize
    child.erase_smoothed_matrix = parent.erase_smoothed_matrix

    # Add link between eNode.ListOf_Input_3dImage and pNode.Input_3dImage
    # Creates a double link source -> destination and destination -> source.
    parent.addDoubleLink(key + ".filtered_reduced_individual_profile",
                         "filtered_reduced_group_profile")
    parent.addDoubleLink(key + ".individual_white_mesh", "average_mesh")
    parent.addDoubleLink(key + ".regions_nomenclature",
                         "regions_nomenclature")
    parent.addDoubleLink(key + ".region", "region")
    parent.addDoubleLink(key + ".normalize", "normalize")
    parent.addDoubleLink(key + ".erase_smoothed_matrix",
                         "erase_smoothed_matrix")


def beforeChildRemovedCallback(self, parent, key, child):
    """
    """
    parent.removeDoubleLink(key + ".filtered_reduced_individual_profile",
                            "filtered_reduced_group_profile")
    parent.removeDoubleLink(key + ".individual_white_mesh", "average_mesh")
    parent.removeDoubleLink(key + ".regions_nomenclature",
                            "regions_nomenclature")
    parent.removeDoubleLink(key + ".region", "region")
    parent.removeDoubleLink(key + ".normalize", "normalize")
    parent.removeDoubleLink(key + ".erase_smoothed_matrix",
                            "erase_smoothed_matrix")


def initialization(self):
    """Provides default values and link of parameters.
    """
    self.erase_smoothed_matrix = False
    self.regions_nomenclature = self.signature[
        "regions_nomenclature"].findValue(
        {"atlasname": "desikan_freesurfer"})

    def reset_label(self, dummy):
        """Read and/or reset the region parameter.

        This callback reads the labels nomenclature and proposes them in the
        signature 'region' of process.
        It also resets the region parameter to default state after
        the nomenclature changes.
        """
        from constel.lib.utils.filetools import read_nomenclature_file
        current = self.region
        self.setValue("region", current, True)
        if self.regions_nomenclature is not None:
            s = [("Select a region in this list", None)]
            self.region = s[0][1]
            s += read_nomenclature_file(
                self.regions_nomenclature.fullPath(), mode=2)
            self.signature["region"].setChoices(*s)
            if isinstance(self.signature["region"], OpenChoice):
                self.signature["region"] = Choice(*s,
                                                  section="Study parameters")
                self.changeSignature(self.signature)
            if current not in s:
                self.setValue("region", s[0][1], True)
            else:
                self.setValue("region", current, True)

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
                atts["_database"] = self.filtered_reduced_group_profile.get(
                    "_database")
                atts["center"] = self.filtered_reduced_group_profile.get(
                    "center")
                atts["studyname"] = self.study_name
                atts["method"] = self.filtered_reduced_group_profile.get(
                    "method")
                atts["gyrus"] = self.filtered_reduced_group_profile.get(
                    "gyrus")
                atts["smoothing"] = self.filtered_reduced_group_profile.get(
                    "smoothing")
                atts["ends_labelled"] = "all",
                atts["reduced"] = "no",
                atts["individual"] = "yes",
                atts["intersubject"] = "no"
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
        if self.subjects_group and self.filtered_reduced_group_profile:
            matrices = []
            registerClass("minf_2.0", Subject, "Subject")
            groupOfSubjects = readMinf(self.subjects_group.fullPath())
            matrices = []
            for subject in groupOfSubjects:
                atts = dict()
                atts["_database"] = self.filtered_reduced_group_profile.get(
                    "_database")
                atts["center"] = self.filtered_reduced_group_profile.get(
                    "center")
                atts["group_of_subjects"] = \
                    self.filtered_reduced_group_profile.get(
                        "group_of_subjects")
                atts["studyname"] = self.study_name
                atts["method"] = self.filtered_reduced_group_profile.get(
                    "method")
                atts["gyrus"] = self.filtered_reduced_group_profile.get(
                    "gyrus")
                atts["smallerlength"] = self.filtered_reduced_group_profile\
                    .get("smallerlength")
                atts["greaterlength"] = self.filtered_reduced_group_profile\
                    .get("greaterlength")
                atts["smoothing"] = self.filtered_reduced_group_profile.get(
                    "smoothing")
                atts["sid"] = subject.attributes().get("subject")
                atts["ends_labelled"] = "all"
                atts["reduced"] = "yes"
                atts["individual"] = "yes"
                atts["intersubject"] = "yes"
                atts['tracking_session'] = ''
                matrix = self.signature[
                    "intersubject_reduced_matrices"].contentType.findValue(
                    atts)
                if matrix is not None:
                    matrices.append(matrix)
            return matrices

    def link_label(self, dummy):
        """
        """
        if self.filtered_reduced_group_profile is not None:
            s = str(self.filtered_reduced_group_profile.get("gyrus"))
            return s

    def mapValuesToChildrenParametersMult(
            destNode, sourceNode, dest, source,
            value1=None, value2=None, value3=None, defaultProcess=None,
            defaultProcessOptions={}, name=None, resultingSize=-1,
            allow_remove=False):
        return mapValuesToChildrenParameters(
            destNode, sourceNode, dest, source, value=value1,
            defaultProcess=defaultProcess,
            defaultProcessOptions=defaultProcessOptions,
            name=name, resultingSize=resultingSize, allow_remove=allow_remove)

    # link of parameters for autocompletion
    self.linkParameters(
        "region", "filtered_reduced_group_profile", link_label)
    self.linkParameters(
        "complete_individual_matrices",
        ("filtered_reduced_group_profile", "subjects_group", "study_name"),
        link_watershed)
    self.linkParameters(
        "intersubject_reduced_matrices",
        ("subjects_group", "filtered_reduced_group_profile"), link_matrices)
    self.linkParameters(None,
                        "regions_nomenclature",
                        reset_label)
    # define the main node of the pipeline
    eNode = ParallelExecutionNode(
        "Reduced_connectivity_matrix", parameterized=self,
        possibleChildrenProcesses=["constel_individual_reduced_matrix"],
        notify=True)
    self.setExecutionNode(eNode)

    # Add callback to warn about child add and remove
    eNode.afterChildAdded.add(
        ExecutionNode.MethodCallbackProxy(self.afterChildAddedCallback))
    eNode.beforeChildRemoved.add(
        ExecutionNode.MethodCallbackProxy(self.beforeChildRemovedCallback))

    # Add links to refresh child nodes when main lists are modified
    eNode.addLink(
        None,
        # "complete_individual_matrices",
        ("complete_individual_matrices", "intersubject_reduced_matrices",
         "regions_parcellation"),
        partial(mapValuesToChildrenParametersMult, eNode,
                eNode,
                # "complete_matrix_smoothed", "complete_individual_matrices",
                ["complete_matrix_smoothed",
                 "reduced_individual_matrix", "regions_parcellation"],
                ["complete_individual_matrices",
                 "intersubject_reduced_matrices", "regions_parcellation"],
                defaultProcess="constel_individual_reduced_matrix",
                name="constel_individual_reduced_matrix",
                allow_remove=True))
