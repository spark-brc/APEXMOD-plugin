layer = QgsProject.instance().mapLayersByName("hru (SWAT)")[0]
provider = layer.dataProvider()
#if provider.fields().indexFromName("HRU_ID2") == -1:
#   field = QgsField("HRU_ID2", QVariant.Int)
#   provider.addAttributes([field])
#   layer.updateFields()
    
field1Id = layer.dataProvider().fields().indexFromName( "HRU_ID" )
attrIdx = layer.dataProvider().fields().indexFromName( "HRU_ID2" )
aList = layer.getFeatures()

featureList = sorted(aList, key=lambda f: f[field1Id])
layer.startEditing()
for i, f in enumerate(featureList):
#    print (f.id())
    layer.changeAttributeValue(f.id(), attrIdx, i+1)
layer.commitChanges()
print('done')