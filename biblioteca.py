import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

# Clase Usuario
class Usuario:
    def __init__(self, idUsuario=None, nombre="", correo=""):
        self.idUsuario = idUsuario
        self.nombre = nombre
        self.correo = correo
    
    def mostrarUsuario(self):
        return f"ID: {self.idUsuario}, Nombre: {self.nombre}, Correo: {self.correo}"

# Clase Material (Clase padre)
class Material:
    def __init__(self, id=None, titulo="", anioPublicacion=0, tipoMaterial=""):
        self.id = id
        self.titulo = titulo
        self.anioPublicacion = anioPublicacion
        self.tipoMaterial = tipoMaterial
    
    def mostrarMaterial(self):
        return f"ID: {self.id}, Titulo: {self.titulo}, Año: {self.anioPublicacion}"

# Clase Libro (hereda de Material)
class Libro(Material):
    def __init__(self, id=None, titulo="", anioPublicacion=0, autor="", isbn=""):
        super().__init__(id, titulo, anioPublicacion, "Libro")
        self.autor = autor
        self.isbn = isbn
    
    def mostrarMaterial(self):
        return f"{super().mostrarMaterial()}, Autor: {self.autor}, ISBN: {self.isbn}"

# Clase Revista (hereda de Material)
class Revista(Material):
    def __init__(self, id=None, titulo="", anioPublicacion=0, numeroEdicion=0):
        super().__init__(id, titulo, anioPublicacion, "Revista")
        self.numeroEdicion = numeroEdicion
    
    def mostrarMaterial(self):
        return f"{super().mostrarMaterial()}, Edición: {self.numeroEdicion}"

# Clase para manejar la conexión a la base de datos
class ConexionBD:
    def __init__(self, host="localhost", database="biblioteca", user="root", password=""):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.conexion = None
    
    def conectar(self):
        try:
            self.conexion = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            if self.conexion.is_connected():
                return True
        except Error as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a MySQL:\n{e}")
            return False
    
    def desconectar(self):
        if self.conexion and self.conexion.is_connected():
            self.conexion.close()

# Clase para operaciones CRUD de Usuario
class UsuarioDAO:
    def __init__(self, conexion):
        self.conexion = conexion
    
    def guardarUsuario(self, usuario):
        try:
            cursor = self.conexion.cursor()
            query = "INSERT INTO Usuario (nombre, correo) VALUES (%s, %s)"
            valores = (usuario.nombre, usuario.correo)
            cursor.execute(query, valores)
            self.conexion.commit()
            cursor.close()
            return True
        except Error as e:
            messagebox.showerror("Error", f"Error al guardar usuario:\n{e}")
            return False
    
    def buscarUsuarioPorNombre(self, nombre):
        try:
            cursor = self.conexion.cursor()
            query = "SELECT * FROM Usuario WHERE nombre LIKE %s"
            cursor.execute(query, (f"%{nombre}%",))
            resultados = cursor.fetchall()
            cursor.close()
            
            usuarios = []
            for row in resultados:
                usuario = Usuario(row[0], row[1], row[2])
                usuarios.append(usuario)
            return usuarios
        except Error as e:
            messagebox.showerror("Error", f"Error al buscar usuario:\n{e}")
            return []
    
    def listarTodos(self):
        try:
            cursor = self.conexion.cursor()
            query = "SELECT * FROM Usuario"
            cursor.execute(query)
            resultados = cursor.fetchall()
            cursor.close()
            
            usuarios = []
            for row in resultados:
                usuario = Usuario(row[0], row[1], row[2])
                usuarios.append(usuario)
            return usuarios
        except Error as e:
            messagebox.showerror("Error", f"Error al listar usuarios:\n{e}")
            return []
    
    # NUEVO: Método para eliminar usuario (mover a papelera)
    def eliminarUsuario(self, idUsuario):
        try:
            cursor = self.conexion.cursor()
            
            # Primero obtener los datos del usuario
            query_select = "SELECT * FROM Usuario WHERE idUsuario = %s"
            cursor.execute(query_select, (idUsuario,))
            usuario = cursor.fetchone()
            
            if not usuario:
                messagebox.showwarning("Advertencia", "Usuario no encontrado")
                return False
            
            # Guardar en tabla de eliminados
            query_backup = "INSERT INTO Usuario_Eliminado (idUsuario, nombre, correo) VALUES (%s, %s, %s)"
            cursor.execute(query_backup, (usuario[0], usuario[1], usuario[2]))
            
            # Eliminar de tabla principal
            query_delete = "DELETE FROM Usuario WHERE idUsuario = %s"
            cursor.execute(query_delete, (idUsuario,))
            
            self.conexion.commit()
            cursor.close()
            return True
        except Error as e:
            messagebox.showerror("Error", f"Error al eliminar usuario:\n{e}")
            self.conexion.rollback()
            return False
    
    # NUEVO: Método para listar usuarios eliminados
    def listarEliminados(self):
        try:
            cursor = self.conexion.cursor()
            query = "SELECT * FROM Usuario_Eliminado ORDER BY fechaEliminacion DESC"
            cursor.execute(query)
            resultados = cursor.fetchall()
            cursor.close()
            
            usuarios = []
            for row in resultados:
                usuario = Usuario(row[0], row[1], row[2])
                usuarios.append(usuario)
            return usuarios
        except Error as e:
            messagebox.showerror("Error", f"Error al listar eliminados:\n{e}")
            return []
    
    # NUEVO: Método para recuperar usuario
    def recuperarUsuario(self, idUsuario):
        try:
            cursor = self.conexion.cursor()
            
            # Obtener datos del usuario eliminado
            query_select = "SELECT * FROM Usuario_Eliminado WHERE idUsuario = %s"
            cursor.execute(query_select, (idUsuario,))
            usuario = cursor.fetchone()
            
            if not usuario:
                messagebox.showwarning("Advertencia", "Usuario no encontrado en papelera")
                return False
            
            # Restaurar en tabla principal
            query_restore = "INSERT INTO Usuario (idUsuario, nombre, correo) VALUES (%s, %s, %s)"
            cursor.execute(query_restore, (usuario[0], usuario[1], usuario[2]))
            
            # Eliminar de papelera
            query_delete = "DELETE FROM Usuario_Eliminado WHERE idUsuario = %s"
            cursor.execute(query_delete, (idUsuario,))
            
            self.conexion.commit()
            cursor.close()
            return True
        except Error as e:
            messagebox.showerror("Error", f"Error al recuperar usuario:\n{e}")
            self.conexion.rollback()
            return False

