#ifndef TRANSFORMACIONES_H
#define TRANSFORMACIONES_H

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

unsigned char* leer_imagen(char* name_file, long* ancho, long* alto, unsigned char* encabezado);

void guardar_imagen(char* name_file, long ancho, long alto, unsigned char* encabezado, unsigned char* pixeles);

void inv_hor_color(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado);

void inv_hor_bn(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado);

void inv_ver_color(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado);

void inv_ver_bn(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado);

void blur_color(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado, int kernel_size);

void blur_bn(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado, int kernel_size);



#endif