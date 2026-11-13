#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "transformaciones.h"

unsigned char* leer_imagen(char* name_file, long* ancho, long* alto, unsigned char* encabezado){
    FILE *archivo = fopen(name_file, "rb");
    if (archivo == NULL){
        printf("No existe %s\n", name_file);
        return NULL;
    }

    for(int i = 0; i < 54; i++){
        encabezado[i] = fgetc(archivo);
    }
    *ancho = encabezado[18] | (encabezado[19] << 8) | (encabezado[20] << 16) | (encabezado[21] << 24);
    *alto = encabezado[22] | (encabezado[23] << 8) | (encabezado[24] << 16) | (encabezado[25] << 24); 
    
    long bytes_totales = ((*ancho)*(*alto)*3);
    unsigned char* pixeles = (unsigned char*)malloc(bytes_totales * sizeof(unsigned char));

    if (pixeles == NULL){
        printf("Imagen demasiado grande");
        fclose(archivo);
        return NULL;
    }

    int j = 0;
    while(!feof(archivo) && j < bytes_totales){
        pixeles[j] = fgetc(archivo);
        j++;
    }

    fclose(archivo);
    return pixeles; 
}

void inv_hor_color(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado) {
    FILE *outputImage = fopen(nombre_archivo_salida, "wb");
    if (outputImage == NULL) return;

   
    for(int i = 0; i < 54; i++) {
        fputc(encabezado[i], outputImage);
    }


    for(long i = 0; i < alto; i++){
        for(long k = 0; k < ancho; k++){
            
            long y = (i * ancho) + (ancho - 1 - k);
            long posicion = y * 3;

            fputc(pixeles[posicion], outputImage);
            fputc(pixeles[posicion + 1], outputImage);
            fputc(pixeles[posicion + 2], outputImage);
        }
    }
    
    fclose(outputImage);
}

void inv_hor_bn(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado){
    FILE *outputImage = fopen(nombre_archivo_salida, "wb");
    if (outputImage == NULL) return;

   
    for(int i = 0; i < 54; i++) {
        fputc(encabezado[i], outputImage);
    }


    for(long i = 0; i < alto; i++){
        for(long k = 0; k < ancho; k++){
            
            long y = (i * ancho) + (ancho - 1 - k);
            long posicion = y * 3;

            unsigned char b = pixeles[posicion];
            unsigned char g = pixeles[posicion + 1];
            unsigned char r = pixeles[posicion + 2];
            
           
            unsigned char pixel_gris = (0.21 * r) + (0.72 * g) + (0.07 * b);
            fputc(pixel_gris, outputImage);
            fputc(pixel_gris, outputImage);
            fputc(pixel_gris, outputImage);
        }
    }
    
    fclose(outputImage);
}

void inv_ver_color(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado) {
    FILE *outputImage = fopen(nombre_archivo_salida, "wb");
    if (outputImage == NULL) return;

   
    for(int i = 0; i < 54; i++) {
        fputc(encabezado[i], outputImage);
    }


    for(long y = alto - 1; y >= 0; y--) {
        for(long x = 0; x < ancho; x++) {
            
            long posicion = (y * ancho + x) * 3;
            
            
            fputc(pixeles[posicion], outputImage);     
            fputc(pixeles[posicion + 1], outputImage); 
            fputc(pixeles[posicion + 2], outputImage); 
        }
    }
    
    fclose(outputImage);
}

void inv_ver_bn(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado) {
    FILE *outputImage = fopen(nombre_archivo_salida, "wb");
    if (outputImage == NULL) return;

   
    for(int i = 0; i < 54; i++) {
        fputc(encabezado[i], outputImage);
    }


    for(long y = alto - 1; y >= 0; y--) {
        for(long x = 0; x < ancho; x++) {
            
            long posicion = (y * ancho + x) * 3;
            
            
            unsigned char b = pixeles[posicion];
            unsigned char g = pixeles[posicion + 1];
            unsigned char r = pixeles[posicion + 2];
            
           
            unsigned char pixel_gris = (0.21 * r) + (0.72 * g) + (0.07 * b);
            fputc(pixel_gris, outputImage);
            fputc(pixel_gris, outputImage);
            fputc(pixel_gris, outputImage);
        }
    }
    
    fclose(outputImage);
}

