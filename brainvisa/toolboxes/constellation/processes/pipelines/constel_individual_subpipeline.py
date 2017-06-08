###############################################################################
# This software and supporting documentation are distributed by CEA/NeuroSpin,
# Batiment 145, 91191 Gif-sur-Yvette cedex, France. This software is governed
# by the CeCILL license version 2 under French law and abiding by the rules of
# distribution of free software. You can  use, modify and/or redistribute the
# software under the terms of the CeCILL license version 2 as circulated by
# CEA, CNRS and INRIA at the following URL "http://www.cecill.info".
###############################################################################


# ---------------------------Imports-------------------------------------------


# Axon python API modules
from brainvisa.processes import Float
from brainvisa.processes import Choice
from brainvisa.processes import ListOf
from brainvisa.processes import Boolean
from brainvisa.processes import Integer
from brainvisa.processes import Signature
from brainvisa.processes import OpenChoice
from brainvisa.processes import ReadDiskItem
from brainvisa.processes import SerialExecutionNode
from brainvisa.processes import ProcessExecutionNode

# Package import
try:
    from constel.lib.utils.filetools import read_file
except:
    pass


# ---------------------------Header--------------------------------------------


name = "Constellation Individual Sub-Pipeline"
userLevel = 3

signature = Signature(
    # --inputs--
    "complete_individual_matrix", ReadDiskItem(
        "Connectivity Matrix", "Sparse Matrix",
        requiredAttributes={"ends_labelled": "all",
                            "reduced": "no",
                            "intersubject": "no"}),
    "regions_nomenclature", ReadDiskItem(
        "Nomenclature ROIs File", "Text File"),
    "region", OpenChoice(),
    "regions_parcellation", ReadDiskItem(
        "ROI Texture", "Aims texture formats",
        requiredAttributes={"side": "both",
                            "vertex_corr": "Yes"}),
    "individual_white_mesh", ReadDiskItem(
        "White Mesh", "Aims mesh formats",
        requiredAttributes={"side": "both",
                            "vertex_corr": "Yes",
                            "inflated": "No",
                            "averaged": "No"}),
    "keep_regions", ListOf(OpenChoice()),
    "smoothing", Float(),
    "normalize", Boolean(),
    "kmax", Integer(),
)


# ---------------------------Functions-----------------------------------------


