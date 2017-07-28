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
	for file in os.listdir(str(seccion)+"/"):
		try:
			with open(str(seccion) +"/"+ file,"r") as f:
				mesas = f.readlines()
				for mesa in mesas:
					acumulado_fpv += float(mesa.split(",")[2])
					acumulado_cambiemos += float(mesa.split(",")[3])
		except:
			continue
	votos_fpv.append(acumulado_fpv/(acumulado_fpv + acumulado_cambiemos))
	votos_cambiemos.append(acumulado_cambiemos/(acumulado_fpv + acumulado_cambiemos))


votos_fpv = votos_fpv[::-1]
votos_fpv = [round(v*100,2) for v in votos_fpv]
votos_cambiemos = votos_cambiemos[::-1]
votos_cambiemos = [round(v*100,2) for v in votos_cambiemos]
nombres = nombres[::-1]

trace1 = go.Bar(
    y=nombres,
    x=votos_fpv,
    name='FPV',
    orientation = 'h',
    marker = dict(
        color = 'rgba(59, 131, 189, 0.8)',
        line = dict(
            color = 'rgba(59, 131, 189, 1.0)',
            width = 2)
    )
)
trace2 = go.Bar(
    y=nombres,
    x=votos_cambiemos,
    name='Cambiemos',
    orientation = 'h',
    marker = dict(
        color = 'rgba(255, 255, 0, 0.8)',
        line = dict(
            color = 'rgba(255, 255, 0, 1.0)',
            width = 2)
    )
)

data = [trace1, trace2]
layout = go.Layout(
    barmode='stack',
    title="Porcentaje de Votos Ballotage 2015",     # more about "layout's" "title": /python/reference/#layout-title
    xaxis=dict(                 # all "layout's" "xaxis" attributes: /python/reference/#layout-xaxis
        title="Porcentaje"            # more about "layout's" "xaxis's" "title": /python/reference/#layout-xaxis-title
    ),
)

fig = go.Figure(data=data, layout=layout)
py.plot(fig, filename='marker-h-bar.html')