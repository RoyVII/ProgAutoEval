import MainGenerator
import os

subdirs = [x[0] for x in os.walk('.')]
subdirs.remove('.')
subdirs.remove('./solution')
try:
	subdirs.remove('./__pycache__')
except:
	s = "nothing"

subdirs = [x.replace("./", "") for x in subdirs]


with open("test_p1.csv", "r") as f:
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

		print(tp, exerciseName, sources, libDirs, libs, mainFile, inputArguments)

		m = MainGenerator.MainGenerator(exerciseName, sources, libDirs=libDirs, libs=libs, mainFile=mainFile, inputArguments=inputArguments)
		
		if tp == "library":
			m.read_template()

		m.generate_outputs()


		for user in subdirs:
			m.perform_tests(user)
