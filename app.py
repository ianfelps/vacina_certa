from flask import Flask, render_template, request
import sqlite3
from datetime import datetime
import folium
import os

app = Flask(__name__, template_folder='template')

def formatar_data(data_str):
    # Espera data no formato 'YYYY-MM-DD'
    try:
        return datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        return data_str or ''

@app.route('/')
def index():
    conn = sqlite3.connect('vacina_certa.db')
    cursor = conn.cursor()

    # Busca campanhas
    cursor.execute("SELECT * FROM VCCTB003_CAMPANHA_VACINACAO")
    campanhas = []
    for row in cursor.fetchall():
        # row[4] = DT_INICIO, row[5] = DT_FIM
        campanha = list(row)
        campanha[4] = formatar_data(campanha[4])
        campanha[5] = formatar_data(campanha[5])
        campanhas.append(campanha)

    # Busca vacinas e seus públicos alvo
    cursor.execute("""
        SELECT v.*, 
               GROUP_CONCAT(p.NO_PUBLICO_ALVO, ', ') as publicos
        FROM VCCTB002_VACINA v
        LEFT JOIN VCCTB006_VACINA_PUBLICO_ALVO vpa ON v.ID_VACINA = vpa.ID_VACINA
        LEFT JOIN VCCTB004_PUBLICO_ALVO p ON vpa.ID_PUBLICO_ALVO = p.ID_PUBLICO_ALVO
        GROUP BY v.ID_VACINA
    """)
    vacinas = cursor.fetchall()

    conn.close()
    return render_template('index.html', campanhas=campanhas, vacinas=vacinas)

@app.route('/busca', methods=['GET'])
def busca():
    conn = sqlite3.connect('vacina_certa.db')
    cursor = conn.cursor()
    cursor.execute("SELECT ID_VACINA, NO_VACINA FROM VCCTB002_VACINA")
    vacinas = cursor.fetchall()
    cursor.execute("SELECT ID_POSTO, NO_POSTO, NR_LATITUDE, NR_LONGITUDE FROM VCCTB001_POSTO")
    postos = cursor.fetchall()

    resultado = None
    mapa_html = None
    vacina_id = request.args.get('vacina')
    posto_id = request.args.get('localizacao')

    if vacina_id and posto_id:
        cursor.execute("""
            SELECT p.NO_POSTO, p.ED_POSTO, s.QT_DISPONIVEL, s.IC_STATUS, p.NR_LATITUDE, p.NR_LONGITUDE
            FROM VCCTB009_SALDO_ESTOQUE s
            JOIN VCCTB001_POSTO p ON s.ID_POSTO = p.ID_POSTO
            WHERE s.ID_POSTO = ? AND s.ID_VACINA = ?
        """, (posto_id, vacina_id))
        resultado = cursor.fetchone()
        if resultado and resultado[4] and resultado[5]:
            # Cria o mapa com Folium
            m = folium.Map(location=[resultado[4], resultado[5]], zoom_start=16)
            folium.Marker(
                [resultado[4], resultado[5]],
                popup=f"{resultado[0]}<br>{resultado[1]}"
            ).add_to(m)
            mapa_html = m._repr_html_()

    conn.close()
    return render_template('busca.html', vacinas=vacinas, postos=postos, resultado=resultado, mapa_html=mapa_html)

@app.route('/sobre')
def sobre():
    """
    Renders the sobre.html page.
    """
    return render_template('sobre.html')

if __name__ == '__main__':
    app.run(debug=True)