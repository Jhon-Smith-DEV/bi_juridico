# importar librerias
import dash
from dash import dcc, html, dependencies as dd
import pandas as pd
import plotly.express as px
import psycopg2
import subprocess

# Consulta SQL
# ------ total ingresos en un rango de fechas
query_ingresofecha = "SELECT fecha, monto FROM contratoservicio ORDER BY fecha;"
#  ------ total ingresos por materia en un rango de fechas
query_ingresomateria = """
SELECT cs.fecha, cs.monto, cj.materia
FROM contratoServicio cs
JOIN casoJuridico cj ON cs.nrocasojuridico = cj.nrocaso;
"""
#  ------ top 10 clientes que generaron mayores ingresos en un rango de fechas determinado
query_topclientes = """
SELECT cs.fecha, cs.monto, c.nombre || ' ' || c.apellidos AS nombre, c.ci
FROM contratoServicio cs
JOIN cliente c ON cs.cicliente = c.ci;
"""
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="bi_juridico",
    user="lid",
    password="12345678"
)
# Cargar en DataFrame
df_ingresofecha = pd.read_sql_query(query_ingresofecha, conn)
df_ingresomateria = pd.read_sql_query(query_ingresomateria, conn)
df_topclientes = pd.read_sql_query(query_topclientes, conn)
# Cerrar conexión
conn.close()

# tratamiento a los datos: ELIMINAR FILAS SI TIEN CAMPOS NULOS
df_ingresofecha = df_ingresofecha.dropna()
df_ingresomateria = df_ingresomateria.dropna()
df_topclientes = df_topclientes.dropna()

print(df_ingresofecha.head(2))
print(df_ingresomateria.head(2))
print(df_topclientes.head(2))

# dashboards
app = dash.Dash(__name__)
app.layout = html.Div([
    html.Div(id='titulo'),
    html.Div(
        dcc.DatePickerRange(
            id='rango-fecha',
            display_format='DD-MM-YYYY'
        ),
        style={'textAlign':'center',
               'border':'black, solid',
               'width':300,
               'marginLeft':'auto',
               'marginRight':'auto'}
    ),
    dcc.RadioItems(
        id='menu',
        options=[
            {'label': 'Ingresos por mes', 'value': 'ingresofecha'},
            {'label': 'Ingresos por materia', 'value': 'ingresomateria'},
            {'label': 'top 10 clientes', 'value': 'topclientes'},
            {'label': 'ACTUALIZAR BD', 'value': 'actualizarbd'},
        ],
        value='gbarras',
        labelStyle={'display': 'inline-block', 'margin-right': '20px'},
        style={'textAlign': 'center'}
    ),
    html.Div(id='estado-sincronizacion', style={'marginTop': '20px', 'color': 'green', 'textAlign':'center'}),
    html.Div(id='suma-monto', style={'fontSize':28,'textAlign':'center'}),
    html.Div([
        dcc.Graph(id='gbarras')
    ])
])

