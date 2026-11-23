import ctypes          # Permite cargar y ejecutar librerías compiladas en C (.dylib / .so)
import os              # Manejo de rutas de archivos, directorios y limpieza de salidas
import time            # Medición de tiempos
import tkinter as tk   # Librería estándar de Python para interfaces gráficas de escritorio
from tkinter import filedialog, messagebox, ttk  # Diálogos de archivos, alertas y widgets nativos
from PIL import Image, ImageTk  # Pillow: carga y redimensionamiento de imágenes BMP para Tkinter

# Obtiene la ruta absoluta de la librería compilada desde transformaciones.c
ruta_lib = os.path.abspath("libtransformaciones.dylib")
lib = ctypes.CDLL(ruta_lib)

# Define los tipos de datos exactos de los parámetros que recibe procesar_lote() en C:
# void procesar_lote(const char** rutas_entrada, const char* carpeta_salida,
#                    int num_imagenes, int mascara_filtros, int kernel, int hilos)
lib.procesar_lote.argtypes = [
    ctypes.POINTER(ctypes.c_char_p),  # Arreglo de cadenas (rutas de entrada)
    ctypes.c_char_p,                  # Ruta de la carpeta de salida
    ctypes.c_int,                     # Cantidad de imágenes en el lote (1 a 10)
    ctypes.c_int,                     # Máscara de bits con las transformaciones activas
    ctypes.c_int,                     # Tamaño del kernel para el filtro Box Blur
    ctypes.c_int,                     # Número de hilos para OpenMP
]
lib.procesar_lote.restype = None      # La función en C no retorna valor (void)

