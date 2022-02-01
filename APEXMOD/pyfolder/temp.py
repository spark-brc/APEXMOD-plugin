import os
import pandas as pd
import glob
import datetime

# if self.dlg.checkBox_head.isChecked() and self.dlg.radioButton_mf_results_m.isChecked():


comps_dic = {
    'NO3': 'Nitrate',
    'P': 'Phosphorus',
    'SO4': 'Sulfate',
    'Ca2': 'Calcium',
    'Mg2': 'Magnesium',
    'Na': 'Sodium',
    'K': 'Potassium',
    'Cl': 'Chloride',
    'CO3': 'Carbonate',
    'HCO3': 'Bicarbonate'}


comps =  [i.lower() for i in comps_dic.values()]
new_comps = []
for i in comps:
    if i == 'nitrate' or i == 'phosphorus':
        i = 'rt3d_' + i
    else:
        i = 'salt_' + i
    new_comps.append(i)
suffixs = ['_mon', '_yr', '_avg_mon']

new_comps2 = []
for comp in new_comps:
    for suf in suffixs:
        new_comps2.append(comp + suf)




print(new_comps2)



# #if __name__ == "__main__":
# wd = "D:/Projects/Tools/APEXMODs/APEXMOD_salt_test/price_apexmf_salt/APEX-MODFLOW/MODFLOW"
# get_dataset(wd)
# print('test')
