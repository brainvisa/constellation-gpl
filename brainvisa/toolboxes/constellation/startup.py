# -*- coding: utf-8 -*-
#  This software and supporting documentation are distributed by
#      Institut Federatif de Recherche 49
#      CEA/NeuroSpin, Batiment 145,
#      91191 Gif-sur-Yvette cedex
#      France
#
# This software is governed by the CeCILL license version 2 under
# French law and abiding by the rules of distribution of free software.
# You can  use, modify and/or redistribute the software under the
# terms of the CeCILL license version 2 as circulated by CEA, CNRS
# and INRIA at the following URL "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license version 2 and that you accept its terms.

from __future__ import absolute_import
import os
from brainvisa.configuration import neuroConfig
from brainvisa.data import neuroHierarchy
import brainvisa.processes
from brainvisa.data import sqlFSODatabase
import constel.info as coninfo

constel_db = os.path.join(
    os.path.dirname(neuroConfig.sharePath),
    'constellation-%d.%d' % (coninfo.version_major, coninfo.version_minor),
    'constellation_atlas_hcp_200s')

for db_name, ontology in (('constellation_matrix', 'brainvisa-3.2.0'),
                          ('freesurfer_gyri', 'freesurfer')):
    db_path = os.path.join(constel_db, db_name)
    if os.path.isdir(db_path):
        if db_path not in [x.directory for x in neuroConfig.dataPath]:
            dbs = neuroConfig.DatabaseSettings(db_path, read_only=True)
            dbs.expert_settings.ontology = ontology
            dbs.builtin = True
            sqliteFileName = os.path.join(
                db_path, 'database-%s.sqlite' % sqlFSODatabase.databaseVersion)
            neuroConfig.dataPath.append(dbs)
            db = neuroHierarchy.SQLDatabase(
                sqliteFileName, db_path, ontology,
                context=brainvisa.processes.defaultContext(), settings=dbs)
            neuroHierarchy.databases.add(db)

            del dbs, db
    del db_path
del db_name, ontology, constel_db
neuroHierarchy.update_soma_workflow_translations()
