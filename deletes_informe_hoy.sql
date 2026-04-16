-- ============================================
-- DELETES PARA ELIMINAR LA INFORMACIÓN DEL 2026-04-13
-- ============================================

-- 1. Eliminar recetas del día
DELETE FROM recetas WHERE atencion_id IN (11, 12, 13, 14);

-- 2. Eliminar atenciones del día
DELETE FROM atenciones WHERE id IN (11, 12, 13, 14);

-- 3. Eliminar turnos del día
DELETE FROM turnos WHERE id IN (25, 26, 27, 28, 29);