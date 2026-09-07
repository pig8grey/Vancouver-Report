#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  6 21:51:48 2024

@author: jeff
"""


import os
import re
import weasyprint
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta, timezone
import glob
from obspy import UTCDateTime,Stream
import pandas as pd
import plotly.graph_objects as go
import plotly.io as io
from plotly.offline import plot
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from itertools import product,combinations
from bs4 import BeautifulSoup
from weasyprint import HTML,CSS
from functools import reduce
import time
from zoneinfo import ZoneInfo
isTrain=False
#critical date before Aug 10 to PST

# isTrain=True
current=datetime.now()-timedelta(days=1)
# current=datetime.now()-timedelta(days=0)
current=datetime(2026,9,6,0,0)
templates_dir='/home/jeff/van/web'
myCSS='/home/jeff/van/web/report.css'
DEST_DIR = f'./plots/{current.year}_{current.month}_{current.day}/\
{current.year}_{current.month}_{current.day}.html'
env = Environment( loader = FileSystemLoader(templates_dir) )

template = env.get_template('report.html')


outputfilename=f'{current.year}_{current.month}_{current.day}.pdf'

if isTrain:
    df=pd.read_csv(f'/home/jeff/van/trains/VA_{current.year}_{current.month:02}_{current.day:02}_logs.csv',sep=',',index_col=False)
else:
    df=pd.read_csv(f'/home/jeff/van/VA_{current.year}_{current.month:02}_{current.day:02}_logs.csv',sep=',',index_col=False)
    acc_info=pd.read_csv(f'acc{current.strftime("%B")}.csv',index_col=0,)
    vel_info=pd.read_csv(f'vel{current.strftime("%B")}.csv',index_col=0,)
    dis_info=pd.read_csv(f'dis{current.strftime("%B")}.csv',index_col=0,)
maxCol=lambda x: max(x.min(), x.max(), key=abs)


def sortTime(a):
    a=re.findall(r'\d{10,16}', a)[0]
    st=int(a)
    return st

def getTime(a):
    a=sortTime(a)
    st=UTCDateTime(str(a))
    st=st.strftime('%H:%M')
    return st


def makeSummary(df):
    coCode={'Power Banglo (E)':'#63bce5','Power Banglo(N)':'#63bce5','Power Banglo (Z)':'#63bce5',
            'Second Narrow (E)':'#f5b935','Second Narrow (N)':'#f5b935','Second Narrow (Z)':'#f5b935',
            'Fraser River (E)':'#4bac35','Fraser River (N)':'#4bac35','Fraser River (Z)':'#4bac35'}
    
    lrank={'Power Banglo (E)':9,'Power Banglo(N)':8,'Power Banglo (Z)':7,'Second Narrow (E)':6,
           'Second Narrow (N)':5,'Second Narrow (Z)':4,'Fraser River (E)':3,
           'Fraser River (N)':2,'Fraser River (Z)':1,
              }
    # print(df.max().to_frame().T.values)
    maxInd,maxVal=[df.max().to_frame().T.columns.values[1:],
                   df.max().to_frame().T.values[0][1:]]

    fig=go.Figure()

    df=df.tail(14)
    for i,v in enumerate(reversed(df.columns.values[1:])):
        fig.add_trace(
            go.Bar(
            y=df['Date'],
            x=df[v],
            name=v,
            textposition = "none", 
            marker_color=coCode[v],
            meta=v,
            orientation='h',
            legendrank=lrank[v],
            hovertemplate=
            "<b>%{meta}</b><br><br>" +
            "Time: %{x}<br>" +
            "Daily PPA(g): %{y}<br>" +
            "<extra></extra>"
            ),
            )
    fig.update_layout(

    margin={
        'l':0, #left margin
        'r':0, #right margin
        'b':0, #bottom margin
        't':0, #top margin
    },
    
    legend=dict(
    orientation="h",
    traceorder='reversed',
    uirevision=3,
    font=dict(
            family="Courier",
            size=12,
            color="black"
        )
    
    ),
    yaxis_title="Date (MST 00:00-23:59)",
    xaxis_title="Daily Maximum PPA in g",

    legend_title="Channels",

        
    font=dict(
        family="Courier New, monospace",
        size=14,
        color="RebeccaPurple"
    ) ) 
    # fig.update_layout(xaxis_range=[0,30])
    fig.update_yaxes(

    dtick=86400000
    )

    # for i,v in enumerate(maxInd[0:3]):
    #     fig.add_vline(x=maxVal[i], line_width=3, line_dash="dash", line_color=coCode[v])
    # plot(fig)
    # fig.write_html("Sep19.html")
    return fig








# def plotData(tr):
#     np.datetime64
#     mytime=[tr.stats.starttime+timedelta(microseconds=1000*i) for i in range(tr.stats.npts)]
    
#     mytime = matplotlib.dates.date2num(mytime)
#     plt.minorticks_on()
#     plt.grid(which='minor', axis='both',color='#DDDDDD', linestyle=':', linewidth=0.5)
#     plt.grid(which='major', axis='both',color='#AAAAAA', linewidth=0.8)
#     myFmt = mdates.DateFormatter('%H:%M:%S')
#     plt.plot(mytime,tr.data)
#     plt.gcf().autofmt_xdate()
#     plt.title('{}-{}-{}-{} Displcement (mm) VS Time'.format(box[tr.stats.station],tr.stats.channel))
#     plt.grid(True, which='both')
    
#     plt.gca().xaxis.set_major_formatter(myFmt)
#     plt.savefig('{}-{}-{}-{} Displcement (mm) VS Time'.format(
#         tr.stats.starttime.year,
#         str(tr.stats.starttime.month).zfill(2),
#         box[tr.stats.station],
#         tr.stats.channel,
#         )
#         ,dpi=500)
#     plt.show()
    
def gettime(path):

    combtime=path.split('.')[0]

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

        return starttime
    except:
        return 0
        return 0
    




def plotSt(st):
    st.plot(outfile='{}.png'.format(
        st[0].stats.station),
        show=False,)

# def plotEvt(st, begin=mydate,isShow=False):
    
#     for i,funct in enumerate(begin):

#         a=st.slice(funct-timedelta(minutes=1),
#                    funct+timedelta(minutes=10))
#         # print(a)
#         a.plot(outfile='{}-{}.png'.format(
#             st[0].stats.station,
#             a[0].stats.starttime.strftime('%Y%m%d%H%M')),
#             show=isShow,)
        









def colorTPT(df_html):
    soup = BeautifulSoup(df_html, 'html.parser')
    ind_rows = soup.find_all(['tr'])

    for i,tag in enumerate(ind_rows):
        if i==0: continue
        ele=tag.find_all(['th','td'])

        for j, indtag in enumerate(ele):
            if len(ele)==9:
                if j<=1:continue
            elif len(ele)==8:
                if j<=0: continue
            if i%2==1:indtag['class']='blue' 
            if i%2==0:indtag['class']='green'
                
    pt0_html=soup.decode_contents()
    return pt0_html

def colorPT(df_html):
    soup = BeautifulSoup(df_html, 'html.parser')
    ind_rows = soup.find_all(['tr'])

    for i,tag in enumerate(ind_rows):
        if i==0: continue
        ele=tag.find_all(['th','td'])
        for j, indtag in enumerate(ele):
            if len(ele)>9:
                if j<=1:continue
            elif len(ele)>8:
                if j==0: continue
            if i%2==1:indtag['class']='blue' 
            if i%2==0:indtag['class']='green'
                
    pt0_html=soup.decode_contents()
    return pt0_html

def colorCN(df_html):
    soup=BeautifulSoup(df_html, 'html.parser')
    ro=soup.find_all('tr')

    for i,v in enumerate(ro):
        if i==0: 
            mytgt=v.find_all('th')
            for j,ele in enumerate(mytgt):
                if j==0:continue
                if j%3==1:
                    ele['class']='blue'
                    continue
                if j%3==2:
                    ele['class']='yellow'
                    continue
                if j%3==0:
                    ele['class']='green'
                    continue
        mytgt=v.find_all('td')
        for j,ele in enumerate(mytgt):
            if j==0:continue
            if j%3==1:
                ele['class']='blue'
                continue
            if j%3==2:
                ele['class']='yellow'
                continue
            if j%3==0:
                ele['class']='green'
                continue

    my_html=soup.decode_contents()
    return my_html


def setupPlotly(pt):
    if pt.empty:return
    
    simpleElements =['Z',
                    'Longitudinal', 
                    'Lateral']
    boxes=['TEA','BEA','TWE','BWE']
    channelSim=[]
    for b,e in product(boxes,simpleElements):channelSim.append('{}-{}'.format(b,e))
    pt=pt[pt['TEA-Z(+ve)']>0.6]
    b=pt.values
    b=b.reshape(len(b),12,-1)
    startVal=np.min(b,axis=2)
    maxVal=np.max(b,axis=2)
    travel=-1*np.diff(b,axis=2).reshape(len(b),-1)
    ti=pt.index.values

    myt=['{}T{}'.format(d,t) for d,t in ti]

    return [startVal,travel,myt,channelSim,maxVal]

def getLowfreq(ar):
    i=0
    result=[]
    while i<len(ar):
        if 'train-enhanced' in ar[i]: 
            temp=ar.pop(i)
            result.append(temp)
        else:i+=1
    return result
    
def processTables(t,df):
    if df.size<=12:
        result = df.iloc[0 : 4]
    else:

        pos=acc_info.index.get_loc(t)
        result = df.iloc[pos : pos + 4]
            


            
    
    
    # if df.index.name == t:
    #     result=df
    
    result.index.name = None
    result = result.reindex(columns=['Vertical', 'North', 'East'])
    
    if pos:result = result.iloc[1:]
    
    # 2. Remove duplicate column names / reset columns
    result.columns = ['Vertical', 'North', 'East']  # enforce correct column names
    result.columns.name = None
    
    # 3. Reset index name if present
    result.index.name = None
    if result.empty: result=df.tail(3)
    # 4. Optional: reorder 2nd–4th rows as desired
    desired_middle = ['Thornton Tunnel North Entrance', 'Second Narrow', 'Lulu Island']
    first_row = result.index[0]
    rest = result.index[1:]
    
    reordered_index = [first_row] + [i for i in desired_middle if i in rest] + [i for i in rest if i not in desired_middle]

    result = result.reindex(reordered_index)
    
    # 5. Convert numeric columns to floats
    for col in ['Vertical', 'North', 'East']:
        result[col] = result[col].astype(float)
    

    return result
    



evttime=[]
coord=[]

for index, row in df.iterrows():
    coord.append(f'{row.values[1]},{row.values[2]}')
    
if isTrain:
    quakes=sorted(glob.glob('/home/jeff/van/plots/{}/trains/*.png'.format(current.strftime("%Y_%m_%d"))),key=sortTime)
else:
    quakes=sorted(glob.glob('/home/jeff/van/plots/{}/quakes/*.png'.format(current.strftime("%Y_%m_%d"))),key=sortTime)
    
    
dis_plot=np.full((len(quakes), 3), '', dtype=object)
acc_plot=np.full((len(quakes), 3), '', dtype=object)
vel_plot=np.full((len(quakes), 3), '', dtype=object)

for i,v in enumerate(quakes):
    pstring=v.replace('/quakes','')
    match = re.search(r'/(\d{12})\.png$', quakes[i])
    match=match.group(1)
    evttime.append(UTCDateTime(match).strftime("%H:%M-%d %B, %Y"))
    pba=f'/home/jeff/van/plots/{current.strftime("%Y_%m_%d")}/PBVAN-{match}-a.png'
    sna=f'/home/jeff/van/plots/{current.strftime("%Y_%m_%d")}/SNVAN-{match}-a.png'
    fra=f'/home/jeff/van/plots/{current.strftime("%Y_%m_%d")}/LUVAN-{match}-a.png'
    
    if os.path.isfile(pba):acc_plot[i][0]=pba
    if os.path.isfile(sna):acc_plot[i][1]=sna
    if os.path.isfile(fra):acc_plot[i][2]=fra



    pbv=f'/home/jeff/van/plots/{current.strftime("%Y_%m_%d")}/PBVAN-{match}-v.png'
    snv=f'/home/jeff/van/plots/{current.strftime("%Y_%m_%d")}/SNVAN-{match}-v.png'
    frv=f'/home/jeff/van/plots/{current.strftime("%Y_%m_%d")}/LUVAN-{match}-v.png'
    
    
    if os.path.isfile(pbv):vel_plot[i][0]=pbv
    if os.path.isfile(snv):vel_plot[i][1]=snv
    if os.path.isfile(frv):vel_plot[i][2]=frv
    
    pbs=f'/home/jeff/van/plots/{current.strftime("%Y_%m_%d")}/PBVAN-{match}-s.png'
    sns=f'/home/jeff/van/plots/{current.strftime("%Y_%m_%d")}/SNVAN-{match}-s.png'
    frs=f'/home/jeff/van/plots/{current.strftime("%Y_%m_%d")}/LUVAN-{match}-s.png'
    
    
    if os.path.isfile(pbv):dis_plot[i][0]=pbs
    if os.path.isfile(snv):dis_plot[i][1]=sns
    if os.path.isfile(frv):dis_plot[i][2]=frs


acc_plot=acc_plot.tolist()
vel_plot=vel_plot.tolist()
dis_plot=dis_plot.tolist()
# fs.insert(0,'')
# lp4.insert(0,'')
# bp410.insert(0,'')
filename = os.path.join(f'./plots/{current.year}_{current.month:02}_{current.day:02}/\
{current.year}_{current.month:02}_{current.day:02}.html')










print('color')
base_url = os.path.dirname(os.path.realpath(__file__))

html_string=template.render(
    isSample=False,
    gCount=0,
    tCount=0,
    mydate=f'{current.year}-{current.month}-{current.day}',
    eqs=quakes,
    evttime=evttime,
    gps=coord,
    accplots=acc_plot,
    velplots=vel_plot,
    displots=dis_plot,



)

css = CSS(myCSS, base_url=base_url)


for index, row in df.iterrows():
    t=UTCDateTime(row.iloc[0]).datetime.replace(tzinfo=timezone.utc)
    t=t.astimezone(ZoneInfo("America/Vancouver"))
    t=t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    # acc_info=acc_info.reset_index()
    # vel_info=vel_info.reset_index()
    # dis_info=dis_info.reset_index()
    # if t in acc_info: 
    acc_result=processTables(t,acc_info)
    vel_result=processTables(t,vel_info)
    dis_result=processTables(t,dis_info)
    
    acc_result.columns = [f"{c}_acc" for c in acc_result.columns]
    vel_result.columns = [f"{c}_vel" for c in vel_result.columns]
    dis_result.columns = [f"{c}_disp" for c in dis_result.columns]
    
    result = pd.concat([acc_result, vel_result, dis_result], axis=1)
    
    metadata = {
    "datetime": t,
    "MLv": row.iloc[1],
    "lat": row.iloc[2],
    "long": row.iloc[3],
    'Depth(km)':row.iloc[4],
    'Epicenter':row.iloc[5]}
    
    meta_df = pd.DataFrame([metadata]*len(result), index=result.index)
    bridges = result.index.tolist() 
    # 2. Create DataFrame for bridges
    bridge_df = pd.DataFrame({"Bridge": bridges}, index=result.index)
    
    # 3. Concatenate metadata + bridge + measurement columns
    final_df = pd.concat([meta_df, bridge_df, result], axis=1)
    
    # 4. Export to CSV
    final_df.to_csv("quake_result.csv",mode='a',index=False,header=False  )




if isTrain:
    HTML(string=html_string,base_url=base_url).write_pdf('/home/jeff/van/{}_report Yale_train.pdf'.format(current.strftime('%Y-%m-%d'))
            ,stylesheets=[css],
                presentational_hints=True)
else:
    # pass
    HTML(string=html_string,base_url=base_url).write_pdf('/home/jeff/van/{}_report Yale.pdf'.format(current.strftime('%Y-%m-%d'))
            ,stylesheets=[css],
                presentational_hints=True)
        
    
    

    
    