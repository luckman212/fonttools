"""CFF to CFF2 converter."""

from fontTools.ttLib import TTFont
from fontTools.ttLib import TTFont, newTable
from fontTools.misc.cliTools import makeOutputFileName
from fontTools.cffLib import TopDictIndex, buildOrder, topDictOperators
from .width import optimizeWidths
from collections import defaultdict


__all__ = ["convertCFF2ToCFF", "main"]


def convertCFF2ToCFF(cff, otFont):
    """Converts this object from CFF2 format to CFF format. This conversion
    is done 'in-place'. The conversion cannot be reversed.

    The CFF2 font cannot be variable. (TODO Accept those and convert to the
    default instance?)

    This assumes a decompiled CFF table. (i.e. that the object has been
    filled via :meth:`decompile`.)"""

    cff.major = 1
    topDict = cff.topDictIndex[0]
    if hasattr(topDict, "VarStore"):
        raise ValueError("Variable CFF2 font cannot be converted to CFF format.")

    topDictData = TopDictIndex(None, isCFF2=True)
    for item in cff.topDictIndex:
        # Iterate over, such that all are decompiled
        topDictData.append(item)
    cff.topDictIndex = topDictData
    topDict = topDictData[0]
    if hasattr(topDict, "Private"):
        privateDict = topDict.Private
    else:
        privateDict = None
    opOrder = buildOrder(topDictOperators)
    topDict.order = opOrder

    fdArray = topDict.FDArray
    charStrings = topDict.CharStrings

    for cs in charStrings.values():
        cs.program.append("endchar")
    for subrSets in [cff.GlobalSubrs] + [
        getattr(fd.Private, "Subrs", []) for fd in fdArray
    ]:
        for cs in subrSets:
            cs.program.append("return")

    # Add (optimal) width to CharStrings that need it.
    widths = defaultdict(list)
    metrics = otFont["hmtx"].metrics
    for glyphName in charStrings.keys():
        cs, fdIndex = charStrings.getItemAndSelector(glyphName)
        if fdIndex == None:
            fdIndex = 0
        widths[fdIndex].append(metrics[glyphName][0])
    for fdIndex, widthList in widths.items():
        bestDefault, bestNominal = optimizeWidths(widthList)
        private = fdArray[fdIndex].Private
        private.defaultWidthX = bestDefault
        private.nominalWidthX = bestNominal
    for glyphName in charStrings.keys():
        cs, fdIndex = charStrings.getItemAndSelector(glyphName)
        if fdIndex == None:
            fdIndex = 0
        private = fdArray[fdIndex].Private
        width = metrics[glyphName][0]
        if width != private.defaultWidthX:
            cs.program.insert(0, width - private.nominalWidthX)


def main(args=None):
    """Convert CFF OTF font to CFF2 OTF font"""
    if args is None:
        import sys

        args = sys.argv[1:]

    import argparse

    parser = argparse.ArgumentParser(
        "fonttools cffLib.CFFToCFF2",
        description="Upgrade a CFF font to CFF2.",
    )
    parser.add_argument(
        "input", metavar="INPUT.ttf", help="Input OTF file with CFF table."
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT.ttf",
        default=None,
        help="Output instance OTF file (default: INPUT-CFF2.ttf).",
    )
    parser.add_argument(
        "--no-recalc-timestamp",
        dest="recalc_timestamp",
        action="store_false",
        help="Don't set the output font's timestamp to the current time.",
    )
    options = parser.parse_args(args)

    import os

    infile = options.input
    if not os.path.isfile(infile):
        parser.error("No such file '{}'".format(infile))

    outfile = (
        makeOutputFileName(infile, overWrite=True, suffix="-CFF2")
        if not options.output
        else options.output
    )

    font = TTFont(infile)
    cff = font["CFF2"].cff

    cff.convertCFF2ToCFF(font)

    del font["CFF2"]
    table = font["CFF "] = newTable("CFF ")
    table.cff = cff


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1:]))