# llamadas de retornos
@app.callback(
[dd.Output('titulo', 'children'),
        dd.Output('gbarras','figure'),
        dd.Output('estado-sincronizacion','children'),
        dd.Output('suma-monto','children')
 ],
    [dd.Input('menu', 'value'),
     dd.Input('rango-fecha','start_date'),
     dd.Input('rango-fecha','end_date')
     # dd.Input('actualizar-btn','value')
     ]
)
def actualizar_vista(menu, fechaInicio, fechaFin): #, valuebtn
    # titulo general de la página
    titulo = html.H1(f"DASHBOARDs", style={'textAlign': 'center'})
    # figura/gráfico/dasboard
    fig = ""
    estado = ""
    montototal = "Total: BS. 0"
    if menu == 'actualizarbd':
        # Ejecutar el script externo que sincroniza los datos
        try:
            subprocess.run(['python', 'actualizar_bd.py'], check=True)
            estado = "✅ Base de datos actualizada correctamente."
        except subprocess.CalledProcessError:
            estado = "❌ Error al actualizar la base de datos."

    if fechaInicio == None or fechaFin==None:
        return titulo, fig, estado, montototal

    if menu == 'ingresofecha' and not df_ingresofecha.empty:
        titulo = html.H1(f"INGRESOS POR MES", style={'textAlign': 'center'})

        # transformación de tipos de datos
        df_ingresofecha['fecha'] = pd.to_datetime(df_ingresofecha['fecha'])
        df_ingresofecha['monto'] = pd.to_numeric(df_ingresofecha['monto']).round(2)
        # selección de registro por rango de fechas
        df_filtrado = df_ingresofecha[(df_ingresofecha['fecha'] >= fechaInicio)&(df_ingresofecha['fecha'] <= fechaFin)]
        if not df_filtrado.empty:
            df_filtrado['mes'] = df_filtrado['fecha'].dt.to_period('M').dt.to_timestamp()
            df_agrupado = df_filtrado.groupby('mes', as_index=False)['monto'].sum()
            # Formatear mes para mostrar como MM-YYYY
            df_agrupado['mes'] = df_agrupado['mes'].dt.strftime('%m-%Y')
            df_agrupado['monto'] = df_agrupado['monto'].round(2)
            sumamonto = df_agrupado['monto'].sum()
            montototal = f'Total: BS. {sumamonto}'
            fig = px.bar(
                df_agrupado,
                x='mes',
                y='monto',
                color='mes',
                text='monto'
            ).update_xaxes(type='category', tickangle=300).update_traces(textposition='outside')
        else:
            fig = ""
    elif menu == 'ingresomateria' and not df_ingresomateria.empty:
        titulo = html.H1(f"INGRESOS POR MATERIA", style={'textAlign': 'center'})
        # transformación de tipos de datos
        df_ingresomateria['fecha'] = pd.to_datetime(df_ingresomateria['fecha'])
        df_ingresomateria['monto'] = pd.to_numeric(df_ingresomateria['monto'])
        # filtrado de registros por rango de fechas
        df_filtrado = df_ingresomateria[
            (df_ingresomateria['fecha']>=fechaInicio)&(df_ingresomateria['fecha']<=fechaFin)
        ]
        if not df_filtrado.empty:
            # agrupar
            df_agrupado = df_filtrado.groupby('materia', as_index=False)['monto'].sum()
            sumamonto=df_agrupado['monto'].sum()
            montototal = f'Total: BS. {sumamonto}'
            # obtener gráfica
            fig = px.bar(
                df_agrupado,
                x='materia',
                y='monto',
                color='materia',
                text='monto'
            ).update_xaxes(type='category').update_traces(textposition='outside')
        else:
            fig = ""

    elif menu == 'topclientes' and not df_topclientes.empty:
        titulo = html.H1(f"TOP 10 CLIENTES", style={'textAlign': 'center'})
        # transformación de tipos de datos
        df_topclientes['fecha'] = pd.to_datetime(df_topclientes['fecha'])
        df_topclientes['monto'] = pd.to_numeric(df_topclientes['monto'])

        # filtrado de registros por rango de fechas
        df_filtrado = df_topclientes[
            (df_topclientes['fecha']>=fechaInicio)&(df_topclientes['fecha']<=fechaFin)
        ]
        if not df_filtrado.empty:
            # agrupar datos
            # df_agrupado = df_topclientes.groupby('ci', as_index=False)['monto'].sum()
            df_agrupado = df_topclientes.groupby('ci', as_index=False).agg(
                nombre=('nombre', 'first'),  # Agrega 'nombre' tomando el primer valor
                monto=('monto', 'sum')  # Agrega 'monto' sumando
            )
            # ordenar dataFrame de forma desendente y tomar los 10 primeros
            df_top = df_agrupado.sort_values(by='monto', ascending=False).head(10)
            # obtener suma total de montos
            sumamonto = df_top['monto'].sum().round(2)
            montototal = f'Total: BS. {sumamonto}'
            # gráficar
            fig = px.bar(
                df_top,
                x='nombre',
                y='monto',
                color='nombre',
                text='monto'
            ).update_xaxes(type='category', tickangle=340).update_traces(textposition='outside')
        else:
            fig=""

    return titulo, fig, estado, montototal


if __name__ == '__main__':
    app.run()
