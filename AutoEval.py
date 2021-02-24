import os
import subprocess
import numpy as np


# OKGREEN = '\033[92m'
# WARNING = '\033[93m'
# FAIL = '\033[91m'
# ENDC = '\033[0m'
OKGREEN = '<span style="color:green">'
WARNING = '<span style="color:orangered">'
FAIL = '<span style="color:red">'
ENDC = '</span>'

OK = 0
ERROR = -2
OK_BUT = -1


COMPILATION_ERR_CODE = -1
LINKING_ERR_CODE = -2
EXECUTION_ERR_CODE = -3
OUTPUT_ERR_CODE = -4
VALGRIND_ERR_CODE = -5

class AutoEval:

	###################################
	# CONSTRUCTOR
	###################################

	def __init__(self, exerciseName, sourceFiles, libDirs=[], libs=[], mainFile="", inputArguments=""):
		self.exerciseName = exerciseName

		self.templateFile = "template_"+exerciseName+".txt"
		self.sourceFiles = sourceFiles
		self.mainFile = mainFile
		self.libDirs = libDirs
		self.libs = libs
		self.inputArguments = inputArguments

		self.header = []
		self.blocks = {}
		self.tests = []
		self.expectedOutputs = []

		# If main not provided we need to load template
		if mainFile == "":
			self.templateLoaded = False
		else:
			self.templateLoaded = True
			self.tests = ["Test main "+ mainFile+",0"]

		self.outputsGenerated = False


	###################################
	# TEMPLATE READER
	###################################

	def read_template(self):
		with open(self.templateFile, 'r') as template:

			line = template.readline()
			while line != '':
				if line != "\n":
					if len(line) > 2 and line[0:3] == "@@@":
						self.header = []
						self.read_header(template)
					elif len(line) > 2 and line[0:3] == "$$$":
						self.read_block(template, line[4:].replace("\n", ""))
					elif len(line) > 2 and line[0:3] == "???":
						self.read_tests(template)

				line = template.readline()

		self.templateLoaded = True



	def read_header(self, template):
		line = template.readline()

		while line != '':
			if line != "\n":
				if len(line) > 2 and line[0:3] == "@@@":
					break

			self.header.append(line)

			line = template.readline()

		return


	def read_block(self, template, blockId):
		self.blocks[blockId] = []

		line = template.readline()

		while line != '':
			if line != "\n":
				if len(line) > 2 and line[0:3] == "$$$":
					break
				
			self.blocks[blockId].append(line)

			line = template.readline()


		return


	def read_tests(self, template):
		line = template.readline()

		while line != '':
			if line != "\n":
				if len(line) > 2 and line[0:3] == "???":
					break
				else:
					self.tests.append(line)

			line = template.readline()

		return



	###################################
	# GENERATE OUTPUTS
	###################################

	def generate_outputs(self):
		if self.templateLoaded != True:
			print("\tTemplate not loaded")
			return

		user = "solution"
		cleanFiles = False

		# Go to user dir
		os.chdir(user)

		print("\tGenerating outputs for exercise "+self.exerciseName)

		with open("report_"+user+"_"+self.exerciseName+".md", 'w') as outFile:

			outFile.write("## Exercise %s %s<br>\n"%(self.exerciseName, user))

			# Compile sources
			ret = self.compile_sources(outFile)

			if ret == ERROR:
				if cleanFiles:
					self.clear()
				os.chdir("..")
				return

			for i, test in enumerate(self.tests):
				# Generate main file for test
				parts = test.split(",")
				testName = parts[0]
				blocksOrder = parts[1].replace("\n", "").split(" ")
				mainFile = "main_"+self.exerciseName+"_"+str(i)+".c"

				outFile.write("#### **Test %d: %s**\n"%(i, testName))

				# Create main file if not provided
				if self.mainFile == "":
					self.write_main(mainFile, blocksOrder)
				else:
					mainFile = self.mainFile

				# Compile main
				ret = self.compile_single(outFile, mainFile)

				if ret == ERROR:
					continue

				# Link objects
				execName = self.link_objects(outFile, self.libDirs, self.libs, self.sourceFiles+[mainFile])

				if execName == "":
					continue

				# Execute tests
				ret, output = self.execute(outFile, execName, self.inputArguments)

				if ret == ERROR:
					if cleanFiles:
						self.clean_file(execName)
						if self.mainFile == "":
							self.clean_file(mainFile)
					continue

				outFile.write(f"\n<pre>{output}</pre>" + "<br>\n")

				# Run Valgrind
				ret = self.run_valgrind(outFile, execName)

				# Save outputs
				self.expectedOutputs.append(output)


				# Clean exec and main
				if cleanFiles:
					self.clean_file(execName)
					if self.mainFile == "":
						self.clean_file(mainFile)

		# Clean objects
		if cleanFiles:
			self.clear()

		# Go back to main dir
		os.chdir("..")

		self.outputsGenerated = True

		return






	###################################
	# PERFORM TESTS
	###################################


	def perform_tests(self, user, cleanFiles=True):
		if self.templateLoaded != True or self.outputsGenerated != True:
			print("\tTemplate not loaded or outputs not generated")
			return

		# Go to user dir
		os.chdir(user)

		print("\tEvaluating "+user)

		feedNums = np.zeros(len(self.tests))
		testsNames = []

		with open("report_"+user+"_"+self.exerciseName+".md", 'w') as outFile, open("feedback_summary_"+user+".txt", 'a') as sumFile:

			outFile.write("## Exercise %s %s<br>\n"%(self.exerciseName, user))
			sumFile.write("\n\n## Exercise %s\n"%(self.exerciseName))

			# Compile sources
			ret = self.compile_sources(outFile)

			if ret == ERROR:
				sumFile.write("Sources compilation error.\n")
				feedNums += COMPILATION_ERR_CODE

				if cleanFiles:
					self.clear()
				os.chdir("..")
				return feedNums, None

			for i, test in enumerate(self.tests):
				# Generate main file for test
				parts = test.split(",")
				testName = parts[0]
				blocksOrder = parts[1].replace("\n", "").split(" ")
				mainFile = "main_"+self.exerciseName+"_"+str(i)+".c"

				outFile.write("#### **Test %d: %s**\n"%(i, testName))
				sumFile.write("%s: "%(testName))
				testsNames.append(testName)


				# Create main file if not provided
				if self.mainFile == "":
					self.write_main(mainFile, blocksOrder)
				else:
					mainFile = self.mainFile

				# Compile main
				ret = self.compile_single(outFile, mainFile)

				if ret == ERROR:
					sumFile.write("Compilation error.\n")
					feedNums[i] += COMPILATION_ERR_CODE
					continue

				# Link objects
				execName = self.link_objects(outFile, self.libDirs, self.libs, self.sourceFiles+[mainFile])

				if execName == "":
					sumFile.write("Linking error.\n")
					feedNums[i] += LINKING_ERR_CODE
					continue

				# Execute tests
				ret, output = self.execute(outFile, execName, self.inputArguments)

				if ret == ERROR:
					testFeedback += "Execution error. "
					feedNums[i] += EXECUTION_ERR_CODE

					'''
					if cleanFiles:
						self.clean_file(execName)
						if self.mainFile == "":
							self.clean_file(mainFile)
					continue
					'''
				else:
					# Compare outputs
					ret = self.compare_outputs(outFile, self.expectedOutputs[i], output)

					testFeedback = ""
					if ret == ERROR:
						testFeedback += "Wrong output. "
						feedNums[i] += OUTPUT_ERR_CODE

				# Run Valgrind
				ret = self.run_valgrind(outFile, execName)

				if ret == ERROR:
					testFeedback += "Memory leaks/errors."
					feedNums[i] += VALGRIND_ERR_CODE

				testFeedback += "\n"
				sumFile.write(testFeedback)


				# Clean exec and main
				if cleanFiles:
					self.clean_file(execName)
					if self.mainFile == "":
						self.clean_file(mainFile)

		# Clean objects
		if cleanFiles:
			self.clear()

		# Go back to main dir
		os.chdir("..")


		return feedNums, testsNames


	def write_main(self, mainFile, blocksOrder):
		with open(mainFile, 'w') as main:
			for line in self.header:
				main.write(line)

			main.write("\n\n/**************************/\n\n")

			main.write("int main(int argc, char * argv[]) {\n")

			for blockId in blocksOrder:
				for line in self.blocks[blockId]:
					main.write("\t"+line)


			main.write("}")

			main.write("\n\n/**************************/\n\n")





	def compile_sources(self, outFile):
		outFile.write("#### **Compiling sources...**<br>\n")

		# Compile sources
		ret = OK
		for source in self.sourceFiles:
			ret = min(ret, self.compile_single(outFile, source))

		return ret

	 
	def compile_single(self, outFile, source):
		ret = OK
		outFile.write(f"gcc -Wall -g -pedantic -c {source}" + " ")
		
		proc = subprocess.Popen(['gcc', '-Wall', '-g', '-pedantic', '-c', source], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		rout, rerr = proc.communicate()

		if rerr == b'':
			outFile.write(OKGREEN + "OK" + ENDC + "<br>\n")
		else:
			error_str = rerr.decode("utf-8")

			if "error:" in error_str:
				# error
				error_str = error_str.replace("error", FAIL + "error" + ENDC + "<br>\n")
				outFile.write(FAIL + "ERROR" + ENDC + "<br>\n")
				outFile.write(f"\n<pre>{error_str}</pre><br>" + "\n")

				#!! TODO: try compiler suggestions


				ret = ERROR

			else:
				# warning
				error_str = error_str.replace("warning", WARNING + "warning" + ENDC + "<br>\n")
				outFile.write(WARNING + "WARNING" + ENDC + "<br>\n")
				outFile.write(f"\n<pre>{error_str}</pre><br>" + "\n")

				ret = OK_BUT
				

		return ret



	def link_objects(self, outFile, libDirs, libs, sources):
		linkCommand = ['gcc', '-Wall', '-g', '-pedantic']

		# Build command
		for source in sources:
			linkCommand.append(source.replace(".c", ".o"))

		for libDir in libDirs:
			linkCommand.append(libDir)

		for lib in libs:
			linkCommand.append(lib)

		linkCommand.append("-o")

		execName = sources[-1].replace(".c", "")
		linkCommand.append(execName)

		outFile.write(" ".join(linkCommand) + " ")


		proc = subprocess.Popen(linkCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		rout, rerr = proc.communicate()


		if rerr == b'':
			outFile.write(OKGREEN + "OK" + ENDC + "<br>\n")
		else:
			error_str = rerr.decode("utf-8")
			error_str = error_str.replace("error", FAIL + "error" + ENDC + "<br>\n")

			outFile.write(FAIL + "ERROR" + ENDC + "\n")
			outFile.write(f"\n<pre>{error_str}</pre>" + "<br>\n")

			execName = ""

		return execName



	def execute(self, outFile, execName, inputArguments=""):
		timeout=5
		ret = OK

		if inputArguments != "":
			inputArguments = " " + inputArguments

		outFile.write("./"+ execName + inputArguments + " ")
		try:
			proc = subprocess.run(['./' + execName + inputArguments], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, shell=True)

			if proc.returncode != 0:
				outFile.write(WARNING + "return code is " + str(proc.returncode) + ENDC + " ")
			
			if proc.stderr == b'':
				outFile.write(OKGREEN + "OK" + ENDC + "<br>\n")
			else:
				error_str = proc.stderr.decode("utf-8")
				error_str = error_str.replace("error", FAIL + "error" + ENDC + "<br>\n")

				outFile.write(FAIL + "ERROR" + ENDC + "\n")
				outFile.write(f"\n<pre>{error_str}</pre>" + "<br>\n")

				ret = ERROR

		except subprocess.TimeoutExpired as error:
			outFile.write(FAIL + "TIMEOUT: " + ENDC + "<br>\n")
			outFile.write(error + "<br>\n")
			ret = ERROR


		return ret, proc.stdout.decode("utf-8")





	def compare_outputs(self, outFile, expected, obtained):
		outFile.write("Expected output... ")
		ret = OK

		if expected == obtained:
			outFile.write(OKGREEN + "OK" + ENDC + "<br>\n")
		elif expected.lower() == obtained.lower():
			outFile.write(WARNING + "OK with case insensitive" + ENDC + "<br>\n")
		elif [c for c in expected if c.isspace() == False] == [c for c in obtained if c.isspace() == False]:
			outFile.write(WARNING + "OK removing spaces" + ENDC + "<br>\n")
			outFile.write(f"\n**Expected:**\n<pre>{expected}</pre>" + "<br>\n")
			outFile.write(f"\n**Obtained:**\n<pre>{obtained}</pre>" + "<br>\n")
		else:
			outFile.write(FAIL + "WRONG" + ENDC + "\n")
			outFile.write(f"\n**Expected:**\n<pre>{expected}</pre>" + "<br>\n")
			outFile.write(f"\n**Obtained:**\n<pre>{obtained}</pre>" + "<br>\n")
			ret = ERROR

		return ret



	def run_valgrind(self, outFile, execName):
		ret = OK

		outFile.write("Running Valgrind... ")
		proc = subprocess.Popen(['valgrind', '--leak-check=full', './' + execName], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		rout, rerr = proc.communicate()
		valgrind_str = rerr.decode("utf-8")
		valgrind_lines = valgrind_str.split("\n")

		if "ERROR SUMMARY: 0 errors from 0 contexts" in valgrind_str:
			outFile.write(OKGREEN + "OK" + ENDC + "<br>\n")
			outFile.write(f"\n<pre> {valgrind_lines[-2]} </pre>" + "<br>\n")
		else:
			outFile.write(FAIL + "ERROR" + ENDC + "<br>\n")
			outFile.write(f"\n<pre> {valgrind_str} </pre>" + "<br>\n")
			ret = ERROR

		return ret




	def clear(self):
		proc = subprocess.call(['rm -rf *.o'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

	def clean_file(self, file):
		proc = subprocess.call(['rm -rf '+file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)