# Clase para operaciones CRUD de Libro
class LibroDAO:
    def __init__(self, conexion):
        self.conexion = conexion
    
    def guardarLibro(self, libro):
        try:
            cursor = self.conexion.cursor()
            query_material = "INSERT INTO Material (titulo, anioPublicacion, tipoMaterial) VALUES (%s, %s, %s)"
            valores_material = (libro.titulo, libro.anioPublicacion, 'Libro')
            cursor.execute(query_material, valores_material)
            material_id = cursor.lastrowid
            query_libro = "INSERT INTO Libro (id, autor, isbn) VALUES (%s, %s, %s)"
            valores_libro = (material_id, libro.autor, libro.isbn)
            cursor.execute(query_libro, valores_libro)
            self.conexion.commit()
            cursor.close()
            return True
        except Error as e:
            messagebox.showerror("Error", f"Error al guardar libro:\n{e}")
            self.conexion.rollback()
            return False
    
    def buscarLibroPorTitulo(self, titulo):
        try:
            cursor = self.conexion.cursor()
            query = """
                SELECT m.id, m.titulo, m.anioPublicacion, l.autor, l.isbn
                FROM Material m 
                INNER JOIN Libro l ON m.id = l.id 
                WHERE m.titulo LIKE %s
                ORDER BY m.id
            """
            cursor.execute(query, (f"%{titulo}%",))
            resultados = cursor.fetchall()
            cursor.close()
            
            libros = []
            for row in resultados:
                libro = Libro(row[0], row[1], row[2], row[3], row[4])
                libros.append(libro)
            return libros
        except Error as e:
            messagebox.showerror("Error", f"Error al buscar libro:\n{e}")
            return []
    
    def listarTodos(self):
        try:
            cursor = self.conexion.cursor()
            query = """
                SELECT m.id, m.titulo, m.anioPublicacion, l.autor, l.isbn
                FROM Material m 
                INNER JOIN Libro l ON m.id = l.id 
                ORDER BY m.id
            """
            cursor.execute(query)
            resultados = cursor.fetchall()
            cursor.close()
            
            libros = []
            for row in resultados:
                libro = Libro(row[0], row[1], row[2], row[3], row[4])
                libros.append(libro)
            return libros
        except Error as e:
            messagebox.showerror("Error", f"Error al listar libros:\n{e}")
            return []
    
    # NUEVO: Método para eliminar libro
    def eliminarLibro(self, idLibro):
        try:
            cursor = self.conexion.cursor()
            
            # Obtener datos del libro
            query_libro = """
                SELECT m.id, m.titulo, m.anioPublicacion, m.tipoMaterial, l.autor, l.isbn
                FROM Material m 
                INNER JOIN Libro l ON m.id = l.id 
                WHERE m.id = %s
            """
            cursor.execute(query_libro, (idLibro,))
            libro = cursor.fetchone()
            
            if not libro:
                messagebox.showwarning("Advertencia", "Libro no encontrado")
                return False
            
            # Guardar en tablas de eliminados
            query_backup_libro = "INSERT INTO Libro_Eliminado (id, autor, isbn) VALUES (%s, %s, %s)"
            cursor.execute(query_backup_libro, (libro[0], libro[4], libro[5]))
            
            query_backup_material = "INSERT INTO Material_Eliminado (id, titulo, anioPublicacion, tipoMaterial) VALUES (%s, %s, %s, %s)"
            cursor.execute(query_backup_material, (libro[0], libro[1], libro[2], libro[3]))
            
            # Eliminar de tablas principales
            query_delete_libro = "DELETE FROM Libro WHERE id = %s"
            cursor.execute(query_delete_libro, (idLibro,))
            
            query_delete_material = "DELETE FROM Material WHERE id = %s"
            cursor.execute(query_delete_material, (idLibro,))
            
            self.conexion.commit()
            cursor.close()
            return True
        except Error as e:
            messagebox.showerror("Error", f"Error al eliminar libro:\n{e}")
            self.conexion.rollback()
            return False
    
    # NUEVO: Listar libros eliminados
    def listarEliminados(self):
        try:
            cursor = self.conexion.cursor()
            query = """
                SELECT m.id, m.titulo, m.anioPublicacion, l.autor, l.isbn
                FROM Material_Eliminado m 
                INNER JOIN Libro_Eliminado l ON m.id = l.id 
                ORDER BY m.fechaEliminacion DESC
            """
            cursor.execute(query)
            resultados = cursor.fetchall()
            cursor.close()
            
            libros = []
            for row in resultados:
                libro = Libro(row[0], row[1], row[2], row[3], row[4])
                libros.append(libro)
            return libros
        except Error as e:
            messagebox.showerror("Error", f"Error al listar eliminados:\n{e}")
            return []
    
    # NUEVO: Recuperar libro
    def recuperarLibro(self, idLibro):
        try:
            cursor = self.conexion.cursor()
            
            # Obtener datos eliminados
            query_libro = """
                SELECT m.id, m.titulo, m.anioPublicacion, m.tipoMaterial, l.autor, l.isbn
                FROM Material_Eliminado m 
                INNER JOIN Libro_Eliminado l ON m.id = l.id 
                WHERE m.id = %s
            """
            cursor.execute(query_libro, (idLibro,))
            libro = cursor.fetchone()
            
            if not libro:
                messagebox.showwarning("Advertencia", "Libro no encontrado en papelera")
                return False
            
            # Restaurar en tablas principales
            query_restore_material = "INSERT INTO Material (id, titulo, anioPublicacion, tipoMaterial) VALUES (%s, %s, %s, %s)"
            cursor.execute(query_restore_material, (libro[0], libro[1], libro[2], libro[3]))
            
            query_restore_libro = "INSERT INTO Libro (id, autor, isbn) VALUES (%s, %s, %s)"
            cursor.execute(query_restore_libro, (libro[0], libro[4], libro[5]))
            
            # Eliminar de papelera
            query_delete_libro = "DELETE FROM Libro_Eliminado WHERE id = %s"
            cursor.execute(query_delete_libro, (idLibro,))
            
            query_delete_material = "DELETE FROM Material_Eliminado WHERE id = %s"
            cursor.execute(query_delete_material, (idLibro,))
            
            self.conexion.commit()
            cursor.close()
            return True
        except Error as e:
            messagebox.showerror("Error", f"Error al recuperar libro:\n{e}")
            self.conexion.rollback()
            return False

