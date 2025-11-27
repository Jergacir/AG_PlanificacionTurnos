let sessionId = null;
let intervaloProgreso = null;
let preferencias = [];

// Actualizar valores de sliders
document.getElementById('poblacion').addEventListener('input', (e) => {
    document.getElementById('valorPoblacion').textContent = e.target.value;
});

document.getElementById('generaciones').addEventListener('input', (e) => {
    document.getElementById('valorGeneraciones').textContent = e.target.value;
});

document.getElementById('mutacion').addEventListener('input', (e) => {
    document.getElementById('valorMutacion').textContent = e.target.value;
});

// Gestión de preferencias
let diasSemanaSeleccionados = [];

document.getElementById('btnAgregarPreferencia').addEventListener('click', () => {
    const numEnfermeras = parseInt(document.getElementById('enfermeras').value);
    document.getElementById('modalEnfermera').max = numEnfermeras;
    
    // Resetear selecciones
    diasSemanaSeleccionados = [];
    document.querySelectorAll('.dia-semana-btn').forEach(btn => {
        btn.classList.remove('active', 'btn-primary');
        btn.classList.add('btn-outline-primary');
    });
    document.getElementById('modalDiasEspecificos').value = '';
    document.getElementById('modalEsEspecialista').checked = false;
    document.getElementById('previaDiasSeleccionados').style.display = 'none';
    
    const modal = new bootstrap.Modal(document.getElementById('modalPreferencia'));
    modal.show();
});

// Manejar selección de días de la semana (SOLO UNO)
document.querySelectorAll('.dia-semana-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const dia = parseInt(e.currentTarget.getAttribute('data-dia'));
        
        if (diasSemanaSeleccionados.includes(dia)) {
            // Deseleccionar
            diasSemanaSeleccionados = [];
            e.currentTarget.classList.remove('active', 'btn-primary');
            e.currentTarget.classList.add('btn-outline-primary');
        } else {
            // Deseleccionar todos los demás
            document.querySelectorAll('.dia-semana-btn').forEach(b => {
                b.classList.remove('active', 'btn-primary');
                b.classList.add('btn-outline-primary');
            });
            
            // Seleccionar solo este
            diasSemanaSeleccionados = [dia];
            e.currentTarget.classList.remove('btn-outline-primary');
            e.currentTarget.classList.add('active', 'btn-primary');
        }
        
        actualizarPreviaDias();
    });
});

function actualizarPreviaDias() {
    const numDias = parseInt(document.getElementById('dias').value);
    const preview = document.getElementById('previaDiasSeleccionados');
    const lista = document.getElementById('listaDiasSeleccionados');
    
    // Calcular todos los días que coinciden con el día de semana seleccionado
    const diasCalculados = [];
    const nombresDias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
    
    if (diasSemanaSeleccionados.length > 0) {
        for (let dia = 0; dia < numDias; dia++) {
            const diaSemana = dia % 7;
            if (diasSemanaSeleccionados.includes(diaSemana)) {
                diasCalculados.push(dia + 1);
            }
        }
        
        const diaNombre = nombresDias[diasSemanaSeleccionados[0]];
        const cantidad = diasCalculados.length;
        lista.innerHTML = `<strong>${diaNombre}</strong> → ${cantidad} días del mes: ${diasCalculados.join(', ')}`;
        preview.style.display = 'block';
    } else {
        preview.style.display = 'none';
    }
}

