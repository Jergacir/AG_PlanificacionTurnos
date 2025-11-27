import numpy as np
import random
from typing import List, Tuple
import matplotlib.pyplot as plt

# ============================================
# PARÁMETROS DEL PROBLEMA
# ============================================

NUM_ENFERMERAS = 10
NUM_DIAS = 30  # Un mes
NUM_TURNOS = 4  # 0=Libre, 1=Mañana, 2=Tarde, 3=Noche

# Especialistas (índices de enfermeras con especialización)
ESPECIALISTAS = [0, 1, 2]

# Preferencias personales: {id_enfermera: [lista de días preferidos libres]}
PREFERENCIAS = {
    0: [6, 13, 20, 27],  # Domingos
    1: [5, 12, 19, 26],  # Sábados
    2: [14, 15],         # Días específicos
    # ... puedes agregar más
}

# ============================================
# CLASE CROMOSOMA (INDIVIDUO)
# ============================================

class Horario:
    """
    Representa un horario completo (cromosoma).
    Matriz de [NUM_ENFERMERAS x NUM_DIAS] donde cada celda contiene el turno asignado.
    """
    def __init__(self, genes=None):
        if genes is None:
            # Inicialización aleatoria
            self.genes = np.random.randint(0, NUM_TURNOS, 
                                          size=(NUM_ENFERMERAS, NUM_DIAS))
        else:
            self.genes = genes.copy()
        
        self.aptitud = 0
        self.penalizacion_dura = 0
        self.penalizacion_blanda = 0
    
    def __str__(self):
        return f"Aptitud: {self.aptitud:.2f} (Duras: {self.penalizacion_dura}, Blandas: {self.penalizacion_blanda})"


# ============================================
# FUNCIÓN DE APTITUD (FITNESS)
# ============================================

def calcular_aptitud(horario: Horario, guardar_detalles: bool = False) -> float:
    """
    Evalúa qué tan bueno es un horario.
    Menor penalización = mejor aptitud.
    """
    penalizacion_dura = 0
    penalizacion_blanda = 0
    
    # Diccionarios para guardar detalles de violaciones
    violaciones_duras = {}
    violaciones_blandas = {}
    
    # --- RESTRICCIONES DURAS ---
    
    # 1. No trabajar Noche seguido de Mañana
    pen, detalle = verificar_noche_manana(horario.genes, guardar_detalles)
    penalizacion_dura += pen
    if guardar_detalles and detalle:
        violaciones_duras['noche_manana'] = detalle
    
    # 2. No más de 6 días consecutivos trabajando
    pen, detalle = verificar_dias_consecutivos(horario.genes, guardar_detalles)
    penalizacion_dura += pen
    if guardar_detalles and detalle:
        violaciones_duras['dias_consecutivos'] = detalle
    
    # 3. Mínimo 1 especialista por turno (excepto Libre)
    pen, detalle = verificar_especialistas_por_turno(horario.genes, guardar_detalles)
    penalizacion_dura += pen
    if guardar_detalles and detalle:
        violaciones_duras['especialistas'] = detalle
    
    # 4. Cobertura mínima por turno
    pen, detalle = verificar_cobertura_minima(horario.genes, guardar_detalles)
    penalizacion_dura += pen
    if guardar_detalles and detalle:
        violaciones_duras['cobertura'] = detalle
    
    # --- RESTRICCIONES BLANDAS ---
    
    # 1. Preferencias personales
    pen, detalle = verificar_preferencias(horario.genes, guardar_detalles)
    penalizacion_blanda += pen
    if guardar_detalles and detalle:
        violaciones_blandas['preferencias'] = detalle
    
    # 2. Equidad en la carga de trabajo
    pen, detalle = verificar_equidad_turnos(horario.genes, guardar_detalles)
    penalizacion_blanda += pen
    if guardar_detalles and detalle:
        violaciones_blandas['equidad'] = detalle
    
    # 3. Distribución equilibrada de turnos nocturnos
    pen, detalle = verificar_distribucion_noches(horario.genes, guardar_detalles)
    penalizacion_blanda += pen
    if guardar_detalles and detalle:
        violaciones_blandas['noches'] = detalle
    
    horario.penalizacion_dura = penalizacion_dura
    horario.penalizacion_blanda = penalizacion_blanda
    
    if guardar_detalles:
        horario.violaciones_duras = violaciones_duras
        horario.violaciones_blandas = violaciones_blandas
    
    # Aptitud = maximizar (menor penalización es mejor)
    # Penalizaciones duras pesan 100x más
    horario.aptitud = -(penalizacion_dura * 100 + penalizacion_blanda)
    
    return horario.aptitud


