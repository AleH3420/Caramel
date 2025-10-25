from datetime import datetime as dt
import pandas as pd


def checkKwargs(kwargs, valid_params):
    invalid_params = set(kwargs) - set(valid_params)
    if invalid_params:
        raise ValueError(f"Invalid params: {invalid_params}")

    return {k: v for k, v in kwargs.items() if k in valid_params}


class Date(object):
    def format(self, **kargs):
        pass


class DateTimeFormat(Date):
    def format(self, path:str, sep:str=' ', sk:int=0, **kwargs):
        valid_params= ['column']
        valid= checkKwargs(kwargs, valid_params)
        
        data= pd.read_csv(path, skiprows= sk, sep= sep, index_col=valid['column'], parse_dates=True)
        
        return data
    

class DateAndTimeFormat(Date):
    def format(self, path:str, sep:str=' ', sk:int=0, **kwargs):
        valid_params= ['c_Date', 'c_Time', 
                      'f_Date', 'f_Time']
        valid= checkKwargs(kwargs, valid_params)

        data= pd.read_csv(path, skiprows= sk, sep= sep)
        N_data= data.shape[0]
        data['datetime']= [dt.strptime(data.iloc[i][valid['c_Date']]+' '+
                                       data.iloc[i][valid['c_Time']],
                                       valid['f_Date']+' '+valid['f_Time'])
                    for i in range(N_data)]
        data.drop([valid.c_Date, valid.c_Time], axis=1, inplace=True)
        data.set_index('datetime', inplace=True)
        return data 
    

class ColumnsFormat(Date):
    def format(self, path:str, sep:str=' ', sk:int=0, **kwargs):
        valid_params= ['c_Year', 'c_Month', 'c_Day', 
                      'c_Hour', 'c_Minute', 'c_Second', 
                      'f_Year', 'f_Month', 'f_Hour']
        valid= checkKwargs(kwargs, valid_params)
        data= pd.read_csv(path, skiprows= sk, sep= sep, header=None)
        N_data= data.shape[0]
        data['datetime']= [dt.strptime(str(int(data.iloc[i][valid['c_Year']]))+'/'+
                                       str(int(data.iloc[i][valid['c_Month']]))+'/'+
                                       str(int(data.iloc[i][valid['c_Day']]))+' '+
                                       str(int(data.iloc[i][valid['c_Hour']]))+':'+
                                       str(int(data.iloc[i][valid['c_Minute']]))+':'+
                                       str(int(data.iloc[i][valid['c_Second']])),
                                       valid['f_Year']+'/'+
                                       valid['f_Month']+'/%d '+
                                       valid['f_Hour']+':%M:%S')
                    for i in range(N_data)]
        data.drop([valid['c_Year'], valid['c_Month'], valid['c_Day'], 
                   valid['c_Hour'], valid['c_Minute'], valid['c_Second']], axis=1, inplace=True)
        data.set_index('datetime', inplace=True)
        return data  


class DayTimeFormat(Date):
    def format(self, path:str, sep:str=' ', sk:int=0, **kwargs):
        valid_params= ['i_Year', 'i_Month', 
                       'c_Day', 'c_Time', 
                       'f_Time']
        valid= checkKwargs(kwargs, valid_params)

        data= pd.read_csv(path, skiprows= sk, sep= sep)
        N_data= data.shape[0]

        data['datetime']= [dt.strptime(str(valid['i_Year'])+'/'+
                                       str(valid['i_Month'])+'/'+
                                       str(data.iloc[i][valid['c_Day']])+
                                       ' '+
                                       data.iloc[i][valid['c_Time']],
                                       '%Y/%m/%d '+ valid['f_Time'])
                    for i in range(N_data)]
        data.drop([valid['c_Day'], valid['c_Time']], axis=1, inplace=True)
        data.set_index('datetime', inplace=True)
        return data 


def GetDate(format_date: str) -> Date:
    formatters = {
        "DateTime": DateTimeFormat(),
        "Datetime": DateAndTimeFormat(),
        "Columns":  ColumnsFormat(),
        "DayTime":  DayTimeFormat()
    }
    if format_date not in formatters:
        raise ValueError(f"Unknown format: {format_date}")

    return formatters[format_date]