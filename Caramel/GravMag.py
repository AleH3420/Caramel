import numpy as np
import pandas as pd
import datetime as dt

class TopoData(object):
    def __init__(self, latitude, longitude, height):
        self. latitude= latitude
        self.longitude= longitude
        self.altitude= height


class TideCorrection(object):
    def __init__(self, data, units):
        self.data= data

        if units== 'nm/s2':
            self.data.g_tide= 10e-4*self.data.g_tide 
        elif units== 'mGal':
            self.data.g_tide= self.data.g_tide   


    def CalculateTideCorrection(self, data):
        self.data= pd.merge(data, self.data, on = 'Datetime', how='left')
        Tide_correction= self.data.g_p- self.data.g_tide

        return Tide_correction
    

class DriftCorrection(object):
    @staticmethod
    def CalculateDriftCorrection(data):
        d0= data.datetime.iloc[0]
        d1= data.datetime.iloc[-1]
        n_days= (d1- d0).days+ 1

        Drift_Correction= []

        for n in range(n_days):
            
            dn= d0+ dt.timedelta(days= n)   
            data_n= data.loc[data.Datetime == dn]

            B0= data_n.head(1).reset_index(drop=True)
            BN= data_n.tail(1).reset_index(drop=True)

            #Pendiente de la recta de la deriva
            m_num= BN.TideCorrection[0]-B0.TideCorrection[0]
            m_den= BN.Datetime[0]-B0.Datetime[0]
            m= m_num/m_den.total_seconds() 
            L= len(data_n.g_p)

            for i in range(L):
                Bi= data_n.loc[[i]].reset_index(drop=True)
                #CD= m*tiempo de cada medición promedio  
                Drift_Correction.append(m*(Bi.Datetime[0]- B0.Datetime[0]).total_seconds()) 

        return Drift_Correction
    

class ObsGrav(object):
    @staticmethod
    def CalculateObsGrav(data, gAbs):
        d0= data.datetime.iloc[0]
        d1= data.datetime.iloc[-1]
        n_days= (d1- d0).days+ 1

        ObsGrav, RelObsGrav, AbsObsGrav= [], [], []

        for n in range(n_days):
            dn= d0+ dt.timedelta(days= n)   
            data_n= data.loc[data.Datetime == dn]
            L= len(data_n.g_p)

            for i in range(L):
                ObsGrav.append(data_n.g_p[i]- data_n.DriftCorrection[i])
                RelObsGrav.append(ObsGrav[-1]- ObsGrav[0])
                AbsObsGrav.append(RelObsGrav[-1]+ gAbs)
                
        gObs=  pd.DataFrame(data = {'Datetime':data.Datetime.to_numpy(), 
                                    'ObsGrav':ObsGrav, 
                                    'RelObsGrav':RelObsGrav, 
                                    'AbsObsGrav':AbsObsGrav})
                
        data.set_index("Datetime", inplace=True)
        gObs.set_index("Datetime", inplace=True)
        
        return pd.concat([data, gObs], axis=1)


class GeoModel(object):
    @staticmethod
    def CalculateGeoModel(data, g_abs=False):
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
            data['g_normal']= g_normal*np.ones(len(data.Height))


        #----- Corrección atmosferica
            data['c_atmosp']= -0.874+ 9.9e-5*data.height- 3.56e-9*data.Height**2


        # ----- Correción de latitud
        radio_Tierra= 6371 #[km]
        delta_y= radio_Tierra*(data.Latitude- latitud_base)*grad2rad
        data['c_latitude']= 0.811*delta_y*np.sin(2*latitud_base*grad2rad)

        return data


class GravData(object):
    def __init__(self, data):
        self.data= data 


    def GravObs(self, data, units, g_abs= 0):
        Tide= TideCorrection(data, units) 
        
        self.data['TideCorrection']= Tide.CalculateTideCorrection(self.data)
        self.data['DriftCorrection']= DriftCorrection.CalculateDriftCorrection(self.data)

        self.data= ObsGrav.CalculateObsGrav(self.data, g_abs)


    def CalculateMeans(self):
        self.data_mean= self.data.groupby(['Name']).mean()


    def FreeAirAnomaly(self):
        mod_Geo= 1


    def __repr__(self):
        return f'datos: {self.data}'


data= pd.DataFrame(data={'Name':'E1', 
               'Datetime': dt.Datetime(2020, 1, 1, 4, 0, 0),
               'g_p':1354, 
               'Latitude':19.991,
               'Longitude':-99.00,
               'Height':1200,
               'H_inst':34}, index=[0])

tide= pd.DataFrame(data= {'Datetime': dt.Datetime(2020, 1, 1, 4, 0, 0),
               'g_tide':154},index=[0])


dataGrav= GravData(data)
print(dataGrav)
dataObs= dataGrav.GravObs(tide, 'nm/s2')
print(dataGrav)