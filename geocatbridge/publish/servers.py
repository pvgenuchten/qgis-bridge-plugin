import json
import psycopg2
from .sldadapter import getCompatibleSldAsZip
from .exporter import exportLayer
from qgiscommons2.network.networkaccessmanager import NetworkAccessManager
from qgis.PyQt.QtCore import QSettings
from geocatbridgecommons.geoservercatalog import GeoServerCatalog
from geocatbridgecommons.catalog import GeodataCatalog, MetadataCatalog
from qgis.core import QgsMessageLog, Qgis, QgsVectorLayerExporter, QgsAuthMethodConfig, QgsApplication, QgsFeatureSink, QgsFields

SERVERS_SETTING = "geocatbridge/BridgeServers"

_servers = {}

def readServers():
    global _servers
    try:
        value = QSettings().value(SERVERS_SETTING)
        if value is not None:
            storedServers = json.loads(value)            
            for serverDef in storedServers:
                s = _serverFromDefinition(serverDef)
                _servers[s.name] = s
    except KeyError:
        pass

def _serverFromDefinition(defn):
    return globals()[defn[0]](**defn[1])

def _updateStoredServers():
    servList = []
    for s in _servers.values():
        d = {k:v for k,v in s.__dict__.items() if not k.startswith("_")}
        servList.append((s.__class__.__name__, d))    
    QSettings().setValue(SERVERS_SETTING, json.dumps(servList))

def allServers():
    return _servers

def addServer(server):
    _servers[server.name] = server
    _updateStoredServers()

def removeServer(name):
    del _servers[name]
    _updateStoredServers()

def geodataServers():
    return {name: server for name, server in _servers.items() if server._isDataCatalog}

def metadataServers():
    return {name: server for name, server in _servers.items() if server._isMetadataCatalog}


class GeodataServer():
    
    def unpublishData(self, layer):
        self.catalog().delete_layer(layer.name())
        self.catalog().delete_style(layer.name())    

class GeoserverServer(GeodataServer):

    UPLOAD_DATA = 0
    STORE_IN_POSTGIS = 1

    def __init__(self, name, url="", authid="", storage=0, workspace="", datastore="", postgisdb=None):
        self.name = name
        self.url = url
        self.authid = authid
        self.storage = storage
        self.workspace = workspace
        self.datastore = datastore
        self.postgisdb = postgisdb
        self._isMetadataCatalog = False
        self._isDataCatalog = True

    def catalog(self):
        nam = NetworkAccessManager(self.authid, debug=False)
        return GeoServerCatalog(self.url, nam, self.workspace)

    def publishStyle(self, layer):
        style = getCompatibleSldAsZip(layer)
        self.catalog().publishStyle(layer.name(), zipfile = style)
        
    def publishLayer(self, layer, fields):        
        if layer.type() == layer.VectorLayer:
            if self.storage == self.UPLOAD_DATA:
                filename = exportLayer(layer, fields)
                style = getCompatibleSldAsZip(layer)
                self.catalog().publish_vector_layer_from_file(filename, layer.name(), layer.crs().authid(), style, layer.name())
            else:
                try:
                    db = allServers()[self.postgisdb]
                except KeyError:
                    raise Exception("Cannot find the selected PostGIS database")
                db.importLayer(layer, fields)                
                self.catalog().publish_vector_layer_from_postgis(postgisdb.host, postgisdb.port, 
                                        postgisdb.database, postgisdb.schema, layer.name(), 
                                        postgisdb._username, postgisdb._password, layer.crs().authid(), 
                                        layer.name(), style, layer.name())
        elif layer.type() == layer.RasterLayer:
            filename = exportLayer(layer, fields)
            style = getCompatibleSldAsZip(layer)
            self.catalog().publish_raster_layer_file(filename, layer.name(), style, layer.name())

    def testConnection(self):
        try:
            self.catalog().gscatalog.gsversion()
            return True
        except:
            return False



class MapserverServer(): 
    pass

class GeocatLiveServer(): 
    pass

class GeonetworkServer():

    PROFILE_DEFAULT = 0
    PROFILE_INSPIRE = 1
    PROFILE_DUTCH = 2

    def __init__(self, name, url="", authid="", profile=""):
        self.name = name
        self.url = url
        self.authid = authid
        self.profile = profile
        self._isMetadataCatalog = True
        self._isDataCatalog = False

    def publishLayerMetadata(self, layer):
        pass

class PostgisServer(): 
    
    def __init__(self, name, authid="", host="localhost", port="5432", schema="public", database="db"):
        self.name = name
        self.host = host
        self.port = port
        self.schema = schema
        self.database = database
        self.authid = authid
        self._isMetadataCatalog = False
        self._isDataCatalog = False
        authConfig = QgsAuthMethodConfig()                
        QgsApplication.authManager().loadAuthenticationConfig(self.authid, authConfig, True)
        self._username = authConfig.config('username')
        self._password = authConfig.config('password')

    def importLayer(self, layer, fields):
        uri = "dbname='%s' key='id' host=%s port=%s user='%s' password='%s' table=\"%s\".\"%s\" (geom) sql=" % (self.database, 
                    self.host, self.port, self._username, self._password, self.schema, layer.name())
        
        qgsfields = QgsFields()
        for f in layer.fields():
            if fields is None or f.name() in fields:
                qgsfields.append(f)
        print (uri)
        exporter = QgsVectorLayerExporter(uri, "postgres", qgsfields,
                                          layer.wkbType(), layer.sourceCrs(), True)

        if exporter.errorCode() != QgsVectorLayerExporter.NoError:
            raise Exception('Error importing to PostGIS: {0}'.format(exporter.errorMessage()))

        features = layer.getFeatures()
        for f in features:
            if not exporter.addFeature(f, QgsFeatureSink.FastInsert):
                raise Exception('Error importing to PostGIS: {0}').format(exporter.errorMessage())
        exporter.flushBuffer()
        if exporter.errorCode() != QgsVectorLayerExporter.NoError:
            raise Exception('Error importing to PostGIS: {0}').format(exporter.errorMessage())

    def testConnection(self):
        con = None
        try:
            print(self._username, self._password)
            con = psycopg2.connect(dbname=self.database, user=self._username, password=self._password, host=self.host, port=self.port)
            cur = con.cursor()
            cur.execute('SELECT version()')
            cur.fetchone()[0]
            return True
        except:
            return False
        finally:
            if con:
                con.close()

class CswServer(): 
    pass