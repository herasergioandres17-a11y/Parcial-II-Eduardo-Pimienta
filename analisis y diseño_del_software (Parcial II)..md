# Análisis y diseño del software: Sistema de Gestión de Tienda Electrónica

## 1. Entidades y atributos

### Entidad: Producto (`productos`)

Representa un componente o artículo electrónico disponible en el inventario de la tienda.

| Atributo | Tipo SQLite | Descripción |
|---|---|---|
| `id` | INTEGER | Llave primaria, autoincrementable |
| `nombre` | TEXT | Nombre o descripción del componente (obligatorio) |
| `precio` | REAL | Precio unitario del producto (obligatorio) |
| `stock` | INTEGER | Cantidad actual disponible en inventario (obligatorio) |

### Entidad: Venta (`ventas`)

Representa el registro de una transacción de salida de producto del inventario.

| Atributo | Tipo SQLite | Descripción |
|---|---|---|
| `id` | INTEGER | Llave primaria, autoincrementable |
| `producto_id` | INTEGER | Llave foránea que referencia a `productos(id)` |
| `cantidad` | INTEGER | Cantidad de unidades vendidas (obligatorio) |
| `fecha` | TEXT | Fecha y hora en que se registró la venta (`YYYY-MM-DD HH:MM:SS`) |

---

## 2. Modelo de datos y relaciones

```text
+-----------------------+          +-----------------------+
|       productos       |          |        ventas         |
+-----------------------+          +-----------------------+
| id (PK)               | 1      N | id (PK)               |
| nombre                |----------| producto_id (FK)      |
| precio                |          | cantidad              |
| stock                 |          | fecha                 |
+-----------------------+          +-----------------------+
```

### Definición de Relación e Integridad Referencial
- **Cardinalidad:** Un producto puede estar asociado a muchas ventas ($1:N$), pero cada registro de venta pertenece a un único producto.
- **Integridad Referencial:** Se habilita mediante la directiva `PRAGMA foreign_keys = ON;` en SQLite.
- **Restricción de Borrado:** Se configura la cláusula `ON DELETE RESTRICT` en la clave foránea para evitar la eliminación accidental de un producto que posea registros asociados en la tabla `ventas`.

```sql
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL,
    stock INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    fecha TEXT NOT NULL,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT
);
```

---

## 3. Diagrama de arquitectura e interacción

```text
+------------------+       +------------------+       +-------------------+
|     Usuario      | <---> |  Programa Python | <---> |   SQLite (DB)     |
+------------------+       +------------------+       +-------------------+
| Menú interactivo |       | Módulo sqlite3   |       | Base de datos:    |
| Datos de consola |       | Validaciones     |       | tienda_electronica|
| Visualización    |       | Manejo de        |       | .db               |
| de resultados    |       | transacciones    |       | Tablas productos  |
|                  |       | (commit/rollback)|       | y ventas          |
+------------------+       +------------------+       +-------------------+
```

### Flujo de Ejecución:
1. **Entrada de usuario:** El usuario interactúa mediante el menú en la consola e ingresa los datos correspondientes.
2. **Validación en Python:** El programa valida tipos de datos (`int`, `float`), valores no negativos y presencia de datos requeridos.
3. **Consulta parametrizada:** Python envía sentencias SQL utilizando placeholders (`?`) para evitar inyección SQL.
4. **Persistencia en SQLite:** La base de datos ejecuta la instrucción dentro de `tienda_electronica.db`.
5. **Respuesta al usuario:** Python procesa la respuesta de SQLite y muestra mensajes o tablas formateadas en pantalla.

---

## 4. Operaciones al registrar una venta

Para garantizar la consistencia en el inventario, el proceso de registro de una venta ejecuta la siguiente secuencia dentro de una **transacción atómica**:

1. **Recepción de datos:** El usuario proporciona el `id` del producto y la `cantidad` a vender.
2. **Validación de datos de entrada:** Se comprueba que la cantidad sea mayor a cero y que los valores sean enteros válidos.
3. **Verificación de existencia:** Se consulta la tabla `productos` para validar si el `id` ingresado existe.
4. **Comprobación de inventario:** Se verifica que el `stock` disponible sea mayor o igual a la `cantidad` solicitada.
5. **Inicio de transacción:** Se inicia explícitamente el bloque transaccional (`BEGIN TRANSACTION;`).
6. **Registro de la venta:** Se inserta el registro correspondiente en la tabla `ventas` guardando el `producto_id`, la `cantidad` y la `fecha` actual.
7. **Actualización de inventario:** Se resta la cantidad vendida al campo `stock` en la tabla `productos`.
8. **Confirmación de la transacción (`commit`):** Se confirman ambos cambios en la base de datos si todo el proceso fue exitoso.
9. **Manejo de excepciones (`rollback`):** En caso de presentarse algún error en cualquier punto de la transacción, se cancelan los cambios ejecutados para mantener la integridad del inventario.

---

## 5. Explicación de la transacción y el mecanismo de Rollback

Una transacción garantiza la propiedad de **Atomicidad** (ACID): todas las operaciones de un bloque se ejecutan con éxito o ninguna surte efecto.

### Operaciones combinadas
En este sistema, registrar una venta requiere dos modificaciones en la base de datos:

```sql
-- Operación 1: Registrar venta
INSERT INTO ventas (producto_id, cantidad, fecha) VALUES (?, ?, ?);

-- Operación 2: Actualizar stock
UPDATE productos SET stock = stock - ? WHERE id = ?;
```

Si por algún motivo el `INSERT` se ejecuta con éxito pero el `UPDATE` falla (o el sistema colapsa), la venta quedaría guardada sin haber descontado el inventario, provocando **inconsistencias en las existencias**.

### Control con `commit()` y `rollback()`
- **`conexion.commit()`:** Guarda de forma permanente en el disco tanto el registro de la venta como el descuento del stock.
- **`conexion.rollback()`:** Si se captura una excepción durante el proceso, revierte la transacción descartando los cambios temporales y devolviendo la base de datos al estado exacto previo al intento de venta.

### Demostración del Reto Rollback
El método `demostrar_reto_rollback()` simula un fallo inducido (`RuntimeError`) entre la inserción de la venta y la actualización del stock:
```text
1. Stock inicial del producto: 10 unidades.
2. Se ejecuta INSERT en la tabla 'ventas' (Dentro de BEGIN TRANSACTION).
3. Se simula un fallo crítico del sistema (RuntimeError).
4. El bloque 'except' captura la falla y ejecuta 'conexion.rollback()'.
5. Resultado: El stock se mantiene en 10 unidades y no se persiste la venta incompleta.
```

---

## 6. Validaciones e integridad del sistema

- **Entrada de datos limpia:** Se valida que los precios y stocks no contengan valores negativos.
- **Búsqueda segura:** Control de existencia de productos previo a operaciones de venta o actualización.
- **Suficiencia de stock:** Control que impide vender una cantidad superior a las existencias disponibles.
- **Integridad referencial activa:** Captura de la excepción `sqlite3.IntegrityError` que evita eliminar productos que tengan historial de ventas.
- **Inyección SQL:** Todas las consultas SQL emplean la sintaxis de parámetros con el comodín `?` en lugar de concatenación de cadenas.