# ============================================
# FUNCIONES DE VERIFICACIÓN DE RESTRICCIONES
# ============================================

def verificar_noche_manana(genes: np.ndarray, guardar_detalles: bool = False):
    """Penaliza si una enfermera trabaja Noche y al día siguiente Mañana."""
    penalizacion = 0
    violaciones = []
    for enfermera in range(NUM_ENFERMERAS):
        for dia in range(NUM_DIAS - 1):
            if genes[enfermera, dia] == 3 and genes[enfermera, dia + 1] == 1:
                penalizacion += 50  # Penalización alta
                if guardar_detalles:
                    violaciones.append(f"Enfermera {enfermera+1}: Noche día {dia+1}, Mañana día {dia+2}")
    return penalizacion, violaciones if guardar_detalles else None


def verificar_dias_consecutivos(genes: np.ndarray, guardar_detalles: bool = False):
    """Penaliza si trabaja más de 6 días seguidos."""
    penalizacion = 0
    violaciones = []
    for enfermera in range(NUM_ENFERMERAS):
        dias_trabajados = 0
        max_consecutivos = 0
        for dia in range(NUM_DIAS):
            if genes[enfermera, dia] != 0:  # No es día libre
                dias_trabajados += 1
                max_consecutivos = max(max_consecutivos, dias_trabajados)
                if dias_trabajados > 6:
                    penalizacion += 30
            else:
                dias_trabajados = 0  # Reset al encontrar día libre
        if guardar_detalles and max_consecutivos > 6:
            violaciones.append(f"Enfermera {enfermera+1}: {max_consecutivos} días consecutivos (máx: 6)")
    return penalizacion, violaciones if guardar_detalles else None


def verificar_especialistas_por_turno(genes: np.ndarray, guardar_detalles: bool = False):
    """Verifica que haya al menos 1 especialista en cada turno (Mañana, Tarde, Noche)."""
    penalizacion = 0
    violaciones = []
    turnos_nombres = {1: 'Mañana', 2: 'Tarde', 3: 'Noche'}
    for dia in range(NUM_DIAS):
        for turno in [1, 2, 3]:  # Mañana, Tarde, Noche
            especialistas_en_turno = 0
            for especialista in ESPECIALISTAS:
                if genes[especialista, dia] == turno:
                    especialistas_en_turno += 1
            
            if especialistas_en_turno == 0:
                penalizacion += 40  # Muy importante
                if guardar_detalles:
                    violaciones.append(f"Día {dia+1}, turno {turnos_nombres[turno]}: sin especialistas")
    return penalizacion, violaciones if guardar_detalles else None


def verificar_cobertura_minima(genes: np.ndarray, guardar_detalles: bool = False):
    """Asegura que cada turno tenga al menos 2 personas (excepto Libre)."""
    penalizacion = 0
    cobertura_minima = 2
    violaciones = []
    turnos_nombres = {1: 'Mañana', 2: 'Tarde', 3: 'Noche'}
    
    for dia in range(NUM_DIAS):
        for turno in [1, 2, 3]:
            personal_en_turno = np.sum(genes[:, dia] == turno)
            if personal_en_turno < cobertura_minima:
                faltante = cobertura_minima - personal_en_turno
                penalizacion += faltante * 20
                if guardar_detalles:
                    violaciones.append(f"Día {dia+1}, turno {turnos_nombres[turno]}: {personal_en_turno} personas (mín: 2)")
    return penalizacion, violaciones if guardar_detalles else None


def verificar_preferencias(genes: np.ndarray, guardar_detalles: bool = False):
    """Penaliza ligeramente si no se respetan preferencias personales."""
    penalizacion = 0
    violaciones = []
    for enfermera, dias_preferidos in PREFERENCIAS.items():
        for dia in dias_preferidos:
            if genes[enfermera, dia] != 0:  # No está libre
                penalizacion += 5
                if guardar_detalles:
                    violaciones.append(f"Enfermera {enfermera+1}: prefería libre el día {dia+1}")
    return penalizacion, violaciones if guardar_detalles else None


def verificar_equidad_turnos(genes: np.ndarray, guardar_detalles: bool = False):
    """Penaliza si hay desequilibrio en días trabajados entre enfermeras."""
    dias_trabajados = []
    for enfermera in range(NUM_ENFERMERAS):
        dias = np.sum(genes[enfermera, :] != 0)
        dias_trabajados.append(dias)
    
    desviacion_estandar = np.std(dias_trabajados)
    penalizacion = int(desviacion_estandar * 3)
    
    detalle = None
    if guardar_detalles:
        min_dias = min(dias_trabajados)
        max_dias = max(dias_trabajados)
        promedio = np.mean(dias_trabajados)
        detalle = [f"Desviación: {desviacion_estandar:.1f} días (min: {min_dias}, max: {max_dias}, promedio: {promedio:.1f})"]
    
    return penalizacion, detalle


