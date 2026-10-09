// Driver: run Masters' boot_conf_BCa() (BOOT_RATIO/BOOT_CONF.CPP) for the mean of a sample file.
// File format: n, then n values. Prints low/high bounds at 2.5%, 5%, 10%.
#include <stdio.h>
#include <stdlib.h>
void boot_conf_BCa(int n, double *x, double (*user_t)(int, double *), int nboot, double *low2p5, double *high2p5,
                   double *low5, double *high5, double *low10, double *high10, double *xwork, double *work2);
static double mean_t(int n, double *x) { double s = 0; for (int i = 0; i < n; i++) s += x[i]; return s / n; }
int main(int argc, char **argv) {
   if (argc != 3) { printf("usage: verify_bca sample.txt nboot\n"); return 1; }
   FILE *fp = fopen(argv[1], "r"); int n;
   if (!fp || fscanf(fp, "%d", &n) != 1) { printf("bad file\n"); return 1; }
   double *x = (double *) malloc(n * sizeof(double));
   for (int i = 0; i < n; i++) if (fscanf(fp, "%lf", &x[i]) != 1) { printf("short file\n"); return 1; }
   fclose(fp);
   int nboot = atoi(argv[2]);
   double *xw = (double *) malloc(n * sizeof(double)), *w2 = (double *) malloc(nboot * sizeof(double));
   double l2, h2, l5, h5, l10, h10;
   boot_conf_BCa(n, x, mean_t, nboot, &l2, &h2, &l5, &h5, &l10, &h10, xw, w2);
   printf("%.8f %.8f %.8f %.8f %.8f %.8f\n", l2, h2, l5, h5, l10, h10);
   return 0;
}
