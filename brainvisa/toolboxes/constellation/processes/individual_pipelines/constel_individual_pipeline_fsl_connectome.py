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
from __future__ import absolute_import
from brainvisa.processes import Float
from brainvisa.processes import Choice
from brainvisa.processes import ListOf
from brainvisa.processes import Boolean
from brainvisa.processes import Integer
from brainvisa.processes import Signature
from brainvisa.processes import OpenChoice
from brainvisa.processes import ReadDiskItem
from brainvisa.processes import neuroHierarchy
from brainvisa.processes import SerialExecutionNode
from brainvisa.processes import ProcessExecutionNode
from brainvisa.processes import ValidationError
import os


def validation(self):
    """This function is executed at BrainVisa startup when the process is
    loaded. It checks some conditions for the process to be available.
    """
    try:
        from constel.lib.utils.filetools import read_nomenclature_file
    except ImportError:
        raise ValidationError(
            "Please make sure that constel module is installed.")


# ---------------------------Header--------------------------------------------


name = "Constellation Individual Pipeline - FSL connectome"
userLevel = 1

signature = Signature(
    "regions_nomenclature", ReadDiskItem(
        "Nomenclature ROIs File", "Text File", section="Nomenclature"),

    "outputs_database", Choice(section="Study parameters"),
    "study_name", OpenChoice(section="Study parameters"),
    "method", Choice(
        ("averaged approach", "avg"),
        ("concatenated approach", "concat"),
        section="Study parameters"),
    "region", OpenChoice(section="Study parameters"),

    # --inputs--
    "probtrackx_indir", ReadDiskItem("directory", "directory",
                                     section="FSL import"),
    "temp_outdir", ReadDiskItem("directory", "directory",
                                section="FSL import"),

    "individual_white_mesh", ReadDiskItem(
        "White Mesh", "Aims mesh formats",
        requiredAttributes={"side": "both",
                            "vertex_corr": "Yes",
                            "inflated": "No",
                            "averaged": "No"},
        section="Freesurfer data"),
    "regions_parcellation", ReadDiskItem(
        "ROI Texture", "Aims texture formats",
        requiredAttributes={"side": "both",
                            "vertex_corr": "Yes"},
        section="Freesurfer data"),

    "regions_selection", Choice("All but main region", "All", "Custom",
                                section="Options"),
    "keep_regions", ListOf(OpenChoice(), section="Options"),
    "min_fibers_length", Float(section="Options"),
    "smoothing", Float(section="Options"),
    "kmax", Integer(section="Options"),
    "normalize", Boolean(section="Options"),
    "erase_smoothed_matrix", Boolean(section="Options"),
)


# ---------------------------Functions-----------------------------------------


def link_keep_regions_value(self, dummy, other=None, oother=None):
    s = [x[1] for x in self.signature["keep_regions"].contentType.values
         if x[1] is not None]
    if self.regions_selection == "All":
        keep_regions = s
    elif self.regions_selection == "All but main region":
        keep_regions = [x for x in s if x != self.region]
    else:
        keep_regions = None
    return keep_regions


