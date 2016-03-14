#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4.QtCore import QVariant
import math

def create(): # вызываем функцию создание нового объекта
    ''' Create new DataBase class '''
    return DataBase() # передаем статус объекта, т.к. передаем только второй параметр, то указываем его с ключевым словом

#путь к файлу с данными
path_input_file = 'C:/Python27/qgis/input_data.txt'

#считываем входной файл 
def read_txt_file(path):
    spisok_1 = []
    spisok_2 = []
    with open (path, u'rt') as fd:
        for line in fd:
            # трансформируем строку в список
            lst = line.split(u',')
            #преобразуем из строки в числа, где это возможно
            for i in lst:
                    try:
                        spisok_1.append(float(i))
                    except ValueError:
                        spisok_1.append(i)
            spisok_2.append(spisok_1)
            spisok_1 = []
    return spisok_2
        
rows = read_txt_file(path_input_file)
for i in rows:
    print i
    
#создаем слой с точками из входного файла
def create_layer_point(list_points):
    #создаем список полей атрибутов
    fields = QgsFields()
    fields.append(QgsField("X", QVariant.Double))
    fields.append(QgsField("Y", QVariant.Double))
    fields.append(QgsField("ID", QVariant.Int))
    fields.append(QgsField("Longitude", QVariant.Double))
    fields.append(QgsField("Latitude", QVariant.Double))
    fields.append(QgsField("Azimuth", QVariant.Double))
    fields.append(QgsField("Angle", QVariant.Double))
    
    #Система координат и проекция
    # WGS84 имеет EpsgCrsId 4326
    crs = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId)
    # создаем экземпляр класса для записи векторных данных. Аргументы:
    layer = QgsVectorFileWriter("c:/Python27/qgis/my_shapes_6.shp", "CP1251", fields, QGis.WKBPoint, crs, "ESRI Shapefile")
    if layer.hasError() != QgsVectorFileWriter.NoError:
        print "Error when creating shapefile: ", layer.hasError()

    #создаем экземпляр слоя
    #layer =  QgsVectorLayer('Point', 'points' , "memory")
    #pr = layer.dataProvider() 
    # add the first point
    pt = QgsFeature()
    #пропускаем заголовок входного текстового файла
    for i in xrange(1,len(list_points),1):
        #print list_points[i],list_points[i][0],list_points[i][1]
        #QgsGeometry.fromPoint(point1) - создать геометрию по координатам для точек
        #добавляем объекты
        pt.setGeometry(QgsGeometry.fromPoint(QgsPoint(list_points[i][0],list_points[i][1])))
        #заполняем табл. атрибутов
        pt.setAttributes(list_points[i])
        layer.addFeature(pt)
    layer = QgsVectorLayer("c:/Python27/qgis/my_shapes_6.shp", "my_shapes", "ogr")
    #update extent of the layer
    layer.updateExtents()
    # add the layer to the canvas
    QgsMapLayerRegistry.instance().addMapLayer(layer)
    return layer
    
layer = create_layer_point(rows)
del layer
    
#Трансформируем в метрическую систему координат
def transform_layer(list_points):
    #начальная проекция
    crsSrc = QgsCoordinateReferenceSystem(4326)    # WGS 84
    #конечная проекция
    crsDest = QgsCoordinateReferenceSystem(32633)  # WGS 84 / UTM zone 33N
    #трансформация
    xform = QgsCoordinateTransform(crsSrc, crsDest)
    
    fields = QgsFields()
    fields.append(QgsField("X", QVariant.Double))
    fields.append(QgsField("Y", QVariant.Double))
    fields.append(QgsField("ID", QVariant.Int))
    fields.append(QgsField("Longitude", QVariant.Double))
    fields.append(QgsField("Latitude", QVariant.Double))
    fields.append(QgsField("Azimuth", QVariant.Double))
    fields.append(QgsField("Angle", QVariant.Double))
    
    layer =  QgsVectorLayer('Point?crs=epsg:32633', 'points' , "memory")
    pr = layer.dataProvider() 
    # add the first point
    pt = QgsFeature()
    caps = layer.dataProvider().capabilities()
    if caps & QgsVectorDataProvider.AddAttributes:
        pr.addAttributes(fields)
    field_names = [field.name() for field in pr.fields()]
    #for i in  field_names:
    #   print i
    
    #создаем список точек и перепроецируем его + добавляем значения атрибутов
    for i in list_points:
        if type(i[0])<>type(u's'):
            pt.setGeometry(QgsGeometry.fromPoint(xform.transform(QgsPoint(i[0],i[1]))))
            print i
            pt.setAttributes(i)
            pr.addFeatures([pt])
    # update extent of the layer
    #layer.updateExtents()
    # add the layer to the canvas
    #QgsMapLayerRegistry.instance().addMapLayers([layer])
    return layer
    
def circle_layer(input_layer):
    pt = QgsFeature()
    features = input_layer.getFeatures()
    #for f in features:
    #    print "F:",f.id(), f.attributes(), f.geometry().asPoint()
    #радиус сектора
    R = 10000
    #список точек
    points = []
    #список значений атрибутов
    attributes = []
    for f in features:
        s2 = []
        #центр - начальная точка сектора
        s2.append(f.geometry().asPoint())
        #15 - начало сектора (в град.), 270 - конец сектора (в град.), 10 - шаг (в град.)
        for grad in xrange(int(f.attributes()[5]), int(f.attributes()[5]+f.attributes()[6]), 5):
            #    из град в рад + вычисление координат точек сектора
            x = R * math.cos(math.radians(grad)) + f.geometry().asPoint()[0]
            y = R * math.sin(math.radians(grad)) + f.geometry().asPoint()[1]
            s2.append(QgsPoint(x,y))
            #    print x, y
        # составление списка точек с помощью класса QgsPoint
        points.append(s2)
        attributes.append(f.attributes())
    #layer =  QgsVectorLayer('Point?crs=epsg:4326', 'points' , "memory")
    layer = QgsVectorLayer('Polygon?crs=epsg:32633&field=X:double&field=Y:double&field=ID:integer&field=Longitude:double&field=Latitude:double&field=Azimuth:double&field=Angle:double', 'poly' , "memory")
    pr = layer.dataProvider() 
    # add the first point
    pt = QgsFeature()
    j = 0
    for i in points:
        '''
        for j in i:
            pt.setGeometry(QgsGeometry.fromPoint(j))
            pr.addFeatures([pt])
        '''
        pt.setGeometry(QgsGeometry.fromPolygon([i]))
        pt.setAttributes(attributes[j])
        j += 1
        pr.addFeatures([pt])
    # update extent of the layer
    layer.updateExtents()
    # add the layer to the canvas
    QgsMapLayerRegistry.instance().addMapLayers([layer])

   
layer = transform_layer(rows)
pr = layer.dataProvider() 
# show some stats
#количество полей в слое
print "fields:", len(pr.fields())
#количество объектов в слое
print "features:", pr.featureCount()
e = layer.extent()

circle_layer(layer)

# iterate over features
#перебрать все объекты слоя
pt = QgsFeature()
features = layer.getFeatures()
for f in features:
    print "F:",f.id(), f.attributes(), f.geometry().asPoint()
