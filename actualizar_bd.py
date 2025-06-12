import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Consulta GraphQL
# url = 'http://localhost:8000/graphql'
url = 'https://40fa-161-138-65-73.ngrok-free.app/graphql'
clientes = """
query MyQuery {
  allClientes {
    ci
    nombre
    apellido
  }
}
"""
casos = """
query MyQuery {
  allCasos {
    id
    meteria
  }
}
"""
servicios = """
query MyQuery {
  allContratos {
    id
    fecha
    precioBS
    cliente {
      ci
    }
    Caso {
      id
    }
  }
}
"""

respuesta_clientes = requests.post(url, json={'query': clientes})
respuesta_casos = requests.post(url, json={'query': casos})
respuesta_servicios = requests.post(url, json={'query': servicios})
if respuesta_clientes.status_code != 200 and respuesta_casos.status_code != 200 and respuesta_servicios != 200:
    raise Exception(f"""
            Error al consultar GraphQL: 
            cliente = {respuesta_clientes.status_code},
            casos = {respuesta_casos.status_code},
            servicios = {respuesta_servicios.status_code}
        """)

# Convertir a DataFrame
data_clientes = respuesta_clientes.json()['data']['allClientes']
data_casos = respuesta_casos.json()['data']['allCasos']
data_servicios = respuesta_servicios.json()['data']['allContratos']
processed_data = []
for servicio in data_servicios:
    # Crear un nuevo diccionario para cada fila con los valores deseados
    """
    "id": "68478fc1090a0ec9d0c8a61c",
        "fecha": "12/12/2025",
        "precioBS": 300,
        "cliente": {
          "ci": "123123123"
        },
        "Caso": null
    """
    processed_row = {
        'nrocontrato': servicio['id'],
        'fecha': servicio['fecha'],
        'monto': servicio['precioBS'],
        'cicliente': servicio['cliente']['ci'] if servicio['cliente'] else None,
        # Extraer 'ci' o None si cicliente es nulo
        'nrocasojuridico': servicio['Caso']['id'] if servicio['Caso'] else None
        # Extraer 'nrocaso' o None si nrocasojuridico es nulo
    }
    processed_data.append(processed_row)

df_clientes = pd.DataFrame(data_clientes, columns=['ci','nombre','apellidos'])
df_casos = pd.DataFrame(data_casos, columns=['nrocaso','materia'])
df_servicios = pd.DataFrame(processed_data, columns=['nrocontrato','fecha','monto','cicliente','nrocasojuridico'])
# Procesar datos
# cliente
df_clientes = df_clientes.drop_duplicates(subset='ci', keep='first')
# casos
df_casos = df_casos.drop_duplicates(subset='nrocaso', keep='first')
# servicios
df_servicios = df_servicios.drop_duplicates(subset='nrocontrato', keep='first')
df_servicios['fecha'] = pd.to_datetime(df_servicios['fecha'])
df_servicios['monto'] = pd.to_numeric(df_servicios['monto']).round(2)

print(">>> CLIENTES")
print(df_clientes.head(2))
# print(df_clientes.dtypes)

print(">>> CASOS")
print(df_casos.head(2))
# print(df_casos.dtypes)

print(">>> SERVICIOS")
print(df_servicios.head(2))
# print(df_servicios.dtypes)

# -----------------------------
try:
    # Conexión
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="bi_juridico",
        user="lid",
        password="12345678"
    )
    cursor = conn.cursor()

    # Convertir DataFrame a lista de tuplas
    registros = list(df_clientes.itertuples(index=False, name=None))
    # Insertar con execute_values
    insert_query = """
            INSERT INTO cliente (ci, nombre, apellidos)
            VALUES %s
            ON CONFLICT (ci) DO NOTHING
        """
    execute_values(cursor, insert_query, registros)

    # Convertir DataFrame a lista de tuplas
    registros = list(df_casos.itertuples(index=False, name=None))
    # Insertar con execute_values
    insert_query = """
            INSERT INTO casojuridico (nrocaso, materia)
            VALUES %s
            ON CONFLICT (nrocaso) DO NOTHING
        """
    execute_values(cursor, insert_query, registros)

    # Convertir DataFrame a lista de tuplas
    registros = list(df_servicios.itertuples(index=False, name=None))
    # Insertar con execute_values
    insert_query = """
            INSERT INTO contratoservicio (nrocontrato, fecha, monto, cicliente, nrocasojuridico)
            VALUES %s
            ON CONFLICT (nrocontrato) DO NOTHING
        """
    execute_values(cursor, insert_query, registros)

    # Confirmar cambios y cerrar conexión
    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Sincronización completada.")
except:
    raise Exception("error al guardar los datos.")