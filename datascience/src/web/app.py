import pandas as pd
from io import StringIO
from slugify import slugify
from flask import Flask, Response, render_template 
from visualization.section_plot import plot_results

app = Flask(__name__)
DATA = pd.read_csv('data/raw/escuelas-elecciones-2015-cordoba-CLEAN.csv')
SECTIONS = DATA[['seccion_nro', 'seccion_nombre',]].drop_duplicates().values
RESULTS = pd.read_csv('data/processed/resultados-secciones-2015.csv', index_col=0)

@app.template_filter('slugify')
def _slugify(string):
    if not string:
        return ""
    return slugify(string)


@app.route("/")
def index():
    sections = DATA[['seccion_nro', 'seccion_nombre',]].drop_duplicates().values

    return render_template(
        'index.html',
        sections=SECTIONS)


@app.route("/seccion/<int:section_nro>")
def sections(section_nro):

    section = DATA[DATA.seccion_nro == section_nro]
    section_name = section.seccion_nombre.unique()[0]
    schools = section[['escuela', 'direccion', 'desde', 'hasta']].drop_duplicates().values
    
    mask = RESULTS.nombre_circuito.str.lstrip('0').isin(section.circuito_nro.str.lstrip('0').unique())
    subset = RESULTS[mask]
    plot = plot_results(subset, section_name)
    return render_template(
        'section.html',
        sections=SECTIONS,
        schools=schools,
        plot=plot)


@app.route("/general/")
def general():
    plot = plot_results(RESULTS, 'general')
    schools = []
    return render_template(
        'section.html',
        sections=SECTIONS,
        plot=plot,
        schools=schools)


@app.route('/seccion/<int:section_nro>.csv')
def sections_csv(section_nro):
    
    output = StringIO()
    section = DATA[DATA.seccion_nro==section_nro]
    schools = section[['escuela', 'direccion', 'desde', 'hasta']].drop_duplicates()
    schools.to_csv(output)
    return Response(output.getvalue(), mimetype="text/csv")

def do_runserver():
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True)

if __name__ == "__main__":
    do_runserver()