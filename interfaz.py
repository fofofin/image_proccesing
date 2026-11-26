import ctypes
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import platform

# Detectar el sistema operativo y elegir la extensión de librería correcta
sistema = platform.system()
if sistema == "Windows":
    nombre_lib = "transformaciones.dll"
elif sistema == "Darwin":  # macOS
    nombre_lib = "libtransformaciones.dylib"
else:  # Linux
    nombre_lib = "libtransformaciones.so"

ruta_lib = os.path.abspath(nombre_lib)

# En Python 3.8+ en Windows, es necesario registrar el directorio para cargar dependencias (como libgomp)
if sistema == "Windows":
    os.add_dll_directory(os.path.dirname(ruta_lib))

lib = ctypes.CDLL(ruta_lib)
# Cargar librería en C


lib.procesar_lote.argtypes = [
    ctypes.POINTER(ctypes.c_char_p),
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
]
lib.procesar_lote.restype = None


class ProcesadorLoteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesador Paralelo BMP (C + OpenMP)")
        self.root.geometry("1020x660")

        self.rutas_entrada = []
        self.carpeta_salida = os.path.abspath("salidas_bmp")
        os.makedirs(self.carpeta_salida, exist_ok=True)

        # --- Panel Izquierdo: Controles y Checkboxes ---
        panel_izq = tk.Frame(root, width=320, padx=15, pady=15, relief=tk.RIDGE, bd=1)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y)

        tk.Button(
            panel_izq,
            text="1. Seleccionar Imágenes (1 a 10)",
            command=self.cargar_imagenes,
            bg="#2563eb",
            fg="black",
            pady=6,
        ).pack(fill=tk.X)

        self.lbl_contador = tk.Label(panel_izq, text="0 imágenes cargadas", fg="#555", pady=5)
        self.lbl_contador.pack()

        tk.Label(panel_izq, text="2. Transformaciones a aplicar:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(10, 5))

        # Checkboxes con su valor de bit correspondiente
        self.filtros_vars = [
            ("Inversión Horizontal (Color)", 1, tk.BooleanVar(value=True)),
            ("Inversión Horizontal (B/N)", 2, tk.BooleanVar(value=False)),
            ("Inversión Vertical (Color)", 4, tk.BooleanVar(value=False)),
            ("Inversión Vertical (B/N)", 8, tk.BooleanVar(value=False)),
            ("Box Blur (Color)", 16, tk.BooleanVar(value=False)),
            ("Box Blur (B/N)", 32, tk.BooleanVar(value=False)),
            ("Detección de Bordes X (Sobel)", 64, tk.BooleanVar(value=False)),
            ("Detección de Bordes Y (Sobel)", 128, tk.BooleanVar(value=False)),
        ]

        for texto, _, var in self.filtros_vars:
            tk.Checkbutton(panel_izq, text=texto, variable=var).pack(anchor="w")

        # Parámetros de paralelismo y kernel
        frame_params = tk.Frame(panel_izq, pady=12)
        frame_params.pack(fill=tk.X)

        tk.Label(frame_params, text="Hilos OpenMP (1-10):").grid(row=0, column=0, sticky="w", pady=4)
        self.spin_hilos = tk.Spinbox(frame_params, from_=1, to=10, width=5)
        self.spin_hilos.delete(0, "end")
        self.spin_hilos.insert(0, "6")
        self.spin_hilos.grid(row=0, column=1, padx=10)

        tk.Label(frame_params, text="Kernel Blur:").grid(row=1, column=0, sticky="w", pady=4)
        self.spin_kernel = tk.Spinbox(frame_params, from_=3, to=201, increment=2, width=5)
        self.spin_kernel.delete(0, "end")
        self.spin_kernel.insert(0, "51")
        self.spin_kernel.grid(row=1, column=1, padx=10)

        tk.Button(
            panel_izq,
            text="3. Procesar Lote en Paralelo",
            command=self.ejecutar_lote,
            bg="#16a34a",
            fg="black",
            font=("Arial", 11, "bold"),
            pady=8,
        ).pack(fill=tk.X, pady=10)

        self.lbl_tiempo = tk.Label(panel_izq, text="Tiempo: --.-- s", font=("Arial", 11, "bold"), fg="#0f766e")
        self.lbl_tiempo.pack(pady=5)

        # --- Panel Derecho: Lista de resultados y Vista Previa ---
        panel_der = tk.Frame(root, padx=15, pady=15)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(panel_der, text="Archivos generados (haz clic para previsualizar):", font=("Arial", 11, "bold")).pack(anchor="w")

        self.lista_resultados = tk.Listbox(panel_der, height=8)
        self.lista_resultados.pack(fill=tk.X, pady=5)
        self.lista_resultados.bind("<<ListboxSelect>>", self.previsualizar_seleccion)

        self.panel_preview = tk.Label(panel_der, text="Vista previa del resultado", relief=tk.GROOVE)
        self.panel_preview.pack(fill=tk.BOTH, expand=True, pady=10)

    def cargar_imagenes(self):
        rutas = filedialog.askopenfilenames(filetypes=[("Imágenes BMP", "*.bmp")])
        if not rutas:
            return
        if len(rutas) > 10:
            messagebox.showwarning("Límite excedido", "Selecciona máximo 10 imágenes. Se tomarán las primeras 10.")
            rutas = rutas[:10]

        self.rutas_entrada = list(rutas)
        self.lbl_contador.config(text=f"{len(self.rutas_entrada)} imagen(es) lista(s)")

    def ejecutar_lote(self):
        if not self.rutas_entrada:
            messagebox.showwarning("Aviso", "Primero selecciona entre 1 y 10 imágenes BMP.")
            return

        # Calcular máscara de bits de los checkboxes marcados
        mascara = 0
        for _, bit, var in self.filtros_vars:
            if var.get():
                mascara |= bit

        if mascara == 0:
            messagebox.showwarning("Aviso", "Marca al menos una transformación.")
            return

        # Limpiar salidas anteriores
        for f in os.listdir(self.carpeta_salida):
            os.remove(os.path.join(self.carpeta_salida, f))

        num_imgs = len(self.rutas_entrada)
        arr_rutas = (ctypes.c_char_p * num_imgs)(*[r.encode("utf-8") for r in self.rutas_entrada])
        hilos = int(self.spin_hilos.get())
        kernel = int(self.spin_kernel.get())

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

        self.lbl_tiempo.config(text=f"Tiempo ({hilos} hilos): {fin - inicio:.4f} s")

        # Actualizar lista de archivos creados
        self.lista_resultados.delete(0, tk.END)
        archivos = sorted(os.listdir(self.carpeta_salida))
        for arch in archivos:
            self.lista_resultados.insert(tk.END, arch)

        if archivos:
            self.lista_resultados.selection_set(0)
            self.mostrar_imagen(os.path.join(self.carpeta_salida, archivos[0]))

    def previsualizar_seleccion(self, event):
        seleccion = self.lista_resultados.curselection()
        if seleccion:
            nombre = self.lista_resultados.get(seleccion[0])
            self.mostrar_imagen(os.path.join(self.carpeta_salida, nombre))

    def mostrar_imagen(self, ruta):
        img = Image.open(ruta)
        img.thumbnail((620, 400))
        foto = ImageTk.PhotoImage(img)
        self.panel_preview.config(image=foto, text="")
        self.panel_preview.image = foto


if __name__ == "__main__":
    root = tk.Tk()
    app = ProcesadorLoteApp(root)
    root.mainloop()
