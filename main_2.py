import numpy as np
import random
from dataclasses import dataclass
from typing import List, Tuple
import matplotlib.pyplot as plt

# ==================== CONFIGURACIÓN DEL PROBLEMA ====================

@dataclass
class ConfiguracionTurnos:
    """Configuración del problema de turnos"""
    num_enfermeras: int = 10
    num_dias: int = 30
    num_especialistas: int = 3  # Enfermeras que son especialistas
    
    # Tipos de turnos
    LIBRE = 0
    MANANA = 1
    TARDE = 2
    NOCHE = 3
    
    # Requisitos mínimos por turno
    min_enfermeras_manana: int = 3
    min_enfermeras_tarde: int = 3
    min_enfermeras_noche: int = 2
    min_especialistas_turno: int = 1
    
    # Límites laborales
    max_dias_consecutivos: int = 6
    min_descanso_noche_manana: int = 1  # Días de descanso entre noche y mañana
    max_turnos_noche_mes: int = 8
    
    # Pesos de penalizaciones
    peso_restriccion_dura: float = 1000.0
    peso_restriccion_blanda: float = 10.0

@dataclass
class Enfermera:
    """Información de cada enfermera"""
    id: int
    es_especialista: bool
    preferencias_libres: List[int]  # Días que prefiere libres
    max_turnos_noche: int = 8

# ==================== CLASE INDIVIDUO ====================

