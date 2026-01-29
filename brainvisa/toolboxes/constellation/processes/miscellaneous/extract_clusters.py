# -*- coding: utf-8 -*-

# Axon python API module
from __future__ import absolute_import
from brainvisa.processes import Signature, String, ReadDiskItem, Integer,\
    neuroHierarchy, OpenChoice, ValidationError, Choice
from six.moves import range
import os


def validation():
    """
    This function is executed at BrainVisa startup when the process is loaded.
    It checks some conditions for the process to be available.
    """
    try:
        from soma import aims
    except ImportError:
        raise ValidationError(
            "Please make sure that aims-free is installed.")


name = "Extract clusters"
userLevel = 2


# Argument declaration
signature = Signature(
    "name_group_of_subjects", String(),
    "white_mesh", ReadDiskItem("White Mesh", "Aims mesh formats"),
    "clustering_texture", ReadDiskItem(
        "Connectivity ROI Texture", "Aims texture formats",
        requiredAttributes={"roi_autodetect": "no",
                            "roi_filtered": "no",
                            "intersubject": "yes",
                            "step_time": "yes",
                            "measure": "no"}),
    "number_of_clusters", Integer(),
    "transfo_joy", ReadDiskItem(
        "Transform Raw T1 MRI to Talairach-AC/PC-Anatomist",
        "Transformation matrix"),
    "transfo_morpho", ReadDiskItem(
        "Transform Raw T1 MRI to Talairach-AC/PC-Anatomist",
        "Transformation matrix"),
    "output_database", Choice()
)


def initialization(self):
    """Provides default values and link of parameters
    """
    databases = [h.name for h in neuroHierarchy.hierarchies()
                 if not h.read_only and h.fso.name == "brainvisa-3.2.0"]
    self.signature["output_database"].setChoices(*databases)
    if len(databases) != 0:
        self.output_database = databases[0]
    else:
        self.signature["output_database"] = OpenChoice()


def execution(self, context):
    from soma import aims

    # load the clustering individual of concatenated approach
    clustering_texture = aims.read(self.clustering_texture.fullPath())
    # error if the number is too great or small
    try:
        assert self.number_of_clusters <= (clustering_texture.size() - 1)
    except AssertionError:
        context.write("ERROR: the number of clusters should be 1 to ",
                      clustering_texture.size() - 1)

    # value of the time step on the clustering texture
    clusters_texture = aims.TimeTexture_S16()
    clusters_texture[0].assign(
        clustering_texture[self.number_of_clusters - 1].arraydata())
    mesh = aims.read(self.white_mesh.fullPath())
    subject = os.path.basename(
        os.path.dirname(self.clustering_texture.fullPath()))
    gyrus = os.path.basename(
        os.path.dirname(os.path.dirname(
                        os.path.dirname(self.clustering_texture.fullPath()))))

    # generate the mesh of each cluster of the texture
    for label in range(1, self.number_of_clusters + 1):
        cluster_submesh = aims.SurfaceManip.meshExtract(
            mesh, clusters_texture, label)[0]
        path = (self.output_database + "/t1-1mm-1/" + subject + "/t1mri/"
                + "default_acquisition/default_analysis/segmentation/mesh/")
        if not os.path.exists(path):
            os.makedirs(path)

        name = (subject + self.name_group_of_subjects + "_" + gyrus
                + "_cluster" + str(label) + ".gii")
        ofile = path + name
        context.write("--> SUBMESH " + str(label) + ": ", ofile)
        aims.write(cluster_submesh, ofile)

        # apply the transfo to obtain a common space to a target subject
        transfo_joy = aims.read(self.transfo_joy.fullPath())
        transfo_morpho = aims.read(self.transfo_morpho.fullPath())
        transfo_target = transfo_joy * transfo_morpho
        aims.SurfaceManip.meshTransform(cluster_submesh, transfo_target)

        path_t = (self.output_database + "/t1-1mm-1/" + subject + "/t1mri/"
                  + "default_acquisition/default_analysis/segmentation/mesh/")
        name_t = (subject + self.name_group_of_subjects + "_" + gyrus
                  + "_cluster" + str(label) + "_transfo_to_target_subject.gii")
        ofile_t = path_t + name_t
        context.write("--> SUBMESH " + str(label) + ": ", ofile_t)
        aims.write(cluster_submesh, ofile_t)
