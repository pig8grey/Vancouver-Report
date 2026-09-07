#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 08:30:00 2024

@author: jeff
"""


import os
import sys
import glob
import obspy
import obspy.signal.filter
import scipy
import gc
import numpy as np
import matplotlib.pyplot as plt 
import matplotlib
from datetime import timedelta
import csv
from obspy import UTCDateTime, read_inventory,Stream
from datetime import datetime, timedelta, timezone
import matplotlib.dates as mdates
from multiprocessing import Pool
import pandas as pd
from meteostat import Hourly
from zoneinfo import ZoneInfo
from matplotlib.patches import Rectangle
from scipy.signal import lfilter,detrend
from astral.sun import sun
from astral import LocationInfo
from collections import deque
from obspy.signal.filter import envelope
from geopy.distance import geodesic
import math
from obspy.taup import TauPyModel
from obspy.geodetics import locations2degrees

BRIDGE_LAT = 49.3025
BRIDGE_LON = -123.0261

P_WAVE_SPEED = 6.0
S_WAVE_SPEED = 3.5
myZone=ZoneInfo("America/Vancouver")
isTrain=False
# isTrain=True
vp=6
vs=3.4
mytime=datetime.now()-timedelta(days=1)

# mytime=datetime.now()-timedelta(days=1)
# mytime=datetime.now()-timedelta(days=0)


mytime=UTCDateTime(2026,9,6)
report_number=mytime.strftime("%B")
print('Train?: ',isTrain)
sensorInfo={'PB':'Thornton Tunnel North Entrance','FR':'Fraser River','SN': 'Second Narrow','LU': 'Lulu Island',
            'PBVAN':'Thornton Tunnel North Entrance','FRVAN':'Fraser River','SNVAN': 'Second Narrow','LUVAN': 'Lulu Island'}
o_info={'BHZ':'Vertical','BHE':'East','BHN':'North'}
matplotlib.use('agg')
res=(1100,1250)

# mytime=UTCDateTime(2025,5,2)
tz=7
sn_cord=(49.29569, -123.02444)
fr_cord=(49.20913, -122.89658)



myZone=ZoneInfo("America/Vancouver")


myyear='{}'.format(mytime.year)
mymonth=f'{mytime.month:02}'
myday=f'{mytime.day:02}'


nexttime=mytime+timedelta(days=1)
myyear2='{}'.format(nexttime.year)
mymonth2=f'{nexttime.month:02}'
myday2=f'{nexttime.day:02}'


if isTrain: df=pd.read_csv(f'/home/jeff/van/trains/VA_{myyear}_{mymonth}_{myday}_logs.csv',sep=',',index_col=False)
else:df=pd.read_csv(f'/home/jeff/van/VA_{myyear}_{mymonth}_{myday}_logs.csv',sep=',',index_col=False)

print(myyear,mymonth,myday)




# df=df[df.notna().all(1)]


# pt=df.pivot_table(index=['Start Date (PST)','Start Time (PST)'],              
# columns=['Box ID',], values=['Z(+ve)', 'Z(-ve)','North(+ve)','South(-ve)',
#         'East(+ve)','West(-ve)'])


        
# pt=pt[pt.notna().all(1)]
# dates=pt.index.values
# evtend=[]
# anend=[]


# for i,v in enumerate(pt.index.values):
#     asd=df[df['Start Time (PST)']==pt.index.values[i][-1]]
#     mt=max(asd['End Time (PST)'])
#     evtend.append(UTCDateTime(mt))




    
# cond = df['Start Time (PST)'].isin(pt.index.get_level_values(1))
# df=df.drop(df[cond].index, inplace = False)
    

# temp_df=df.drop(df[cond].index, inplace = False)

# mydate=[UTCDateTime('{}T{}'.format(d[0],d[1])) for d in dates]
# antime=[UTCDateTime(f'{myyear}/{mymonth}/{myday}T{currenttime}') for currenttime in temp_df['Start Time (PST)'].to_list()]
# anend=[UTCDateTime(currenttime) for currenttime in temp_df['End Time (PST)'].to_list()]
# antime=antime[0:4]
# anend=anend[0:4]



def changeTime(st,myZone=ZoneInfo("America/Vancouver")):
    for i,tr in enumerate(st):
        t=tr.stats.starttime.datetime.replace(tzinfo=timezone.utc)
        st[i].stats.starttime=UTCDateTime(t.astimezone(myZone).strftime("%Y%m%d%H%M%S"))

        if tr.stats.station=='040':tr.stats.station='BWE'
        if tr.stats.station=='042':tr.stats.station='BEA'
        if tr.stats.station=='089':tr.stats.station='TEA'
        if tr.stats.station=='074':tr.stats.station='TWE'
        
    return st



class CNPlotter():
    
    __slots__='files2','files','disst','stst','vst','vfiles','vfiles2','accst'
    def __init__(self,mytime):
        self.files2=['/home/jeff/acc/PBVA/Acc_PBVA_VA_{}_{}_{}.mseed'.format(
                    myyear,
                    mymonth,
                    myday,),
          '/home/jeff/acc/SNVAN/Acc_SNVAN_VA_{}_{}_{}.mseed'.format(
                    myyear,
                    mymonth,
                    myday,),   
          '/home/jeff/acc/LUVAN/Acc_LUVAN_VA_{}_{}_{}.mseed'.format(
                    myyear,
                    mymonth,
                    myday,),   
            ] 
        self.files=['/home/jeff/acc/PBVAN/Acc_PBVAN_VA_{}_{}_{}.mseed'.format(
                    myyear2,
                    mymonth2,
                    myday2,),
          '/home/jeff/acc/SNVAN/Acc_SNVAN_VA_{}_{}_{}.mseed'.format(
                    myyear2,
                    mymonth2,


                    myday2,),   
          '/home/jeff/acc/LUVAN/Acc_LUVAN_VA_{}_{}_{}.mseed'.format(
                    myyear2,
                    mymonth2,
                    myday2,),   
            ] 
        self.vfiles=['/home/jeff/cndata/PBVAN/PBVAN_VA_{}_{}_{}.mseed'.format(
                    myyear,
                    mymonth,
                    myday,),
          '/home/jeff/cndata/SNVAN/SNVAN_VA_{}_{}_{}.mseed'.format(
                    myyear,
                    mymonth,
                    myday,),   
          '/home/jeff/cndata/LUVAN/LUVAN_VA_{}_{}_{}.mseed'.format(
                    myyear,
                    mymonth,
                    myday,),   


            ] 


        self.vfiles2=['/home/jeff/cndata/PBVAN/PBVAN_VA_{}_{}_{}.mseed'.format(
                    myyear2,
                    mymonth2,
                    myday2,),
          '/home/jeff/cndata/SNVAN/SNVAN_VA_{}_{}_{}.mseed'.format(
                    myyear2,
                    mymonth2,
                    myday2,),   
          '/home/jeff/cndata/LUVAN/LUVAN_VA_{}_{}_{}.mseed'.format(
                    myyear2,
                    mymonth2,
                    myday2,),   


            ] 


        
        self.disst=obspy.Stream()
        self.accst=obspy.Stream()
        self.vst=obspy.Stream()
        self.stst=obspy.Stream()
        
            
            
    def plotSt2(self,st,debug=False,avs=''):
        daily=False
        if st:
            if debug: 
                est=st.copy()
                est.filter('lowpass',freq=1.0)
            
            start_date = st[0].stats.starttime
            sampling_rate = st[0].stats.sampling_rate
            print()
            if st[0].stats.npts>3*3600*1000:daily=True
            # Calculate time values
            sensor=st[0].stats.station
            plt.rcParams['figure.dpi'] = 80
            plt.rcParams['figure.figsize'] = [8.0, 9.0]
            # Create subplots
            
            fig, axes = plt.subplots(nrows=3, ncols=1, sharex=True, figsize=(8.0, 9.0))
            
            # Plot the first waveform
            if avs=='v':
                axes[0].plot(st.select(channel='B*Z')[0].times(type="matplotlib"), 
                             st.select(channel='B*Z')[0].data*1000.0, label=f'{sensor}\nVertical')
            else:
                axes[0].plot(st.select(channel='B*Z')[0].times(type="matplotlib"), 
                             st.select(channel='B*Z')[0].data, label=f'{sensor}\nVertical')
            if debug:
                axes[0].plot(est.select(channel='B*Z')[0].times(type="matplotlib"), 
                             envelope(est.select(channel='B*Z')[0].data), label=f'{sensor}\nVertical')
            axes[0].set_ylabel('Accleration (%g)')
            axes[0].legend(loc="upper left")

            if len(st)>1:
                # Plot the second waveform
                if (len(st.select(channel='*N'))):
                    
                    if avs=='v':
                        axes[1].plot(st.select(channel='B*N')[0].times(type="matplotlib"), 
                                     st.select(channel='B*N')[0].data*1000.0, label=f'{sensor}\nNorth')
                    else:
                        axes[1].plot(st.select(channel='B*N')[0].times(type="matplotlib"), 
                                     st.select(channel='B*N')[0].data, label=f'{sensor}\nNorth')
                    axes[1].legend(loc="upper left")
                    
                    # Plot the third waveform
                if (len(st.select(channel='*E'))):
                    if avs=='v':
                        axes[2].plot(st.select(channel='B*E')[0].times(type="matplotlib"), 
                                     st.select(channel='B*E')[0].data*1000.0, label=f'{sensor}\nEast')
                    else:
                        axes[2].plot(st.select(channel='B*E')[0].times(type="matplotlib"), 
                                     st.select(channel='B*E')[0].data, label=f'{sensor}\nEast')
                    axes[2].set_xlabel('Time (PST)')

            
            if st.select(channel='B*E')[0].stats.npts>3600*1000:
                axes[2].xaxis.set_major_locator(mdates.HourLocator(interval=3))  # Set ticks every 6 hours
            else:
                axes[2].xaxis.set_major_locator(mdates.MinuteLocator(interval=1)) 
                
            axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            axes[2].legend(loc="upper left")
            
            if avs=='a':
                axes[0].set_ylabel('Accleration (%g)')
                axes[1].set_ylabel('Accleration (%g)')
                axes[2].set_ylabel('Accleration (%g)')
            if avs=='v':
                axes[0].set_ylabel('Velocity (mm/s)')
                axes[1].set_ylabel('Velocity (mm/s)')
                axes[2].set_ylabel('Velocity (mm/s)')
            if avs=='s':
                 axes[0].set_ylabel('Displacement (mm)')
                 axes[1].set_ylabel('Displacement (mm)')   
                 axes[2].set_ylabel('Displacement (mm)')   
                 
                 
            if debug:
                axes[1].plot(est.select(channel='B*N')[0].times(type="matplotlib"), 
                             envelope(est.select(channel='B*N')[0].data), label=f'{sensor}\nVertical')
                axes[2].plot(st.select(channel='B*E')[0].times(type="matplotlib"), 
                             envelope(est.select(channel='B*E')[0].data), label=f'{sensor}\nVertical')    
                

                    

            # Customize the overall plot
            plotname=st[0].stats.starttime.strftime('%Y%m%d%H%M')
            plt.subplots_adjust(hspace=0, wspace=0)  # Adjust the right margin as needed
            plt.tight_layout()  # Increase padding between subplots
            fig.savefig(f'/home/jeff/van/plots/{myyear}_{mymonth}_{myday}/{sensor}-{plotname}-{avs}.png')
            plt.clf()
            plt.close(fig)
            gc.collect()
            return
        
        
    def filter_AC(self):
        for i,st in enumerate(self.stst):
            if st:
                self.stst[i]=st.filter('lowpass',freq=35.0)
                self.stst[i]=st.filter('lowpass',freq=35.0)
                self.stst[i]=st.slice(st[i].stats.starttime+timedelta(minutes=5),st[i].stats.endtime)
            

            
    # def convE(self,st):
    #     Gf=2.08
    #     Rg=130.0
    #     Rl=0.5
    #     Vex=5.0
    #     gain=16.0
    #     result=st.copy()
    #     for i,tr in enumerate(st):
    #         volt=-1.0*tr.data*2.5/2**31/gain
    #         result[i].data=(-4.0*(volt/Vex)/(2.08*(1.0+2.0*(volt/Vex))))*(1.0+Rl/Rg)
    #     return result
    
    def convE(self,st):
        Gf=2.08
        Rg=120.0
        Rl=0.5
        Vex=5.0
        gain=16.0
        result=st.copy()
        for i,tr in enumerate(st):
            volt=-1.0*tr.data*2.5/2**31/gain
            # result[i].data=(-4.0*(volt/Vex)/(2.08*(1.0+2.0*(volt/Vex))))*(1.0+Rl/Rg)
            result[i].data=(-4.0/Gf)*(volt/Vex)
        return result    

    
    def plotDay(self):
        # for i,st in enumerate(self.disst):self.plotSt2(st) 
        with Pool(processes=4) as pool:
            pool.map(self.plotSt2,self.disst)
        return
            
    def getStress(self):
        self.filter_AC()
        with Pool(processes=4) as pool:
            self.stst=pool.map(self.convE,self.stst)
        # for i,st in enumerate(self.stst):self.stst[i]=self.convE(st)
        
        return self.stst
            

            
cn=CNPlotter(mytime)     


    

    
    
def changeTime(st,myZone=ZoneInfo("America/Vancouver")):
    for i,tr in enumerate(st):
        t=tr.stats.starttime.datetime.replace(tzinfo=timezone.utc)
        t=tr.stats.starttime.datetime.replace(tzinfo=timezone.utc)
        st[i].stats.starttime=UTCDateTime(t.astimezone(myZone).strftime("%Y%m%d%H%M%S"))
    return st



        
def corrSB(data,prev):
    
    x1,x2,xx1,xx2,xxx1,xxx2,xxxx1,xxxx2=prev

    nump=[1,-2,1]
    denp=[1,-1.999912035,0.99991204]
        
    num1=[1.0,-1.914500,0.918283]
    den1=[1.0,-1.99808,0.998084]  
    

    
    num2=[1,-1.999996845429212, 0.999996845429212]
    den2=[1,-1.996481293746107,0.996487599189977]        
    
    [data,x12]=lfilter(num1,den1,data,zi=[x1,x2])
    x1,x2=x12
    [data,xx12]=lfilter(nump,denp,data,zi=[xx1,xx2])
    xx1,xx2=xx12
    data=np.cumsum(data)
    [data,xxx12]=lfilter(num2,den2,data,zi=[xxx1,xxx2])
    xxx1,xxx2=xxx12
    # [data,xxxx12]=lfilter(num2,den2,data,zi=[xxxx1,xxxx2])
    # xxxx1,xxxx2=xxxx12
    data=data/2**31*2.5/20.5
    

    return [x1,x2,xx1,xx2,xxx1,xxx2,data]



    
def gettime(path):

    combtime=path.split('.')[0]


    if sys.platform.startswith('win'):
        checklen=combtime.split('\\')
    else:
        checklen=combtime.split('/')
    

    if len(checklen)<2:
        checklen = combtime.split('/')


    try:    
        if len(checklen[-1])>5:
            a=[s for s in checklen[-1].split('_') if s.isdigit()]
            starttime=datetime.strptime(a[0], '%Y%m%d%H%M%S')

            # ID=checklen[-2]
        else:
            dirs=path.split('/')
            
            if len(dirs)<2:
                dirs=path.split('\\')
            hms=dirs[-2]
            ymd=dirs[-3]
            hd=dirs[-1].split('.')[0]
            year=2000+int(ymd[0:2])
            month=int(ymd[2:4])
            day=int(ymd[4:])
            hour=int(hms[0:2])
            minute=int(hms[2:4])
            second=int(hms[4:])
            
            starttime=datetime(year,month,day,hour,minute,second)
            
            starttime=starttime+timedelta(hours=int(hd))


            # ID=checklen[-4]

       
        return starttime
    except:
        return 0
    
def findDistance(coord1, coord2):
    """
    Calculate the distance in kilometers between two coordinates.
    
    Args:
        coord1: Tuple of (latitude, longitude) in degrees for the first point.
        coord2: Tuple of (latitude, longitude) in degrees for the second point.
    
    Returns:
        Distance in kilometers between the two points.
    """
    R = 6371  # Radius of the Earth in kilometers

    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance


def OriginalCN(data,prev=np.zeros(8)):
    
    x1,x2,xx1,xx2,xxx1,xxx2,xxxx1,xxxx2=prev

    nump=[1,-2,1]
    denp=[1,-1.999912035,0.99991204]
        
    num1=[1.0,-1.914500,0.918283]
    den1=[1.0,-1.99808,0.998084]  
    

    
    num2=[1,-2,1]
    den2=[1,-1.9991203,0.9991207]          
    
    [data,x12]=lfilter(num1,den1,data,zi=[x1,x2])
    x1,x2=x12
    [data,xx12]=lfilter(nump,denp,data,zi=[xx1,xx2])
    xx1,xx2=xx12
    
    [data,xxx12]=lfilter(num2,den2,data,zi=[xxx1,xxx2])
    xxx1,xxx2=xxx12
    [data,xxxx12]=lfilter(num2,den2,data,zi=[xxxx1,xxxx2])
    xxxx1,xxxx2=xxxx12
    
    data=data/2**31*2.5/20.5
    

    return [x1,x2,xx1,xx2,xxx1,xxx2,data]


def getAcc(data):
    return 1000.0*np.diff(data)/9.806*100.0

def getDis(data):
    return np.cumsum(data)
    
def downsample(factor,values):
    buffer_ = deque([],maxlen=factor)
    downsampled_values = []
    for i,value in enumerate(values):
        buffer_.appendleft(value)
        if (i-1)%factor==0:
            #Take max value out of buffer
            # or you can take higher value if their difference is too big, otherwise just average
            downsampled_values.append(max(max(buffer_), min(buffer_), key=abs))
    return np.array(downsampled_values)


def readStream(mypath):
    a=Stream()
    if os.path.isfile(mypath[0]):a=obspy.read(mypath[0])    
    if os.path.isfile(mypath[1]):a.extend(obspy.read(mypath[1]))
    a=a.trim(UTCDateTime(f'{myyear}-{mymonth}-{myday}T00:00'),
             UTCDateTime(f'{myyear2}-{mymonth2}-{myday2}T07:59:59.999'))
    return a

def format_number(value):
    # Format the number to have at most 5 decimal places
    return "{:.7f}".format(value)




def plotWeather(df):
    plt.clf()
    plt.rcParams['figure.figsize'] = [8.0, 9.0]
    plt.figure().set_figheight(9)
    plt.rcParams['figure.dpi'] = 80
    myFmt = mdates.DateFormatter('%H:%M')
    plt.gca().xaxis.set_major_formatter(myFmt)

    # plt.title(f'{myyear}-{mymonth}-{myday}, Hourly Temperature °C')
    plt.plot_date(df.index.to_numpy(),df.values,'-')
    plt.ylabel('Temperature °C')
    plt.xlabel('Time')
    plt.savefig(f'/home/jeff/van/plots/{myyear}_{mymonth}_{myday}/{myyear}-{mymonth}-{myday}_temperature.png')
    return
    


def writeLogcsv(data,filename,mode='a'):
    print(data)
    file_exists = os.path.exists(filename)

    with open(filename, mode, newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        
        if isinstance(data, dict):
            formatted_data = [format_number(value) if isinstance(value, float) else value for value in data.values()]
            csv_writer.writerow(formatted_data)
        elif isinstance(data, list):
            formatted_data = [format_number(value) if isinstance(value, float) else value for value in data]
            csv_writer.writerow(formatted_data)

    return

def writecsv(data,filename):
    #filename=f'./beaspecial.csv'
    file_exists = os.path.exists(filename)
    header=[]
    
    with open(filename, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        
        if not file_exists:
            # If the file didn't exist, write the header row
            if header:
                csv_writer.writerow(header)

        if isinstance(data, dict):
            formatted_data = [format_number(value) if isinstance(value, float) else value for value in data.values()]
            csv_writer.writerow(formatted_data)
        elif isinstance(data, list):
            formatted_data = [format_number(value) if isinstance(value, float) else value for value in data]
            csv_writer.writerow(formatted_data)

    return

def plotEvt(st, begin=[],finish=[],isShow=False,res=res,avs=''):
    
    result={}
    
    if not st: 
        result.update({f'East':0})
        result.update({f'North':0})
        result.update({f'Vertical':0})
        return result
    print(begin,finish)
    for i,funct in enumerate(begin):
        print(funct)
        a=st.slice(funct-timedelta(minutes=0),
                   finish[i])
        # print(a)
        if any(a):
            t=a[0].stats.starttime
            cn.plotSt2(a,avs=avs)
            info=(f'{sensorInfo[a[0].stats.station]}')
            for i,tr in enumerate(a):
                if avs=='v':
                    result.update({f'{o_info[tr.stats.channel]}':tr.max()*1000.0})
                else:
                    result.update({f'{o_info[tr.stats.channel]}':tr.max()})
                
            # a.select(sampling_rate=1000).plot(outfile='/home/jeff/van/plots/{}_{}_{}/{}-{}.png'.format(
            #     t.year,
            #     str(t.month).zfill(2),
            #     str(t.day).zfill(2),
            #     st[0].stats.station,
            #     (funct-timedelta(minutes=2)).strftime('%Y%m%d%H%M')),
            #     show=isShow,size=res,equal_scale=False)
        else: print('Empty Stream')
    return result


    



def rotate_and_reverse_horizontal(vectors, angle_degrees):
    """
    Rotates a 3D vector around the Z-axis by the given angle and reverses polarity
    of the horizontal (East and North) components only.

    Parameters:
        vector: array-like, shape (3,)
            The input vector [East, North, Up].
        angle_degrees: float
            The rotation angle in degrees. Positive is counter-clockwise.

    Returns:
        transformed_vector: np.ndarray, shape (3,)
            The transformed vector [East, North, Up].
    """
    # Extract East, North, Up components
    east, north, up = vectors
    vectors = np.array(vectors) 
    # Convert angle to radians
    theta = np.radians(angle_degrees)
    Rz = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta),  np.cos(theta)]
    ])  # shape (2,2)

    # Rotate horizontal (East, North) components
    horizontal = vectors[:2, :]  # shape (2, N)
    rotated_horizontal = Rz @ horizontal  # matrix multiplication (2x2 @ 2xN) => (2xN)
    rotated_horizontal = -rotated_horizontal
    # Keep Z (Up) unchanged
    rotated_vectors = np.vstack((rotated_horizontal, vectors[2, :]))  # shape (3, N)

    return rotated_vectors





def toVel(st):
    if not st: return
    for i,tr in enumerate(st):
        st[i].data=OriginalCN(tr.data)[-1]
    if st[0].stats.station=='FR':
        print("Rotating Fraser River")
        vector=[st.select(channel='*E')[0].data,st.select(channel='*N')[0].data,st.select(channel='*Z')[0].data]
        rotated_vector = rotate_and_reverse_horizontal(vector, -15)
        for i,tr in enumerate(st):
            if tr.stats.channel=='BHZ':
                st[i].data=rotated_vector[2]
            if tr.stats.channel=='BHN':
                st[i].data=rotated_vector[1]
            if tr.stats.channel=='BHE':
                st[i].data=rotated_vector[0]
    return st
   
def toAcc(st):
    if not st: return
    acc=st.copy()
    for i,tr in enumerate(acc):
        acc[i].data=getAcc(acc[i].data)
    return acc
 
def toDis(st):
    if not st: return
    dis=st.copy()
    for i,tr in enumerate(dis):
        dis[i].data=getDis(dis[i].data)
    dis=dis.filter('highpass',freq=0.1)
    return dis


def getMaxMin(st,mt='s'):
    result=[]
    
    t=st[0].stats.starttime
    z=0
    lon=0
    lat=0
    
    
    if len(st)>1:
        try:
            if mt=='s':
                z=st.select(channel='B*1')[0].data
                lon=st.select(channel='B*2')[0].data
                lat=st.select(channel='B*3')[0].data
            if mt=='d':
                z=st.select(channel='*Z')[0].data
                lat=st.select(channel='*E')[0].data
                lon=st.select(channel='*N')[0].data
        except:pass
        t=t
        if mt=='d':t=t+timedelta(minutes=1)
        
        result.append([t.strftime('%Y/%m/%d'),
                       t.strftime('%H:%M:%S'),
                       st[0].stats.station,
                       np.max(z),
                       np.max(lon),np.max(lat),
                       np.min(z),np.min(lon)
                       ,np.min(lat),
                       st[0].stats.endtime.strftime('%Y/%m/%dT%H:%M:%S')])
    else:

        z=st.select(channel='B*Z')[0].data
        
        t=t
        result.append([t.strftime('%Y/%m/%d'),
                       t.strftime('%H:%M:%S'),
                       st[0].stats.station,
                       np.max(z),
                       0,0,
                       np.min(z),0
                       ,0,
                       st[0].stats.endtime.strftime('%Y/%m/%dT%H:%M:%S')])
    return result

        
def fixCorrupt(st):
    window = np.hanning(st[0].stats.npts)
    # flattop_window=scipy.signal.nuttall(st[0].stats.npts)
    for i,tr in enumerate (st):
        st[i].data=st[i].data * window 
        # st[i].data=st[i].data * flattop_window 
    return st
        
def trimStream(st,current,evttimes,antimes):
        
    for i,funct in enumerate(evttimes):
        st=st.cutout(funct[0],funct[1])
        
    # for i,ant in enumerate(antimes):
    #     st=st.cutout(ant[0],ant[1])    
    st=st.merge(method=0,fill_value=0)

    return st

def floor_to_minute(utc_time):
    """Rounds an ObsPy UTCDateTime DOWN to the exact minute (00 seconds)."""
    return UTCDateTime(utc_time.year, utc_time.month, utc_time.day, utc_time.hour, utc_time.minute)

def ceil_to_minute(utc_time):
    """Rounds an ObsPy UTCDateTime UP to the next full minute (00 seconds)."""
    floored = floor_to_minute(utc_time)
    if utc_time > floored:
        return floored + 60.0 # Add exactly 60 seconds
    return floored

def calculate_sensor_windows(row):
    

    origin = UTCDateTime(row['Start Time (UTC)'])
    model = TauPyModel(model="iasp91")
    eq_lat = row['lat']
    eq_lon = row['long']
    
    # 1. FIX: Force the pandas cell to a string, strip "UTC", and use ObsPy's native time object.
    # This prevents the Timestamp vs Int crash entirely.

    # 2. Convert coordinate distance to degrees for the TauP model
    dist_degree = locations2degrees(eq_lat, eq_lon, BRIDGE_LAT, BRIDGE_LON)

    # 3. Assume 10km depth if depth wasn't scraped
    depth_km = row.get('Depth_km', 10.0)

    # 4. Ask the model for P and S wave travel times
    arrivals = model.get_travel_times(source_depth_in_km=depth_km, 
                                      distance_in_degree=dist_degree, 
                                      phase_list=["p", "P", "s", "S", "Pn", "Sn"])

    p_arrivals = [a.time for a in arrivals if a.name.lower().startswith('p')]
    s_arrivals = [a.time for a in arrivals if a.name.lower().startswith('s')]


    p_wave_travel_time = min(p_arrivals)
    s_wave_travel_time = min(s_arrivals)

    # 5. Calculate exact ETA (ObsPy UTCDateTime + float = new time in seconds)
    p_wave_eta = origin + p_wave_travel_time
    s_wave_eta = origin + s_wave_travel_time

    # 10s pre-buffer, 30s post-buffer
    window_start = p_wave_eta - 60.0
    window_end = s_wave_eta + 60.0

    window_start=window_start.datetime.replace(tzinfo=timezone.utc)
    window_end= window_end.datetime.replace(tzinfo=timezone.utc)
    
    window_start=UTCDateTime(window_start.astimezone(myZone).strftime("%Y%m%d%H%M%S"))
    window_end=UTCDateTime(window_end.astimezone(myZone).strftime("%Y%m%d%H%M%S"))
    
    
    return floor_to_minute(window_start),ceil_to_minute(window_end)
    

def removefft(signal):
    fs = 1000.0  # Sampling rate in Hz (e.g., 1 sample per second)

    
    # FFT
    n = len(signal)
    fft_vals = np.fft.fft(signal)
    freqs = np.fft.fftfreq(n, d=1/fs)
    
    # Create a mask for 0.05–0.2 Hz (both positive and negative freqs)
    # mask = (np.abs(freqs) >= 0.05) & (np.abs(freqs) <= 1.0)
    mask = np.abs(freqs) <= 1.0
    # Zero out frequencies outside the range
    filtered_fft = fft_vals * mask
    
    # Inverse FFT to get filtered time-domain signal
    filtered_signal = np.fft.ifft(filtered_fft).real
    return filtered_signal


print('Reading')
with Pool(processes=4) as pool:
    cn.vst=pool.map(readStream,zip(cn.vfiles,cn.vfiles2))
    
print('Changing Time')
with Pool(processes=4) as pool:
    cn.vst=pool.map(changeTime,cn.vst)

td=4
if isTrain: td=14
a=Stream()

for index, row in df.iterrows():
    startTime=UTCDateTime(row['Start Time (UTC)'])
    startTime=startTime.datetime.replace(tzinfo=timezone.utc)
    startTime=startTime.astimezone(myZone)
    startTime=UTCDateTime(startTime.replace(tzinfo=None))   
    a+=cn.vst[1].slice(startTime-timedelta(minutes=10),startTime+timedelta(minutes=20))
    mytime,myend=calculate_sensor_windows(row)
    
cn.vst[1]=a

for i,st in enumerate(cn.vst):
    cn.vst[i]=cn.vst[i].select(sampling_rate=1000).merge(method=0,fill_value=0)
    # cn.vst[i]=cn.vst[i].filter('lowpass',freq=1)
# for i,st in enumerate(cn.vst):
#     for j,tr in enumerate(st):
#         cn.vst[i][j].data=removefft(cn.vst[i][j].data)
# cn.vst[2]=cn.vst[2].slice(startTime-timedelta(minutes=10),startTime+timedelta(minutes=20))    
for i,st in enumerate(cn.vst):
    cn.vst[i]=toVel(cn.vst[i])  


for index, row in df.iterrows():
    startTime=UTCDateTime(row['Start Time (UTC)'])
    startTime=startTime.datetime.replace(tzinfo=timezone.utc)
    startTime=startTime.astimezone(myZone)
    startTime=UTCDateTime(startTime.replace(tzinfo=None))   
    mytime,myend=calculate_sensor_windows(row)
    
    mydir='/home/jeff/van/plots/{}_{}_{}'.format(myyear,
                mymonth,
                myday,)
    
    if not os.path.isdir(mydir):os.mkdir(mydir)

    print('Plotting')

    velMax=[[0,0,0],[0,0,0],[0,0,0]]
    info=['Thornton Tunnel North Entrance','Second Narrow','Lulu Island']
    for i,st in enumerate(cn.vst):

        print(mytime,myend)
        velMax[i]=plotEvt(cn.vst[i],[mytime],[myend],avs='v')

    maxdf=pd.DataFrame(velMax,index=info)
    if isTrain:
        maxdf.to_csv(f'vel{report_number}_train.csv',mode='a',index_label=f'{startTime}')
    else:
        maxdf.to_csv(f'vel{report_number}.csv',mode='a',index_label=f'{startTime}')

cn.accst=cn.vst.copy() 

for i,st in enumerate(cn.vst):
       cn.accst[i]=toAcc(cn.vst[i])   
       
for index, row in df.iterrows():
    startTime=UTCDateTime(row['Start Time (UTC)'])  
    startTime=startTime.datetime.replace(tzinfo=timezone.utc)
    startTime=startTime.astimezone(myZone)
    startTime=UTCDateTime(startTime.replace(tzinfo=None))
    mytime,myend=calculate_sensor_windows(row)
    
    accMax=[[0,0,0],[0,0,0],[0,0,0]]
    info=['Thornton Tunnel North Entrance','Second Narrow','Lulu Island']

        
    for i,st in enumerate(cn.accst):
        accMax[i]=plotEvt(cn.accst[i],[mytime],[myend],avs='a')
    maxdf=pd.DataFrame(accMax,index=info)
    if isTrain:
        maxdf.to_csv(f'acc{report_number}_train.csv',mode='a',index_label=f'{startTime}')
    else:
        maxdf.to_csv(f'acc{report_number}.csv',mode='a',index_label=f'{startTime}')
    

cn.accst=[]



cn.disst=cn.vst.copy() 


for i,st in enumerate(cn.vst):
       cn.disst[i]=toDis(cn.vst[i])   
       
for index, row in df.iterrows():
    startTime=UTCDateTime(row['Start Time (UTC)'])
    startTime=startTime.datetime.replace(tzinfo=timezone.utc)
    startTime=startTime.astimezone(myZone)
    startTime=UTCDateTime(startTime.replace(tzinfo=None))
    mytime,myend=calculate_sensor_windows(row)
    
    disMax=[[0,0,0],[0,0,0],[0,0,0]]
    info=['Thornton Tunnel North Entrance','Second Narrow','Lulu Island']

        
    for i,st in enumerate(cn.disst):
        disMax[i]=plotEvt(cn.disst[i],[mytime],[myend],avs='s')
    maxdf=pd.DataFrame(disMax,index=info)
    if isTrain:
        maxdf.to_csv(f'dis{report_number}_train.csv',mode='a',index_label=f'{startTime}')
    else:
        maxdf.to_csv(f'dis{report_number}.csv',mode='a',index_label=f'{startTime}')



        
        

    
