def verificar_distribucion_noches(genes: np.ndarray, guardar_detalles: bool = False):
    """Verifica que los turnos nocturnos estén bien distribuidos."""
    noches_por_enfermera = []
    
    for enfermera in range(NUM_ENFERMERAS):
        noches = np.sum(genes[enfermera, :] == 3)
        noches_por_enfermera.append(noches)
    
    desviacion = np.std(noches_por_enfermera)
    penalizacion = int(desviacion * 5)
    
    detalle = None
    if guardar_detalles:
        min_noches = min(noches_por_enfermera)
        max_noches = max(noches_por_enfermera)
        promedio = np.mean(noches_por_enfermera)
        detalle = [f"Desviación: {desviacion:.1f} noches (min: {min_noches}, max: {max_noches}, promedio: {promedio:.1f})"]
    
    return penalizacion, detalle


# ============================================
# OPERADORES GENÉTICOS
# ============================================

def crear_poblacion_inicial(tamanio: int) -> List[Horario]:
    """Crea población inicial de horarios aleatorios."""
    return [Horario() for _ in range(tamanio)]


def seleccion_torneo(poblacion: List[Horario], k: int = 3) -> Horario:
    """
    Selección por torneo: elige k individuos al azar y retorna el mejor.
    """
    torneo = random.sample(poblacion, k)
    return max(torneo, key=lambda x: x.aptitud)


def cruce_uniforme(padre1: Horario, padre2: Horario) -> Tuple[Horario, Horario]:
    """
    Cruce uniforme: cada gen tiene 50% de probabilidad de venir de cada padre.
    """
    mascara = np.random.rand(NUM_ENFERMERAS, NUM_DIAS) > 0.5
    
    genes_hijo1 = np.where(mascara, padre1.genes, padre2.genes)
    genes_hijo2 = np.where(mascara, padre2.genes, padre1.genes)
    
    return Horario(genes_hijo1), Horario(genes_hijo2)


def cruce_un_punto(padre1: Horario, padre2: Horario) -> Tuple[Horario, Horario]:
    """
    Cruce de un punto: divide por una enfermera y combina.
    """
    punto_corte = random.randint(1, NUM_ENFERMERAS - 1)
    
    genes_hijo1 = np.vstack([padre1.genes[:punto_corte], 
                             padre2.genes[punto_corte:]])
    genes_hijo2 = np.vstack([padre2.genes[:punto_corte], 
                             padre1.genes[punto_corte:]])
    
    return Horario(genes_hijo1), Horario(genes_hijo2)


def mutacion(horario: Horario, prob_mutacion: float = 0.01):
    """
    Mutación: cambia aleatoriamente algunos turnos.
    """
    for enfermera in range(NUM_ENFERMERAS):
        for dia in range(NUM_DIAS):
            if random.random() < prob_mutacion:
                horario.genes[enfermera, dia] = random.randint(0, NUM_TURNOS - 1)


def mutacion_inteligente(horario: Horario, prob_mutacion: float = 0.05):
    """
    Mutación que intenta mejorar violaciones específicas.
    """
    if random.random() < prob_mutacion:
        # Intenta arreglar turno Noche-Mañana
        for enfermera in range(NUM_ENFERMERAS):
            for dia in range(NUM_DIAS - 1):
                if horario.genes[enfermera, dia] == 3 and horario.genes[enfermera, dia + 1] == 1:
                    horario.genes[enfermera, dia + 1] = random.choice([0, 2, 3])


# ============================================
# ALGORITMO GENÉTICO PRINCIPAL
# ============================================

