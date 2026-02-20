"""
Test independiente para verificar la conexión a MySQL y la creación de tablas.
Ejecutar desde la carpeta code/:
    python -m tests.test_database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from database.repository import engine, check_connection, create_tables, get_connection
from database.models import Alumno, Progreso
from sqlalchemy import text


def test_settings():
    """1. Verificar que las variables de configuración MySQL están definidas."""
    print("=" * 60)
    print("TEST 1: Variables de configuración MySQL")
    print("=" * 60)
    required = {
        "MYSQL_HOST": settings.MYSQL_HOST,
        "MYSQL_PORT": settings.MYSQL_PORT,
        "MYSQL_USER": settings.MYSQL_USER,
        "MYSQL_PASSWORD": settings.MYSQL_PASSWORD,
        "MYSQL_DB": settings.MYSQL_DB,
    }
    all_ok = True
    for key, value in required.items():
        status = "OK" if value else "FALTA"
        if not value:
            all_ok = False
        print(f"  {key}: {value} [{status}]")

    if all_ok:
        print(">> PASS: Todas las variables están definidas.\n")
    else:
        print(">> FAIL: Faltan variables de configuración.\n")
    return all_ok


def test_check_connection():
    """2. Verificar que check_connection() conecta a MySQL correctamente."""
    print("=" * 60)
    print("TEST 2: check_connection()")
    print("=" * 60)
    try:
        result = check_connection()
        if result:
            print(">> PASS: Conexión exitosa a MySQL.\n")
        else:
            print(">> FAIL: check_connection() retornó False.\n")
        return result
    except Exception as e:
        print(f">> FAIL: Excepción -> {e}\n")
        return False


def test_create_tables():
    """3. Verificar que las tablas se crean sin errores."""
    print("=" * 60)
    print("TEST 3: create_tables()")
    print("=" * 60)
    try:
        create_tables()
        # Verificar que las tablas existen consultándolas
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES;"))
            tables = [row[0] for row in result]
            print(f"  Tablas encontradas: {tables}")

            expected = ["alumnos", "progresos"]
            missing = [t for t in expected if t not in tables]
            if missing:
                print(f">> FAIL: Faltan tablas -> {missing}\n")
                return False

        print(">> PASS: Tablas 'alumnos' y 'progresos' creadas correctamente.\n")
        return True
    except Exception as e:
        print(f">> FAIL: Excepción -> {e}\n")
        return False


def test_get_connection():
    """4. Verificar que get_connection() devuelve una sesión funcional."""
    print("=" * 60)
    print("TEST 4: get_connection() (sesión SQLAlchemy)")
    print("=" * 60)
    try:
        gen = get_connection()
        session = next(gen)
        # Ejecutar una consulta simple para verificar que la sesión funciona
        result = session.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1, f"Se esperaba 1, se obtuvo {value}"
        # Cerrar la sesión limpiamente
        try:
            next(gen)
        except StopIteration:
            pass
        print(">> PASS: Sesión SQLAlchemy funcional.\n")
        return True
    except Exception as e:
        print(f">> FAIL: Excepción -> {e}\n")
        return False


def test_crud_basico():
    """5. Verificar operaciones CRUD básicas con la tabla Alumno."""
    print("=" * 60)
    print("TEST 5: CRUD básico (Alumno)")
    print("=" * 60)
    gen = get_connection()
    session = next(gen)
    try:
        # Crear
        alumno_test = Alumno(
            nombre="Test Usuario",
            nivel="principiante",
            email="test_db_connection@test.com",
            password="hashed_test_password"
        )
        session.add(alumno_test)
        session.commit()
        print(f"  Creado alumno con id={alumno_test.id}")

        # Leer
        found = session.query(Alumno).filter_by(email="test_db_connection@test.com").first()
        assert found is not None, "No se encontró el alumno creado"
        assert found.nombre == "Test Usuario"
        print(f"  Leído alumno: {found.nombre}")

        # Eliminar (limpiar)
        session.delete(found)
        session.commit()
        print("  Eliminado alumno de prueba")

        print(">> PASS: CRUD básico funciona correctamente.\n")
        return True
    except Exception as e:
        session.rollback()
        print(f">> FAIL: Excepción -> {e}\n")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("   TEST DE CONEXIÓN A BASE DE DATOS MySQL")
    print("#" * 60 + "\n")

    results = {}
    results["settings"] = test_settings()

    if results["settings"]:
        results["check_connection"] = test_check_connection()
        results["create_tables"] = test_create_tables()
        results["get_connection"] = test_get_connection()
        results["crud_basico"] = test_crud_basico()
    else:
        print("Abortando tests: faltan variables de configuración.\n")

    # Resumen
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    for name, passed in results.items():
        print(f"  {name}: {'PASS' if passed else 'FAIL'}")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"\n  {passed}/{total} tests pasados.")

    if passed < total:
        sys.exit(1)
