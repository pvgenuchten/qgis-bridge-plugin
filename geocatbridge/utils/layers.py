import uuid 

from qgis.core import (
    QgsCoordinateTransform,
    QgsMapLayer,
    QgsProject)

from qgis.gui import QgsMetadataWidget

from qgis.utils import iface

def publishableLayers():
    layers = [layer for layer in QgsProject.instance().mapLayers().values() 
            if layer.type() in [QgsMapLayer.VectorLayer, QgsMapLayer.RasterLayer]]
    return layers

def layerFromName(name):
    layers = publishableLayers()
    for layer in layers:
        if layer.name() == name:
            return layer    

def fieldsForLayer(layer):
    if layer.type() == QgsMapLayer.VectorLayer:
        return [f.name() for f in layer.fields()]
    else:
        return []

def isVectorLayer(layer):
    return layer.type() != layer.VectorLayer

def metadataForLayer(layer):
    return layer.metadata().clone()

def htmlMetadataForLayer(layer):
    return layer.htmlMetadata()

def bboxStringFromLayer(layer):
    bbox = layer.extent()
    if bbox.isEmpty():
        bbox.grow(1)
    return ",".join([str(v) for v in [bbox.xMinimum(), bbox.yMinimum(), bbox.xMaximum(), bbox.yMaximum()]])

def crsAuthidFromLayer(layer):
    return layer.crs().authid()

def bboxStringFromLayers(layers):   
    bbox = QgsRectangle()
    for layer in layers:
        xform = QgsCoordinateTransform(layer.crs(), projectCrsAuthid(), QgsProject.instance())
        extent = xform.transform(layer.extent())
        bbox.combineExtentWith(extent)
    return ",".join([str(v) for v in [bbox.xMinimum(), bbox.yMinimum(), bbox.xMaximum(), bbox.yMaximum()]])

def projectCrsAuthid():
    return iface.mapCanvas().mapSettings().destinationCrs()

def metadataLanguages():
    return QgsMetadataWidget.parseLanguages()

def uuidForLayer(layer):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, layer.source()))