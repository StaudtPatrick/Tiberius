import sys
import os

starting_bin = int(sys.argv[1])
stopping_bin = int(sys.argv[2])

os.system("python -m fitting_utils.generate_LDCS")

for i in range(starting_bin,stopping_bin):
	os.system("python -m fitting_utils.gppm_fit %d"%i)
 
os.system("python -m fitting_utils.plot_output -s -st -cp")
os.system("python -m fitting_utils.model_table_generator")

try:
	os.system("mkdir SPEC_tables")
	os.system("mkdir SPEC_plots")
	os.system("mkdir SPEC_pickled_objects")
except: 
	pass

os.system("mv *.pickle SPEC_pickled_objects/")
os.system("mv *.txt SPEC_tables/")
os.system("mv *.png SPEC_plots/")
os.system("mv *.pdf SPEC_plots/")
os.system("mv SPEC_tables/fitting_input.txt .")
#os.system("mv SPEC_tables/LD_coefficients.txt .")
