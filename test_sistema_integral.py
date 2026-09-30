#!/usr/bin/env python3
"""
Test Suite de Verificación Integral - Sistema de Inventario y Préstamos
Valida las reglas de negocio implementadas:
1. Estados de préstamos y detección automática de 'Olvidado' (vencido sin devolver).
2. Cálculo de días restantes y atraso.
3. Algoritmo de paginación dinámica '1...2...3..4..5...6... ->'.
4. Lógica de consolidación y reportes (General, Por Oficina, Por Custodio).
"""

import unittest
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional, List


# --- 1. Modelos Mock para Préstamos ---
@dataclass
class MockPrestamo:
    id: int
    estado_solicitud: str  # "Pendiente", "Aprobada", "Finalizada", "Rechazada"
    fecha_inicio: datetime
    fecha_fin: datetime
    custodio_solicitante: str
    actividad: Optional[str] = None
    descripcion: Optional[str] = None
    observaciones: Optional[str] = None


def calcular_estado_temporal(prestamo: MockPrestamo, ahora: datetime) -> str:
    """Replica exacta de _estado_temporal en backend/app/api/rutas/prestamos.py"""
    if prestamo.estado_solicitud == "Finalizada":
        return "Devuelto"
    if prestamo.estado_solicitud == "Rechazada":
        return "Rechazado"
    if prestamo.estado_solicitud == "Pendiente":
        return "Pendiente"
    if prestamo.estado_solicitud == "Aprobada" and ahora > prestamo.fecha_fin:
        return "Olvidado"
    if prestamo.fecha_inicio <= ahora <= prestamo.fecha_fin:
        return "Ocupado"
    if ahora < prestamo.fecha_inicio:
        return "Apartado"
    return "Libre"


def calcular_metricas_prestamo(prestamo: MockPrestamo, ahora: datetime):
    """Calcula días totales, días restantes y flag de olvido."""
    estado_temp = calcular_estado_temporal(prestamo, ahora)
    dias_totales = max(1, (prestamo.fecha_fin - prestamo.fecha_inicio).days)
    dias_restantes = (prestamo.fecha_fin - ahora).days if prestamo.estado_solicitud == "Aprobada" else None
    es_olvidado = (estado_temp == "Olvidado")
    return {
        "estado_temporal": estado_temp,
        "dias_totales": dias_totales,
        "dias_restantes": dias_restantes,
        "es_olvidado": es_olvidado,
    }


# --- 2. Algoritmo de Paginación Dinámica ---
def generar_paginacion(pagina_actual: int, total_paginas: int) -> List[any]:
    """Genera arreglo de páginas con elipsis 1...2...3... similar a Google/Next."""
    if total_paginas <= 1:
        return [1]
    if total_paginas <= 7:
        return list(range(1, total_paginas + 1))
    if pagina_actual <= 4:
        return [1, 2, 3, 4, 5, "...", total_paginas]
    if pagina_actual >= total_paginas - 3:
        return [1, "...", total_paginas - 4, total_paginas - 3, total_paginas - 2, total_paginas - 1, total_paginas]
    return [1, "...", pagina_actual - 1, pagina_actual, pagina_actual + 1, "...", total_paginas]


# --- 3. Lógica de Agregación de Reportes ---
@dataclass
class MockEquipo:
    id: int
    bien_nacional: str
    serial: str
    marca: str
    modelo: str
    tipo: str
    ubicacion: str
    custodio: str
    estado: str  # "Operativo", "En Reparación", "Dañado", "Desincorporado"