document.getElementById('btnGuardarPreferencia').addEventListener('click', () => {
    const numEnfermeras = parseInt(document.getElementById('enfermeras').value);
    const numDias = parseInt(document.getElementById('dias').value);
    
    const enfermera = parseInt(document.getElementById('modalEnfermera').value);
    const esEspecialista = document.getElementById('modalEsEspecialista').checked;
    const diasEspecificos = document.getElementById('modalDiasEspecificos').value;
    
    if (enfermera < 1 || enfermera > numEnfermeras) {
        alert(`Enfermera debe estar entre 1 y ${numEnfermeras}`);
        return;
    }
    
    // Calcular días desde días de semana seleccionados
    const diasArray = [];
    for (let dia = 0; dia < numDias; dia++) {
        const diaSemana = dia % 7;
        if (diasSemanaSeleccionados.includes(diaSemana)) {
            diasArray.push(dia);
        }
    }
    
    // Agregar días específicos
    if (diasEspecificos.trim()) {
        const especificos = diasEspecificos.split(',')
            .map(d => parseInt(d.trim()) - 1)
            .filter(d => d >= 0 && d < numDias && !diasArray.includes(d));
        diasArray.push(...especificos);
    }
    
    if (diasArray.length === 0) {
        alert('Debe seleccionar un día de la semana preferido o ingresar días específicos.');
        return;
    }
    
    preferencias.push({
        enfermera: enfermera - 1,
        dias: diasArray.sort((a, b) => a - b),
        esEspecialista: esEspecialista
    });
    
    actualizarListaPreferencias();
    
    // Limpiar y cerrar modal
    diasSemanaSeleccionados = [];
    document.querySelectorAll('.dia-semana-btn').forEach(btn => {
        btn.classList.remove('active', 'btn-primary');
        btn.classList.add('btn-outline-primary');
    });
    document.getElementById('modalDiasEspecificos').value = '';
    document.getElementById('modalEsEspecialista').checked = false;
    bootstrap.Modal.getInstance(document.getElementById('modalPreferencia')).hide();
});

function actualizarListaPreferencias() {
    const lista = document.getElementById('listaPreferencias');
    
    // Actualizar contador de especialistas
    const numEspecialistas = preferencias.filter(p => p.esEspecialista).length;
    document.getElementById('contadorEspecialistas').textContent = numEspecialistas;
    
    if (preferencias.length === 0) {
        lista.innerHTML = '<small class="text-muted">Sin preferencias configuradas</small>';
        return;
    }
    
    let html = '';
    preferencias.forEach((pref, idx) => {
        const diasTexto = pref.dias.map(d => d + 1).join(', ');
        const especialistaIcon = pref.esEspecialista ? '<i class="bi bi-star-fill text-warning" title="Especialista"></i> ' : '';
        const alertClass = pref.esEspecialista ? 'alert-warning' : 'alert-secondary';
        
        html += `
            <div class="alert ${alertClass} alert-dismissible fade show p-2 mb-2" role="alert">
                <small>${especialistaIcon}<strong>Enfermera ${pref.enfermera + 1}</strong>: ${pref.dias.length} días preferidos</small>
                <button type="button" class="btn-close btn-sm" data-idx="${idx}"></button>
            </div>
        `;
    });
    
    lista.innerHTML = html;
    
    // Agregar event listeners a los botones de eliminar
    lista.querySelectorAll('.btn-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const idx = parseInt(e.target.getAttribute('data-idx'));
            preferencias.splice(idx, 1);
            actualizarListaPreferencias();
        });
    });
}

// Enviar formulario
document.getElementById('formParametros').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const datos = {
        poblacion: document.getElementById('poblacion').value,
        generaciones: document.getElementById('generaciones').value,
        mutacion: document.getElementById('mutacion').value,
        enfermeras: document.getElementById('enfermeras').value,
        dias: document.getElementById('dias').value,
        preferencias: preferencias
    };
    
    // Ocultar mensaje inicial y resultados
    document.getElementById('mensajeInicial').style.display = 'none';
    document.getElementById('areaResultados').style.display = 'none';
    
    // Mostrar área de progreso
    document.getElementById('areaProgreso').style.display = 'block';
    document.getElementById('btnGenerar').disabled = true;
    
    try {
        const response = await fetch('/iniciar_ag', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        });
        
        const resultado = await response.json();
        sessionId = resultado.session_id;
        
        // Iniciar monitoreo de progreso
        intervaloProgreso = setInterval(actualizarProgreso, 500);
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error al iniciar el algoritmo genético');
        document.getElementById('btnGenerar').disabled = false;
    }
});

