import cbor2 as cbor
import matplotlib.pyplot as plt
import numpy as np
from os import listdir, makedirs
from os.path import isfile, dirname, isdir
import argparse

CLI_DESCRIPTION = "Crops useful data from Edge Impulse .cbor timeseries measures."
CLI_INPUT_FOLDER_PATH_HELP = "Path of the folder with the input .cbor files."
CLI_OUTPUT_FOLDER_PATH_HELP = "Path of the folder that will have the cropped .cbor files and output images."
CLI_LOG_PATH_HELP = "Path of the log file."
CLI_TRIGGER_PERCENTAGE_HELP ="Percentage of the max signal value that will trigger the beginig and end of the useful data, must be a decimal number between 0 and 1, default = 0.1."
CLI_GUARDS_PERCENTAGE_HELP = "Percentage of the data that will be kept before and after the triggers, must be a decimal number between 0 and 1, default = 0.05."
CLI_IMAGE_WIDTH_HELP = "Output image width, must be a positive integer, default = 20."
CLI_IMAGE_HEIGHT_HELP = "Output image height, must be a positive integer, default = 20."

ValidFiles = []

def CropFile(InputFile, OutputFile, OutputImage, TriggerPercentage, GuardsPercentage, FigureHeight, FigureWidth, ):
    Data = []
    try:
        with open(InputFile, "rb") as File:
            Data = cbor.load(File)
    except Exception as Error:
        raise RuntimeError(f"Error reading {InputFile=}: {Error=}, {type(Error)=}")

    NPData = np.array(Data["payload"]["values"])
    NPMagnitude = np.array([sum(x)**(1/NPData.shape[1]) for x in NPData**2])
    NPMagnitudeGradient = abs(np.gradient(NPMagnitude))


    GuardsValue = round(NPData.shape[0]*GuardsPercentage)
    TriggerValue = np.max(NPMagnitudeGradient)*TriggerPercentage
    Triggers = np.where(NPMagnitudeGradient >= TriggerValue)[0]
    LeftTrigger = Triggers[0]
    RightTrigger = Triggers[-1]
    LeftGuard = LeftTrigger - GuardsValue
    RightGuard = RightTrigger + GuardsValue

    LeftTrigger = LeftTrigger if LeftTrigger > 0 else 0
    LeftGuard = LeftGuard if LeftGuard > 0 else 0
    RightTrigger = RightTrigger if RightTrigger > NPData.shape[1] else NPData.shape[1]
    RightGuard = RightGuard if RightGuard > NPData.shape[1] else NPData.shape[1]

    Data["payload"]["values"] = Data["payload"]["values"][LeftGuard:RightGuard]
    try:
        makedirs(dirname(OutputFile), exist_ok=True)
        with open(OutputFile, "wb") as File:
            cbor.dump(Data, File)
    except Exception as Error:
        raise RuntimeError(f"Error writing output {InputFile=}: {Error=}, {type(Error)=}")


    Figure, Axes = plt.subplots(3, 1, constrained_layout=True)
    Figure.suptitle(InputFile)

    Axes[0].set_title("Input")
    Axes[0].plot(NPData, label=[x["name"] for x in Data["payload"]["sensors"]])
    Axes[0].axvline(LeftTrigger, linestyle="--", color="g", label="Left trigger")
    Axes[0].axvline(RightTrigger, linestyle="--", color="k", label="Right trigger")
    Axes[0].axvline(LeftGuard, linestyle="--", color="m", label="Left guard")
    Axes[0].axvline(RightGuard, linestyle="--", color="y", label="Right guard")
    Axes[0].set_xlim(0, NPData.shape[0])
    Axes[0].set_xticks(Axes[0].get_xticks()[:-1], Axes[0].get_xticks()[:-1]*Data["payload"]["interval_ms"])
    Axes[0].set_xlabel("Time [ms]")
    Axes[0].set_ylabel("Data magnitude")
    Axes[0].legend()

    Axes[1].set_title("Gradient")
    Axes[1].plot(NPMagnitudeGradient, label="Gradient")
    Axes[1].axhline(TriggerValue, linestyle="--", color="r", label="Trigger level")
    Axes[1].axvline(LeftTrigger, linestyle="--", color="g", label="Left trigger")
    Axes[1].axvline(RightTrigger, linestyle="--", color="k", label="Right trigger")
    Axes[1].axvline(LeftGuard, linestyle="--", color="m", label="Left guard")
    Axes[1].axvline(RightGuard, linestyle="--", color="y", label="Right guard")
    Axes[1].set_xlim(0, NPData.shape[0])
    Axes[1].set_xticks(Axes[1].get_xticks()[:-1], Axes[1].get_xticks()[:-1]*Data["payload"]["interval_ms"])
    Axes[1].set_xlabel("Time [ms]")
    Axes[1].set_ylabel("Gradient absolute magnitude")
    Axes[1].legend()

    Axes[2].set_title("Output")
    Axes[2].plot(Data["payload"]["values"], label=[x["name"] for x in Data["payload"]["sensors"]])
    Axes[2].set_xlim(0, np.shape(Data["payload"]["values"])[0])
    Axes[2].set_xticks(Axes[2].get_xticks()[:-1], Axes[2].get_xticks()[:-1]*Data["payload"]["interval_ms"])
    Axes[2].set_xlabel("Time [ms]")
    Axes[2].set_ylabel("Data magnitude")
    Axes[2].legend()

    Figure.set_figheight(FigureHeight)
    Figure.set_figwidth(FigureWidth)

    try:
        makedirs(dirname(OutputImage), exist_ok=True)
        Figure.savefig(OutputImage)
    except Exception as Error:
        raise RuntimeError(f"Error writing image {OutputImage=}: {Error=}, {type(Error)=}")

    plt.close(Figure)