class Individuo:
    """Representa una solución (horario completo de turnos)"""
    
    def __init__(self, config: ConfiguracionTurnos, enfermeras: List[Enfermera]):
        self.config = config
        self.enfermeras = enfermeras
        # Matriz [enfermera][día] = tipo_turno
        self.cromosoma = np.zeros((config.num_enfermeras, config.num_dias), dtype=int)
        self.aptitud = 0.0
        self.penalizacion_dura = 0.0
        self.penalizacion_blanda = 0.0
        
    def inicializar_aleatorio(self):
        """Genera un horario aleatorio"""
        for enfermera_id in range(self.config.num_enfermeras):
            for dia in range(self.config.num_dias):
                # 30% probabilidad de día libre, resto distribuido entre turnos
                if random.random() < 0.3:
                    self.cromosoma[enfermera_id][dia] = self.config.LIBRE
                else:
                    self.cromosoma[enfermera_id][dia] = random.randint(
                        self.config.MANANA, self.config.NOCHE
                    )
    
    def calcular_aptitud(self) -> float:
        """Calcula la aptitud del horario (menor es mejor)"""
        self.penalizacion_dura = 0.0
        self.penalizacion_blanda = 0.0
        
        # RESTRICCIONES DURAS
        self.penalizacion_dura += self._verificar_noche_manana()
        self.penalizacion_dura += self._verificar_dias_consecutivos()
        self.penalizacion_dura += self._verificar_especialistas_por_turno()
        self.penalizacion_dura += self._verificar_minimo_personal()
        self.penalizacion_dura += self._verificar_max_turnos_noche()
        
        # RESTRICCIONES BLANDAS
        self.penalizacion_blanda += self._verificar_preferencias()
        self.penalizacion_blanda += self._verificar_equidad_carga()
        
        # Aptitud total (queremos minimizar)
        self.aptitud = (self.penalizacion_dura * self.config.peso_restriccion_dura + 
                       self.penalizacion_blanda * self.config.peso_restriccion_blanda)
        
        return self.aptitud
    
    # -------- RESTRICCIONES DURAS --------
    
    def _verificar_noche_manana(self) -> float:
        """Penaliza turno noche seguido de mañana"""
        penalizacion = 0
        for enfermera_id in range(self.config.num_enfermeras):
            for dia in range(self.config.num_dias - 1):
                turno_actual = self.cromosoma[enfermera_id][dia]
                turno_siguiente = self.cromosoma[enfermera_id][dia + 1]
                
                if turno_actual == self.config.NOCHE and turno_siguiente == self.config.MANANA:
                    penalizacion += 1
        
        return penalizacion
    
    def _verificar_dias_consecutivos(self) -> float:
        """Penaliza más de 6 días consecutivos trabajando"""
        penalizacion = 0
        for enfermera_id in range(self.config.num_enfermeras):
            dias_consecutivos = 0
            for dia in range(self.config.num_dias):
                if self.cromosoma[enfermera_id][dia] != self.config.LIBRE:
                    dias_consecutivos += 1
                    if dias_consecutivos > self.config.max_dias_consecutivos:
                        penalizacion += 1
                else:
                    dias_consecutivos = 0
        
        return penalizacion
    
    def _verificar_especialistas_por_turno(self) -> float:
        """Verifica que haya al menos 1 especialista por turno ocupado"""
        penalizacion = 0
        especialistas_ids = [e.id for e in self.enfermeras if e.es_especialista]
        
        for dia in range(self.config.num_dias):
            for tipo_turno in [self.config.MANANA, self.config.TARDE, self.config.NOCHE]:
                # Contar enfermeras en este turno
                enfermeras_en_turno = np.sum(self.cromosoma[:, dia] == tipo_turno)
                
                if enfermeras_en_turno > 0:
                    # Contar especialistas en este turno
                    especialistas_en_turno = sum(
                        1 for esp_id in especialistas_ids 
                        if self.cromosoma[esp_id][dia] == tipo_turno
                    )
                    
                    if especialistas_en_turno < self.config.min_especialistas_turno:
                        penalizacion += 1
        
        return penalizacion
    
    def _verificar_minimo_personal(self) -> float:
        """Verifica personal mínimo por turno"""
        penalizacion = 0
        
        for dia in range(self.config.num_dias):
            enfermeras_manana = np.sum(self.cromosoma[:, dia] == self.config.MANANA)
            enfermeras_tarde = np.sum(self.cromosoma[:, dia] == self.config.TARDE)
            enfermeras_noche = np.sum(self.cromosoma[:, dia] == self.config.NOCHE)
            
            if enfermeras_manana < self.config.min_enfermeras_manana:
                penalizacion += (self.config.min_enfermeras_manana - enfermeras_manana)
            
            if enfermeras_tarde < self.config.min_enfermeras_tarde:
                penalizacion += (self.config.min_enfermeras_tarde - enfermeras_tarde)
            
            if enfermeras_noche < self.config.min_enfermeras_noche:
                penalizacion += (self.config.min_enfermeras_noche - enfermeras_noche)
        
        return penalizacion
    
    def _verificar_max_turnos_noche(self) -> float:
        """Verifica límite de turnos noche por mes"""
        penalizacion = 0
        
        for enfermera_id in range(self.config.num_enfermeras):
            turnos_noche = np.sum(self.cromosoma[enfermera_id, :] == self.config.NOCHE)
            max_permitido = self.enfermeras[enfermera_id].max_turnos_noche
            
            if turnos_noche > max_permitido:
                penalizacion += (turnos_noche - max_permitido)
        
        return penalizacion
    
    # -------- RESTRICCIONES BLANDAS --------
    
    def _verificar_preferencias(self) -> float:
        """Penaliza violación de preferencias personales"""
        penalizacion = 0
        
        for enfermera in self.enfermeras:
            for dia_preferido in enfermera.preferencias_libres:
                if dia_preferido < self.config.num_dias:
                    if self.cromosoma[enfermera.id][dia_preferido] != self.config.LIBRE:
                        penalizacion += 1
        
        return penalizacion
    
    def _verificar_equidad_carga(self) -> float:
        """Penaliza desbalance en la carga de trabajo"""
        dias_trabajados = []
        
        for enfermera_id in range(self.config.num_enfermeras):
            dias = np.sum(self.cromosoma[enfermera_id, :] != self.config.LIBRE)
            dias_trabajados.append(dias)
        
        # Calcular desviación estándar (queremos que sea baja)
        desviacion = np.std(dias_trabajados)
        
        return desviacion
    
    def copiar(self):
        """Crea una copia del individuo"""
        nuevo = Individuo(self.config, self.enfermeras)
        nuevo.cromosoma = self.cromosoma.copy()
        nuevo.aptitud = self.aptitud
        return nuevo

# ==================== OPERADORES GENÉTICOS ====================

