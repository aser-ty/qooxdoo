#!/usr/bin/env python

import sys, string, re, os, random, shutil, optparse
import config, tokenizer, loader, compile, docgenerator, tree, treegenerator





def filetool(filepath, filename, content=""):
  # Concatting and Splitting
  outputFileName = os.path.normpath(os.path.join(filepath, filename))
  outputFileDir = os.path.dirname(outputFileName)

  # Check/Create directory
  if not os.path.exists(outputFileDir):
    os.makedirs(outputFileDir)

  # Writing file
  outputFile = file(outputFileName, "w")
  outputFile.write(content)
  outputFile.flush()
  outputFile.close()





def getparser():
  parser = optparse.OptionParser("usage: %prog [options]")

  # From file
  parser.add_option("--from-file", dest="fromFile", metavar="FILENAME", help="Read options from FILENAME.")
  parser.add_option("--export-to-file", dest="exportToFile", metavar="FILENAME", help="Store options to FILENAME.")

  # Source Directories
  parser.add_option("-s", "--source-directory", action="append", dest="sourceDirectories", metavar="DIRECTORY", default=[], help="Add source directory.")

  # Destination Directories
  parser.add_option("--source-output-directory", dest="sourceOutputDirectory", metavar="DIRECTORY", help="Define output directory for source JavaScript files.")
  parser.add_option("--token-output-directory", dest="tokenOutputDirectory", metavar="DIRECTORY", help="Define output directory for tokenized JavaScript files.")
  parser.add_option("--compile-output-directory", dest="compileOutputDirectory", metavar="DIRECTORY", help="Define output directory for compiled JavaScript files.")
  parser.add_option("--resource-output-directory", dest="resourceOutputDirectory", metavar="DIRECTORY", help="Define resource output directory.")
  parser.add_option("--api-output-directory", dest="apiOutputDirectory", metavar="DIRECTORY", help="Define api output directory.")

  # Destination Filenames
  parser.add_option("--source-output-filename", dest="sourceOutputFilename", default="qx.js", metavar="FILENAME", help="Name of output file from source build process.")
  parser.add_option("--compile-output-filename", dest="compileOutputFilename", default="qx.js", metavar="FILENAME", help="Name of output file from compiler.")
  parser.add_option("--api-json-output-filename", dest="apiJsonOutputFilename", default="api.js", metavar="FILENAME", help="Name of JSON API file.")
  parser.add_option("--api-xml-output-filename", dest="apiXmlOutputFilename", default="api.xml", metavar="FILENAME", help="Name of XML API file.")

  # Actions
  parser.add_option("-c", "--compile-source", action="store_true", dest="compileSource", default=False, help="Compile source files.")
  parser.add_option("-r", "--copy-resources", action="store_true", dest="copyResources", default=False, help="Copy resource files.")
  parser.add_option("--store-tokens", action="store_true", dest="storeTokens", default=False, help="Store tokenized content of source files.")
  parser.add_option("-g", "--generate-source", action="store_true", dest="generateSource", default=False, help="Generate source version.")
  parser.add_option("-a", "--generate-api", action="store_true", dest="generateApi", default=False, help="Generate API documentation.")
  parser.add_option("--print-files", action="store_true", dest="printFiles", default=False, help="Output known files.")
  parser.add_option("--print-modules", action="store_true", dest="printModules", default=False, help="Output known modules.")
  parser.add_option("--print-include", action="store_true", dest="printList", default=False, help="Output sorted file list.")

  # General options
  parser.add_option("-q", "--quiet", action="store_false", dest="verbose", default=False, help="Quiet output mode.")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="Verbose output mode.")

  # Include/Exclude
  parser.add_option("-i", "--include", action="append", dest="include", help="Include ID")
  parser.add_option("-e", "--exclude", action="append", dest="exclude", help="Exclude ID")

  # Include/Exclude options
  parser.add_option("--disable-include-dependencies", action="store_false", dest="enableIncludeDependencies", default=True, help="Enable include dependencies.")
  parser.add_option("--disable-exclude-dependencies", action="store_false", dest="enableExcludeDependencies", default=True, help="Enable exclude dependencies.")
  parser.add_option("--disable-auto-dependencies", action="store_false", dest="enableAutoDependencies", default=True, help="Disable detection of dependencies.")

  # Compile options
  parser.add_option("--add-new-lines", action="store_true", dest="addNewLines", default=False, help="Keep newlines in compiled files.")
  parser.add_option("--add-file-ids", action="store_true", dest="addFileIds", default=False, help="Add file IDs to compiled output.")
  parser.add_option("--compress-strings", action="store_true", dest="compressStrings", default=False, help="Compress Strings.")
  parser.add_option("--store-separate-scripts", action="store_true", dest="storeSeparateScripts", default=False, help="Store compiled javascript files separately, too.")

  # Source options
  parser.add_option("--relative-source-path", dest="relativeSourcePath", default="", metavar="PATH", help="Defines the relative source path.")

  return parser