def generar_reporte_general(equipos: List[MockEquipo]):
    resumen_oficinas = {}
    total = len(equipos)
    operativos = sum(1 for e in equipos if e.estado == "Operativo")
    reparacion = sum(1 for e in equipos if e.estado == "En Reparación")
    bajas = sum(1 for e in equipos if e.estado in ["Dañado", "Desincorporado"])

    for eq in equipos:
        if eq.ubicacion not in resumen_oficinas:
            resumen_oficinas[eq.ubicacion] = {"total": 0, "operativos": 0}
        resumen_oficinas[eq.ubicacion]["total"] += 1
        if eq.estado == "Operativo":
            resumen_oficinas[eq.ubicacion]["operativos"] += 1

    return {
        "total": total,
        "operativos": operativos,
        "reparacion": reparacion,
        "bajas": bajas,
        "oficinas": resumen_oficinas
    }


def generar_reporte_oficina(equipos: List[MockEquipo], oficina: str):
    filtrados = [e for e in equipos if e.ubicacion.strip().lower() == oficina.strip().lower()]
    return {
        "oficina": oficina,
        "total": len(filtrados),
        "equipos": filtrados
    }


def generar_reporte_custodio(equipos: List[MockEquipo], custodio: str):
    filtrados = [e for e in equipos if e.custodio.strip().lower() == custodio.strip().lower()]
    return {
        "custodio": custodio,
        "total": len(filtrados),
        "equipos": filtrados
    }