def seleccion_torneo(poblacion: List[Individuo], tam_torneo: int = 3) -> Individuo:
    """Selecciona un individuo mediante torneo"""
    competidores = random.sample(poblacion, tam_torneo)
    return min(competidores, key=lambda ind: ind.aptitud)

def cruce_uniforme(padre1: Individuo, padre2: Individuo) -> Tuple[Individuo, Individuo]:
    """Cruce uniforme: intercambia días completos entre padres"""
    hijo1 = padre1.copiar()
    hijo2 = padre2.copiar()
    
    # Por cada día, decidir de qué padre heredar
    for dia in range(padre1.config.num_dias):
        if random.random() < 0.5:
            # Intercambiar columna completa (todos los turnos de ese día)
            hijo1.cromosoma[:, dia] = padre2.cromosoma[:, dia].copy()
            hijo2.cromosoma[:, dia] = padre1.cromosoma[:, dia].copy()
    
    return hijo1, hijo2

def mutacion_adaptativa(individuo: Individuo, prob_mutacion: float):
    """Mutación que cambia turnos aleatorios"""
    for enfermera_id in range(individuo.config.num_enfermeras):
        for dia in range(individuo.config.num_dias):
            if random.random() < prob_mutacion:
                # Cambiar a un turno aleatorio
                individuo.cromosoma[enfermera_id][dia] = random.randint(0, 3)

def mutacion_inteligente(individuo: Individuo):
    """Mutación dirigida a corregir restricciones duras"""
    # Corregir noche-mañana consecutivos
    for enfermera_id in range(individuo.config.num_enfermeras):
        for dia in range(individuo.config.num_dias - 1):
            if (individuo.cromosoma[enfermera_id][dia] == individuo.config.NOCHE and
                individuo.cromosoma[enfermera_id][dia + 1] == individuo.config.MANANA):
                # Cambiar el turno de mañana a libre o tarde
                individuo.cromosoma[enfermera_id][dia + 1] = random.choice(
                    [individuo.config.LIBRE, individuo.config.TARDE]
                )

# ==================== ALGORITMO GENÉTICO PRINCIPAL ====================