def argparser(cmdlineargs):

  # Parse arguments
  (options, args) = getparser().parse_args(cmdlineargs)

  # Export to file
  if options.exportToFile != None:
    print
    print "  EXPORTING:"
    print "----------------------------------------------------------------------------"

    print " * Translating options..."

    optionString = "# Exported configuration from build.py\n\n"
    ignoreValue = True
    lastWasKey = False

    for arg in cmdlineargs:
      if arg == "--export-to-file":
        ignoreValue = True

      elif arg.startswith("--"):
        if lastWasKey:
          optionString += "\n"

        optionString += arg[2:]
        ignoreValue = False
        lastWasKey = True

      elif arg.startswith("-"):
        print "   * Couldn't export short argument: %s" % arg
        optionString += "\n# Ignored short argument %s\n" % arg
        ignoreValue = True

      elif not ignoreValue:
        optionString += " = %s\n" % arg
        ignoreValue = True
        lastWasKey = False



    print " * Export to file: %s" % options.exportToFile
    exportFile = file(options.exportToFile, "w")
    exportFile.write(optionString)
    exportFile.flush()
    exportFile.close()

    sys.exit(0)

  # Read from file
  elif options.fromFile != None:

    print
    print "  INITIALIZATION:"
    print "----------------------------------------------------------------------------"

    print "  * Reading configuration..."

    # Convert file content into arguments
    fileargs = {}
    fileargpos = 0
    fileargid = "default"
    currentfileargs = []
    fileargs[fileargid] = currentfileargs

    for line in file(options.fromFile).read().split("\n"):
      line = line.strip()

      if line == "" or line.startswith("#") or line.startswith("//"):
        continue

      # Splitting line
      line = line.split("=")

      # Extract key element
      key = line.pop(0).strip()

      # Separate packages
      if key == "package":
        fileargpos += 1
        fileargid = line[0].strip()

        print "    - Found package: %s" % fileargid

        currentfileargs = []
        fileargs[fileargid] = currentfileargs
        continue

      key = "--%s" % key

      if len(line) > 0:
        line = line[0].split(",")

        for elem in line:
          currentfileargs.append(key)
          currentfileargs.append(elem.strip())

      else:
        currentfileargs.append(key)

    # Parse
    defaultargs = fileargs["default"]

    if len(fileargs) > 1:
      (fileDb, moduleDb) = load(getparser().parse_args(defaultargs)[0])

      for filearg in fileargs:
        if filearg == "default":
          continue

        print
        print
        print "**************************** Next Package **********************************"
        print "PACKAGE: %s" % filearg

        combinedargs = []
        combinedargs.extend(defaultargs)
        combinedargs.extend(fileargs[filearg])

        options = getparser().parse_args(combinedargs)[0]
        execute(fileDb, moduleDb, options, filearg)

    else:
      options = getparser().parse_args(defaultargs)[0]
      (fileDb, moduleDb) = load(options)
      execute(fileDb, moduleDb, options)

  else:
    print
    print "  INITIALIZATION:"
    print "----------------------------------------------------------------------------"

    print "  * Processing arguments..."

    (fileDb, moduleDb) = load(options)
    execute(fileDb, moduleDb, options)







def main():
  if len(sys.argv[1:]) == 0:
    basename = os.path.basename(sys.argv[0])
    print "usage: %s [options]" % basename
    print "Try '%s -h' or '%s --help' to show the help message." % (basename, basename)
    sys.exit(1)

  argparser(sys.argv[1:])






