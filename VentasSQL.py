from datetime import datetime
import sqlite3

DB_NAME = "tienda_electronica.db"


def obtener_conexion():
  """Establece y retorna la conexión a la base de datos SQLite."""
  conexion = sqlite3.connect(DB_NAME)
  conexion.execute("PRAGMA foreign_keys = ON;")
  return conexion


def inicializar_base_datos():
  """Crea las tablas necesarias si no existen."""
  conexion = obtener_conexion()
  cursor = conexion.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT
        )
    """)

  conexion.commit()
  conexion.close()


def registrar_producto():
  print("\n--- REGISTRAR NUEVO PRODUCTO ---")
  nombre = input("Nombre del componente: ").strip()
  try:
    precio = float(input("Precio unitario: "))
    stock = int(input("Cantidad inicial en stock: "))
    if precio < 0 or stock < 0:
      print("Error: El precio y el stock no pueden ser negativos.")
      return
  except ValueError:
    print("Error: Ingrese valores numéricos válidos para precio y stock.")
    return

  conexion = obtener_conexion()
  cursor = conexion.cursor()
  cursor.execute(
      "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
      (nombre, precio, stock),
  )
  conexion.commit()
  conexion.close()
  print("Producto registrado correctamente.")


def consultar_productos():
  conexion = obtener_conexion()
  cursor = conexion.cursor()
  cursor.execute("SELECT id, nombre, precio, stock FROM productos")
  productos = cursor.fetchall()
  conexion.close()

  print("\n--- LISTADO DE PRODUCTOS ---")
  if not productos:
    print("No hay productos registrados.")
    return

  print(f"{'ID':<5} | {'NOMBRE':<25} | {'PRECIO':<10} | {'STOCK':<5}")
  print("-" * 53)
  for p in productos:
    print(f"{p[0]:<5} | {p[1]:<25} | ${p[2]:<9.2f} | {p[3]:<5}")


def actualizar_producto():
  consultar_productos()
  try:
    prod_id = int(input("\nIngrese el ID del producto a actualizar: "))
  except ValueError:
    print("ID inválido.")
    return

  conexion = obtener_conexion()
  cursor = conexion.cursor()
  cursor.execute(
      "SELECT id, nombre, precio, stock FROM productos WHERE id = ?", (prod_id,)
  )
  producto = cursor.fetchone()

  if not producto:
    print("El producto no existe.")
    conexion.close()
    return

  print(
      f"Producto seleccionado: {producto[1]} (Precio: ${producto[2]}, Stock:"
      f" {producto[3]})"
  )
  print("1. Actualizar precio")
  print("2. Actualizar stock")
  opcion = input("Seleccione una opción: ")

  try:
    if opcion == "1":
      nuevo_precio = float(input("Nuevo precio: "))
      if nuevo_precio < 0:
        print("El precio no puede ser negativo.")
        conexion.close()
        return
      cursor.execute(
          "UPDATE productos SET precio = ? WHERE id = ?", (nuevo_precio, prod_id)
      )
      conexion.commit()
      print("Precio actualizado correctamente.")
    elif opcion == "2":
      nuevo_stock = int(input("Nuevo stock: "))
      if nuevo_stock < 0:
        print("El stock no puede ser negativo.")
        conexion.close()
        return
      cursor.execute(
          "UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, prod_id)
      )
      conexion.commit()
      print("Stock actualizado correctamente.")
    else:
      print("Opción no válida.")
  except ValueError:
    print("Error en el valor ingresado.")
  finally:
    conexion.close()


def eliminar_producto():
  consultar_productos()
  try:
    prod_id = int(input("\nIngrese el ID del producto a eliminar: "))
  except ValueError:
    print("ID inválido.")
    return

  conexion = obtener_conexion()
  cursor = conexion.cursor()
  try:
    cursor.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
    if cursor.rowcount == 0:
      print("El producto no existe.")
    else:
      conexion.commit()
      print("Producto eliminado correctamente.")
  except sqlite3.IntegrityError:
    print("Error: No se puede eliminar el producto porque tiene ventas asociadas.")
  finally:
    conexion.close()


def registrar_venta():
  consultar_productos()
  try:
    prod_id = int(input("\nIngrese el ID del producto a vender: "))
    cantidad_venta = int(input("Cantidad a vender: "))
    if cantidad_venta <= 0:
      print("La cantidad debe ser mayor a cero.")
      return
  except ValueError:
    print("Ingrese valores numéricos válidos.")
    return

  conexion = obtener_conexion()
  cursor = conexion.cursor()

  try:
    conexion.execute("BEGIN TRANSACTION;")

    cursor.execute("SELECT stock FROM productos WHERE id = ?", (prod_id,))
    resultado = cursor.fetchone()

    if not resultado:
      raise Exception("El producto especificado no existe.")

    stock_actual = resultado[0]

    if stock_actual < cantidad_venta:
      raise Exception(f"Stock insuficiente. Disponible: {stock_actual}")

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO ventas (producto_id, cantidad, fecha) VALUES (?, ?, ?)",
        (prod_id, cantidad_venta, fecha_actual),
    )

    nuevo_stock = stock_actual - cantidad_venta
    cursor.execute(
        "UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, prod_id)
    )

    conexion.commit()
    print("Venta registrada e inventario actualizado.")

  except Exception as e:
    conexion.rollback()
    print(f"Transacción revertida (Rollback). Motivo: {e}")
  finally:
    conexion.close()


def mostrar_historial_ventas():
  conexion = obtener_conexion()
  cursor = conexion.cursor()

  query = """
        SELECT v.id, p.nombre, v.cantidad, v.fecha 
        FROM ventas v
        JOIN productos p ON v.producto_id = p.id
    """
  cursor.execute(query)
  ventas = cursor.fetchall()
  conexion.close()

  print("\n--- HISTORIAL DE VENTAS ---")
  if not ventas:
    print("No hay ventas registradas.")
    return

  print(
      f"{'ID VENTA':<10} | {'PRODUCTO':<25} | {'CANTIDAD':<10} |"
      f" {'FECHA':<20}"
  )
  print("-" * 72)
  for v in ventas:
    print(f"{v[0]:<10} | {v[1]:<25} | {v[2]:<10} | {v[3]:<20}")


def demostrar_reto_rollback():
  consultar_productos()
  try:
    prod_id = int(
        input("\n[RETO ROLLBACK] Ingrese ID del producto para prueba de error: ")
    )
  except ValueError:
    print("ID inválido.")
    return

  conexion = obtener_conexion()
  cursor = conexion.cursor()

  cursor.execute("SELECT stock FROM productos WHERE id = ?", (prod_id,))
  res = cursor.fetchone()
  if not res:
    print("Producto no encontrado.")
    conexion.close()
    return
  stock_inicial = res[0]
  print(f"Stock inicial antes de la prueba: {stock_inicial}")

  try:
    conexion.execute("BEGIN TRANSACTION;")

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO ventas (producto_id, cantidad, fecha) VALUES (?, ?, ?)",
        (prod_id, 1, fecha_actual),
    )
    print("-> Venta insertada temporalmente en la transacción...")

    print("-> Simulando fallo del sistema antes de actualizar el inventario...")
    raise RuntimeError("Error simulado.")

    conexion.commit()

  except Exception as e:
    conexion.rollback()
    print(f"Excepción capturada: {e}")
    print("Se ejecutó rollback. Cambios revertidos.")
  finally:
    conexion.close()

  conexion = obtener_conexion()
  cursor = conexion.cursor()
  cursor.execute("SELECT stock FROM productos WHERE id = ?", (prod_id,))
  stock_final = cursor.fetchone()[0]
  conexion.close()

  print(f"Stock final después del rollback: {stock_final}")
  if stock_inicial == stock_final:
    print("Prueba exitosa: El stock permaneció intacto.")
  else:
    print("La prueba falló: El stock fue modificado.")


def main():
  inicializar_base_datos()
  while True:
    print("\n========================================")
    print("   SISTEMA DE GESTIÓN - TIENDA ELECTRÓNICA")
    print("========================================")
    print("1. Registrar producto")
    print("2. Consultar productos")
    print("3. Actualizar producto (precio/stock)")
    print("4. Eliminar producto")
    print("5. Registrar venta")
    print("6. Ver historial de ventas (JOIN)")
    print("7. [Reto] Demostrar funcionamiento de Rollback")
    print("8. Salir")

    opcion = input("\nSeleccione una opción (1-8): ").strip()

    if opcion == "1":
      registrar_producto()
    elif opcion == "2":
      consultar_productos()
    elif opcion == "3":
      actualizar_producto()
    elif opcion == "4":
      eliminar_producto()
    elif opcion == "5":
      registrar_venta()
    elif opcion == "6":
      mostrar_historial_ventas()
    elif opcion == "7":
      demostrar_reto_rollback()
    elif opcion == "8":
      print("\nSaliendo del sistema...")
      break
    else:
      print("Opción no válida. Intente de nuevo.")


if __name__ == "__main__":
  main()