class AlgoritmoGeneticoTurnos:
    """Clase principal del Algoritmo Genético"""
    
    def __init__(self, config: ConfiguracionTurnos, enfermeras: List[Enfermera]):
        self.config = config
        self.enfermeras = enfermeras
        self.poblacion: List[Individuo] = []
        self.mejor_individuo: Individuo = None
        self.historial_aptitud = []
        
    def inicializar_poblacion(self, tam_poblacion: int = 100):
        """Crea la población inicial"""
        self.poblacion = []
        for _ in range(tam_poblacion):
            individuo = Individuo(self.config, self.enfermeras)
            individuo.inicializar_aleatorio()
            individuo.calcular_aptitud()
            self.poblacion.append(individuo)
        
        self.mejor_individuo = min(self.poblacion, key=lambda ind: ind.aptitud)
    
    def evolucionar(self, num_generaciones: int = 500, prob_cruce: float = 0.8, 
                    prob_mutacion: float = 0.1, elitismo: int = 2):
        """Ejecuta el algoritmo genético"""
        
        for generacion in range(num_generaciones):
            nueva_poblacion = []
            
            # Elitismo: mantener los mejores
            self.poblacion.sort(key=lambda ind: ind.aptitud)
            for i in range(elitismo):
                nueva_poblacion.append(self.poblacion[i].copiar())
            
            # Generar resto de la población
            while len(nueva_poblacion) < len(self.poblacion):
                # Selección
                padre1 = seleccion_torneo(self.poblacion)
                padre2 = seleccion_torneo(self.poblacion)
                
                # Cruce
                if random.random() < prob_cruce:
                    hijo1, hijo2 = cruce_uniforme(padre1, padre2)
                else:
                    hijo1, hijo2 = padre1.copiar(), padre2.copiar()
                
                # Mutación
                mutacion_adaptativa(hijo1, prob_mutacion)
                mutacion_adaptativa(hijo2, prob_mutacion)
                
                # Mutación inteligente ocasional
                if random.random() < 0.1:
                    mutacion_inteligente(hijo1)
                if random.random() < 0.1:
                    mutacion_inteligente(hijo2)
                
                # Calcular aptitud
                hijo1.calcular_aptitud()
                hijo2.calcular_aptitud()
                
                nueva_poblacion.extend([hijo1, hijo2])
            
            # Reemplazar población
            self.poblacion = nueva_poblacion[:len(self.poblacion)]
            
            # Actualizar mejor individuo
            mejor_actual = min(self.poblacion, key=lambda ind: ind.aptitud)
            if mejor_actual.aptitud < self.mejor_individuo.aptitud:
                self.mejor_individuo = mejor_actual.copiar()
            
            # Guardar historial
            self.historial_aptitud.append(self.mejor_individuo.aptitud)
            
            # Mostrar progreso
            if generacion % 50 == 0:
                print(f"Generación {generacion}: Aptitud = {self.mejor_individuo.aptitud:.2f} "
                      f"(Duras: {self.mejor_individuo.penalizacion_dura:.0f}, "
                      f"Blandas: {self.mejor_individuo.penalizacion_blanda:.2f})")
        
        return self.mejor_individuo
    
    def graficar_evolucion(self):
        """Muestra gráfica de evolución"""
        plt.figure(figsize=(10, 6))
        plt.plot(self.historial_aptitud, linewidth=2)
        plt.xlabel('Generación')
        plt.ylabel('Aptitud (menor es mejor)')
        plt.title('Evolución del Algoritmo Genético')
        plt.grid(True, alpha=0.3)
        plt.show()
    
    def imprimir_solucion(self):
        """Imprime el mejor horario encontrado"""
        print("\n" + "="*80)
        print("MEJOR SOLUCIÓN ENCONTRADA")
        print("="*80)
        print(f"Aptitud Total: {self.mejor_individuo.aptitud:.2f}")
        print(f"Penalización Restricciones Duras: {self.mejor_individuo.penalizacion_dura:.0f}")
        print(f"Penalización Restricciones Blandas: {self.mejor_individuo.penalizacion_blanda:.2f}")
        print("\nHorario (L=Libre, M=Mañana, T=Tarde, N=Noche):")
        print("-"*80)
        
        nombres_turnos = {0: 'L', 1: 'M', 2: 'T', 3: 'N'}
        
        # Encabezado
        print(f"{'Enf':>4} ", end='')
        for dia in range(min(30, self.config.num_dias)):
            print(f"{dia+1:>2}", end=' ')
        print()
        print("-"*80)
        
        # Filas de enfermeras
        for enf_id in range(self.config.num_enfermeras):
            especialista = "*" if self.enfermeras[enf_id].es_especialista else " "
            print(f"{enf_id+1:>3}{especialista} ", end='')
            for dia in range(min(30, self.config.num_dias)):
                turno = self.mejor_individuo.cromosoma[enf_id][dia]
                print(f" {nombres_turnos[turno]}", end=' ')
            print()
        
        print("\n* = Especialista")

# ==================== EJEMPLO DE USO ====================

if __name__ == "__main__":
    # Configuración
    config = ConfiguracionTurnos(
        num_enfermeras=10,
        num_dias=30,
        num_especialistas=3
    )
    
    # Crear enfermeras
    enfermeras = []
    for i in range(config.num_enfermeras):
        es_especialista = i < config.num_especialistas
        # Preferencias aleatorias (2-3 días que prefieren libres)
        preferencias = random.sample(range(30), random.randint(2, 3))
        
        enfermeras.append(Enfermera(
            id=i,
            es_especialista=es_especialista,
            preferencias_libres=preferencias,
            max_turnos_noche=8
        ))
    
    # Crear y ejecutar algoritmo genético
    print("Iniciando Algoritmo Genético para Planificación de Turnos...")
    print(f"Población: 100 | Generaciones: 500\n")
    
    ag = AlgoritmoGeneticoTurnos(config, enfermeras)
    ag.inicializar_poblacion(tam_poblacion=100)
    
    mejor_solucion = ag.evolucionar(
        num_generaciones=500,
        prob_cruce=0.8,
        prob_mutacion=0.15,
        elitismo=2
    )
    
    # Mostrar resultados
    ag.imprimir_solucion()
    ag.graficar_evolucion()