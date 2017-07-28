# -*- coding: utf-8 -*-
import os
import plotly.offline as py
import plotly.graph_objs as go
import cufflinks as cf

cf.set_config_file(offline=True, world_readable=True)

def plot_results(section, name):
    section.set_index('nombre_circuito')
    circuito = section.nombre_circuito.str.lstrip('0').drop_duplicates()
    fpv = section.votos_fpv
    cambiemos = section.votos_cambiemos
    trace1 = go.Bar(
        x=circuito,
        y=fpv,
        name='FPV',
        marker=dict(
            color='rgba(59, 131, 189, 0.8)',
            line=dict(
                color='rgba(59, 131, 189, 1.0)',
                width=2)
        )
    )
    trace2 = go.Bar(
        x=circuito,
        y=cambiemos,
        name='Cambiemos',
        marker=dict(
            color='rgba(255, 255, 0, 0.8)',
            line=dict(
                color='rgba(255, 255, 0, 1.0)',
                width=2)
        )
    )

    data = [trace2, trace1]

    layout = go.Layout(
        barmode='stacked',
        title="Votos en %s" % name,
        yaxis=dict(
            title="Porcentaje"
        ),
        xaxis=dict(
            title="Circuitos de %s" % name
        ),
    )

    fig = go.Figure(data=data, layout=layout)
    return py.plot(fig, show_link=False, output_type="div", include_plotlyjs=True)
