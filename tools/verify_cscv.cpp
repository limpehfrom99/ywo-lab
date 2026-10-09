// Driver: run Masters' cscvcore() (CSCV_CORE.CPP, criterion = mean in CRITER.CPP) on a matrix file.
// File format: ncases n_systems n_blocks, then n_systems rows of ncases values (case changes fastest).
#include <stdio.h>
#include <stdlib.h>
double cscvcore(int ncases, int n_systems, int n_blocks, double *returns, int *indices, int *lengths,
                int *flags, double *work, double *is_crits, double *oos_crits);
int main(int argc, char **argv) {
   if (argc != 2) { printf("usage: verify_cscv matrix.txt\n"); return 1; }
   FILE *fp = fopen(argv[1], "r");
   int ncases, nsys, nb;
   if (!fp || fscanf(fp, "%d %d %d", &ncases, &nsys, &nb) != 3) { printf("bad file\n"); return 1; }
   double *r = (double *) malloc(sizeof(double) * (size_t) ncases * nsys);
   for (long i = 0; i < (long) ncases * nsys; i++) if (fscanf(fp, "%lf", &r[i]) != 1) { printf("short file\n"); return 1; }
   fclose(fp);
   int *ind = (int *) malloc(nb * sizeof(int)), *len = (int *) malloc(nb * sizeof(int)), *flags = (int *) malloc(nb * sizeof(int));
   double *work = (double *) malloc(ncases * sizeof(double)), *isc = (double *) malloc(nsys * sizeof(double)), *oosc = (double *) malloc(nsys * sizeof(double));
   printf("%.10f\n", cscvcore(ncases, nsys, nb, r, ind, len, flags, work, isc, oosc));
   return 0;
}
