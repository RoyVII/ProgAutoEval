import AutoEval
import os
import argparse




def plotTable(title, rowsNames, columnNames, data):
	import matplotlib.pyplot as plt
	import numpy as np


	COMPILATION_ERR_CODE = -1
	LINKING_ERR_CODE = -2
	EXECUTION_ERR_CODE = -3
	OUTPUT_ERR_CODE = -4
	VALGRIND_ERR_CODE = -5


	nRows = len(rowsNames)
	nCols = len(columnNames)
	columnNames_aux = columnNames.copy()
	cellText = []
	colors = []


	for i in range(nRows):
		rowsNames[i] = "Test %d: %s"%(i, rowsNames[i])

		cellText.append([])
		colors.append([])

		for j in range(nCols):
			cellText[-1].append("")

			columnNames_aux[j] = columnNames[j][-3:]

			if data[j][i] == 0:
				# OK
				colors[-1].append("limegreen")
			elif data[j][i] == COMPILATION_ERR_CODE:
				# Compiling error
				colors[-1].append("black")
			elif data[j][i] == LINKING_ERR_CODE:
				# Linking error
				colors[-1].append("darkmagenta")
			elif data[j][i] == EXECUTION_ERR_CODE:
				# Execution error
				colors[-1].append("red")
			elif data[j][i] == OUTPUT_ERR_CODE:
				# Wrong output
				colors[-1].append("yellow")
			elif data[j][i] == VALGRIND_ERR_CODE:
				# Memory error
				colors[-1].append("orange")
			elif data[j][i] == EXECUTION_ERR_CODE + VALGRIND_ERR_CODE:
				# Execution error and memory error
				colors[-1].append("red")
			elif data[j][i] == OUTPUT_ERR_CODE + VALGRIND_ERR_CODE:
				# Wrong output and memory error
				colors[-1].append("orange")
			else:
				# Nothing
				colors[-1].append("w")


	
	width=5*2.5
	height=3*2.5
	col_width=.075


	headings=columnNames
	fig=plt.figure()
	ax=fig.add_subplot(111, frameon=False, xticks=[], yticks=[])


	the_table = ax.table(cellText=cellText, rowLabels=rowsNames, colLabels=columnNames_aux, colWidths=[col_width]*np.array(data).shape[0], loc='lower right', cellColours=colors) #remove colLabels
	the_table.auto_set_font_size(False) 
	the_table.set_fontsize(10) 
	#the_table.scale(1, 1.6)

	'''
	#custom heading titles - new portion
	hoffset=0.42 #find this number from trial and error
	voffset=0.66 #find this number from trial and error
	line_fac=0.98 #controls the length of the dividing line
	count=0
	for string in headings:
		ax.annotate('  '+string, xy=(hoffset+count*col_width,voffset),
			xycoords='axes fraction', ha='left', va='bottom', 
			rotation=45, size=10)

		#add a dividing line
		ax.annotate('', xy=(hoffset+(count+0.5)*col_width,voffset), 
			xytext=(hoffset+(count+0.5)*col_width+line_fac/width,voffset+line_fac/height),
			xycoords='axes fraction', arrowprops={'arrowstyle':'-'})
		

		count+=1
	'''

	ax.axis('tight')


	#plt.show()
	plt.savefig("summary_"+title, bbox_inches='tight')






subdirs = [ name for name in os.listdir('.') if os.path.isdir(os.path.join('.', name)) ]
subdirs.sort()
subdirs.remove('solution')
try:
	subdirs.remove('__pycache__')
except:
	s = "nothing"

try:
	subdirs.remove('.git')
except:
	s = "nothing"


print("Users to evaluate: ", subdirs, end="\n")

# Possible arguments and details
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--file", required=True)
ap.add_argument("-P", "--plot", required=False, default=False)
args = vars(ap.parse_args())

filename = args['file']
doPlot = bool(int(args['plot']))


with open(filename, "r") as f:
	f.readline() # First line with the headers

	for exercise in f:
		parts = exercise.replace("\n", "").split(";")

		exerciseName = parts[0]
		sources = [x for x in parts[1].split(" ") if x != ''] # Avoids ['']
		libDirs = [x for x in parts[2].split(" ") if x != '']
		includeDirs = [x for x in parts[3].split(" ") if x != '']
		libs = [x for x in parts[4].split(" ") if x != '']
		compileFlags = [x for x in parts[5].split(" ") if x != '']
		linkFlags = [x for x in parts[6].split(" ") if x != '']
		mainFile = parts[7]

		print("\nTest with arguments: ", exerciseName, sources, libDirs, libs, compileFlags, linkFlags, mainFile)

		m = AutoEval.AutoEval(exerciseName, sources, libDirs=libDirs, libs=libs, compileFlags=compileFlags, linkFlags=linkFlags, mainFile=mainFile)
		
		
		m.read_template()
		m.generate_outputs()

		testsNames = []
		testsResults = []

		for user in subdirs:

			# Check if there is another subfolder
			ls = [ name for name in os.listdir(user) if os.path.isdir(os.path.join(user, name)) ]
			anotherLevel = False
			if (len(ls) == 1 and ls[0] == user):
				os.chdir(user)
				anotherLevel = True

			res, resNames = m.perform_tests(user)

			# Return to cwd
			if anotherLevel == True:
				reports = [user+"/"+f for f in os.listdir(user) if f.startswith("report")]
				for report in reports:
					os.replace(report, report.replace(user+"/", ""))

				os.chdir("..")

			testsResults.append(res)
			if resNames is not None:
				testsNames = resNames

		if doPlot:
			plotTable(exerciseName, testsNames, subdirs, testsResults)












