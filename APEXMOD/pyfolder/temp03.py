import operator
import numpy as np
import os
import pandas as pd



def zon_stat_sub():
    input1 = QgsProject.instance().mapLayersByName("salt_sub (SALT)")[0]
    provider1 = input1.dataProvider()
    rsfiles = ['ca', 'cl', 'so4', 'na', 'mg', 'k', 'hco3', 'co3']

    for rsf in rsfiles:
        input2 = QgsProject.instance().mapLayersByName("interp_{}".format(rsf))[0]
        provider2 = input2.dataProvider()
        if provider1.fields().indexFromName(rsf) != -1:
            attrIdx = provider1.fields().indexFromName(rsf)
            provider1.deleteAttributes([attrIdx])
            
        params = {
            'INPUT_RASTER': input2,
            'RASTER_BAND':1,
            'INPUT_VECTOR': input1,
            'COLUMN_PREFIX':'{}_'.format(rsf),
            'STATISTICS':[2]            
            }
        processing.run("qgis:zonalstatistics", params)
    print('zonal statistics for subs ... done')


def zon_stat_grid():
    input1 = QgsProject.instance().mapLayersByName("salt_grid (SALT)")[0]
    provider1 = input1.dataProvider()
    rsfiles = ['ca', 'cl', 'so4', 'na', 'mg', 'k', 'hco3', 'co3']

    for rsf in rsfiles:
        input2 = QgsProject.instance().mapLayersByName("interp_{}".format(rsf))[0]
        provider2 = input2.dataProvider()
        if provider1.fields().indexFromName(rsf) != -1:
            attrIdx = provider1.fields().indexFromName(rsf)
            provider1.deleteAttributes([attrIdx])
            
        params = {
            'INPUT_RASTER': input2,
            'RASTER_BAND':1,
            'INPUT_VECTOR': input1,
            'COLUMN_PREFIX':'{}_'.format(rsf),
            'STATISTICS':[2]            
            }
        processing.run("qgis:zonalstatistics", params)
    print('zonal statistics for grids ... done')


def zon_stat_frac():
    rstfiles = ["caso4_frac", "caco3_frac"]

    sub_lyr = QgsProject.instance().mapLayersByName("salt_sub (SALT)")[0]
    grid_lyr = QgsProject.instance().mapLayersByName("salt_grid (SALT)")[0]
    sub_provider1 = sub_lyr.dataProvider()
    grid_provider1 = sub_lyr.dataProvider()

    for rsf in rstfiles:
        rst_lyr = QgsProject.instance().mapLayersByName("{}".format(rsf))[0]
        # rst_lyr_prv = rst_lyr.dataProvider()

        if sub_lyr.fields().indexFromName(rsf) != -1:
            attrIdx = sub_provider1.fields().indexFromName(rsf)
            sub_provider1.deleteAttributes([attrIdx])
        if grid_lyr.fields().indexFromName(rsf) != -1:
            attrIdx = sub_provider1.fields().indexFromName(rsf)
            grid_provider1.deleteAttributes([attrIdx])
        sub_params = {
            'INPUT_RASTER': rst_lyr,
            'RASTER_BAND':1,
            'INPUT_VECTOR': sub_lyr,
            'COLUMN_PREFIX':'{}_'.format(rsf),
            'STATISTICS':[2]            
            }
        processing.run("qgis:zonalstatistics", sub_params)

        grid_params = {
            'INPUT_RASTER': rst_lyr,
            'RASTER_BAND':1,
            'INPUT_VECTOR': grid_lyr,
            'COLUMN_PREFIX':'{}_'.format(rsf),
            'STATISTICS':[2]            
            }
        processing.run("qgis:zonalstatistics", grid_params)

    print('zonal statistics for subs and grids ... done')



def init_conc_frac_grids(wd, colnum, rownum):
    input1 = QgsProject.instance().mapLayersByName("salt_grid (SALT)")[0]
    provider = input1.dataProvider()
    grid_id_idx = provider.fields().indexFromName("grid_id")

    # transfer the shapefile layer to a python list 
    l = []
    for i in input1.getFeatures():
        l.append(i.attributes())

    # then sort by grid_id
    l_sorted = sorted(l, key=operator.itemgetter(grid_id_idx))
    rsfiles = ['ca', 'cl', 'so4', 'na', 'mg', 'k', 'hco3', 'co3']

    for rsf in rsfiles:
        c_idx = provider.fields().indexFromName("{}_mean".format(rsf))
        cons = [g[c_idx] for g in l_sorted]
        out_arr = np.reshape(cons, (colnum, rownum))
        np.savetxt(os.path.join(wd, "c{}.tmp".format(rsf)), out_arr, fmt='%.5e')
        print(" c{}.tmp ... done".format(rsf))
    rst_fracs = ["caso4_frac", "caco3_frac"]
    for rf in rst_fracs:
        rf_idx = provider.fields().indexFromName("{}".format(rf))
        fracs = [g[rf_idx] for g in l_sorted]
        out_arr = np.reshape(fracs, (colnum, rownum))
        np.savetxt(os.path.join(wd, "fr{}.tmp".format(rf)), out_arr, fmt='%.5e')
        print(" fr{}.tmp ... done".format(rf))        


def init_conc_subs(wd):
    input1 = QgsProject.instance().mapLayersByName("salt_sub (SALT)")[0]
    provider = input1.dataProvider()
    sub_id_idx = provider.fields().indexFromName("Subbasin")

    # transfer the shapefile layer to a python list 
    l = []
    for i in input1.getFeatures():
        l.append(i.attributes())

    # then sort by grid_id
    l_sorted = sorted(l, key=operator.itemgetter(sub_id_idx))
    rsfiles = ['so4','ca', 'mg','na','k','cl','co3','hco3']
    df = pd.DataFrame()
    for rsf in rsfiles:
        c_idx = provider.fields().indexFromName("{}_mean".format(rsf))
        cons = [g[c_idx] for g in l_sorted]
        df['{}'.format(rsf)] = cons
    df.to_csv(os.path.join(wd, 'initconc_sub.txt'), index=False, sep='\t', float_format='%.5e')



def ion_fracs(wd):
    ionf = np.zeros((218, 5))
    np.savetxt(os.path.join(wd, "ionf.tmp"), ionf, fmt='%.1f')

def ion_irrigation(wd):
    ionf = np.zeros((218, 8))
    np.savetxt(os.path.join(wd, "ion_irr.tmp"), ionf, fmt='%.1f')


def cno3_cp(wd, colnum, rownum):
    ionf = np.zeros((colnum, rownum))
    np.savetxt(os.path.join(wd, "cno3.tmp"), ionf, fmt='%.1f')
    np.savetxt(os.path.join(wd, "cp.tmp"), ionf, fmt='%.1f')

wd = "d:/Projects/Watersheds/Green/Analysis/AMRSs/init_salt_concs/"
colnum = 185
rownum = 117
init_conc_frac_grids(wd, colnum, rownum)
# init_conc_subs(wd)
# ion_fracs(wd)
# ion_irrigation(wd)
# cno3_cp(wd, colnum, rownum)
# zon_stat_frac()

# if __name__ == '__main__':
    # wd = "D:\\Projects\\RegionalCalibration\\Autocalibration\\ani_apexmf_cal_v03"
    # os.chdir(wd)

    # zon_stat_sub()
    # zon_stat_grid()