# Clase para operaciones CRUD de Revista
class RevistaDAO:
    def __init__(self, conexion):
        self.conexion = conexion
    
    def guardarRevista(self, revista):
        try:
            cursor = self.conexion.cursor()
            query_material = "INSERT INTO Material (titulo, anioPublicacion, tipoMaterial) VALUES (%s, %s, %s)"
            valores_material = (revista.titulo, revista.anioPublicacion, 'Revista')
            cursor.execute(query_material, valores_material)
            material_id = cursor.lastrowid
            query_revista = "INSERT INTO Revista (id, numeroEdicion) VALUES (%s, %s)"
            valores_revista = (material_id, revista.numeroEdicion)
            cursor.execute(query_revista, valores_revista)
            self.conexion.commit()
            cursor.close()
            return True
        except Error as e:
            messagebox.showerror("Error", f"Error al guardar revista:\n{e}")
            self.conexion.rollback()
            return False
    
    def buscarRevistaPorTitulo(self, titulo):
        try:
            cursor = self.conexion.cursor()
            query = """
                SELECT m.id, m.titulo, m.anioPublicacion, r.numeroEdicion
                FROM Material m
                INNER JOIN Revista r ON m.id = r.id 
                WHERE m.titulo LIKE %s
                ORDER BY m.id
            """
            cursor.execute(query, (f"%{titulo}%",))
            resultados = cursor.fetchall()
            cursor.close()
            
            revistas = []
            for row in resultados:
                revista = Revista(row[0], row[1], row[2], row[3])
                revistas.append(revista)
            return revistas
        except Error as e:
            messagebox.showerror("Error", f"Error al buscar revista:\n{e}")
            return []
    
    def listarTodas(self):
        try:
            cursor = self.conexion.cursor()
            query = """
                SELECT m.id, m.titulo, m.anioPublicacion, r.numeroEdicion
                FROM Material m
                INNER JOIN Revista r ON m.id = r.id 
                ORDER BY m.id
            """
            cursor.execute(query)
            resultados = cursor.fetchall()
            cursor.close()
            
            revistas = []
            for row in resultados:
                revista = Revista(row[0], row[1], row[2], row[3])
                revistas.append(revista)
            return revistas
        except Error as e:
            messagebox.showerror("Error", f"Error al listar revistas:\n{e}")
            return []
    
    # NUEVO: Eliminar revista
    def eliminarRevista(self, idRevista):
        try:
            cursor = self.conexion.cursor()
            
            # Obtener datos
            query_revista = """
                SELECT m.id, m.titulo, m.anioPublicacion, m.tipoMaterial, r.numeroEdicion
                FROM Material m 
                INNER JOIN Revista r ON m.id = r.id 
                WHERE m.id = %s
            """
            cursor.execute(query_revista, (idRevista,))
            revista = cursor.fetchone()
            
            if not revista:
                messagebox.showwarning("Advertencia", "Revista no encontrada")
                return False
            
            # Guardar en eliminados
            query_backup_revista = "INSERT INTO Revista_Eliminada (id, numeroEdicion) VALUES (%s, %s)"
            cursor.execute(query_backup_revista, (revista[0], revista[4]))
            
            query_backup_material = "INSERT INTO Material_Eliminado (id, titulo, anioPublicacion, tipoMaterial) VALUES (%s, %s, %s, %s)"
            cursor.execute(query_backup_material, (revista[0], revista[1], revista[2], revista[3]))
            
            # Eliminar
            query_delete_revista = "DELETE FROM Revista WHERE id = %s"
            cursor.execute(query_delete_revista, (idRevista,))
            
            query_delete_material = "DELETE FROM Material WHERE id = %s"
            cursor.execute(query_delete_material, (idRevista,))
            
            self.conexion.commit()
            cursor.close()
            return True
        except Error as e:
            messagebox.showerror("Error", f"Error al eliminar revista:\n{e}")
            self.conexion.rollback()
            return False
    
    # NUEVO: Listar eliminadas
    def listarEliminadas(self):
        try:
            cursor = self.conexion.cursor()
            query = """
                SELECT m.id, m.titulo, m.anioPublicacion, r.numeroEdicion
                FROM Material_Eliminado m 
                INNER JOIN Revista_Eliminada r ON m.id = r.id 
                ORDER BY m.fechaEliminacion DESC
            """
            cursor.execute(query)
            resultados = cursor.fetchall()
            cursor.close()
            
            revistas = []
            for row in resultados:
                revista = Revista(row[0], row[1], row[2], row[3])
                revistas.append(revista)
            return revistas
        except Error as e:
            messagebox.showerror("Error", f"Error al listar eliminadas:\n{e}")
            return []
    
    # NUEVO: Recuperar revista
    def recuperarRevista(self, idRevista):
        try:
            cursor = self.conexion.cursor()
            
            # Obtener datos eliminados
            query_revista = """
                SELECT m.id, m.titulo, m.anioPublicacion, m.tipoMaterial, r.numeroEdicion
                FROM Material_Eliminado m 
                INNER JOIN Revista_Eliminada r ON m.id = r.id 
                WHERE m.id = %s
            """
            cursor.execute(query_revista, (idRevista,))
            revista = cursor.fetchone()
            
            if not revista:
                messagebox.showwarning("Advertencia", "Revista no encontrada en papelera")
                return False
            
            # Restaurar
            query_restore_material = "INSERT INTO Material (id, titulo, anioPublicacion, tipoMaterial) VALUES (%s, %s, %s, %s)"
            cursor.execute(query_restore_material, (revista[0], revista[1], revista[2], revista[3]))
            
            query_restore_revista = "INSERT INTO Revista (id, numeroEdicion) VALUES (%s, %s)"
            cursor.execute(query_restore_revista, (revista[0], revista[4]))
            
            # Eliminar de papelera
            query_delete_revista = "DELETE FROM Revista_Eliminada WHERE id = %s"
            cursor.execute(query_delete_revista, (idRevista,))
            
            query_delete_material = "DELETE FROM Material_Eliminado WHERE id = %s"
            cursor.execute(query_delete_material, (idRevista,))
            
            self.conexion.commit()
            cursor.close()
            return True
        except Error as e:
            messagebox.showerror("Error", f"Error al recuperar revista:\n{e}")
            self.conexion.rollback()
            return False

