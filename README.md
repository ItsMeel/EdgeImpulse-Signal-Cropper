# EdgeImpulse-Signal-Cropper
Utility that mass crops time series data from edge impulse in form of .cbor files.

## Requirements:
  - Python.
  - Matplotlib -> Used for generate views of each signal and how is cropped.
  - Numpy -> Used for manipulate data in form of arrays.
  - cbor2 -> Used to parse .cbor file type.

To install these dependencies, write in the terminal `python -m pip install cbor2 numpy matplotlib`

## Usage:

To use the script is very simple, just execute `python EdgeImpulseSignalCropper.py -i InputPath -o OutputPath -l LogPath -t TriggerValue -g GuardsValue` where:
  - InputPath -> Location of the directory with all the input .cbor files.
  - OutputPath -> Location of the directory where all the cropped .cbor files and signal views will be saved.
  - LogPath -> File location of the log.
  - TriggerValue -> Which percentage of the max signal amplitude will be use to trigger the crop.
  - GuardsValue -> How much percentage of the signal will be saved before and after the triggers.

To get help, use the command `python EdgeImpulseSignalCropper.py -h`

## Example:
We have a directory on `E:\InputSignals` and we want to save the output files on `E:\OutputSignals` directory, the log will be on `E:\Log.txt`, we want to start saving signals when it reaches 50% of its peak value and finally we want to preserve 10% extra of the signal before and after the triggers.

The command to use is `python EdgeImpulseSignalCropper.py -i E:\InputSignals -o E:\OutputSignals -l E:\Log.txt -t 0.5 -g 0.1`