def load(options):

  ######################################################################
  #  INITIAL CHECK
  ######################################################################

  if options.sourceDirectories == None or len(options.sourceDirectories) == 0:
    basename = os.path.basename(sys.argv[0])
    print "You must define at least one source directory!"
    print "usage: %s [options]" % basename
    print "Try '%s -h' or '%s --help' to show the help message." % (basename, basename)
    sys.exit(1)
  else:
    # Normalizing directories
    i=0
    for directory in options.sourceDirectories:
      options.sourceDirectories[i] = os.path.normpath(options.sourceDirectories[i])
      i+=1

  print
  print "  LOADING:"
  print "----------------------------------------------------------------------------"









  ######################################################################
  #  SCANNING FOR FILES
  ######################################################################

  print "  * Indexing files..."

  (fileDb, moduleDb) = loader.indexDirectories(options.sourceDirectories, options.verbose)

  print "  * Found %s files" % len(fileDb)

  if options.printFiles:
    print
    print "  KNOWN FILES:"
    print "----------------------------------------------------------------------------"
    print "  * These are all known files:"
    for fileEntry in fileDb:
      print "    - %s (%s)" % (fileEntry, fileDb[fileEntry]["path"])

  if options.printModules:
    print
    print "  KNOWN MODULES:"
    print "----------------------------------------------------------------------------"
    print "  * These are all known modules:"
    for moduleEntry in moduleDb:
      print "    * %s" % moduleEntry
      for fileEntry in moduleDb[moduleEntry]:
        print "      - %s" % fileEntry






  ######################################################################
  #  PLUGIN: AUTO DEPENDENCIES
  ######################################################################

  if options.enableAutoDependencies:
    print
    print "  AUTO DEPENDENCIES:"
    print "----------------------------------------------------------------------------"

    print "  * Detecting dependencies..."

    for fileEntry in fileDb:
      fileContent = fileDb[fileEntry]["content"]
      if options.verbose:
        print "    * %s" % fileEntry

      for depFileEntry in fileDb:
        if depFileEntry != fileEntry:
          if fileContent.find(depFileEntry) != -1:

            if depFileEntry in fileDb[fileEntry]["optionalDeps"]:
              if options.verbose:
                print "      - Optional: %s" % depFileEntry

            elif depFileEntry in fileDb[fileEntry]["loadDeps"]:
              if options.verbose:
                print "      - Load: %s" % depFileEntry

            elif depFileEntry in fileDb[fileEntry]["runtimeDeps"]:
              if options.verbose:
                print "      - Runtime: %s" % depFileEntry

            else:
              if options.verbose:
                print "      - Missing: %s" % depFileEntry

              fileDb[fileEntry]["runtimeDeps"].append(depFileEntry)



  return fileDb, moduleDb







