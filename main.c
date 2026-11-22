/*
 * Descripción: Procesa 10 imágenes BMP en paralelo utilizando OpenMP
 * con 1, 2, 4, 6, 8, 10 (cambiando) hilos. Aplica transformaciones de reflexión horizontal y vertical,
 * desenfoque y detección de bordes, tanto a color como en escala de grises.
 * Guarda las imágenes resultantes y mide el tiempo total de ejecución.
 * Autor: [Santiago Alejandro Muradás Ramírez, A01739610]
 *        [Adolfo Rodríguez Rodríguez, A01739189]
 *        [Juliana López Carbonell, A01739515]
 * Fecha: [22/10/2026]
 */

#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include "transformaciones.h"

int main() {
    const char* entradas[10] = {
        "imagen1.bmp", "imagen2.bmp", "imagen3.bmp", "imagen4.bmp", "imagen5.bmp",
        "imagen6.bmp", "imagen7.bmp", "imagen8.bmp", "imagen9.bmp", "imagen10.bmp"
    };

    double inicio = omp_get_wtime();

    #pragma omp parallel for num_threads(6)
    for (int i = 0; i < 10; i++) {
        long ancho, alto;
        unsigned char encabezado[54];
        char salida[100];

        unsigned char* pixeles = leer_imagen((char*)entradas[i], &ancho, &alto, encabezado);

        if (pixeles != NULL) {
            sprintf(salida, "hor_color_%d.bmp", i + 1);
            inv_hor_color(salida, pixeles, ancho, alto, encabezado);

            sprintf(salida, "hor_bn_%d.bmp", i + 1);
            inv_hor_bn(salida, pixeles, ancho, alto, encabezado);

            sprintf(salida, "ver_color_%d.bmp", i + 1);
            inv_ver_color(salida, pixeles, ancho, alto, encabezado);

            sprintf(salida, "ver_bn_%d.bmp", i + 1);
            inv_ver_bn(salida, pixeles, ancho, alto, encabezado);

            sprintf(salida, "border_dx_%d.bmp", i + 1);
            border_dx(salida, pixeles, ancho, alto, encabezado);

            sprintf(salida, "blur_color_%d.bmp", i + 1);
            blur_color(salida, pixeles, ancho, alto, encabezado, 9);
            
            sprintf(salida, "blur_bn_%d.bmp", i + 1);
            blur_bn(salida, pixeles, ancho, alto, encabezado, 9);

            sprintf(salida, "border_dy_%d.bmp", i + 1);
            border_dy(salida, pixeles, ancho, alto, encabezado);

            free(pixeles);
            printf("Hilo %d terminó con %s\n", omp_get_thread_num(), entradas[i]);
        }
    }

    double fin = omp_get_wtime();
    printf("Todas las imágenes terminaron en %.4f segundos.\n", fin - inicio);
    return 0;
}
