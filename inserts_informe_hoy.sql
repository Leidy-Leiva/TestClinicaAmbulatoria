-- ============================================
-- INSERTS PARA GENERAR INFORME DEL DÍA 2026-04-13
-- Usando datos existentes en la BD
-- ============================================

-- 1. Insertar turnos para hoy (2026-04-13) - Clínica Centro Médico Norte (id=2)
INSERT INTO turnos (paciente_id, medico_id, clinica_id, fecha, hora, tipo_atencion, motivo, estado, prioridad)
VALUES 
(1, 3, 2, '2026-04-13', '08:00', 'Dermatología', 'Seguimiento de lesión en piel', 'atendido', 2),
(2, 4, 2, '2026-04-13', '09:00', 'Cardiología', 'Dolor torácico ocasional', 'atendido', 3),
(3, 3, 2, '2026-04-13', '10:30', 'Dermatología', 'Manchas en la cara', 'atendido', 1),
(4, 4, 2, '2026-04-13', '11:00', 'Cardiología', 'Chequeo preventivo', 'atendido', 1),
(5, 3, 2, '2026-04-13', '14:00', 'Dermatología', 'Nueva valoración', 'programado', 2);

-- 2. Insertar atenciones para hoy (2026-04-13)
INSERT INTO atenciones (turno_id, paciente_id, medico_id, diagnostico, sintomas, tratamiento, observaciones, estado)
VALUES 
(25, 1, 3, 'Dermatitis seborreica en seguimiento', 'Lesión en cuero cabelludo con descamación', 'Crema de ketoconazol 2% aplicación diaria por 14 días', 'Mejoría respecto aControls anteriores. Continuar tratamiento.', 'atendido'),
(26, 2, 4, 'Dolores torácicos tipo anginosos', 'Dolor precordial irradiado al brazo izquierdo, relación con esfuerzo', 'Eco Doppler cardíaco programado. Ácido acetilsalicílico 100mg diario.', 'Sin hallazgos agudos. Requiere estudio completo.', 'atendido'),
(27, 3, 3, 'Melasma facial', 'Manchas cafes en mejillas y frente', 'Protector solar SPF 50+. Hidratante con vitamina C.', 'Evitar exposición solar directa. Control en 30 días.', 'atendido'),
(28, 4, 4, 'Hipertensión arterial en control', 'Asintomático, presión controlada', 'Continuar Losartán 50mg. Reducir sal. Ejercicio regular.', 'Presión arterial 128/82 mmHg. Buen control.', 'atendido');

-- 3. Insertar recetas para hoy (2026-04-13)
INSERT INTO recetas (atencion_id, paciente_id, medicamento_id, cantidad, dosis, frecuencia, duracion, instrucciones)
VALUES 
-- Recetas para atención 25 (paciente 1 - Dermatología)
(11, 1, 4, 14, '1 crema', 'Aplicar 2 veces al día', '14 días', 'Aplicar sobre la lesion después del baño'),
-- Recetas para atención 26 (paciente 2 - Cardiología)
(12, 2, 1, 30, '1 tableta', 'Una vez al día', '30 días', 'Tomar en la mañana con el estómago vacío'),
(12, 2, 11, 20, '1 tableta', 'Cada 12 horas', '10 días', 'Tomar con comida para evitar malestar estomacal'),
-- Recetas para atención 27 (paciente 3 - Dermatología)
(13, 3, 9, 30, '1 tableta', 'Una vez al día', '30 días', 'Tomar en la noche. Evitar exposición al sol'),
(13, 3, 1, 20, '1 tableta', 'Cada 8 horas si hay dolor', '5 días', 'Solo si presenta dolor o inflamación'),
-- Recetas para atención 28 (paciente 4 - Cardiología)
(14, 4, 7, 30, '1 tableta', 'Una vez al día', '30 días', 'Tomar a la misma hora todos los días');