class ProcesadorLoteApp:
    def __init__(self, root):
        """Inicializa la ventana principal, variables de estado y componentes visuales."""
        self.root = root
        self.root.title("Procesador Paralelo BMP (C + OpenMP)")
        self.root.geometry("1020x660")

        # Lista que almacenará las rutas absolutas de las imágenes seleccionadas
        self.rutas_entrada = []

        # Crea el directorio donde C guardará las imágenes procesadas
        self.carpeta_salida = os.path.abspath("salidas_bmp")
        os.makedirs(self.carpeta_salida, exist_ok=True)

        # PANEL IZQUIERDO: CONTROLES, FILTROS Y PARÁMETROS
        panel_izq = tk.Frame(root, width=320, padx=15, pady=15, relief=tk.RIDGE, bd=1)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y)

        # Boton para seleccionar imagenes
        tk.Button(
           panel_izq,
           text="1. Seleccionar Imágenes (1 a 10)",
           command=self.cargar_imagenes,
           bg="#2563eb",
           fg="black",
           pady=6,
        ).pack(fill=tk.X)

        # Etiqueta informativa sobre cuántas imágenes están cargadas actualmente
        self.lbl_contador = tk.Label(panel_izq, text="0 imágenes cargadas", fg="#555", pady=5)
        self.lbl_contador.pack()

        tk.Label(
            panel_izq,
            text="2. Transformaciones a aplicar:",
            font=("Arial", 11, "bold"),
        ).pack(anchor="w", pady=(10, 5))

        # Lista de tuplas: (Etiqueta visual, Valor de bit en C, Variable booleana de Tkinter)
        # Cada filtro ocupa 1 bit distinto (potencias de 2: 1, 2, 4, 8, 16, 32)
        self.filtros_vars = [
            ("Inversión Horizontal (Color)", 1, tk.BooleanVar(value=True)),
            ("Inversión Horizontal (B/N)", 2, tk.BooleanVar(value=False)),
            ("Inversión Vertical (Color)", 4, tk.BooleanVar(value=False)),
            ("Inversión Vertical (B/N)", 8, tk.BooleanVar(value=False)),
            ("Box Blur (Color)", 16, tk.BooleanVar(value=False)),
            ("Box Blur (B/N)", 32, tk.BooleanVar(value=False)),
        ]

        # Genera dinámicamente un Checkbutton por cada transformación disponible
        for texto, _, var in self.filtros_vars:
            tk.Checkbutton(panel_izq, text=texto, variable=var).pack(anchor="w")

        # Contenedor en cuadrícula (grid) para los selectores numéricos
        frame_params = tk.Frame(panel_izq, pady=12)
        frame_params.pack(fill=tk.X)

        # Selector de cantidad de hilos OpenMP (de 1 secuencial hasta 10 en paralelo)
        tk.Label(frame_params, text="Hilos OpenMP (1-10):").grid(row=0, column=0, sticky="w", pady=4)
        self.spin_hilos = tk.Spinbox(frame_params, from_=1, to=10, width=5)
        self.spin_hilos.delete(0, "end")
        self.spin_hilos.insert(0, "6")  # Valor inicial por defecto: 6 hilos
        self.spin_hilos.grid(row=0, column=1, padx=10)

        # Selector del tamaño de ventana (kernel) para el Box Blur (solo valores impares)
        tk.Label(frame_params, text="Kernel Blur:").grid(row=1, column=0, sticky="w", pady=4)
        self.spin_kernel = tk.Spinbox(frame_params, from_=3, to=201, increment=2, width=5)
        self.spin_kernel.delete(0, "end")
        self.spin_kernel.insert(0, "51")  # Valor inicial por defecto: 51x51
        self.spin_kernel.grid(row=1, column=1, padx=10)

        # Botón principal que dispara la llamada a la función paralela en C
        tk.Button(
            panel_izq,
            text="3. Procesar Lote en Paralelo",
            command=self.ejecutar_lote,
            bg="#16a34a",
            fg="black",
            font=("Arial", 11, "bold"),
            pady=8,
        ).pack(fill=tk.X, pady=10)

        # Etiqueta donde se mostrará el tiempo total medido tras procesar el lote
        self.lbl_tiempo = tk.Label(
            panel_izq,
            text="Tiempo: --.-- s",
            font=("Arial", 11, "bold"),
            fg="#0f766e",
        )
        self.lbl_tiempo.pack(pady=5)

        # PANEL DERECHO: LISTA DE ARCHIVOS GENERADOS Y VISTA PREVIA
        panel_der = tk.Frame(root, padx=15, pady=15)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(
            panel_der,
            text="Archivos generados (haz clic para previsualizar):",
            font=("Arial", 11, "bold"),
        ).pack(anchor="w")

        # Lista desplegable con los nombres de los archivos BMP creados en salidas_bmp/
        self.lista_resultados = tk.Listbox(panel_der, height=8)
        self.lista_resultados.pack(fill=tk.X, pady=5)
        # Vincula el evento de selección de un elemento con la actualización de la imagen
        self.lista_resultados.bind("<<ListboxSelect>>", self.previsualizar_seleccion)

        # Marco donde se renderizará la vista previa de la imagen seleccionada
        self.panel_preview = tk.Label(panel_der, text="Vista previa del resultado", relief=tk.GROOVE)
        self.panel_preview.pack(fill=tk.BOTH, expand=True, pady=10)



    def cargar_imagenes(self):
        """Abre el explorador de archivos para elegir entre 1 y 10 imágenes BMP."""
        rutas = filedialog.askopenfilenames(filetypes=[("Imágenes BMP", "*.bmp")])
        if not rutas:
            return  # El usuario canceló la selección

        # Limita el lote a un máximo de 10 imágenes para controlar memoria y disco
        if len(rutas) > 10:
            messagebox.showwarning(
                "Límite excedido",
                "Selecciona máximo 10 imágenes. Se tomarán las primeras 10.",
            )
            rutas = rutas[:10]

        self.rutas_entrada = list(rutas)
        self.lbl_contador.config(text=f"{len(self.rutas_entrada)} imagen(es) lista(s)")

    def ejecutar_lote(self):
        """Empaqueta parámetros, invoca al motor en C y actualiza los resultados."""
        if not self.rutas_entrada:
            messagebox.showwarning("Aviso", "Primero selecciona entre 1 y 10 imágenes BMP.")
            return

        # Construye la máscara de bits aplicando operación OR (|=) por cada filtro marcado
        mascara = 0
        for _, bit, var in self.filtros_vars:
            if var.get():
                mascara |= bit

        if mascara == 0:
            messagebox.showwarning("Aviso", "Marca al menos una transformación.")
            return

        # Elimina archivos de corridas previas para que la lista solo muestre el lote actual
        for f in os.listdir(self.carpeta_salida):
            os.remove(os.path.join(self.carpeta_salida, f))

        num_imgs = len(self.rutas_entrada)

        # Convierte las rutas de Python (str) a un arreglo de punteros char* de C (bytes UTF-8)
        arr_rutas = (ctypes.c_char_p * num_imgs)(
            *[r.encode("utf-8") for r in self.rutas_entrada]
        )
        hilos = int(self.spin_hilos.get())
        kernel = int(self.spin_kernel.get())

        # Toma el tiempo antes y después de ejecutar la función paralela en C
        inicio = time.perf_counter()
        lib.procesar_lote(
            arr_rutas,
            self.carpeta_salida.encode("utf-8"),
            num_imgs,
            mascara,
            kernel,
            hilos,
        )
        fin = time.perf_counter()

        # Muestra en pantalla el tiempo exacto que tomó procesar todo el lote
        self.lbl_tiempo.config(text=f"Tiempo ({hilos} hilos): {fin - inicio:.4f} s")

        # Rellena el Listbox con los nuevos archivos BMP generados
        self.lista_resultados.delete(0, tk.END)
        archivos = sorted(os.listdir(self.carpeta_salida))
        for arch in archivos:
            self.lista_resultados.insert(tk.END, arch)

        # Selecciona y muestra automáticamente el primer resultado generado
        if archivos:
            self.lista_resultados.selection_set(0)
            self.mostrar_imagen(os.path.join(self.carpeta_salida, archivos[0]))

    def previsualizar_seleccion(self, event):
        """Detecta qué archivo seleccionó el usuario en la lista y lo muestra."""
        seleccion = self.lista_resultados.curselection()
        if seleccion:
            nombre = self.lista_resultados.get(seleccion[0])
            self.mostrar_imagen(os.path.join(self.carpeta_salida, nombre))

    def mostrar_imagen(self, ruta):
        """Carga una imagen BMP, la escala sin deformarla y la dibuja en la interfaz."""
        img = Image.open(ruta)
        # thumbnail ajusta la imagen dentro de 620x400 manteniendo su relación de aspecto
        img.thumbnail((620, 400))
        foto = ImageTk.PhotoImage(img)

        self.panel_preview.config(image=foto, text="")
        # Guarda una referencia en el widget para evitar que el Garbage Collector borre la imagen
        self.panel_preview.image = foto

if __name__ == "__main__":
    root = tk.Tk()
    app = ProcesadorLoteApp(root)
    root.mainloop()  # Inicia el bucle principal de eventos de la ventana