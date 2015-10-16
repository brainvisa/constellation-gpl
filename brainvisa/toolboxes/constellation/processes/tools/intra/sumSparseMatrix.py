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
* this process

Main dependencies: Axon python API, Soma-base, constel

Author: Sandrine Lefranc, 2015
"""

#----------------------------Imports-------------------------------------------


# axon python API module
from brainvisa.processes import Signature, ReadDiskItem, Float, String, \
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
    if not find_in_path("AimsSumSparseMatrix") \
            or not find_in_path("AimsSparseMatrixSmoothing"):  # checks command
        raise ValidationError(
            "AimsSumSparseMatrix or AimsSparseMatrixSmoothing is not contained"
            "in PATH environnement variable."
            "Please make sure that aims is installed.")


#----------------------------Header--------------------------------------------


name = "Smoothing Matrix"
userLevel = 2

signature = Signature(
    # --inputs--
    "matrix_of_fibers_near_cortex", ReadDiskItem(
        "Connectivity Matrix", "Matrix sparse",
        requiredAttributes={"ends_labelled": "both",
                            "reduced": "No",
                            "dense": "No",
                            "intersubject": "No"}),
    "matrix_of_distant_fibers", ReadDiskItem(
        "Connectivity Matrix", "Matrix sparse",
        requiredAttributes={"ends_labelled": "single",
                            "reduced": "No",
                            "dense": "No",
                            "intersubject": "No"}),
    "ROIs_nomenclature", ReadDiskItem("Nomenclature ROIs File", "Text File"),
    "ROI", String(),
    "gyri_texture", ReadDiskItem(
        "ROI Texture", "Aims texture formats",
        requiredAttributes={"side": "both", "vertex_corr": "Yes"}),
    "white_mesh", ReadDiskItem(
        "White Mesh", "Aims mesh formats",
        requiredAttributes={"side": "both", "vertex_corr": "Yes"}),
    "smoothing", Float(),

    # --outputs--
    "complete_connectivity_matrix", WriteDiskItem(
        "Connectivity Matrix", "Matrix sparse",
        requiredAttributes={"ends_labelled": "mixed",
                            "reduced": "No",
                            "dense": "No",
                            "intersubject": "No"}),
)


#----------------------------Functions-----------------------------------------


def initialization(self):
    """Provides default values and link of parameters"""

    # default values
    self.smoothing = 3.0
    self.ROIs_nomenclature = self.signature["ROIs_nomenclature"].findValue({})

    def link_matrix2ROI(self, dummy):
        """Define the attribut 'gyrus' from fibertracts pattern for the
        signature 'ROI'.
        """
        if self.matrix_of_fibers_near_cortex is not None:
            s = str(self.matrix_of_fibers_near_cortex.get("gyrus"))
            name = self.signature["ROI"].findValue(s)
        return name

    def link_matrix(sef, dummy):
        """
        """
        if self.matrix_of_fibers_near_cortex is not None:
            attrs = dict(
                self.matrix_of_fibers_near_cortex.hierarchyAttributes())
            attrs["smallerlength1"] = None
            attrs["greaterlength1"] = None
            filename = self.signature[
                "matrix_of_distant_fibers"].findValue(attrs)
            return filename

    def link_smooth(self, dummy):
        """
        """
        if (self.matrix_of_distant_fibers and self.smoothing) is not None:
            attrs = dict(self.matrix_of_distant_fibers.hierarchyAttributes())
            attrs["smoothing"] = str(self.smoothing)
            attrs["smallerlength2"] = None
            attrs["greaterlength2"] = None
            filename = self.signature[
                "complete_connectivity_matrix"].findValue(attrs)
            print attrs
            return filename

    # link of parameters for autocompletion
    self.linkParameters("ROI", "matrix_of_fibers_near_cortex", link_matrix2ROI)
    self.linkParameters("matrix_of_fibers_near_cortex",
                        "matrix_of_distant_fibers", link_matrix)
    self.linkParameters("complete_connectivity_matrix",
                        ("matrix_of_distant_fibers", "smoothing"), link_smooth)


#----------------------------Main program--------------------------------------


def execution(self, context):
    """Sum of two matrices and smoothing"""
    # selects the ROI label corresponding to ROI name
    ROIlabel = select_ROI_number(self.ROIs_nomenclature.fullPath(), self.ROI)

    # sum matrix
    context.system("AimsSumSparseMatrix",
                   "-i", self.matrix_of_distant_fibers,
                   "-i", self.matrix_of_fibers_near_cortex,
                   "-o", self.complete_connectivity_matrix)

    # smoothing matrix: -s in millimetres
    context.system("AimsSparseMatrixSmoothing",
                   "-i", self.complete_connectivity_matrix,
                   "-m", self.white_mesh,
                   "-o", self.complete_connectivity_matrix,
                   "-s", self.smoothing,
                   "-l", self.gyri_texture,
                   "-p", ROIlabel)