// Actualizar progreso
async function actualizarProgreso() {
    if (!sessionId) return;
    
    try {
        const response = await fetch(`/obtener_progreso/${sessionId}`);
        const progreso = await response.json();
        
        if (progreso.error) {
            clearInterval(intervaloProgreso);
            alert('Error: ' + progreso.error);
            document.getElementById('btnGenerar').disabled = false;
            return;
        }
        
        // Actualizar barra de progreso
        const porcentaje = Math.round(progreso.porcentaje);
        document.getElementById('barraProgreso').style.width = porcentaje + '%';
        document.getElementById('barraProgreso').textContent = porcentaje + '%';
        
        // Actualizar métricas
        document.getElementById('genActual').textContent = 
            `${progreso.generacion_actual}/${progreso.total_generaciones}`;
        document.getElementById('mejorAptitud').textContent = 
            progreso.mejor_aptitud.toFixed(2);
        document.getElementById('penDuras').textContent = progreso.penalizacion_dura;
        document.getElementById('penBlandas').textContent = progreso.penalizacion_blanda;
        
        // Si completó, obtener resultados
        if (progreso.completado) {
            clearInterval(intervaloProgreso);
            await mostrarResultados();
            document.getElementById('btnGenerar').disabled = false;
        }
        
    } catch (error) {
        console.error('Error al obtener progreso:', error);
    }
}

// Mostrar resultados finales
async function mostrarResultados() {
    try {
        const response = await fetch(`/obtener_resultado/${sessionId}`);
        const resultado = await response.json();
        
        // Ocultar progreso
        document.getElementById('areaProgreso').style.display = 'none';
        
        // Mostrar área de resultados
        document.getElementById('areaResultados').style.display = 'block';
        
        // Actualizar indicador de calidad
        mostrarIndicadorCalidad(resultado);
        
        // Actualizar métricas finales
        document.getElementById('aptitudFinal').textContent = resultado.aptitud.toFixed(2);
        document.getElementById('penDurasFinal').textContent = resultado.penalizacion_dura;
        document.getElementById('penBlandasFinal').textContent = resultado.penalizacion_blanda;
        
        // Mostrar violaciones
        mostrarViolaciones(resultado);
        
        // Generar tabla de horarios
        generarTablaHorarios(resultado.horario, resultado.especialistas || []);
        
    } catch (error) {
        console.error('Error al obtener resultados:', error);
    }
}

// Mostrar indicador de calidad del horario
function mostrarIndicadorCalidad(resultado) {
    const alerta = document.getElementById('alertaCalidad');
    const icono = document.getElementById('calidadIcono');
    const texto = document.getElementById('calidadTexto');
    const descripcion = document.getElementById('calidadDescripcion');
    
    if (resultado.es_optimo) {
        alerta.className = 'alert alert-success mb-4';
        icono.className = 'bi bi-check-circle-fill';
        texto.textContent = 'Horario Óptimo';
        descripcion.textContent = '¡Excelente! El horario cumple todas las restricciones duras y tiene mínimas violaciones blandas.';
    } else if (resultado.es_aceptable) {
        alerta.className = 'alert alert-warning mb-4';
        icono.className = 'bi bi-exclamation-circle-fill';
        texto.textContent = 'Horario Aceptable';
        descripcion.textContent = 'El horario cumple todas las restricciones obligatorias, pero tiene algunas restricciones blandas sin cumplir.';
    } else {
        alerta.className = 'alert alert-danger mb-4';
        icono.className = 'bi bi-x-circle-fill';
        texto.textContent = 'Horario No Válido';
        descripcion.textContent = '¡Atención! El horario viola restricciones obligatorias. Se recomienda ejecutar el algoritmo con más generaciones.';
    }
}

