# -*- coding: utf-8 -*-
"""
/***************************************************************************
 APEXMOD
                                 A QGIS plugin
 This plugin helps link APEX and MODFLOW model.
                             -------------------
        begin                : 2020-01-23
        copyright            : (C) 2020 by Seonggyu Park
        email                : seonggyu.park@brc.tamus.edu
        git sha              : https://github.com/spark-brc/APEXMOD
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load APEXMOD class from file APEXMOD.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .APEXMOD import APEXMOD
    return APEXMOD(iface)
