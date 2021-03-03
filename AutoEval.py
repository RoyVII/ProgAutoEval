import os
import subprocess
import numpy as np
import shutil


# OKGREEN = '\033[92m'
# WARNING = '\033[93m'
# FAIL = '\033[91m'
# ENDC = '\033[0m'
OKGREEN = '<span style="color:green">'
WARNING = '<span style="color:orangered">'
FAIL = '<span style="color:red">'
ENDC = '</span>'

OK = 0
ERROR = -1
OK_BUT = -2


COMPILATION_ERR_CODE = -1
LINKING_ERR_CODE = -2
EXECUTION_ERR_CODE = -3
OUTPUT_ERR_CODE = -4
VALGRIND_ERR_CODE = -5

BLOCKS_TEMPLATE = 0
MAINS_TEMPLATE = 1

class AutoEval:

	###################################
	# CONSTRUCTOR
	###################################

	def __init__(self, exerciseName, sourceFiles, libDirs=[], libs=[], compileFlags=[], linkFlags=[], mainFile="", inputArguments=""):
		self.exerciseName = exerciseName

		self.templateFile = "template_"+exerciseName+".txt"
		self.sourceFiles = sourceFiles
		self.mainFile = mainFile
		self.libDirs = libDirs
		self.libs = libs
		self.compileFlags = compileFlags
		self.linkFlags = linkFlags
		self.inputArguments = inputArguments


		self.tests = []
		self.expectedOutputs = []
		self.templateType = BLOCKS_TEMPLATE

		# In case of blocks template
		self.header = []
		self.blocks = {}

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

			if len(line) > 2 and line[0:3] == "@$?":
				self.templateType = MAINS_TEMPLATE
				line = template.readline()

				while line != '':
					if line != "\n":
						self.tests.append(line)

					line = template.readline()

			else:
				self.templateType = BLOCKS_TEMPLATE

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

	def generate_outputs(self, cleanFiles=True):
		if self.templateLoaded != True:
			print("\tTemplate not loaded")
			return

		user = "solution"

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

				outFile.write("#### **Test %d: %s**\n"%(i, testName))

				# Create main file if not provided
				mainFile = self.generate_main(parts[1], i)

				# Compile main
				ret = self.compile_single(outFile, mainFile, self.compileFlags)

				if ret == ERROR:
					continue

				# Link objects
				execName = self.link_objects(outFile, self.libDirs, self.libs, self.sourceFiles+[mainFile], self.linkFlags)

				if execName == "":
					continue

				# Execute tests
				ret, output = self.execute(outFile, execName, self.inputArguments)

				if ret == ERROR:
					if cleanFiles:
						self.clean_file(execName)

					continue

				outFile.write(f"\n<pre>{output}</pre>" + "<br>\n")

				# Run Valgrind
				ret = self.run_valgrind(outFile, execName)

				# Save outputs
				self.expectedOutputs.append(output)


				# Clean exec and main
				if cleanFiles:
					self.clean_file(execName)

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

				outFile.write("#### **Test %d: %s**\n"%(i, testName))
				sumFile.write("%s: "%(testName))
				testsNames.append(testName)


				# Create main file if not provided
				mainFile = self.generate_main(parts[1], i)

				# Compile main
				ret = self.compile_single(outFile, mainFile, self.compileFlags)

				if ret == ERROR:
					sumFile.write("Compilation error.\n")
					feedNums[i] += COMPILATION_ERR_CODE

					if cleanFiles:
						if self.mainFile == "":
							self.clean_file(mainFile)
					continue

				# Link objects
				execName = self.link_objects(outFile, self.libDirs, self.libs, self.sourceFiles+[mainFile], self.linkFlags)

				if execName == "":
					sumFile.write("Linking error.\n")
					feedNums[i] += LINKING_ERR_CODE

					if cleanFiles:
						if self.mainFile == "":
							self.clean_file(mainFile)
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
				elif ret == -3:
					testFeedback += "Timeout error. "
					feedNums[i] += EXECUTION_ERR_CODE

					
					if cleanFiles:
						self.clean_file(execName)
						if self.mainFile == "":
							self.clean_file(mainFile)
					continue
					
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


	def generate_main(self, auxString, testIdx):
		if self.mainFile == "":
			if self.templateType == BLOCKS_TEMPLATE:
				blocksOrder = auxString.replace("\n", "").split(" ")
				mainFile = "main_"+self.exerciseName+"_"+str(testIdx)+".c"
				self.write_main(mainFile, blocksOrder)

			elif self.templateType == MAINS_TEMPLATE:
				mainPath = auxString.replace("\n", "")
				mainFile = mainPath.split("/")[-1]
				self.copy_main(mainPath)

		else:
			mainFile = self.mainFile

		return mainFile



	def write_main(self, mainFile, blocksOrder):
		with open(mainFile, 'w') as main:
			for line in self.header:
				main.write(line)

			main.write("\n\n/**************************/\n\n")

			#main.write("int main(int argc, char * argv[]) {\n")

			for blockId in blocksOrder:
				for line in self.blocks[blockId]:
					main.write(line)


			#main.write("}")

			main.write("\n\n/**************************/\n\n")


	def copy_main(self, mainPath):
		shutil.copy2(mainPath, ".")


	def compile_sources(self, outFile):
		outFile.write("#### **Compiling sources...**<br>\n")

		# Compile sources
		ret = OK
		for source in self.sourceFiles:
			ret = min(ret, self.compile_single(outFile, source, self.compileFlags))

		return ret

	 
	def compile_single(self, outFile, source, flags):
		ret = OK

		compileCommand = ['gcc']

		# Build command
		for flag in flags:
			compileCommand.append(flag)

		compileCommand.append("-c")

		compileCommand.append(source)

		outFile.write(" ".join(compileCommand) + " ")
		
		proc = subprocess.Popen(compileCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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



	def link_objects(self, outFile, libDirs, libs, sources, flags):
		linkCommand = ['gcc']

		# Build command
		for flag in flags:
			linkCommand.append(flag)

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
		retStr = ""

		if inputArguments != "":
			inputArguments = " " + inputArguments

		outFile.write("./"+ execName + inputArguments + " ")
		try:
			proc = subprocess.run(['./' + execName + inputArguments], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, shell=True)
			retStr = proc.stdout.decode("utf-8")

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
			outFile.write(FAIL + "TIMEOUT: " + ENDC + " ")
			outFile.write(str(timeout) + " seconds <br>\n")
			ret = -3

		return ret, retStr





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