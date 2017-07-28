# -*- coding: utf-8 -*-

import plotly.offline as py
import plotly.graph_objs as go
import os

votos_fpv = []
votos_cambiemos = []
secciones = ["001","002","003","004","005","006","007","008","009","010","011","012","013","014","015","016","017","018","019","020","021","022","023","024","025","026"]
nombres = ["Capital",                                 
"Calamuchita",                             
"Colón",                                   
"Cruz del Eje",                            
"General Roca",                            
"General San Martín",                      
"Ischilin",                                
"Juárez Celman",                           
"Marcos Juárez",                           
"Minas",                                    
"Pocho",                                    
"Punilla",                                  
"Río Cuarto",                               
"Río Primero",                              
"Río Seco",                                 
"Río Segundo",                              
"Roque Sáenz Peña",                         
"San Alberto",
"San Javier",                               
"San Justo",                                
"Santa María",                              
"Sobremonte",                               
"Tercero Arriba",                           
"Totoral",                                  
"Tulumba",                                 
"Unión"] 

for seccion in secciones:
    acumulado_fpv = 0
    acumulado_cambiemos = 0
    circuitos=[]
    for file in sorted(os.listdir(str(seccion)+"/")):
        circuitos.append(file[:-4])
        try:
            with open(str(seccion) +"/"+ file,"r") as f:
                mesas = f.readlines()
                for mesa in mesas:
                    acumulado_fpv += float(mesa.split(",")[2])
                    acumulado_cambiemos += float(mesa.split(",")[3])   
        except:
            continue
        try:
            votos_fpv.append(acumulado_fpv/(acumulado_fpv + acumulado_cambiemos))
            votos_cambiemos.append(acumulado_cambiemos/(acumulado_fpv + acumulado_cambiemos))
        except:
            continue
        acumulado_fpv = 0
        acumulado_cambiemos = 0

    #print votos_fpv
    #print votos_cambiemos
    
    trace1 = go.Bar(
        x=circuitos,
        y=votos_fpv,
        name='FPV',
        marker = dict(
        color = 'rgba(59, 131, 189, 0.8)',
        line = dict(
            color = 'rgba(59, 131, 189, 1.0)',
            width = 2)
    )
    )
    trace2 = go.Bar(
        x=circuitos,
        y=votos_cambiemos,
        name='Cambiemos',
        marker = dict(
        color = 'rgba(255, 255, 0, 0.8)',
        line = dict(
            color = 'rgba(255, 255, 0, 1.0)',
            width = 2)
    )
    )

    data = [trace2, trace1]

    layout = go.Layout(
        barmode='group',
        title="Votos en " + nombres[int(seccion)-1],     # more about "layout's" "title": /python/reference/#layout-title
        yaxis=dict(                 # all "layout's" "xaxis" attributes: /python/reference/#layout-xaxis
            title="Porcentaje"            # more about "layout's" "xaxis's" "title": /python/reference/#layout-xaxis-title
        ),
        xaxis=dict(                 # all "layout's" "xaxis" attributes: /python/reference/#layout-xaxis
            title="Circuitos de "+ nombres[int(seccion)-1]           # more about "layout's" "xaxis's" "title": /python/reference/#layout-xaxis-title
        ),
    )

    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='seccion:' + nombres[int(seccion)-1] + "_3.html")

    votos_fpv = []
    votos_cambiemos = []
