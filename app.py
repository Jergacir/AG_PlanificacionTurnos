from flask import Flask, render_template, request, jsonify, session
from algoritmo_genetico import *
import threading
import uuid
import time

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui_12345'

# Diccionario para almacenar el progreso de cada sesión
progreso_sesiones = {}
resultados_sesiones = {}

class ProgresoAG:
    """Clase para trackear el progreso del AG"""
    def __init__(self, session_id):
        self.session_id = session_id
        self.generacion_actual = 0
        self.total_generaciones = 0
        self.mejor_aptitud = 0
        self.penalizacion_dura = 0
        self.penalizacion_blanda = 0
        self.completado = False
        self.error = None

# Modificar la función algoritmo_genetico para reportar progreso
def algoritmo_genetico_con_progreso(
    session_id,
    tamanio_poblacion=100,
    num_generaciones=500,
    prob_mutacion=0.02,
    elitismo=2,
    num_enfermeras=10,
    num_dias=30
):
    """Versión del AG que reporta progreso"""
    global progreso_sesiones, resultados_sesiones
    
    # Actualizar variables globales
    global NUM_ENFERMERAS, NUM_DIAS
    NUM_ENFERMERAS = num_enfermeras
    NUM_DIAS = num_dias
    
    progreso = ProgresoAG(session_id)
    progreso.total_generaciones = num_generaciones
    progreso_sesiones[session_id] = progreso
    
    try:
        # Crear población inicial
        poblacion = crear_poblacion_inicial(tamanio_poblacion)
        
        # Evaluar población inicial
        for individuo in poblacion:
            calcular_aptitud(individuo)
        
        mejor_aptitud_por_gen = []
        
        for generacion in range(num_generaciones):
            # Ordenar por aptitud
            poblacion.sort(key=lambda x: x.aptitud, reverse=True)
            
            mejor = poblacion[0]
            mejor_aptitud_por_gen.append(mejor.aptitud)
            
            # Actualizar progreso
            progreso.generacion_actual = generacion + 1
            progreso.mejor_aptitud = float(mejor.aptitud)
            progreso.penalizacion_dura = int(mejor.penalizacion_dura)
            progreso.penalizacion_blanda = int(mejor.penalizacion_blanda)
            
            # Condición de parada
            if mejor.penalizacion_dura == 0 and mejor.penalizacion_blanda < 20:
                progreso.completado = True
                break
            
            # Nueva generación
            nueva_poblacion = poblacion[:elitismo]
            
            while len(nueva_poblacion) < tamanio_poblacion:
                padre1 = seleccion_torneo(poblacion)
                padre2 = seleccion_torneo(poblacion)
                
                if random.random() < 0.8:
                    hijo1, hijo2 = cruce_uniforme(padre1, padre2)
                else:
                    hijo1, hijo2 = Horario(padre1.genes), Horario(padre2.genes)
                
                mutacion(hijo1, prob_mutacion)
                mutacion_inteligente(hijo1, 0.05)
                mutacion(hijo2, prob_mutacion)
                mutacion_inteligente(hijo2, 0.05)
                
                calcular_aptitud(hijo1)
                calcular_aptitud(hijo2)
                
                nueva_poblacion.extend([hijo1, hijo2])
            
            poblacion = nueva_poblacion[:tamanio_poblacion]
        
        # Resultado final
        poblacion.sort(key=lambda x: x.aptitud, reverse=True)
        mejor_solucion = poblacion[0]
        
        # Calcular aptitud con detalles para obtener violaciones
        calcular_aptitud(mejor_solucion, guardar_detalles=True)
        
        progreso.completado = True
        
        # Guardar resultado
        resultados_sesiones[session_id] = {
            'horario': mejor_solucion.genes.tolist(),
            'aptitud': float(mejor_solucion.aptitud),
            'penalizacion_dura': int(mejor_solucion.penalizacion_dura),
            'penalizacion_blanda': int(mejor_solucion.penalizacion_blanda),
            'evoluciones': mejor_aptitud_por_gen,
            'violaciones_duras': mejor_solucion.violaciones_duras if hasattr(mejor_solucion, 'violaciones_duras') else {},
            'violaciones_blandas': mejor_solucion.violaciones_blandas if hasattr(mejor_solucion, 'violaciones_blandas') else {}
        }
        
    except Exception as e:
        progreso.error = str(e)
        progreso.completado = True


