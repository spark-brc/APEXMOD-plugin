# <img src="./imgs/icon.png" style="float" width="80" align="center"> &nbsp; APEXMOD

#### :exclamation: ***Note:*** `APEXMOD is compatible with QGIS3.`

APEXMOD is a QGIS-based graphical user interface that facilitates linking [APEX](https://epicapex.tamu.edu/apex//) and [MODFLOW](https://www.usgs.gov/mission-areas/water-resources/science/modflow-and-related-programs?qt-science_center_objects=0#qt-science_center_objects), running APEX-MODFLOW simulations, and viewing results.  

This repository contains source codes and an executable for the Alpha version of APEXMOD.
- __[Installer](https://github.com/spark-brc/APEXMOD/releases/tag/1.0.a):__ APEXMOD 1.0.a.exe
- **[Inputs](https://github.com/spark-brc/APEXMOD/raw/master/Inputs/Animas.zip):** Animas Dataset zip file
- **[Source Code](https://github.com/spark-brc/APEXMOD/tree/master/APEXMOD)**
- **[Tutorial Document (example)](https://github.com/spark-brc/qswatmod/blob/master/QSWATMOD%20Tutorial.pdf)** will be provided soon!

-----
# <img src="./imgs/icon2.png" style="float" width="80" align="center"> &nbsp; Installation
The QGIS3 software must be installed on the system prior to the installation of APEXMOD. We've tested APEXMOD with the “long term release (LTR)” (3.10.4 ~ 3.10.10) versions of QGIS3.

- Install one of the versions of QGIS. It can be downloaded from https://qgis.org/en/site/forusers/download.html.
- Download [the APEXMOD installer](https://github.com/spark-brc/APEXMOD/raw/master/Installer/APEXMOD.exe) and install it by running APEXMOD 1.0.a.exe or a later version. The APEXMOD is installed into the user's home directory *(~\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\APEXMOD)*, which we will refer to as the APEXMOD plugin directory.

<p align="center">
    <img src="./imgs/fig_01.png" width="200" align="center">
</p>
<p align="center">
    <img src="./imgs/fig_02.png" width="500">
</p>

APEXMOD includes all dependencies ([FloPy](https://www.usgs.gov/software/flopy-python-package-creating-running-and-post-processing-modflow-based-models) ([Bakker et al., 2016](https://onlinelibrary.wiley.com/doi/abs/10.1002/hyp.10933)) and [PyShp](https://pypi.org/project/pyshp/)) directly in the plugin to avoid user-installation.  
- Open QGIS3 after the installation of APEXMOD is finished.

If you don't see APEXMOD icon on the toolbar,
- Go to Plugins menu and open Manage and Install Plugins
<p align="center">
    <img src="./imgs/fig_03.png" width="700">
</p>

- Click the installed tab and check APEXMOD box to activate the plugin.
<p align="center">
    <img src="./imgs/fig_04.png" width="450">

Now, you will see the APEXMOD icon on the toolbar.
<p align="center">
    <img src="./imgs/fig_05.png" width="300">
</p>

<br>

# References
[Bakker, M., Post, V., Langevin, C. D., Hughes, J. D., White, J. T., Starn, J. J. and Fienen, M. N., 2016, Scripting MODFLOW Model Development Using Python and FloPy: Groundwater, v. 54, p. 733–739, doi:10.1111/gwat.12413.](https://ngwa.onlinelibrary.wiley.com/doi/full/10.1111/gwat.12413)