def initialization(self):
    """Provides default values and link of parameters.
    """
    # default value
    self.smoothing = 3.0
    self.kmax = 12
    self.normalize = True
    self.regions_nomenclature = self.signature[
        "regions_nomenclature"].findValue(
        {"atlasname": "desikan_freesurfer"})

    def link_keep_regions(self, dummy):
        """
        """
        if self.regions_nomenclature is not None:
            s = []
            s += read_file(
                self.regions_nomenclature.fullPath(), mode=2)
            self.signature["keep_regions"] = ListOf(Choice(*s))
            self.changeSignature(self.signature)

    def reset_label(self, dummy):
        """Read and/or reset the region parameter.

        This callback reads the labels nomenclature and proposes them in the
        signature 'region' of process.
        It also resets the region parameter to default state after
        the nomenclature changes.
        """
        current = self.region
        self.setValue("region", current, True)
        if self.regions_nomenclature is not None:
            s = [("Select a region in this list", None)]
            # temporarily set a value which will remain valid
            self.region = s[0][1]
            s += read_file(
                self.regions_nomenclature.fullPath(), mode=2)
            self.signature["region"].setChoices(*s)
            if isinstance(self.signature["region"], OpenChoice):
                self.signature["region"] = Choice(*s)
                self.changeSignature(self.signature)
            if current not in s:
                self.setValue("region", s[0][1], True)
            else:
                self.setValue("region", current, True)

    # link of parameters for autocompletion
    self.linkParameters(None,
                        "regions_nomenclature",
                        reset_label)
    self.linkParameters("keep_regions",
                        "regions_nomenclature",
                        link_keep_regions)

    # define the main node of a pipeline
    eNode = SerialExecutionNode(self.name, parameterized=self)

    ###########################################################################
    #    link of parameters with the process: "Smoothing Individual Matrix"   #
    ###########################################################################

    eNode.addChild(
        "smoothing", ProcessExecutionNode("constel_smooth_matrix", optional=1))

    eNode.addDoubleLink("smoothing.complete_individual_matrix",
                        "complete_individual_matrix")
    eNode.addDoubleLink("smoothing.regions_nomenclature",
                        "regions_nomenclature")
    eNode.addDoubleLink("smoothing.region",
                        "region")
    eNode.addDoubleLink("smoothing.individual_white_mesh",
                        "individual_white_mesh")
    eNode.addDoubleLink("smoothing.regions_parcellation",
                        "regions_parcellation")
    eNode.addDoubleLink("smoothing.smoothing",
                        "smoothing")

    ###########################################################################
    #    link of parameters with the process: "Mean Connectivity Profile"     #
    ###########################################################################

    eNode.addChild(
        "MeanProfile", ProcessExecutionNode("constel_mean_individual_profile",
                                            optional=1))

    eNode.addDoubleLink("MeanProfile.complete_matrix_smoothed",
                        "smoothing.complete_matrix_smoothed")
    eNode.addDoubleLink("MeanProfile.regions_nomenclature",
                        "regions_nomenclature")
    eNode.addDoubleLink("MeanProfile.region",
                        "region")
    eNode.addDoubleLink("MeanProfile.regions_parcellation",
                        "regions_parcellation")

    ###########################################################################
    #    link of parameters with the process: "Remove Internal Connections"   #
    ###########################################################################

    eNode.addChild("InternalConnections",
                   ProcessExecutionNode("constel_normalize_individual_profile",
                                        optional=1))

    eNode.addDoubleLink("InternalConnections.mean_individual_profile",
                        "MeanProfile.mean_individual_profile")
    eNode.addDoubleLink("InternalConnections.regions_nomenclature",
                        "regions_nomenclature")
    eNode.addDoubleLink("InternalConnections.region",
                        "region")
    eNode.addDoubleLink("InternalConnections.regions_parcellation",
                        "regions_parcellation")
    eNode.addDoubleLink("InternalConnections.keep_regions",
                        "keep_regions")

    ###########################################################################
    #        link of parameters with the process: "Watershed"                 #
    ###########################################################################

    eNode.addChild(
        "Watershed",
        ProcessExecutionNode("constel_individual_high_connectivity_regions",
                             optional=1, selected=False))

    eNode.addDoubleLink("Watershed.normed_individual_profile",
                        "InternalConnections.normed_individual_profile")
    eNode.addDoubleLink("Watershed.individual_white_mesh",
                        "individual_white_mesh")

    ###########################################################################
    # link of parameters with the process: "Filtering Watershed"              #
    ###########################################################################

    eNode.addChild("FilteringWatershed",
                   ProcessExecutionNode("constel_individual_regions_filtering",
                                        optional=1, selected=False))

    eNode.addDoubleLink("FilteringWatershed.reduced_individual_profile",
                        "Watershed.reduced_individual_profile")
    eNode.addDoubleLink("FilteringWatershed.complete_matrix_smoothed",
                        "MeanProfile.complete_matrix_smoothed")
    eNode.addDoubleLink("FilteringWatershed.regions_nomenclature",
                        "regions_nomenclature")
    eNode.addDoubleLink("FilteringWatershed.region",
                        "region")
    eNode.addDoubleLink("FilteringWatershed.regions_parcellation",
                        "regions_parcellation")
    eNode.addDoubleLink("FilteringWatershed.individual_white_mesh",
                        "individual_white_mesh")

    ###########################################################################
    #    link of parameters with the process: "Reduced Connectivity Matrix"   #
    ###########################################################################

    eNode.addChild("ReducedMatrix",
                   ProcessExecutionNode("constel_individual_reduced_matrix",
                                        optional=1, selected=False))

    eNode.addDoubleLink("ReducedMatrix.complete_matrix_smoothed",
                        "FilteringWatershed.complete_matrix_smoothed")
    eNode.addDoubleLink("ReducedMatrix.regions_nomenclature",
                        "regions_nomenclature")
    eNode.addDoubleLink("ReducedMatrix.region",
                        "region")
    eNode.addDoubleLink("ReducedMatrix.regions_parcellation",
                        "regions_parcellation")
    eNode.addDoubleLink("ReducedMatrix.individual_white_mesh",
                        "individual_white_mesh")
    eNode.addDoubleLink("ReducedMatrix.normalize",
                        "normalize")

    ###########################################################################
    #        link of parameters with the process: "Clustering"                #
    ###########################################################################

    eNode.addChild("ClusteringIntraSubjects",
                   ProcessExecutionNode("constel_individual_clustering",
                                        optional=1, selected=False))

    #eNode.ClusteringIntraSubjects.removeLink("regions_parcellation",
    #                                         "individual_white_mesh")
    eNode.addDoubleLink("ClusteringIntraSubjects.reduced_individual_matrix",
                        "ReducedMatrix.reduced_individual_matrix")
    eNode.addDoubleLink("ClusteringIntraSubjects.regions_nomenclature",
                        "regions_nomenclature")
    eNode.addDoubleLink("ClusteringIntraSubjects.region",
                        "region")
    eNode.addDoubleLink("ClusteringIntraSubjects.regions_parcellation",
                        "regions_parcellation")
    eNode.addDoubleLink("ClusteringIntraSubjects.individual_white_mesh",
                        "individual_white_mesh")
    eNode.addDoubleLink("ClusteringIntraSubjects.kmax",
                        "kmax")

    self.setExecutionNode(eNode)