@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/iniciar_ag', methods=['POST'])
def iniciar_ag():
    """Inicia la ejecución del algoritmo genético"""
    datos = request.get_json()
    
    # Crear ID de sesión único
    session_id = str(uuid.uuid4())
    
    # Actualizar preferencias y especialistas globales si se proporcionan
    if 'preferencias' in datos:
        global PREFERENCIAS, ESPECIALISTAS
        PREFERENCIAS.clear()
        especialistas_temp = []
        
        for pref in datos['preferencias']:
            enfermera = int(pref['enfermera'])
            dias = [int(d) for d in pref['dias']]
            PREFERENCIAS[enfermera] = dias
            
            # Si es especialista, agregarlo a la lista
            if pref.get('esEspecialista', False):
                especialistas_temp.append(enfermera)
        
        # Actualizar lista de especialistas solo si se proporcionaron
        if especialistas_temp:
            ESPECIALISTAS = especialistas_temp
        else:
            # Si no hay especialistas definidos, usar los primeros 3
            ESPECIALISTAS = [0, 1, 2]
    
    # Extraer parámetros
    params = {
        'session_id': session_id,
        'tamanio_poblacion': int(datos.get('poblacion', 150)),
        'num_generaciones': int(datos.get('generaciones', 300)),
        'prob_mutacion': float(datos.get('mutacion', 0.03)),
        'num_enfermeras': int(datos.get('enfermeras', 10)),
        'num_dias': int(datos.get('dias', 30))
    }
    
    # Ejecutar en thread separado para no bloquear Flask
    thread = threading.Thread(
        target=algoritmo_genetico_con_progreso,
        kwargs=params
    )
    thread.start()
    
    return jsonify({
        'success': True,
        'session_id': session_id
    })


@app.route('/obtener_progreso/<session_id>')
def obtener_progreso(session_id):
    """Retorna el progreso actual del AG"""
    if session_id not in progreso_sesiones:
        return jsonify({'error': 'Sesión no encontrada'}), 404
    
    progreso = progreso_sesiones[session_id]
    
    return jsonify({
        'generacion_actual': int(progreso.generacion_actual),
        'total_generaciones': int(progreso.total_generaciones),
        'porcentaje': float((progreso.generacion_actual / progreso.total_generaciones * 100) if progreso.total_generaciones > 0 else 0),
        'mejor_aptitud': float(progreso.mejor_aptitud),
        'penalizacion_dura': int(progreso.penalizacion_dura),
        'penalizacion_blanda': int(progreso.penalizacion_blanda),
        'completado': progreso.completado,
        'error': progreso.error
    })


@app.route('/obtener_resultado/<session_id>')
def obtener_resultado(session_id):
    """Retorna el resultado final del AG"""
    if session_id not in resultados_sesiones:
        return jsonify({'error': 'Resultado no disponible'}), 404
    
    resultado = resultados_sesiones[session_id]
    
    # Convertir horario a formato legible
    turnos_nombres = {0: 'Libre', 1: 'Mañana', 2: 'Tarde', 3: 'Noche'}
    horario_formateado = []
    
    for enfermera_idx, dias in enumerate(resultado['horario']):
        fila = {
            'enfermera': f'Enfermera {enfermera_idx + 1}',
            'turnos': [turnos_nombres[int(turno)] for turno in dias]
        }
        horario_formateado.append(fila)
    
    # Obtener información de especialistas
    especialistas_info = [idx + 1 for idx in ESPECIALISTAS] if ESPECIALISTAS else []
    
    return jsonify({
        'horario': horario_formateado,
        'aptitud': float(resultado['aptitud']),
        'penalizacion_dura': int(resultado['penalizacion_dura']),
        'penalizacion_blanda': int(resultado['penalizacion_blanda']),
        'evoluciones': [float(x) for x in resultado['evoluciones']],
        'violaciones_duras': resultado.get('violaciones_duras', {}),
        'violaciones_blandas': resultado.get('violaciones_blandas', {}),
        'es_optimo': int(resultado['penalizacion_dura']) == 0 and int(resultado['penalizacion_blanda']) < 20,
        'es_aceptable': int(resultado['penalizacion_dura']) == 0,
        'especialistas': especialistas_info
    })


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