void blur_color(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado, int kernel_size) {
    long total_bytes = ancho * alto * 3;

    unsigned char *temp = (unsigned char*)malloc(total_bytes);
    unsigned char *output = (unsigned char*)malloc(total_bytes);

    if (!temp || !output) {
        printf("Memoria insuficiente \n");
        if (temp) free(temp);
        if (output) free(output);
        return;
    }

    int k = kernel_size / 2;

    for (long y = 0; y < alto; y++) {
        for (long x = 0; x < ancho; x++) {
            int sumB = 0, sumG = 0, sumR = 0, count = 0;

            for (int dx = -k; dx <= k; dx++) {
                long nx = x + dx;
                if (nx >= 0 && nx < ancho) {
                    long idx = (y * ancho + nx) * 3;
                    sumB += pixeles[idx + 0];
                    sumG += pixeles[idx + 1];
                    sumR += pixeles[idx + 2];
                    count++;
                }
            }

            long index = (y * ancho + x) * 3;
            temp[index + 0] = sumB / count;
            temp[index + 1] = sumG / count;
            temp[index + 2] = sumR / count;
        }
    }

    
    for (long y = 0; y < alto; y++) {
        for (long x = 0; x < ancho; x++) {
            int sumB = 0, sumG = 0, sumR = 0, count = 0;

            for (int dy = -k; dy <= k; dy++) {
                long ny = y + dy;
                if (ny >= 0 && ny < alto) {
                    long idx = (ny * ancho + x) * 3;
                    sumB += temp[idx + 0];
                    sumG += temp[idx + 1];
                    sumR += temp[idx + 2];
                    count++;
                }
            }

            long index = (y * ancho + x) * 3;
            output[index + 0] = sumB / count;
            output[index + 1] = sumG / count;
            output[index + 2] = sumR / count;
        }
    }

    
    FILE *outputImage = fopen(nombre_archivo_salida, "wb");
    if (outputImage != NULL) {
        
        for (int i = 0; i < 54; i++) {
            fputc(encabezado[i], outputImage);
        }
        
        for (long i = 0; i < total_bytes; i++) {
            fputc(output[i], outputImage);
        }
        fclose(outputImage);
    }

    free(temp);
    free(output);
}

void blur_bn(char* nombre_archivo_salida, unsigned char *pixeles, long ancho, long alto, unsigned char* encabezado, int kernel_size) {
    long total_bytes = ancho * alto * 3;

    unsigned char *temp = (unsigned char*)malloc(total_bytes);
    unsigned char *output = (unsigned char*)malloc(total_bytes);

    if (!temp || !output) {
        printf("Memoria insuficiente \n");
        if (temp) free(temp);
        if (output) free(output);
        return;
    }

    int k = kernel_size / 2;

    // Paso 1: Desenfoque Horizontal
    for (long y = 0; y < alto; y++) {
        for (long x = 0; x < ancho; x++) {
            int sumB = 0, sumG = 0, sumR = 0, count = 0;

            for (int dx = -k; dx <= k; dx++) {
                long nx = x + dx;
                if (nx >= 0 && nx < ancho) {
                    long idx = (y * ancho + nx) * 3;
                    sumB += pixeles[idx + 0];
                    sumG += pixeles[idx + 1];
                    sumR += pixeles[idx + 2];
                    count++;
                }
            }

            long index = (y * ancho + x) * 3;
            temp[index + 0] = sumB / count;
            temp[index + 1] = sumG / count;
            temp[index + 2] = sumR / count;
        }
    }

    
    for (long y = 0; y < alto; y++) {
        for (long x = 0; x < ancho; x++) {
            int sumB = 0, sumG = 0, sumR = 0, count = 0;

            for (int dy = -k; dy <= k; dy++) {
                long ny = y + dy;
                if (ny >= 0 && ny < alto) {
                    long idx = (ny * ancho + x) * 3;
                    sumB += temp[idx + 0];
                    sumG += temp[idx + 1];
                    sumR += temp[idx + 2];
                    count++;
                }
            }

            unsigned char b = sumB / count;
            unsigned char g = sumG / count;
            unsigned char r = sumR / count;

            
            unsigned char pixel_gris = (unsigned char)(0.21 * r + 0.72 * g + 0.07 * b);

            long index = (y * ancho + x) * 3;
            output[index + 0] = pixel_gris;
            output[index + 1] = pixel_gris;
            output[index + 2] = pixel_gris;
        }
    }

    FILE *outputImage = fopen(nombre_archivo_salida, "wb");
    if (outputImage != NULL) {
        for (int i = 0; i < 54; i++) {
            fputc(encabezado[i], outputImage);
        }
        for (long i = 0; i < total_bytes; i++) {
            fputc(output[i], outputImage);
        }
        fclose(outputImage);
    }

    free(temp);
    free(output);
}