// Mostrar violaciones detalladas
function mostrarViolaciones(resultado) {
    const divDuras = document.getElementById('violacionesDuras');
    const divBlandas = document.getElementById('violacionesBlandas');
    
    // Violaciones duras
    if (Object.keys(resultado.violaciones_duras).length === 0) {
        divDuras.innerHTML = '<p class="text-success mb-0"><i class="bi bi-check-circle"></i> ¡Sin violaciones!</p>';
    } else {
        let html = '<ul class="list-unstyled mb-0">';
        for (const [tipo, violaciones] of Object.entries(resultado.violaciones_duras)) {
            const titulo = {
                'noche_manana': 'Turnos Noche-Mañana consecutivos',
                'dias_consecutivos': 'Días consecutivos excedidos',
                'especialistas': 'Falta de especialistas',
                'cobertura': 'Cobertura mínima insuficiente'
            }[tipo] || tipo;
            
            html += `<li class="mb-2"><strong>${titulo}:</strong><ul class="small">`;
            violaciones.forEach(v => {
                html += `<li>${v}</li>`;
            });
            html += '</ul></li>';
        }
        html += '</ul>';
        divDuras.innerHTML = html;
    }
    
    // Violaciones blandas
    if (Object.keys(resultado.violaciones_blandas).length === 0) {
        divBlandas.innerHTML = '<p class="text-success mb-0"><i class="bi bi-check-circle"></i> ¡Sin violaciones!</p>';
    } else {
        let html = '<ul class="list-unstyled mb-0">';
        for (const [tipo, violaciones] of Object.entries(resultado.violaciones_blandas)) {
            const titulo = {
                'preferencias': 'Preferencias no respetadas',
                'equidad': 'Equidad de carga de trabajo',
                'noches': 'Distribución de turnos nocturnos'
            }[tipo] || tipo;
            
            html += `<li class="mb-2"><strong>${titulo}:</strong><ul class="small">`;
            violaciones.forEach(v => {
                html += `<li>${v}</li>`;
            });
            html += '</ul></li>';
        }
        html += '</ul>';
        divBlandas.innerHTML = html;
    }
}

// Generar tabla de horarios
let especialistasGlobal = [];

function generarTablaHorarios(horario, especialistas = []) {
    const encabezado = document.getElementById('encabezadoTabla');
    const cuerpo = document.getElementById('cuerpoTabla');
    
    especialistasGlobal = especialistas;
    
    // Mostrar leyenda si hay especialistas
    if (especialistas.length > 0) {
        document.getElementById('leyendaEspecialistas').style.display = 'inline';
    }
    
    // Limpiar tabla
    encabezado.innerHTML = '';
    cuerpo.innerHTML = '';
    
    const numDias = horario[0].turnos.length;
    
    // Crear encabezado
    let htmlEncabezado = '<th>Enfermera</th>';
    for (let dia = 0; dia < numDias; dia++) {
        htmlEncabezado += `<th>Día ${dia + 1}</th>`;
    }
    encabezado.innerHTML = htmlEncabezado;
    
    // Crear filas
    horario.forEach((fila, idx) => {
        const enfermeraNum = idx + 1;
        const esEspecialista = especialistas.includes(enfermeraNum);
        const especialistaIcon = esEspecialista ? '<i class="bi bi-star-fill text-warning"></i> ' : '';
        const filaClass = esEspecialista ? 'table-warning' : '';
        
        let htmlFila = `<td class="fw-bold ${filaClass}">${especialistaIcon}${fila.enfermera}</td>`;
        
        fila.turnos.forEach(turno => {
            const clase = `turno-${turno.toLowerCase()}`;
            htmlFila += `<td class="${clase}">${turno}</td>`;
        });
        
        cuerpo.innerHTML += `<tr class="${filaClass}">${htmlFila}</tr>`;
    });
}

// Descargar CSV
document.getElementById('btnDescargar').addEventListener('click', async () => {
    if (!sessionId) return;
    
    const response = await fetch(`/obtener_resultado/${sessionId}`);
    const resultado = await response.json();
    
    let csv = 'Enfermera,';
    const numDias = resultado.horario[0].turnos.length;
    for (let i = 0; i < numDias; i++) {
        csv += `Día ${i + 1},`;
    }
    csv = csv.slice(0, -1) + '\n';
    
    resultado.horario.forEach(fila => {
        csv += fila.enfermera + ',';
        csv += fila.turnos.join(',') + '\n';
    });
    
    // Descargar archivo
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'horario_turnos.csv';
    a.click();
});
