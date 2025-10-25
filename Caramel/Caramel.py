import numpy as np
import pandas as pd
from datetime import datetime as dt, timedelta 
import plotly.graph_objects as go
import DateFormat as date

class TopoData(object):
    def __init__(self, latitude, longitude, height):
        self. latitude= latitude
        self.longitude= longitude
        self.altitude= height


class TideCorrection(object):
    def __init__(self, path, sep, sr, units, date_format, c_data, **kwargs):
        self.date_format= date.GetDate(date_format)
        self.data= self.date_format.format(path, sep, sr, **kwargs)
        if units== 'nm/s2':
            self.data['g_tide']= 10e-4*self.data.iloc[:,-1:]

        elif units== 'mGal':
            self.data['g_tide']= self.data.iloc[:,-1:]
 

    def CalculateTideCorrection(self, data):
        self.data= pd.merge_asof(data, self.data, on = 'datetime', direction='nearest')
        Tide_correction= self.data.GRAV- self.data.g_tide
        return Tide_correction
    

class DriftCorrection(object):
    @staticmethod
    def CalculateDriftCorrection(data):
        data= data.copy()
        
        d0= data.datetime.iloc[0]
        d1= data.datetime.iloc[-1]
        n_days= (d1- d0).days+ 1
        
        Drift_Correction= []
        for n in range(n_days):
            
            dn= d0+ timedelta(days= n)   
            data_n= data
            B0= data_n.head(1).reset_index(drop=True)
            BN= data_n.tail(1).reset_index(drop=True)

            #Pendiente de la recta de la deriva
            m_num= BN.TideCorrection[0]-B0.TideCorrection[0]
            m_den= BN.datetime[0]-B0.datetime[0]
            m= m_num/m_den.total_seconds() 
            L= len(data_n.iloc[:,0])
            for i in range(L):
                Bi= data_n.loc[[i]].reset_index(drop=True)
                #CD= m*tiempo de cada medición promedio  
                Drift_Correction.append(m*(Bi.datetime[0]- B0.datetime[0]).total_seconds()) 

        return Drift_Correction
    

class ObsGrav(object):
    @staticmethod
    def CalculateObsGrav(data, gAbs):
        d0= data.datetime.iloc[0]
        d1= data.datetime.iloc[-1]
        
        n_days= (d1- d0).days+ 1

        ObsGrav, RelObsGrav, AbsObsGrav= [], [], []

        for n in range(n_days):
            dn= d0+ timedelta(days= n)   
            data_n= data
            L= len(data_n.iloc[:,0])

            for i in range(L):
                ObsGrav.append(data_n.GRAV[i]- data_n.DriftCorrection[i])
                RelObsGrav.append(ObsGrav[-1]- ObsGrav[0])
                AbsObsGrav.append(RelObsGrav[-1]+ gAbs)
                
        gObs=  pd.DataFrame(data = {'datetime':data.datetime, 
                                    'ObsGrav':ObsGrav, 
                                    'RelObsGrav':RelObsGrav, 
                                    'AbsObsGrav':AbsObsGrav})
                
        data.set_index("datetime", inplace=True)
        gObs.set_index("datetime", inplace=True)
        
        return pd.concat([data, gObs], axis=1)


class GeoModel(object):
    @staticmethod
    def CalculateGeoModel(data, g_abs=False):
        model= data[['Name', 'Latitude', 'Longitude', 'Height']]
        pi= np.pi
        grad2rad= pi/180
        latitud_base = data.Latitude.iloc[0]
        if g_abs==True:
        # ----- Gravedad normal - Fórmula Somigliana
            g_e= 978032.67715
            k= 0.001931851353
            e2= 0.0066943800229
            g_normal= g_e*(1+ k*np.sin(latitud_base*grad2rad)**2) \
                        /(1- e2*np.sin(latitud_base*grad2rad)**2) **(1/2)
            model['g_normal']= g_normal*np.ones(len(data.Height))


        #----- Corrección atmosferica
            model['g_atmosp']= -0.874+ 9.9e-5*data.height- 3.56e-9*data.Height**2


        # ----- Correción de latitud
        radio_Tierra= 6371 #[km]
        delta_y= radio_Tierra*(data.Latitude- latitud_base)*grad2rad
        model['g_latitude']= 0.811*delta_y*np.sin(2*latitud_base*grad2rad)

        return data


class GravData(object):
    def __init__(self, name, path, sep, sr, date_format, **kwargs):
        """
        link to datetime formats: https://docs.python.org/3/library/datetime.html
        """
        self.name= name
        self.date_format= date.GetDate(date_format)
        self.data= self.date_format.format(path, sep, sr, **kwargs)


    def GravObs(self, path, sep, sr, units, date_format, c_data, g_abs= 0, **kwargs):
        Tide= TideCorrection(path, sep, sr, units, date_format, c_data, **kwargs) 
        a= pd.DataFrame(Tide.CalculateTideCorrection(self.data))
        self.data.reset_index(inplace=True)
        self.data['TideCorrection']= a
        self.data['DriftCorrection']= DriftCorrection.CalculateDriftCorrection(self.data)
        self.data= ObsGrav.CalculateObsGrav(self.data, g_abs)


    def CalculateDistance(self, idx_x0):
        self.data['Distance']= ((self.data['X']- self.data.iloc[idx_x0]['X'])**2 +
                                 (self.data['Y']-self.data.iloc[idx_x0]['Y'])**2)**(1/2)


    def CalculateMeans(self):
        self.data.reset_index(inplace=True)
        self.data_mean= self.data.groupby(['ESTACION']).agg(['mean', 'std'])
        self.data_mean.columns = self.data_mean.columns.map("_".join)

        print(self.data_mean)


    def FreeAirAnomaly(self):
        mod_Geo= 1


    def plot(self, data, y, y_err):
        fig= go.Figure()
        fig.add_trace(go.Scatter(x=data['Distance_mean'], y=data[y], 
                                 error_y=dict(array=10*data[y_err], visible=True),
                                 mode='markers+text', 
                             textposition='bottom center', text= data.index,))
        fig.show()
    

    def __repr__(self):
        return f'datos: {self.data}'


# Corregir el ciclo diario, modificar el formato datetime e identificar solo el número de días 
# en un archivo grande.

# Corregir el nombre de las columnas y agregarlo al número de columna dado por el usuario.