# Interfaz Gráfica
class BibliotecaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Biblioteca")
        self.root.geometry("950x700")
        self.root.configure(bg='#f0f0f0')
        
        # Conexión a la base de datos
        self.bd = ConexionBD(
            host="localhost",
            database="biblioteca",
            user="root",
            password="123456"  # CAMBIAR CONTRASEÑA AQUÍ
        )
        
        if not self.bd.conectar():
            messagebox.showerror("Error", "No se pudo conectar a la base de datos")
            self.root.destroy()
            return
        
        # Crear objetos DAO
        self.usuarioDAO = UsuarioDAO(self.bd.conexion)
        self.libroDAO = LibroDAO(self.bd.conexion)
        self.revistaDAO = RevistaDAO(self.bd.conexion)
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        # Título principal
        titulo = tk.Label(self.root, text="📚 SISTEMA DE BIBLIOTECA", 
                         font=("Arial", 24, "bold"), bg='#2c3e50', fg='white', pady=15)
        titulo.pack(fill=tk.X)
        
        # Notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Crear pestañas
        self.crear_pestaña_usuarios()
        self.crear_pestaña_libros()
        self.crear_pestaña_revistas()
        self.crear_pestaña_papelera()  # NUEVA PESTAÑA
        
    def crear_pestaña_usuarios(self):
        frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(frame, text="👤 USUARIOS")
        
        # Frame para agregar usuario
        frame_agregar = tk.LabelFrame(frame, text="Agregar Usuario", font=("Arial", 12, "bold"),
                                      bg='white', fg='#2c3e50', padx=20, pady=20)
        frame_agregar.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(frame_agregar, text="Nombre:", bg='white', font=("Arial", 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.entry_usuario_nombre = tk.Entry(frame_agregar, width=40, font=("Arial", 10))
        self.entry_usuario_nombre.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(frame_agregar, text="Correo:", bg='white', font=("Arial", 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.entry_usuario_correo = tk.Entry(frame_agregar, width=40, font=("Arial", 10))
        self.entry_usuario_correo.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Button(frame_agregar, text="💾 Guardar Usuario", command=self.guardar_usuario,
                 bg='#27ae60', fg='white', font=("Arial", 10, "bold"), cursor='hand2').grid(row=2, column=0, columnspan=2, pady=10)
        
        # Frame para buscar y listar
        frame_buscar = tk.LabelFrame(frame, text="Buscar y Listar Usuarios", font=("Arial", 12, "bold"),
                                     bg='white', fg='#2c3e50', padx=20, pady=20)
        frame_buscar.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(frame_buscar, text="Buscar por nombre:", bg='white', font=("Arial", 10)).pack()
        self.entry_buscar_usuario = tk.Entry(frame_buscar, width=40, font=("Arial", 10))
        self.entry_buscar_usuario.pack(pady=5)
        
        frame_botones = tk.Frame(frame_buscar, bg='white')
        frame_botones.pack(pady=10)
        
        tk.Button(frame_botones, text="🔍 Buscar", command=self.buscar_usuario,
                 bg='#3498db', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(frame_botones, text="📋 Listar Todos", command=self.listar_usuarios,
                 bg='#9b59b6', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # NUEVO: Frame para eliminar
        frame_eliminar = tk.Frame(frame_buscar, bg='white')
        frame_eliminar.pack(pady=10)
        
        tk.Label(frame_eliminar, text="ID a eliminar:", bg='white', font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.entry_eliminar_usuario = tk.Entry(frame_eliminar, width=10, font=("Arial", 10))
        self.entry_eliminar_usuario.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_eliminar, text="🗑️ Eliminar", command=self.eliminar_usuario,
                 bg='#e74c3c', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Área de resultados
        self.text_usuarios = scrolledtext.ScrolledText(frame_buscar, height=12, font=("Courier", 9))
        self.text_usuarios.pack(fill=tk.BOTH, expand=True, pady=10)
    
    def crear_pestaña_libros(self):
        frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(frame, text="📖 LIBROS")
        
        # Frame para agregar libro
        frame_agregar = tk.LabelFrame(frame, text="Agregar Libro", font=("Arial", 12, "bold"),
                                      bg='white', fg='#2c3e50', padx=20, pady=20)
        frame_agregar.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(frame_agregar, text="Título:", bg='white', font=("Arial", 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.entry_libro_titulo = tk.Entry(frame_agregar, width=40, font=("Arial", 10))
        self.entry_libro_titulo.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(frame_agregar, text="Autor:", bg='white', font=("Arial", 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.entry_libro_autor = tk.Entry(frame_agregar, width=40, font=("Arial", 10))
        self.entry_libro_autor.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(frame_agregar, text="Año:", bg='white', font=("Arial", 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.entry_libro_anio = tk.Entry(frame_agregar, width=40, font=("Arial", 10))
        self.entry_libro_anio.grid(row=2, column=1, pady=5, padx=10)
        
        tk.Label(frame_agregar, text="ISBN:", bg='white', font=("Arial", 10)).grid(row=3, column=0, sticky='w', pady=5)
        self.entry_libro_isbn = tk.Entry(frame_agregar, width=40, font=("Arial", 10))
        self.entry_libro_isbn.grid(row=3, column=1, pady=5, padx=10)
        
        tk.Button(frame_agregar, text="💾 Guardar Libro", command=self.guardar_libro,
                 bg='#27ae60', fg='white', font=("Arial", 10, "bold"), cursor='hand2').grid(row=4, column=0, columnspan=2, pady=10)
        
        # Frame para buscar y listar
        frame_buscar = tk.LabelFrame(frame, text="Buscar y Listar Libros", font=("Arial", 12, "bold"),
                                     bg='white', fg='#2c3e50', padx=20, pady=20)
        frame_buscar.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(frame_buscar, text="Buscar por título:", bg='white', font=("Arial", 10)).pack()
        self.entry_buscar_libro = tk.Entry(frame_buscar, width=40, font=("Arial", 10))
        self.entry_buscar_libro.pack(pady=5)
        
        frame_botones = tk.Frame(frame_buscar, bg='white')
        frame_botones.pack(pady=10)
        
        tk.Button(frame_botones, text="🔍 Buscar", command=self.buscar_libro,
                 bg='#3498db', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(frame_botones, text="📋 Listar Todos", command=self.listar_libros,
                 bg='#9b59b6', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # NUEVO: Frame para eliminar
        frame_eliminar = tk.Frame(frame_buscar, bg='white')
        frame_eliminar.pack(pady=10)
        
        tk.Label(frame_eliminar, text="ID a eliminar:", bg='white', font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.entry_eliminar_libro = tk.Entry(frame_eliminar, width=10, font=("Arial", 10))
        self.entry_eliminar_libro.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_eliminar, text="🗑️ Eliminar", command=self.eliminar_libro,
                 bg='#e74c3c', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Área de resultados
        self.text_libros = scrolledtext.ScrolledText(frame_buscar, height=8, font=("Courier", 9))
        self.text_libros.pack(fill=tk.BOTH, expand=True, pady=10)
    
    def crear_pestaña_revistas(self):
        frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(frame, text="📰 REVISTAS")
        
        # Frame para agregar revista
        frame_agregar = tk.LabelFrame(frame, text="Agregar Revista", font=("Arial", 12, "bold"),
                                      bg='white', fg='#2c3e50', padx=20, pady=20)
        frame_agregar.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(frame_agregar, text="Título:", bg='white', font=("Arial", 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.entry_revista_titulo = tk.Entry(frame_agregar, width=40, font=("Arial", 10))
        self.entry_revista_titulo.grid(row=0, column=1, pady=5, padx=10)
        
        tk.Label(frame_agregar, text="Año:", bg='white', font=("Arial", 10)).grid(row=1, column=0, sticky='w', pady=5)
        self.entry_revista_anio = tk.Entry(frame_agregar, width=40, font=("Arial", 10))
        self.entry_revista_anio.grid(row=1, column=1, pady=5, padx=10)
        
        tk.Label(frame_agregar, text="Número de Edición:", bg='white', font=("Arial", 10)).grid(row=2, column=0, sticky='w', pady=5)
        self.entry_revista_edicion = tk.Entry(frame_agregar, width=40, font=("Arial", 10))
        self.entry_revista_edicion.grid(row=2, column=1, pady=5, padx=10)
        
        tk.Button(frame_agregar, text="💾 Guardar Revista", command=self.guardar_revista,
                 bg='#27ae60', fg='white', font=("Arial", 10, "bold"), cursor='hand2').grid(row=3, column=0, columnspan=2, pady=10)
        
        # Frame para buscar y listar
        frame_buscar = tk.LabelFrame(frame, text="Buscar y Listar Revistas", font=("Arial", 12, "bold"),
                                     bg='white', fg='#2c3e50', padx=20, pady=20)
        frame_buscar.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(frame_buscar, text="Buscar por título:", bg='white', font=("Arial", 10)).pack()
        self.entry_buscar_revista = tk.Entry(frame_buscar, width=40, font=("Arial", 10))
        self.entry_buscar_revista.pack(pady=5)
        
        frame_botones = tk.Frame(frame_buscar, bg='white')
        frame_botones.pack(pady=10)
        
        tk.Button(frame_botones, text="🔍 Buscar", command=self.buscar_revista,
                 bg='#3498db', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(frame_botones, text="📋 Listar Todas", command=self.listar_revistas,
                 bg='#9b59b6', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # NUEVO: Frame para eliminar
        frame_eliminar = tk.Frame(frame_buscar, bg='white')
        frame_eliminar.pack(pady=10)
        
        tk.Label(frame_eliminar, text="ID a eliminar:", bg='white', font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.entry_eliminar_revista = tk.Entry(frame_eliminar, width=10, font=("Arial", 10))
        self.entry_eliminar_revista.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_eliminar, text=" Eliminar", command=self.eliminar_revista,
                 bg='#e74c3c', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Área de resultados
        self.text_revistas = scrolledtext.ScrolledText(frame_buscar, height=8, font=("Courier", 9))
        self.text_revistas.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # NUEVA PESTAÑA: Papelera de reciclaje
    def crear_pestaña_papelera(self):
        frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(frame, text="🗑️ PAPELERA")
        
        # Título
        tk.Label(frame, text="Recuperación de Datos Eliminados", 
                font=("Arial", 16, "bold"), bg='white', fg='#e74c3c').pack(pady=10)
        
        # Notebook interno para diferentes tipos
        notebook_papelera = ttk.Notebook(frame)
        notebook_papelera.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Pestaña usuarios eliminados
        frame_usuarios_elim = tk.Frame(notebook_papelera, bg='white')
        notebook_papelera.add(frame_usuarios_elim, text="Usuarios")
        
        frame_botones_usu = tk.Frame(frame_usuarios_elim, bg='white')
        frame_botones_usu.pack(pady=10)
        
        tk.Button(frame_botones_usu, text=" Ver Eliminados", command=self.listar_usuarios_eliminados,
                 bg='#95a5a6', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        frame_recuperar_usu = tk.Frame(frame_usuarios_elim, bg='white')
        frame_recuperar_usu.pack(pady=10)
        
        tk.Label(frame_recuperar_usu, text="ID a recuperar:", bg='white', font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.entry_recuperar_usuario = tk.Entry(frame_recuperar_usu, width=10, font=("Arial", 10))
        self.entry_recuperar_usuario.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_recuperar_usu, text=" Recuperar", command=self.recuperar_usuario,
                 bg='#16a085', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        self.text_usuarios_eliminados = scrolledtext.ScrolledText(frame_usuarios_elim, height=20, font=("Courier", 9))
        self.text_usuarios_eliminados.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        # Pestaña libros eliminados
        frame_libros_elim = tk.Frame(notebook_papelera, bg='white')
        notebook_papelera.add(frame_libros_elim, text="Libros")
        
        frame_botones_lib = tk.Frame(frame_libros_elim, bg='white')
        frame_botones_lib.pack(pady=10)
        
        tk.Button(frame_botones_lib, text=" Ver Eliminados", command=self.listar_libros_eliminados,
                 bg='#95a5a6', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        frame_recuperar_lib = tk.Frame(frame_libros_elim, bg='white')
        frame_recuperar_lib.pack(pady=10)
        
        tk.Label(frame_recuperar_lib, text="ID a recuperar:", bg='white', font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.entry_recuperar_libro = tk.Entry(frame_recuperar_lib, width=10, font=("Arial", 10))
        self.entry_recuperar_libro.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_recuperar_lib, text=" Recuperar", command=self.recuperar_libro,
                 bg='#16a085', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        self.text_libros_eliminados = scrolledtext.ScrolledText(frame_libros_elim, height=20, font=("Courier", 9))
        self.text_libros_eliminados.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        # Pestaña revistas eliminadas
        frame_revistas_elim = tk.Frame(notebook_papelera, bg='white')
        notebook_papelera.add(frame_revistas_elim, text="Revistas")
        
        frame_botones_rev = tk.Frame(frame_revistas_elim, bg='white')
        frame_botones_rev.pack(pady=10)
        
        tk.Button(frame_botones_rev, text=" Ver Eliminadas", command=self.listar_revistas_eliminadas,
                 bg='#95a5a6', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        frame_recuperar_rev = tk.Frame(frame_revistas_elim, bg='white')
        frame_recuperar_rev.pack(pady=10)
        
        tk.Label(frame_recuperar_rev, text="ID a recuperar:", bg='white', font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.entry_recuperar_revista = tk.Entry(frame_recuperar_rev, width=10, font=("Arial", 10))
        self.entry_recuperar_revista.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_recuperar_rev, text=" Recuperar", command=self.recuperar_revista,
                 bg='#16a085', fg='white', font=("Arial", 10, "bold"), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        self.text_revistas_eliminadas = scrolledtext.ScrolledText(frame_revistas_elim, height=20, font=("Courier", 9))
        self.text_revistas_eliminadas.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
    
    # Métodos para USUARIOS
    def guardar_usuario(self):
        nombre = self.entry_usuario_nombre.get().strip()
        correo = self.entry_usuario_correo.get().strip()
        
        if not nombre or not correo:
            messagebox.showwarning("Advertencia", "Por favor completa todos los campos")
            return
        
        usuario = Usuario(nombre=nombre, correo=correo)
        if self.usuarioDAO.guardarUsuario(usuario):
            messagebox.showinfo("Éxito", f"Usuario '{nombre}' guardado exitosamente")
            self.entry_usuario_nombre.delete(0, tk.END)
            self.entry_usuario_correo.delete(0, tk.END)
    
    def buscar_usuario(self):
        nombre = self.entry_buscar_usuario.get().strip()
        if not nombre:
            messagebox.showwarning("Advertencia", "Ingresa un nombre para buscar")
            return
        
        usuarios = self.usuarioDAO.buscarUsuarioPorNombre(nombre)
        self.text_usuarios.delete(1.0, tk.END)
        
        if usuarios:
            self.text_usuarios.insert(tk.END, f"Usuarios encontrados: {len(usuarios)}\n")
            self.text_usuarios.insert(tk.END, "="*80 + "\n")
            for usuario in usuarios:
                self.text_usuarios.insert(tk.END, f"{usuario.mostrarUsuario()}\n")
        else:
            self.text_usuarios.insert(tk.END, "No se encontraron usuarios con ese nombre")
    
    def listar_usuarios(self):
        usuarios = self.usuarioDAO.listarTodos()
        self.text_usuarios.delete(1.0, tk.END)
        
        if usuarios:
            self.text_usuarios.insert(tk.END, f"Total de usuarios: {len(usuarios)}\n")
            self.text_usuarios.insert(tk.END, "="*80 + "\n")
            for usuario in usuarios:
                self.text_usuarios.insert(tk.END, f"{usuario.mostrarUsuario()}\n")
        else:
            self.text_usuarios.insert(tk.END, "No hay usuarios almacenados")
    
    # NUEVO: Eliminar usuario
    def eliminar_usuario(self):
        id_usuario = self.entry_eliminar_usuario.get().strip()
        if not id_usuario:
            messagebox.showwarning("Advertencia", "Ingresa un ID")
            return
        
        try:
            id_usuario = int(id_usuario)
        except ValueError:
            messagebox.showerror("Error", "El ID debe ser un número")
            return
        
        confirmacion = messagebox.askyesno("Confirmar", f"¿Eliminar usuario con ID {id_usuario}?")
        if confirmacion:
            if self.usuarioDAO.eliminarUsuario(id_usuario):
                messagebox.showinfo("Éxito", "Usuario eliminado y movido a papelera")
                self.entry_eliminar_usuario.delete(0, tk.END)
                self.listar_usuarios()
    
    # NUEVO: Listar usuarios eliminados
    def listar_usuarios_eliminados(self):
        usuarios = self.usuarioDAO.listarEliminados()
        self.text_usuarios_eliminados.delete(1.0, tk.END)
        
        if usuarios:
            self.text_usuarios_eliminados.insert(tk.END, f"Total eliminados: {len(usuarios)}\n")
            self.text_usuarios_eliminados.insert(tk.END, "="*80 + "\n")
            for usuario in usuarios:
                self.text_usuarios_eliminados.insert(tk.END, f"{usuario.mostrarUsuario()}\n")
        else:
            self.text_usuarios_eliminados.insert(tk.END, "No hay usuarios eliminados")
    
    # NUEVO: Recuperar usuario
    def recuperar_usuario(self):
        id_usuario = self.entry_recuperar_usuario.get().strip()
        if not id_usuario:
            messagebox.showwarning("Advertencia", "Ingresa un ID")
            return
        
        try:
            id_usuario = int(id_usuario)
        except ValueError:
            messagebox.showerror("Error", "El ID debe ser un número")
            return
        
        if self.usuarioDAO.recuperarUsuario(id_usuario):
            messagebox.showinfo("Éxito", "Usuario recuperado exitosamente")
            self.entry_recuperar_usuario.delete(0, tk.END)
            self.listar_usuarios_eliminados()
    
    # Métodos para LIBROS
    def guardar_libro(self):
        titulo = self.entry_libro_titulo.get().strip()
        autor = self.entry_libro_autor.get().strip()
        anio = self.entry_libro_anio.get().strip()
        isbn = self.entry_libro_isbn.get().strip()
        
        if not all([titulo, autor, anio, isbn]):
            messagebox.showwarning("Advertencia", "Por favor completa todos los campos")
            return
        
        try:
            anio = int(anio)
        except ValueError:
            messagebox.showerror("Error", "El año debe ser un número")
            return
        
        libro = Libro(titulo=titulo, anioPublicacion=anio, autor=autor, isbn=isbn)
        if self.libroDAO.guardarLibro(libro):
            messagebox.showinfo("Éxito", f"Libro '{titulo}' guardado exitosamente")
            self.entry_libro_titulo.delete(0, tk.END)
            self.entry_libro_autor.delete(0, tk.END)
            self.entry_libro_anio.delete(0, tk.END)
            self.entry_libro_isbn.delete(0, tk.END)
    
    def buscar_libro(self):
        titulo = self.entry_buscar_libro.get().strip()
        if not titulo:
            messagebox.showwarning("Advertencia", "Ingresa un título para buscar")
            return
        
        libros = self.libroDAO.buscarLibroPorTitulo(titulo)
        self.text_libros.delete(1.0, tk.END)
        
        if libros:
            self.text_libros.insert(tk.END, f"Libros encontrados: {len(libros)}\n")
            self.text_libros.insert(tk.END, "="*80 + "\n")
            for libro in libros:
                self.text_libros.insert(tk.END, f"{libro.mostrarMaterial()}\n")
        else:
            self.text_libros.insert(tk.END, "No se encontraron libros con ese título")
    
    def listar_libros(self):
        libros = self.libroDAO.listarTodos()
        self.text_libros.delete(1.0, tk.END)
        
        if libros:
            self.text_libros.insert(tk.END, f"Total de libros: {len(libros)}\n")
            self.text_libros.insert(tk.END, "="*80 + "\n")
            for libro in libros:
                self.text_libros.insert(tk.END, f"{libro.mostrarMaterial()}\n")
        else:
            self.text_libros.insert(tk.END, "No hay libros almacenados")
    
    # NUEVO: Eliminar libro
    def eliminar_libro(self):
        id_libro = self.entry_eliminar_libro.get().strip()
        if not id_libro:
            messagebox.showwarning("Advertencia", "Ingresa un ID")
            return
        
        try:
            id_libro = int(id_libro)
        except ValueError:
            messagebox.showerror("Error", "El ID debe ser un número")
            return
        
        confirmacion = messagebox.askyesno("Confirmar", f"¿Eliminar libro con ID {id_libro}?")
        if confirmacion:
            if self.libroDAO.eliminarLibro(id_libro):
                messagebox.showinfo("Éxito", "Libro eliminado y movido a papelera")
                self.entry_eliminar_libro.delete(0, tk.END)
                self.listar_libros()
    
    # NUEVO: Listar libros eliminados
    def listar_libros_eliminados(self):
        libros = self.libroDAO.listarEliminados()
        self.text_libros_eliminados.delete(1.0, tk.END)
        
        if libros:
            self.text_libros_eliminados.insert(tk.END, f"Total eliminados: {len(libros)}\n")
            self.text_libros_eliminados.insert(tk.END, "="*80 + "\n")
            for libro in libros:
                self.text_libros_eliminados.insert(tk.END, f"{libro.mostrarMaterial()}\n")
        else:
            self.text_libros_eliminados.insert(tk.END, "No hay libros eliminados")
    
    # NUEVO: Recuperar libro
    def recuperar_libro(self):
        id_libro = self.entry_recuperar_libro.get().strip()
        if not id_libro:
            messagebox.showwarning("Advertencia", "Ingresa un ID")
            return
        
        try:
            id_libro = int(id_libro)
        except ValueError:
            messagebox.showerror("Error", "El ID debe ser un número")
            return
        
        if self.libroDAO.recuperarLibro(id_libro):
            messagebox.showinfo("Éxito", "Libro recuperado exitosamente")
            self.entry_recuperar_libro.delete(0, tk.END)
            self.listar_libros_eliminados()
    
    # Métodos para REVISTAS
    def guardar_revista(self):
        titulo = self.entry_revista_titulo.get().strip()
        anio = self.entry_revista_anio.get().strip()
        edicion = self.entry_revista_edicion.get().strip()
        
        if not all([titulo, anio, edicion]):
            messagebox.showwarning("Advertencia", "Por favor completa todos los campos")
            return
        
        try:
            anio = int(anio)
            edicion = int(edicion)
        except ValueError:
            messagebox.showerror("Error", "El año y la edición deben ser números")
            return
        
        revista = Revista(titulo=titulo, anioPublicacion=anio, numeroEdicion=edicion)
        if self.revistaDAO.guardarRevista(revista):
            messagebox.showinfo("Éxito", f"Revista '{titulo}' guardada exitosamente")
            self.entry_revista_titulo.delete(0, tk.END)
            self.entry_revista_anio.delete(0, tk.END)
            self.entry_revista_edicion.delete(0, tk.END)
    
    def buscar_revista(self):
        titulo = self.entry_buscar_revista.get().strip()
        if not titulo:
            messagebox.showwarning("Advertencia", "Ingresa un título para buscar")
            return
        
        revistas = self.revistaDAO.buscarRevistaPorTitulo(titulo)
        self.text_revistas.delete(1.0, tk.END)
        
        if revistas:
            self.text_revistas.insert(tk.END, f"Revistas encontradas: {len(revistas)}\n")
            self.text_revistas.insert(tk.END, "="*80 + "\n")
            for revista in revistas:
                self.text_revistas.insert(tk.END, f"{revista.mostrarMaterial()}\n")
        else:
            self.text_revistas.insert(tk.END, "No se encontraron revistas con ese título")
    
    def listar_revistas(self):
        revistas = self.revistaDAO.listarTodas()
        self.text_revistas.delete(1.0, tk.END)
        
        if revistas:
            self.text_revistas.insert(tk.END, f"Total de revistas: {len(revistas)}\n")
            self.text_revistas.insert(tk.END, "="*80 + "\n")
            for revista in revistas:
                self.text_revistas.insert(tk.END, f"{revista.mostrarMaterial()}\n")
        else:
            self.text_revistas.insert(tk.END, "No hay revistas almacenadas")
    
    # NUEVO: Eliminar revista
    def eliminar_revista(self):
        id_revista = self.entry_eliminar_revista.get().strip()
        if not id_revista:
            messagebox.showwarning("Advertencia", "Ingresa un ID")
            return
        
        try:
            id_revista = int(id_revista)
        except ValueError:
            messagebox.showerror("Error", "El ID debe ser un número")
            return
        
        confirmacion = messagebox.askyesno("Confirmar", f"¿Eliminar revista con ID {id_revista}?")
        if confirmacion:
            if self.revistaDAO.eliminarRevista(id_revista):
                messagebox.showinfo("Éxito", "Revista eliminada y movida a papelera")
                self.entry_eliminar_revista.delete(0, tk.END)
                self.listar_revistas()
    
    # NUEVO: Listar revistas eliminadas
    def listar_revistas_eliminadas(self):
        revistas = self.revistaDAO.listarEliminadas()
        self.text_revistas_eliminadas.delete(1.0, tk.END)
        
        if revistas:
            self.text_revistas_eliminadas.insert(tk.END, f"Total eliminadas: {len(revistas)}\n")
            self.text_revistas_eliminadas.insert(tk.END, "="*80 + "\n")
            for revista in revistas:
                self.text_revistas_eliminadas.insert(tk.END, f"{revista.mostrarMaterial()}\n")
        else:
            self.text_revistas_eliminadas.insert(tk.END, "No hay revistas eliminadas")
    
    # NUEVO: Recuperar revista
    def recuperar_revista(self):
        id_revista = self.entry_recuperar_revista.get().strip()
        if not id_revista:
            messagebox.showwarning("Advertencia", "Ingresa un ID")
            return
        
        try:
            id_revista = int(id_revista)
        except ValueError:
            messagebox.showerror("Error", "El ID debe ser un número")
            return
        
        if self.revistaDAO.recuperarRevista(id_revista):
            messagebox.showinfo("Éxito", "Revista recuperada exitosamente")
            self.entry_recuperar_revista.delete(0, tk.END)
            self.listar_revistas_eliminadas()
    
    def cerrar_aplicacion(self):
        self.bd.desconectar()
        self.root.destroy()

# Programa principal
def main():
    root = tk.Tk()
    app = BibliotecaGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.cerrar_aplicacion)
    root.mainloop()

if __name__ == "__main__":
    main()