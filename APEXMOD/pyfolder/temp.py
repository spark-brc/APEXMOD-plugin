import os
import pandas as pd
import glob
import datetime
import numpy as np

tot_feats = 75

wd = "D:\\Workshops\\2022_test\\model02\\APEX-MODFLOW\\MODFLOW"
infile = "amf_apex_percno3.out"
y = ("APEX", "Subarea,", "NO3")
stdate = '1/1/1987'
with open(os.path.join(wd, infile), "r") as f:
    data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]
data1 = [x.split()[2] for x in data]
data_array = np.reshape(data1, (tot_feats, int(len(data1)/tot_feats)), order='F')
column_names = ["{:03d}".format(int(x.split()[0])) for x in data[0:tot_feats]]
df_ = pd.DataFrame(data_array.T, columns=column_names)
df_.sort_index(axis=1, inplace=True)
df_.index = pd.date_range(stdate, periods=len(df_))
df_ = df_.astype(float)
df_ = df_.resample('M').mean()
print(df_)
# # dateList = df_.index.strftime("%m-%d-%Y").tolist()
# # if self.dlg.radioButton_rt3d_m.isChecked(): 
# df_ = df_.resample('M').mean()
#     # dateList = df_.index.strftime("%b-%Y").tolist()
# # elif self.dlg.radioButton_rt3d_y.isChecked(): 
#     # df_ = df_.resample('A').mean()
#     # dateList = df_.index.strftime("%Y").tolist()
# print(df_)