def algoritmo_genetico(
    tamanio_poblacion: int = 100,
    num_generaciones: int = 500,
    prob_mutacion: float = 0.02,
    elitismo: int = 2
) -> Horario:
    """
    Ejecuta el algoritmo genético para encontrar el mejor horario.
    
    Args:
        tamanio_poblacion: Número de individuos por generación
        num_generaciones: Número de iteraciones
        prob_mutacion: Probabilidad de mutación por gen
        elitismo: Número de mejores individuos que pasan directamente
    
    Returns:
        Mejor horario encontrado
    """
    # Crear población inicial
    poblacion = crear_poblacion_inicial(tamanio_poblacion)
    
    # Evaluar población inicial
    for individuo in poblacion:
        calcular_aptitud(individuo)
    
    # Estadísticas para graficar
    mejor_aptitud_por_gen = []
    promedio_aptitud_por_gen = []
    
    print("Generación | Mejor Aptitud | Pen. Duras | Pen. Blandas")
    print("-" * 60)
    
    for generacion in range(num_generaciones):
        # Ordenar por aptitud
        poblacion.sort(key=lambda x: x.aptitud, reverse=True)
        
        mejor = poblacion[0]
        promedio = np.mean([ind.aptitud for ind in poblacion])
        
        mejor_aptitud_por_gen.append(mejor.aptitud)
        promedio_aptitud_por_gen.append(promedio)
        
        # Mostrar progreso cada 50 generaciones
        if generacion % 50 == 0:
            print(f"{generacion:10d} | {mejor.aptitud:13.2f} | {mejor.penalizacion_dura:10d} | {mejor.penalizacion_blanda:12d}")
        
        # Condición de parada: solución perfecta (sin penalizaciones duras)
        if mejor.penalizacion_dura == 0 and mejor.penalizacion_blanda < 20:
            print(f"\n¡Solución óptima encontrada en generación {generacion}!")
            break
        
        # Nueva generación
        nueva_poblacion = poblacion[:elitismo]  # Elitismo
        
        while len(nueva_poblacion) < tamanio_poblacion:
            # Selección
            padre1 = seleccion_torneo(poblacion)
            padre2 = seleccion_torneo(poblacion)
            
            # Cruce
            if random.random() < 0.8:  # 80% probabilidad de cruce
                hijo1, hijo2 = cruce_uniforme(padre1, padre2)
            else:
                hijo1, hijo2 = Horario(padre1.genes), Horario(padre2.genes)
            
            # Mutación
            mutacion(hijo1, prob_mutacion)
            mutacion_inteligente(hijo1, 0.05)
            mutacion(hijo2, prob_mutacion)
            mutacion_inteligente(hijo2, 0.05)
            
            # Evaluar hijos
            calcular_aptitud(hijo1)
            calcular_aptitud(hijo2)
            
            nueva_poblacion.extend([hijo1, hijo2])
        
        poblacion = nueva_poblacion[:tamanio_poblacion]
    
    # Resultado final
    poblacion.sort(key=lambda x: x.aptitud, reverse=True)
    mejor_solucion = poblacion[0]
    
    print("\n" + "=" * 60)
    print("MEJOR SOLUCIÓN ENCONTRADA:")
    print(mejor_solucion)
    
    # Graficar evolución
    graficar_evolucion(mejor_aptitud_por_gen, promedio_aptitud_por_gen)
    
    return mejor_solucion


# ============================================
# VISUALIZACIÓN
# ============================================

def graficar_evolucion(mejor_aptitud: List[float], promedio_aptitud: List[float]):
    """Grafica la evolución de la aptitud."""
    plt.figure(figsize=(10, 6))
    plt.plot(mejor_aptitud, label='Mejor Aptitud', linewidth=2)
    plt.plot(promedio_aptitud, label='Aptitud Promedio', alpha=0.7)
    plt.xlabel('Generación')
    plt.ylabel('Aptitud')
    plt.title('Evolución del Algoritmo Genético')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()


def mostrar_horario(horario: Horario):
    """Muestra el horario en formato legible."""
    turnos_nombres = {0: 'Libre', 1: 'Mañana', 2: 'Tarde', 3: 'Noche'}
    
    print("\nHORARIO GENERADO:")
    print("Enfermera | ", end="")
    for dia in range(min(14, NUM_DIAS)):  # Mostrar solo 2 semanas
        print(f"D{dia+1:2d} ", end="")
    print()
    print("-" * 80)
    
    for enfermera in range(NUM_ENFERMERAS):
        print(f"E{enfermera+1:2d}      | ", end="")
        for dia in range(min(14, NUM_DIAS)):
            turno = horario.genes[enfermera, dia]
            print(f"{turnos_nombres[turno][0]:3s} ", end="")
        print()


# ============================================
# EJECUCIÓN
# ============================================

if __name__ == "__main__":
    print("ALGORITMO GENÉTICO - PLANIFICACIÓN DE TURNOS DE PERSONAL")
    print("=" * 60)
    
    mejor_horario = algoritmo_genetico(
        tamanio_poblacion=150,
        num_generaciones=300,
        prob_mutacion=0.03,
        elitismo=3
    )
    
    mostrar_horario(mejor_horario)
