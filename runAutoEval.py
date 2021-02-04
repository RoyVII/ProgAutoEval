import AutoEval
import os
import sys

subdirs = [ name for name in os.listdir('.') if os.path.isdir(os.path.join('.', name)) ]
subdirs.reverse()
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

filename = sys.argv[1]


with open(filename, "r") as f:
	f.readline() # First line with the headers

	for test in f:
		parts = test.replace("\n", "").split(",")

		tp = parts[0]
		exerciseName = parts[1]
		sources = [x for x in parts[2].split(" ") if x != ''] # Avoids ['']
		libDirs = [x for x in parts[3].split(" ") if x != '']
		libs = [x for x in parts[4].split(" ") if x != '']
		mainFile = parts[5]
		inputArguments = parts[6]

		print("\nTest with arguments: ",tp, exerciseName, sources, libDirs, libs, mainFile, inputArguments)

		m = AutoEval.AutoEval(exerciseName, sources, libDirs=libDirs, libs=libs, mainFile=mainFile, inputArguments=inputArguments)
		
		if tp == "library":
			m.read_template()

		m.generate_outputs()


		for user in subdirs:
			m.perform_tests(user)