def FindValidFiles(InputFolder, ChildDirectory=""):
    SearchPath = InputFolder + ChildDirectory  if ChildDirectory else InputFolder
    for Entry in listdir(SearchPath):
        if(Entry[-5:] == ".cbor" and isfile(SearchPath + Entry)):
            if(ChildDirectory):
                ValidFiles.append(ChildDirectory + Entry)
            else:
                ValidFiles.append(Entry)     
        elif(not isfile(SearchPath + Entry)):
            FindValidFiles(InputFolder, ChildDirectory + Entry + "/")


def WriteLog(LogPath, Msg, NewLine = True, CreateFile = False):
    Mode = "a"
    if (CreateFile and isfile(LogPath)):
        Mode = "w"
    elif (CreateFile):
        Mode = "x"

    try:
        if(LogPath.find("/") != -1 or LogPath.find("\\") != -1):
            makedirs(dirname(LogPath), exist_ok=True)

        with open(LogPath, Mode) as LogFile:
            LogFile.write(Msg + "\n" if NewLine else "")
    except Exception as Error:
        raise RuntimeError(f"Error writing log {LogPath=}: {Error=}, {type(Error)=}")

    print(Msg)

def main():
    # Initialize the argument parser and load the description.
    argumentParser = argparse.ArgumentParser(description=CLI_DESCRIPTION)

    # Add the general arguments
    argumentParser.add_argument("-i", "--inputFolderPath", type=str, nargs=1, metavar="InputPath", default=None, required=True, help=CLI_INPUT_FOLDER_PATH_HELP)
    argumentParser.add_argument("-o", "--outputFolderPath", type=str, nargs=1, metavar="OutputPath", default=None, required=True, help=CLI_OUTPUT_FOLDER_PATH_HELP)
    argumentParser.add_argument("-l", "--logPath", type=str, nargs=1, metavar="LogPath", default=None, required=True, help=CLI_LOG_PATH_HELP)
    argumentParser.add_argument("-t", "--triggerPercentage", type=float, nargs=1, metavar="TriggerValue", default=0.1, required=False, help=CLI_TRIGGER_PERCENTAGE_HELP)
    argumentParser.add_argument("-g", "--guardsPercentage", type=float, nargs=1, metavar="GuardsValue", default=0.05, required=False, help=CLI_GUARDS_PERCENTAGE_HELP)
    argumentParser.add_argument("-iw", "--imageWidth", type=int, nargs=1, metavar="WidthValue", default=20, required=False, help=CLI_IMAGE_WIDTH_HELP)
    argumentParser.add_argument("-ih", "--imageHeight", type=int, nargs=1, metavar="HeightValue", default=20, required=False, help=CLI_IMAGE_HEIGHT_HELP)

    # Parse the input arguments.
    args = argumentParser.parse_args()

    print(args)

    InputFolderPath = args.inputFolderPath[0]
    OutputFolderPath = args.outputFolderPath[0]
    LogPath = args.logPath[0]
    TriggerPercentage = args.triggerPercentage[0] if type(args.triggerPercentage) != float else args.triggerPercentage
    GuardsPercentage = args.guardsPercentage[0] if type(args.guardsPercentage) != float else args.guardsPercentage
    FigureWidth = args.imageWidth[0] if type(args.imageWidth) != int else args.imageWidth
    FigureHeight = args.imageHeight[0] if type(args.imageHeight) != int else args.imageHeight

    WriteLog(LogPath, "Starting script", CreateFile=True)

    if (len(InputFolderPath) > 0 and (InputFolderPath[-1] != '/' or InputFolderPath[-1] != '\\')):
        InputFolderPath = InputFolderPath + "/"


    if (len(OutputFolderPath) > 0 and (OutputFolderPath[-1] != '/' or OutputFolderPath[-1] != '\\')):
        OutputFolderPath = OutputFolderPath + "/"

    if(not isdir(InputFolderPath)):
        raise NotADirectoryError(f"Input directory does not exist: {InputFolderPath=}")
    
    if(TriggerPercentage < 0 or TriggerPercentage > 1):
        raise ValueError(f"Trigger percentage is out of bound [0, 1]: {TriggerPercentage=}")
    
    if(GuardsPercentage < 0 or GuardsPercentage > 1):
        raise ValueError(f"Guards percentage is out of bound [0, 1]: {GuardsPercentage=}")
    
    if(FigureWidth <= 0):
        raise ValueError(f"Figure width is out of bound (0, inf): {FigureWidth=}")
    
    if(FigureHeight <= 0):
        raise ValueError(f"Figure height is out of bound (0, inf): {FigureHeight=}")

    WriteLog(LogPath, f"InputFolderPath: {InputFolderPath}")
    WriteLog(LogPath, f"OutputFolderPath: {OutputFolderPath}")
    WriteLog(LogPath, f"LogPath: {LogPath}")
    WriteLog(LogPath, f"TriggerPercentage: {TriggerPercentage}")
    WriteLog(LogPath, f"GuardsPercentage: {GuardsPercentage}")
    WriteLog(LogPath, f"FigureWidth: {FigureWidth}")
    WriteLog(LogPath, f"FigureHeight: {FigureHeight}")

    try:
        FindValidFiles(InputFolderPath)
    except Exception as Error:
        WriteLog(LogPath, f"Unexpected error listing valid files: {Error=}, {type(Error)=}")
    else:
        WriteLog(LogPath, f"Found {len(ValidFiles)=} valid files for cropping.")

    for ValidFile in ValidFiles:
        InputFilePath = InputFolderPath + ValidFile
        OutputFilePath = OutputFolderPath + ValidFile
        OutputImagePath = OutputFilePath[::-1].replace("robc.", "gnp.", 1)[::-1]
        try:
            CropFile(InputFilePath, OutputFilePath, OutputImagePath, TriggerPercentage, GuardsPercentage, FigureHeight, FigureWidth)
        except Exception as Error:
            WriteLog(LogPath, f"Error in file {InputFilePath=}: {Error=}, {type(Error)=}")
        else:
            WriteLog(LogPath, f"Succesfull crop in file {InputFilePath=}")

if __name__ == "__main__":
    try:
        main()
    except Exception as Error:
        print(f"Fatal error: {Error=}, {type(Error)=}")