def initialization(self):
    """Provides default values and link of parameters.
    """
    from constel.lib.utils.filetools import read_nomenclature_file

    # Get a list of possible databases while respecting the ontology
    databases = [h.name for h in neuroHierarchy.hierarchies()
                 if h.fso.name == "brainvisa-3.2.0" and not h.builtin
                 and not h.read_only]
    self.signature["outputs_database"].setChoices(*databases)
    if len(databases) != 0:
        self.outputs_database = databases[0]
    else:
        self.signature["outputs_database"] = OpenChoice(
                                                section="Study parameters")

    self.signature['probtrackx_indir'].databaseUserLevel = 2
    self.signature['temp_outdir'].databaseUserLevel = 2

    # default values
    self.smoothing = 3.0
    self.min_fibers_length = 20.0
    self.kmax = 12
    self.normalize = True
    self.erase_smoothed_matrix = True
    self.regions_nomenclature = self.signature[
        "regions_nomenclature"].findValue(
        {"atlasname": "desikan_freesurfer"})

    def link_keep_regions(self, dummy):
        """
        """
        if self.regions_nomenclature is not None:
            self.keep_regions = None
            s = []
            s += read_nomenclature_file(
                self.regions_nomenclature.fullPath(), mode=2)
            self.signature["keep_regions"] = ListOf(Choice(*s),
                                                    section="Options")
            self.changeSignature(self.signature)

    def fill_study_choice(self, dummy=None):
        """
        """
        choices = set()
        if self.outputs_database is not None:
            if neuroHierarchy.databases.hasDatabase(self.outputs_database):
                database = neuroHierarchy.databases.database(
                    self.outputs_database)
                sel = {"method": self.method}
                choices.update(
                    [x[0] for x in database.findAttributes(
                        ["studyname"], selection=sel,
                        _type="Connectivity Matrix")])
            else:
                choices = []
        self.signature["study_name"].setChoices(*sorted(choices))
        if len(choices) != 0 and self.isDefault("study_name") \
                and self.study_name not in choices:
            self.setValue("study_name", list(choices)[0], True)

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

    def link_mesh(self, dummy):
        if self.probtrackx_indir is None:
            return None
        match = {
            "subject": os.path.basename(self.probtrackx_indir.fullName()),
        }
        return self.signature["individual_white_mesh"].findValue(match)

    def link_regions_parcellation(self, dummy):
        if self.method == "concat":
            if self.individual_white_mesh is None:
                return None
            return self.signature["regions_parcellation"].findValue(
                self.individual_white_mesh)
        match = {"averaged": "Yes"}
        if self.individual_white_mesh is not None:
            match["_database"] = self.individual_white_mesh.get("_database")
            match["freesurfer_group_of_subjects"] \
                = self.individual_white_mesh.get(
                    "freesurfer_group_of_subjects")
            res = self.signature["regions_parcellation"].findValue(match)
            if res is None:
                del match["freesurfer_group_of_subjects"]
                res = self.signature["regions_parcellation"].findValue(match)
            return match

    # link of parameters for autocompletion
    self.linkParameters(None,
                        "regions_nomenclature",
                        reset_label)
    self.linkParameters(None,
                        ("outputs_database", "method"),
                        fill_study_choice)
    self.linkParameters(None,
                        "regions_nomenclature",
                        link_keep_regions)
    self.linkParameters("individual_white_mesh", "probtrackx_indir", link_mesh)
    self.addLink("keep_regions",
                 ("regions_nomenclature", "regions_selection", "region"),
                 self.link_keep_regions_value)
    self.linkParameters("regions_parcellation",
                        ("method", "individual_white_mesh"),
                        link_regions_parcellation)

    # define the main node of a pipeline
    eNode = SerialExecutionNode(self.name, parameterized=self)

    ###########################################################################
    #    link of parameters with the process: "FSL connectome"                #
    ###########################################################################

    eNode.addChild(
        "confsl", ProcessExecutionNode("constel_fsl_connectome", optional=1))

    eNode.addDoubleLink("confsl.probtrackx_indir",
                        "probtrackx_indir")
    eNode.addDoubleLink("confsl.regions_parcellation",
                        "regions_parcellation")
    eNode.addDoubleLink("confsl.regions_nomenclature",
                        "regions_nomenclature")
    eNode.addDoubleLink("confsl.region",
                        "region")
    eNode.addDoubleLink("confsl.temp_outdir",
                        "temp_outdir")

    ###########################################################################
    #    link of parameters with the process: "Import FSL connectome"         #
    ###########################################################################

    eNode.addChild(
        "import", ProcessExecutionNode("import_fsl_connectome", optional=1))

    eNode.addDoubleLink("import.outputs_database",
                        "outputs_database")
    eNode.addDoubleLink("import.study_name",
                        "study_name")
    eNode.addDoubleLink("import.method",
                        "method")
    eNode.addDoubleLink("import.regions_nomenclature",
                        "regions_nomenclature")
    eNode.addDoubleLink("import.region",
                        "region")
    eNode.addDoubleLink("import.min_fibers_length",
                        "min_fibers_length")
    eNode.addDoubleLink("import.fsl_connectome",
                        "confsl.output_connectome")

    ###########################################################################
    #    "Constellation Individual Sub-pipeline"                              #
    ###########################################################################

    eNode.addChild("subpipeline",
                   ProcessExecutionNode("constel_individual_subpipeline",
                                        optional=1))

    eNode.subpipeline.executionNode().ClusteringIntraSubjects.removeLink(
        "regions_parcellation", "individual_white_mesh")
    eNode.addDoubleLink("subpipeline.complete_individual_matrix",
                        "import.complete_individual_matrix")
    eNode.addDoubleLink("subpipeline.regions_nomenclature",
                        "regions_nomenclature")
    eNode.addDoubleLink("subpipeline.region",
                        "region")
    eNode.addDoubleLink("subpipeline.regions_parcellation",
                        "regions_parcellation")
    eNode.addDoubleLink("subpipeline.individual_white_mesh",
                        "individual_white_mesh")
    eNode.addDoubleLink("subpipeline.smoothing",
                        "smoothing")
    eNode.addDoubleLink("subpipeline.normalize",
                        "normalize")
    eNode.addDoubleLink("subpipeline.regions_selection",
                        "regions_selection")
    eNode.addDoubleLink("subpipeline.kmax",
                        "kmax")
    eNode.addDoubleLink("subpipeline.erase_smoothed_matrix",
                        "erase_smoothed_matrix")

    self.setExecutionNode(eNode)

    fill_study_choice(self)
    if len(self.signature["study_name"].values) != 0:
        self.study_name = self.signature["study_name"].values[0][0]
