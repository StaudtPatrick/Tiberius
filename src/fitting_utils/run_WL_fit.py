import os

os.system("python -m fitting_utils.generate_LDCS")
os.system("python -m fitting_utils.gppm_fit '0'")


try:
	os.system("mkdir WL_tables")
	os.system("mkdir WL_plots")
	os.system("mkdir WL_pickled_objects")
except:
	pass

os.system("mv *.pickle WL_pickled_objects/")
os.system("mv *.txt WL_tables/")
os.system("mv *.png WL_plots/")
os.system("mv *.pdf WL_plots/")
os.system("mv WL_tables/fitting_input.txt .")
#os.system("mv tables/LD_coefficients.txt .")