def execute(fileDb, moduleDb, options, pkgid=""):

  additionalOutput = []


  ######################################################################
  #  SORTING FILES
  ######################################################################

  print
  print "  LIST SORT:"
  print "----------------------------------------------------------------------------"

  if options.verbose:
    print "  * Include: %s" % options.include
    print "  * Exclude: %s" % options.exclude

  print "  * Sorting files..."

  sortedIncludeList = loader.getSortedList(options, fileDb, moduleDb)

  if options.printList:
    print
    print "  INCLUDE ORDER:"
    print "----------------------------------------------------------------------------"
    print "  * The files will be included in this order:"
    for key in sortedIncludeList:
      print "    - %s" % key







  ######################################################################
  #  PLUGIN: COMPRESS STRINGS
  ######################################################################

  if options.compressStrings:
    print
    print "  STRING COMPRESSION:"
    print "----------------------------------------------------------------------------"

    print "  * Searching for string instances..."

    compressedStrings = {}

    for fileId in sortedIncludeList:
      if options.verbose:
        print "    - %s" % fileId

      for token in fileDb[fileId]["tokens"]:
        if token["type"] != "string":
          continue

        if token["detail"] == "doublequotes":
          compressSource = "\"%s\"" % token["source"]
        else:
          compressSource = "'%s'" % token["source"]

        if not compressedStrings.has_key(compressSource):
          compressedStrings[compressSource] = 1
        else:
          compressedStrings[compressSource] += 1


    if options.verbose:
      print "  * Sorting strings..."

    compressedList = []

    for compressSource in compressedStrings:
      compressedList.append({ "source" : compressSource, "usages" : compressedStrings[compressSource] })

    pos = 0
    while pos < len(compressedList):
      item = compressedList[pos]
      if item["usages"] <= 1:
        compressedList.remove(item)

      else:
        pos += 1

    compressedList.sort(lambda x, y: y["usages"]-x["usages"])

    print "  * Found %s string instances" % len(compressedList)

    if options.verbose:
      print "  * Building replacement map..."

    compressMap = {}
    compressCounter = 0
    compressJavaScript = "QXS%s=[" % pkgid

    for item in compressedList:
      if compressCounter != 0:
        compressJavaScript += ","

      compressMap[item["source"]] = compressCounter
      compressCounter += 1
      compressJavaScript += item["source"]

    compressJavaScript += "];"

    additionalOutput.append(compressJavaScript)

    print "  * Updating tokens..."

    for fileId in sortedIncludeList:
      if options.verbose:
        print "    - %s" % fileId

      for token in fileDb[fileId]["tokens"]:
        if token["type"] != "string":
          continue

        if token["detail"] == "doublequotes":
          compressSource = "\"%s\"" % token["source"]
        else:
          compressSource = "'%s'" % token["source"]

        if compressSource in compressMap:
          token["source"] = "QXS%s[%s]" % (pkgid, compressMap[compressSource])
          token["detail"] = "compressed"





  ######################################################################
  #  PLUGIN: STORE TOKENS
  ######################################################################

  if options.storeTokens:

    if options.tokenOutputDirectory == None:
      print "    * You must define the token directory!"
      sys.exit(1)

    else:
      options.tokenOutputDirectory = os.path.normpath(options.tokenOutputDirectory)

      # Normalizing directory
      if not os.path.exists(options.tokenOutputDirectory):
        os.makedirs(options.tokenOutputDirectory)

    print "  * Storing tokens..."

    for fileId in sortedIncludeList:
      if options.verbose:
        print "    - %s" % fileId

      tokenString = tokenizer.convertTokensToString(fileDb[fileId]["tokens"])
      tokenSize = len(tokenString) / 1000.0

      if options.verbose:
        print "    * writing tokens to file (%s KB)..." % tokenSize

      tokenFileName = os.path.join(options.tokenOutputDirectory, fileId + config.TOKENEXT)

      tokenFile = file(tokenFileName, "w")
      tokenFile.write(tokenString)
      tokenFile.flush()
      tokenFile.close()




  ######################################################################
  #  GENERATE API
  ######################################################################

  if options.generateApi:
    print
    print "  GENERATE API:"
    print "----------------------------------------------------------------------------"

    if options.apiOutputDirectory == None:
      print "    * You must define the API output directory!"
      sys.exit(1)

    else:
      options.apiOutputDirectory = os.path.normpath(options.apiOutputDirectory)

      # Normalizing directory
      if not os.path.exists(options.apiOutputDirectory):
        os.makedirs(options.apiOutputDirectory)

    docTree = None

    print "  * Docufying tokens"

    for fileId in fileDb:
      if options.verbose:
        print "  - %s" % fieId

      docTree = docgenerator.createDoc(fileDb[fileId]["tree"], docTree)

    if docTree:
      print "  * Doing post work..."
      docgenerator.postWorkPackage(docTree, docTree)

    print "  * Writing files..."
    filetool(options.apiOutputDirectory, options.apiJsonOutputFilename, tree.nodeToJsonString(docTree).encode("utf-8"))
    filetool(options.apiOutputDirectory, options.apiXmlOutputFilename, tree.nodeToXmlString(docTree).encode("utf-8"))




  ######################################################################
  #  COPY RESOURCES
  ######################################################################

  if options.copyResources:

    print
    print "  COPY RESOURCES:"
    print "----------------------------------------------------------------------------"

    print "  * Creating needed directories..."

    if options.resourceOutputDirectory == None:
      print "    * You must define the resource output directory!"
      sys.exit(1)

    else:
      options.resourceOutputDirectory = os.path.normpath(options.resourceOutputDirectory)

      # Normalizing directory
      if not os.path.exists(options.resourceOutputDirectory):
        os.makedirs(options.resourceOutputDirectory)

    for fileId in sortedIncludeList:
      filePath = fileDb[fileId]["path"]
      fileContent = fileDb[fileId]["content"]
      fileResourceList = loader.extractResources(fileContent)

      if len(fileResourceList) > 0:
        print "  * Found %i resources in %s" % (len(fileResourceList), fileId)

        for fileResource in fileResourceList:
          resourceId = fileId + "." + fileResource
          resourcePath = resourceId.replace(".", os.sep)

          if options.verbose:
            print "    * ResourcePath: %s" % resourcePath

          sourceDir = os.path.join(os.path.dirname(filePath), fileResource)
          destDir = os.path.join(options.resourceOutputDirectory, resourcePath)

          for root, dirs, files in os.walk(sourceDir):

            # Filter ignored directories
            for ignoredDir in config.DIRIGNORE:
              if ignoredDir in dirs:
                dirs.remove(ignoredDir)

            # Searching for items (resource files)
            for itemName in files:

              # Generate absolute source file path
              itemSourcePath = os.path.join(root, itemName)

              # Extract relative path and directory
              itemRelPath = itemSourcePath.replace(sourceDir + os.sep, "")
              itemRelDir = os.path.dirname(itemRelPath)

              # Generate destination directory and file path
              itemDestDir = os.path.join(destDir, itemRelDir)
              itemDestPath = os.path.join(itemDestDir, itemName)

              # Check/Create destination directory
              if not os.path.exists(itemDestDir):
                os.makedirs(itemDestDir)

              # Copy file
              shutil.copyfile(itemSourcePath, itemDestPath)






  ######################################################################
  #  SOURCE
  ######################################################################

  if options.generateSource:
    print
    print "  GENERATING SOURCE VERSION:"
    print "----------------------------------------------------------------------------"

    if options.sourceOutputDirectory == None:
      print "    * You must define the source output directory!"
      sys.exit(1)

    else:
      options.sourceOutputDirectory = os.path.normpath(options.sourceOutputDirectory)

    print "  * Generating includer..."

    sourceOutput = ""

    for fileId in sortedIncludeList:
      sourceOutput += 'document.write(\'<script type="text/javascript" src="%s%s"></script>\');\n' % (os.path.join(options.relativeSourcePath, fileId.replace(".", os.sep)), config.JSEXT)

    # Store file
    filetool(options.sourceOutputDirectory, options.sourceOutputFilename, sourceOutput)






  ######################################################################
  #  COMPILE
  ######################################################################

  if options.compileSource:
    print
    print "  GENERATING COMPILED VERSION:"
    print "----------------------------------------------------------------------------"

    if options.compileSource:
      compiledOutput = ""

      print "  * Compiling tokens..."

      if options.compileOutputDirectory == None:
        print "    * You must define the compile directory!"
        sys.exit(1)

      else:
        options.compileOutputDirectory = os.path.normpath(options.compileOutputDirectory)

      for fileId in sortedIncludeList:
        if options.verbose:
          print "    - %s" % fileId

        compiledFileContent = compile.compile(fileDb[fileId]["tokens"], options.addNewLines)

        if options.addFileIds:
          compiledOutput += "/* ID: " + fileId + " */\n" + compiledFileContent + "\n"
        else:
          compiledOutput += compiledFileContent

        if options.storeSeparateScripts:
          if options.verbose:
            print "      * writing compiled file..."
          filetool(options.compileOutputDirectory, fileId.replace(".", os.path.sep) + config.JSEXT, compiledFileContent)

      print "  * Saving compiled output %s..." % options.compileOutputFilename
      filetool(options.compileOutputDirectory, options.compileOutputFilename, "".join(additionalOutput) + compiledOutput)







######################################################################
#  MAIN LOOP
######################################################################

if __name__ == '__main__':
  try:
    main()

  except KeyboardInterrupt:
    print "  * Keyboard Interrupt"
    sys.exit(1)