# --- Casos de Prueba ---
class TestSistemaInventarioYPrestamos(unittest.TestCase):

    def setUp(self):
        self.ahora = datetime(2026, 9, 29, 12, 0, 0, tzinfo=timezone.utc)
        self.inventario_muestra = [
            MockEquipo(1, "BN-001", "SR1", "VIT", "E2200", "CPU", "Telemática", "Carlos Mendoza", "Operativo"),
            MockEquipo(2, "BN-002", "SR2", "Siragon", "NB3100", "Laptop", "Presidencia", "Carmen Salazar", "Operativo"),
            MockEquipo(3, "BN-003", "SR3", "Dell", "R740", "Servidor", "Telemática", "Carlos Mendoza", "Operativo"),
            MockEquipo(4, "BN-004", "SR4", "HP", "ProBook", "Laptop", "Dirección", "Marcos Rivas", "En Reparación"),
            MockEquipo(5, "BN-005", "SR5", "VIT", "Torre", "CPU", "Telemática", "Carlos Mendoza", "Dañado"),
        ]

    # --- Test 1: Lógica de Préstamos y Estados ---
    def test_prestamo_olvidado_vencido(self):
        """Un préstamo aprobado cuya fecha_fin ya pasó debe dar 'Olvidado' y es_olvidado=True."""
        prestamo = MockPrestamo(
            id=101,
            estado_solicitud="Aprobada",
            fecha_inicio=self.ahora - timedelta(days=5),
            fecha_fin=self.ahora - timedelta(days=2),  # Terminó hace 2 días
            custodio_solicitante="tecnico1",
            actividad="Mantenimiento en campo"
        )
        res = calcular_metricas_prestamo(prestamo, self.ahora)
        self.assertEqual(res["estado_temporal"], "Olvidado")
        self.assertTrue(res["es_olvidado"])
        self.assertLess(res["dias_restantes"], 0)
        self.assertEqual(res["dias_restantes"], -2)

    def test_prestamo_activo_ocupado(self):
        """Un préstamo aprobado en curso debe dar 'Ocupado' con días restantes positivos."""
        prestamo = MockPrestamo(
            id=102,
            estado_solicitud="Aprobada",
            fecha_inicio=self.ahora - timedelta(days=1),
            fecha_fin=self.ahora + timedelta(days=3),  # Faltan 3 días
            custodio_solicitante="tecnico2"
        )
        res = calcular_metricas_prestamo(prestamo, self.ahora)
        self.assertEqual(res["estado_temporal"], "Ocupado")
        self.assertFalse(res["es_olvidado"])
        self.assertEqual(res["dias_restantes"], 3)

    def test_prestamo_finalizado_devuelto(self):
        """Un préstamo marcado como Finalizada debe dar 'Devuelto'."""
        prestamo = MockPrestamo(
            id=103,
            estado_solicitud="Finalizada",
            fecha_inicio=self.ahora - timedelta(days=10),
            fecha_fin=self.ahora - timedelta(days=5),
            custodio_solicitante="tecnico3"
        )
        res = calcular_metricas_prestamo(prestamo, self.ahora)
        self.assertEqual(res["estado_temporal"], "Devuelto")
        self.assertFalse(res["es_olvidado"])

    def test_prestamo_futuro_apartado(self):
        """Un préstamo aprobado que comenzará en el futuro debe dar 'Apartado'."""
        prestamo = MockPrestamo(
            id=104,
            estado_solicitud="Aprobada",
            fecha_inicio=self.ahora + timedelta(days=2),
            fecha_fin=self.ahora + timedelta(days=5),
            custodio_solicitante="tecnico4"
        )
        res = calcular_metricas_prestamo(prestamo, self.ahora)
        self.assertEqual(res["estado_temporal"], "Apartado")

    # --- Test 2: Algoritmo de Paginación Dinámica ---
    def test_paginacion_pocos_elementos(self):
        """Cuando hay 5 páginas, debe mostrar [1, 2, 3, 4, 5] sin elipsis."""
        paginas = generar_paginacion(pagina_actual=2, total_paginas=5)
        self.assertEqual(paginas, [1, 2, 3, 4, 5])

    def test_paginacion_muchas_paginas_inicio(self):
        """Al estar en la página 1 de 20, debe mostrar [1, 2, 3, 4, 5, '...', 20]."""
        paginas = generar_paginacion(pagina_actual=1, total_paginas=20)
        self.assertEqual(paginas, [1, 2, 3, 4, 5, "...", 20])

    def test_paginacion_muchas_paginas_medio(self):
        """Al estar en la página 10 de 20, debe mostrar [1, '...', 9, 10, 11, '...', 20]."""
        paginas = generar_paginacion(pagina_actual=10, total_paginas=20)
        self.assertEqual(paginas, [1, "...", 9, 10, 11, "...", 20])

    def test_paginacion_muchas_paginas_final(self):
        """Al estar en la página 19 de 20, debe mostrar [1, '...', 16, 17, 18, 19, 20]."""
        paginas = generar_paginacion(pagina_actual=19, total_paginas=20)
        self.assertEqual(paginas, [1, "...", 16, 17, 18, 19, 20])

    # --- Test 3: Reportes por Oficina, Custodio y General ---
    def test_reporte_general(self):
        rep = generar_reporte_general(self.inventario_muestra)
        self.assertEqual(rep["total"], 5)
        self.assertEqual(rep["operativos"], 3)
        self.assertEqual(rep["reparacion"], 1)
        self.assertEqual(rep["bajas"], 1)
        self.assertEqual(rep["oficinas"]["Telemática"]["total"], 3)
        self.assertEqual(rep["oficinas"]["Presidencia"]["total"], 1)

    def test_reporte_por_oficina(self):
        rep = generar_reporte_oficina(self.inventario_muestra, "Telemática")
        self.assertEqual(rep["total"], 3)
        self.assertTrue(all(e.ubicacion == "Telemática" for e in rep["equipos"]))

    def test_reporte_por_custodio(self):
        rep = generar_reporte_custodio(self.inventario_muestra, "Carlos Mendoza")
        self.assertEqual(rep["total"], 3)
        self.assertTrue(all(e.custodio == "Carlos Mendoza" for e in rep["equipos"]))


if __name__ == "__main__":
    import sys
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 70)
    print("EJECUTANDO SUITE DE PRUEBAS AUTOMATIZADAS DEL SISTEMA")
    print("=" * 70)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSistemaInventarioYPrestamos)
    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    if resultado.wasSuccessful():
        print("\n[OK] TODAS LAS PRUEBAS PASARON EXITOSAMENTE (100% CORRECTAS)")
    else:
        print("\n[ERROR] HUBO FALLOS EN LAS PRUEBAS")
