import Caramel as gm 

pathD= '/home/alehflz/Documents/GitHub/PGD/2025-I/Gravimetría/Data/'
pathR= '/home/alehflz/Documents/GitHub/PGD/2025-1/Gravimetría/Data/2.0.Grav_Observada/'

# ----- Archivo de marea grAV_mitacional
rD= pathD+'0.0.20240827/20240827_CG6_mod.csv'
rM= pathD+"1.1.Marea/Marea60s.TSF"

GravData= gm.GravData(name='08_26', path=rD, sep=',', sr=0,
                      date_format='DayTime', 
                      i_Year='2025', i_Month='8', 
                       c_Day='DIA', c_Time='HORA', 
                       f_Time='%H:%M:%S')

GravData.GravObs(path=rM, sep='\s+', sr=22, 
                 units='nm/s2', g_abs=977902.9086,
                 date_format='Columns', c_data=7,
                 c_Year=0, c_Month=1, c_Day=2, 
                 c_Hour=3, c_Minute=4, c_Second=5, 
                 f_Year='%Y', f_Month='%m', f_Hour='%H')
print(GravData)
GravData.CalculateDistance(idx_x0=6)
GravData.CalculateMeans()
GravData.plot(GravData.data_mean, 'RelObsGrav_mean', 'AbsObsGrav_std')