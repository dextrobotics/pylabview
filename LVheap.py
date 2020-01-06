# -*- coding: utf-8 -*-

""" LabView RSRC file format heap parsers.

    Heap formats are used for Front Panel and Block Diagram strorage in a RSRC file.
"""

# Copyright (C) 2019 Mefistotelis <mefistotelis@gmail.com>
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.


import enum
import re

from hashlib import md5
from io import BytesIO
from types import SimpleNamespace
from ctypes import *

import LVconnector
import LVmisc
from LVmisc import eprint

class HEAP_FORMAT(enum.Enum):
    """ Heap storage formats
    """
    Unknown = 0
    VersionT = 1
    XMLVer = 2
    BinVerA = 3
    BinVerB = 4
    BinVerC = 5


class NODE_SCOPE(enum.IntEnum):
    """ Heap node scope
    """
    TagOpen = 0 # Opening of a tag
    TagLeaf = 1 # Short tag, opening and closing as single entry
    TagClose = 2 # Closing of a tag


class SL_SYSTEM_TAGS(enum.Enum):
    SL__object = -3
    SL__array = -4
    SL__reference = -5
    SL__arrayElement = -6
    SL__rootObject = -7


class SL_SYSTEM_ATTRIB_TAGS(enum.Enum):
    SL__class = -2
    SL__uid = -3
    SL__stockObj = -4
    SL__elements = -5
    SL__index = -6
    SL__stockSource = -7


class OBJ_FIELD_TAGS(enum.Enum):
    OF__activeDiag = 1
    OF__activeMarker = 2
    OF__activePlot = 3
    OF__activeThumb = 4
    OF__activeXScale = 5
    OF__activeYScale = 6
    OF__alarmName = 7
    OF__bary = 8
    OF__bgColor = 9
    OF__bindings = 10
    OF__blinkList = 11
    OF__borderColor = 12
    OF__botOrRight = 13
    OF__bounds = 14
    OF__buf = 15
    OF__callOffset = 16
    OF__callType = 17
    OF__callee = 18
    OF__caller = 19
    OF__callerGlyphBounds = 20
    OF__caseSelDCO = 21
    OF__cboxDsOffset = 22
    OF__cboxTdOffset = 23
    OF__cbrIcon = 24
    OF__cinPath = 25
    OF__className = 26
    OF__clumpNum = 27
    OF__cnst = 28
    OF__code = 29
    OF__color = 30
    OF__colorDSO = 31
    OF__colorTDO = 32
    OF__cols = 33
    OF__commentMode = 34
    OF__companionDiag = 35
    OF__conId = 36
    OF__conNum = 37
    OF__conPane = 38
    OF__confState = 39
    OF__configNode = 40
    OF__connectorTM = 41
    OF__cons = 42
    OF__tRect = 43
    OF__ctlDataObj = 44
    OF__dBounds = 45
    OF__dIdx = 46
    OF__dataNodeList = 47
    OF__dco = 48
    OF__dcoAgg = 49
    OF__dcoFiller = 50
    OF__dcoList = 51
    OF__ddo = 52
    OF__ddoIndex = 53
    OF__ddoList = 54
    OF__ddoListList = 55
    OF__defaultDiag = 56
    OF__delDCO = 57
    OF__depth = 58
    OF__description = 59
    OF__diagDefined = 60
    OF__diagFiller1 = 61
    OF__diagFiller2 = 62
    OF__diagramList = 63
    OF__docBounds = 64
    OF__dsOffset = 65
    OF__dsw = 66
    OF__dynBounds = 67
    OF__dynLink = 68
    OF__eOracleIdx = 69
    OF__ePtrOff = 70
    OF__eSizeOff = 71
    OF__eltDCO = 72
    OF__embedToken = 73
    OF__errCode = 74
    OF__errIn = 75
    OF__errOfst = 76
    OF__errOut = 77
    OF__eventObj_unused = 78
    OF__fName = 79
    OF__fgColor = 80
    OF__filler = 81
    OF__filterNodeList = 82
    OF__firstNodeIdx = 83
    OF__focusRow = 84
    OF__format = 85
    OF__formula = 86
    OF__frontRow = 87
    OF__funcTD = 88
    OF__graphCursor = 89
    OF__graphType = 90
    OF__growAreaBounds = 91
    OF__growObj = 92
    OF__growTermsList = 93
    OF__growViewObj = 94
    OF__hFlags = 95
    OF__hGrowNodeList = 96
    OF__hSEnd = 97
    OF__hSStart = 98
    OF__headerImage = 99
    OF__hierarchyColor = 100
    OF__histDSOffset = 101
    OF__histTD = 102
    OF__histTDOffset = 103
    OF__hoodBounds = 104
    OF__hotPoint = 105
    OF__howGrow = 106
    OF__i = 107
    OF__iconBounds = 108
    OF__id = 109
    OF__image = 110
    OF__inArrDCO = 111
    OF__inVILib = 112
    OF__index = 113
    OF__indexPosCol = 114
    OF__indexPosRow = 115
    OF__indexing = 116
    OF__innerLpTunDCO = 117
    OF__innerR = 118
    OF__innerSeq = 119
    OF__inplace = 120
    OF__instance = 121
    OF__instanceSelector = 122
    OF__instrStyle = 123
    OF__intermediateList = 124
    OF__invokeFlags = 125
    OF__keyMappingList = 126
    OF__label = 127
    OF__lastSignalKind = 128
    OF__legendLbl = 129
    OF__lenDCO = 130
    OF__lengthDCOList = 131
    OF__level = 132
    OF__libPath = 133
    OF__listFlags = 134
    OF__listboxFlags = 135
    OF__loopEndDCO = 136
    OF__loopIndexDCO = 137
    OF__loopTimingDCO = 138
    OF__lpTunDCO = 139
    OF__lsrDCOList = 140
    OF__mJasterWizard = 141
    OF__mask = 142
    OF__master_unused = 143
    OF__masterPart = 144
    OF__mate = 145
    OF__maxPaneSize = 146
    OF__maxPanelSize = 147
    OF__mclFlags = 148
    OF__menuInstanceUsed = 149
    OF__methCode = 150
    OF__methName = 151
    OF__minPaneSize = 152
    OF__minPanelSize = 153
    OF__nChunks = 154
    OF__nConnections = 155
    OF__nDims = 156
    OF__nInputs = 157
    OF__nLabels = 158
    OF__nMajDivs = 159
    OF__nRC = 160
    OF__nVisItems = 161
    OF__nmxFiller = 162
    OF__nodeInfo = 163
    OF__nodeList = 164
    OF__nodeName = 165
    OF__numFrozenCols = 166
    OF__numFrozenRows = 167
    OF__numRows = 168
    OF__numSubVIs = 169
    OF__oMId = 170
    OF__oRC = 171
    OF__objFlags = 172
    OF__omidDSOffset = 173
    OF__omidTDOffset = 174
    OF__omidTypeDesc = 175
    OF__orderList = 176
    OF__origin = 177
    OF__otherSide = 178
    OF__outerR = 179
    OF__outputDCO = 180
    OF__outputNode = 181
    OF__ownerSignal = 182
    OF__pBounds = 183
    OF__pMap = 184
    OF__pMapOfst = 185
    OF__pageList = 186
    OF__paneFlags = 187
    OF__paneHierarchy = 188
    OF__paramIdx = 189
    OF__paramTableOffset = 190
    OF__parmIndex = 191
    OF__partID = 192
    OF__partOrder = 193
    OF__partsList = 194
    OF__pattern = 195
    OF__pctTransparent = 196
    OF__permDCOList = 197
    OF__permutation = 198
    OF__pixmap = 199
    OF__pos = 200
    OF__preferredInstIndex = 201
    OF__primIndex = 202
    OF__primResID = 203
    OF__priv = 204
    OF__privDataList = 205
    OF__propList = 206
    OF__refList = 207
    OF__resetJumpLabel = 208
    OF__revisionInfoCreator = 209
    OF__revisionInfoTlkitID = 210
    OF__revisionInfoTlkitVersion = 211
    OF__ringDsOffset = 212
    OF__ringTdOffset = 213
    OF__root = 214
    OF__rowHeight = 215
    OF__rsrDCO = 216
    OF__rsrcID = 217
    OF__rtPopupData = 218
    OF__rtPopupString = 219
    OF__rtPopupVersion = 220
    OF__rtdsoff = 221
    OF__savedState = 222
    OF__screenRes = 223
    OF__scriptName = 224
    OF__sdllName = 225
    OF__selLabData = 226
    OF__selString = 227
    OF__selectionColor = 228
    OF__seqLocDCOList = 229
    OF__sequenceList = 230
    OF__shortCount = 231
    OF__signalIndex = 232
    OF__signalList = 233
    OF__simDiagFlags = 234
    OF__simparam = 235
    OF__simtype = 236
    OF__simulationDiag = 237
    OF__sizeRect = 238
    OF__slaveList_unused = 239
    OF__slocFiller = 240
    OF__snFiller = 241
    OF__splitterFlags = 242
    OF__srDCOList = 243
    OF__srcDCO = 244
    OF__stamp = 245
    OF__state = 246
    OF__stateTD = 247
    OF__streamData = 248
    OF__strings = 249
    OF__structColor = 250
    OF__subPanelFlags = 251
    OF__subVIGlyphBounds = 252
    OF__symmetry = 253
    OF__tInset = 254
    OF__tabWidth = 255
    OF__table = 256
    OF__tableFlags = 257
    OF__tagDevice = 258
    OF__tagDisplayFilter = 259
    OF__tagSubTypeClass = 260
    OF__tagType = 261
    OF__tagTypeClass = 262
    OF__tblOffset = 263
    OF__tdOffset = 264
    OF__termBMPs = 265
    OF__termBounds = 266
    OF__termHotPoint = 267
    OF__termList = 268
    OF__textDivider = 269
    OF__textRec = 270
    OF__threadInfo = 271
    OF__timeDataNodeDMux = 272
    OF__timeDataNodeMux = 273
    OF__timeLoop = 274
    OF__timeOutDCO = 275
    OF__tool = 276
    OF__topOrLeft = 277
    OF__treeFlags = 278
    OF__tsH = 279
    OF__tunnelList = 280
    OF__type = 281
    OF__typeCode = 282
    OF__typeDesc = 283
    OF__userDiagram = 284
    OF__vTblPtr = 285
    OF__varTypeDesc = 286
    OF__vblName = 287
    OF__version = 288
    OF__viPath = 289
    OF__viState = 290
    OF__visClust = 291
    OF__width = 292
    OF__winFlags = 293
    OF__wireGlyphID = 294
    OF__wireID = 295
    OF__wireTable = 296
    OF__wizData = 297
    OF__wizDataH = 298
    OF__wizDataID = 299
    OF__wizID = 300
    OF__wizVersion = 301
    OF__xflags = 302
    OF__zPlaneList = 303
    OF__zPlaneListList = 304
    OF__zoom = 305
    OF__srcDCO1 = 306
    OF__srcDCO2 = 307
    OF__srcDCO3 = 308
    OF__srcDCO4 = 309
    OF__cRectAbove = 310
    OF__cRectBelow = 311
    OF__variantIndex = 312
    OF__termListLength = 313
    OF__refListLength = 314
    OF__hGrowNodeListLength = 315
    OF__dataTypeDesc = 316
    OF__hair = 317
    OF__displayName = 318
    OF__selLabFlags = 319
    OF__lastSelRow = 320
    OF__lastSelCol = 321
    OF__scrollPosV = 322
    OF__scrollPosH = 323
    OF__totalBounds = 324
    OF__srcRect = 325
    OF__labelPosRow = 326
    OF__labelPosCol = 327
    OF__simparamOut = 328
    OF__innerMate = 329
    OF__outerMate = 330
    OF__flatSeq = 331
    OF__timeSeq = 332
    OF__slaveMods = 333
    OF__slaveOwner = 334
    OF__simConfigNode = 335
    OF__simOutputNode = 336
    OF__glyphs = 337
    OF__pUseStoredSize = 338
    OF__pUseStoredPos = 339
    OF__pRuntimeType = 340
    OF__pRuntimeTop = 341
    OF__pRuntimeLeft = 342
    OF__pRuntimeWidth = 343
    OF__pRuntimeHeight = 344
    OF__pRuntimeMonitor = 345
    OF__libVersion = 346
    OF__ratio = 347
    OF__annexDDOFlag = 348
    OF__xCtlState = 349
    OF__wizList = 350
    OF__lockedObjectList = 351
    OF__lockedSignalList = 352
    OF__masterStateEnum = 353
    OF___Quit_StateEnum = 354
    OF__stopCodeEnum = 355
    OF__stateLoop = 356
    OF__stateCase = 357
    OF__stateCaseOutputTunnel = 358
    OF__stateList = 359
    OF__isSubVICall = 360
    OF__name = 361
    OF__transitionEnum = 362
    OF__transitionCase = 363
    OF__transCaseOutputTunnel = 364
    OF__transitionList = 365
    OF__stateBounds = 366
    OF__terminal = 367
    OF__stateConst = 368
    OF__exitAngle = 369
    OF__entranceAngle = 370
    OF__stiffness = 371
    OF__labelPos = 372
    OF__pinCorner = 373
    OF__currentlyScripting = 374
    OF__textNodeLabel = 375
    OF__heapFlags = 376
    OF__refreshFilter = 377
    OF__plugInData = 378
    OF__xTunDDO = 379
    OF__gridFlags = 380
    OF__headerFiles = 381
    OF__sceneView = 382
    OF__lastAutoScale = 383
    OF__autoScaleDelay = 384
    OF__reserveCB = 385
    OF__unreserveCB = 386
    OF__abortCB = 387
    OF__paramInfo = 388
    OF__extFuncFlags = 389
    OF__tMI = 390
    OF__lineNumbers = 391
    OF__fPath = 392
    OF__mDate = 393
    OF__errHandle = 394
    OF__xTunnelDir = 395
    OF__sCFlag = 396
    OF__sCStNGuid = 397
    OF__sCDiagSubType = 398
    OF__sCDiagFlag = 399
    OF__isLoopCaseTransition = 400
    OF__selectorXNode = 401
    OF__iFeedbackLoop = 402
    OF__cellPosRow = 403
    OF__cellPosCol = 404
    OF__font = 405
    OF__mode = 406
    OF__height = 407
    OF__glyphIndex = 408
    OF__flags = 409
    OF__attributeList = 410
    OF__qtWidget = 411
    OF__fLoopCondTerm = 412
    OF__isInterface = 413
    OF__loopLimitDCO = 414
    OF__loopTestDCO = 415
    OF__overrideType = 416
    OF__maxWordLength = 417
    OF__override = 418
    OF__overflow = 419
    OF__quantize = 420
    OF__tunOrdList = 421
    OF__sceneGLContext = 422
    OF__poserList = 423
    OF__decomposer = 424
    OF__recomposer = 425
    OF__arrayDCO = 426
    OF__variantDCO = 427
    OF__valueDCO = 428
    OF__typeDCO = 429
    OF__inputDataDCO = 430
    OF__outputDataDCO = 431
    OF__poser = 432
    OF__dataValRefDCO = 433
    OF__write = 434
    OF__showTimestamp = 435
    OF__name4 = 436
    OF__privDataDSO = 437
    OF__privDataTMI = 438
    OF__disabledList = 439
    OF__multiSegPipeFlange1Size = 422
    OF__multiSegPipeFlange2Size = 423
    OF__multiSegPipeFlange1Depth = 424
    OF__multiSegPipeFlange2Depth = 425
    OF__multiSegPipeWidth = 426
    OF__staticState = 427
    OF__funcName = 428
    OF__mFilePath = 429
    OF__tagDLLPath = 430
    OF__recursiveFunc = 430
    OF__tagDLLName = 431
    OF__tunnelLink = 451
    OF__activeBus = 452
    OF__terminal_ID = 453
    OF__implementingNode = 454
    OF__fboxlineList = 455
    OF__compressedWireTable = 456
    OF__sharedCloneAllocationFlags = 457
    OF__initOrderIndex = 458
    OF__ringSparseValues = 459
    OF__ringDisabledIndicies = 460
    OF__scrollbarMin = 461
    OF__scrollbarMax = 462
    OF__scrollbarInc = 463
    OF__scrollbarVis = 464
    OF__browseOptions = 465
    OF__decomposeArraySplitNodeSplitDimension = 466
    OF__rowHeaders = 467
    OF__columnHeaders = 468
    OF__activeCell = 469
    OF__scaleDMin = 470
    OF__scaleDMax = 471
    OF__scaleDStart = 472
    OF__scaleDIncr = 473
    OF__scaleDMinInc = 474
    OF__scaleDMultiplier = 475
    OF__scaleDOffset = 476
    OF__scaleRRef = 477
    OF__scaleRngf = 478
    OF__scaleCenter = 479
    OF__scaleRadius = 480
    OF__scaleRMin = 481
    OF__scaleRMax = 482
    OF__scaleFunIdx = 483
    OF__scaleLoColor = 484
    OF__scaleHiColor = 485
    OF__scaleColorData = 486
    OF__minDataSel = 487
    OF__maxDataSel = 488
    OF__pivotDataSel = 489
    OF__absTime_min = 490
    OF__absTime_max = 491
    OF__absTime_inc = 492
    OF__baseListboxItemStrings = 493
    OF__baseListboxDoubleClickedRow = 494
    OF__baseListboxClickedColumnHeader = 495
    OF__baseListboxDragRow = 496
    OF__listboxClickedCell = 497
    OF__listboxDisabledItems = 498
    OF__listboxGlyphColumns = 499
    OF__treeNodeArray = 500
    OF__treeDragIntoRow = 501
    OF__arrayIndices = 502
    OF__arraySelectionStart = 503
    OF__arraySelectionEnd = 504
    OF__comboBoxIndex = 505
    OF__comboBoxValues = 506
    OF__tabArrayFirstTab = 507
    OF__tabArrayFg = 508
    OF__tabArrayBg = 509
    OF__tabArrayTabInfoArray = 510
    OF__tabControlPageSelValue = 511
    OF__tabControlPageInfoArray = 512
    OF__StdNumMin = 513
    OF__StdNumMax = 514
    OF__StdNumInc = 515
    OF__CBRExecAlias = 516
    OF__CBRExecResolved = 517
    OF__CBRRefPathAlias = 518
    OF__CBRRefPath = 519
    OF__CBRCfgMode = 520
    OF__commentSelInfoArray = 521
    OF__commentSelLabData = 522
    OF__GVNGrowTerms = 523
    OF__GVNMaxGrowTerms = 524
    OF__GVMinGVWidth = 525
    OF__GVHoodTermWidth = 526
    OF__GVGrowTermsInfo = 527
    OF__PlugInDLLName = 528
    OF__PlugInLoadProcName = 529
    OF__PropItemName = 530
    OF__PropItemCode = 531
    OF__ActiveXItemDataSize = 532
    OF__ActiveXItemObjMgrFlags = 533
    OF__ActiveXItemOrigVarType = 534
    OF__ActiveXItemOrigIndex = 535
    OF__DotNetItemDataSize = 536
    OF__DotNetItemObjMgrFlags = 537
    OF__DotNetItemDotNetFlags = 538
    OF__DotNetItemType = 539
    OF__SharedVariableCustomRule = 540
    OF__GraphMPlot = 541
    OF__GraphActivePlot = 542
    OF__GraphActiveCursor = 543
    OF__GraphCursors = 544
    OF__GraphFlags = 545
    OF__GraphTreeData = 546
    OF__GraphPlotImages = 547
    OF__GraphAnnotations = 548
    OF__GraphActivePort = 549
    OF__GraphCursorButtons = 550
    OF__GraphCursorLegendData = 551
    OF__GraphPlotLegendData = 552
    OF__GraphMinPlotNum = 553
    OF__GraphBusOrg = 554
    OF__GraphScalePalette = 555
    OF__GraphScaleData = 556
    OF__IntensityGraphCT = 557
    OF__IntensityGraphBMP = 558
    OF__IntensityGraphBounds = 559
    OF__SimDiagFeedThroughData = 560
    OF__SimDiagSimNodeMapData = 561
    OF__SimDiagCompNodeMapData = 562
    OF__SimDiagSignalMapData = 563
    OF__SimDiagAdditionalData = 564
    OF__SelectDefaultCase = 565
    OF__SelectNRightType = 566
    OF__SelectRangeArray32 = 567
    OF__SelectRangeArray64 = 568
    OF__SelectStringArray = 569
    OF__EventNodeEvents = 570
    OF__DefaultData = 571
    OF__ParForWorkers = 572
    OF__ParForIndexDistribution = 573
    OF__StateData = 574
    OF__MinButSize = 575
    OF__possibleMSNDCOTypes = 576
    OF__feedbackNodeDelay = 577
    OF__englishName = 578
    OF__SharedVariableDynamicResID = 579
    OF__ParForNumStaticWorkers = 580
    OF__OMRCFlags = 581
    OF__SimDiagSimParamData = 582
    OF__SelectSelLabFlags = 583
    OF__SelectSelLabData = 584
    OF__CommentSelLabFlags = 585
    OF__CommentSelLabData = 586
    OF__UDClassItemDataSize = 587
    OF__UDClassItemPropName = 588
    OF__ConstValue = 589
    OF__EventNodeOccurrence = 590
    OF__EventSelLabFlags = 591
    OF__EventSelLabData = 592
    OF__ChunkSize = 593
    OF__DebuggingEnabled = 594
    OF__SlaveFBInputNode = 595
    OF__HiddenFBNode = 596
    OF__InnerChunkSize = 597
    OF__savedSize = 598
    OF__nodeFlags2 = 599
    OF__OutputInstanceNumberFromP = 600
    OF__CBRSaveStyle = 601
    OF__JoinCBRTimeout = 602
    OF__OffScreenSceneView = 603
    OF__OffScreenGLContext = 604
    OF__scaleRMin32 = 605
    OF__scaleRMax32 = 606
    OF__TunnelType = 607
    OF__DefaultTunnelType = 608
    OF__FpgaImplementation = 609
    OF__IsConditional = 610
    OF__ConditionDCOList = 611
    OF__LpTunConditionDCO = 612
    OF__MSNFlags = 613
    OF__arrayOfStringsIsCellArray = 614
    OF__MouseWheelSupport = 615
    OF__GraphMPlot2013 = 616
    OF__GraphBusOrg2013 = 617
    OF__attachedObject = 618
    OF__attachment = 619
    OF__ScaleAutoscalePadding = 620
    OF__ThralledTunnelUID = 621
    OF__GraphCursors2014 = 622
    OF__GraphAnnotations2014 = 623
    OF__kSLHDefaultValueMatchesCtlVI = 624
    OF__kSLHFieldDefaultValueMatchesCtlVI = 625
    OF__FpgaEnableBoundsMux = 626


class HeapNode(object):
    def __init__(self, vi, po, parentNode, tagId, scopeInfo):
        """ Creates new Section object, represention one of possible contents of a Block.

        Support of a section is mostly implemented in Block, so there isn't much here.
        """
        self.vi = vi
        self.po = po
        self.properties = []
        self.data = None
        self.parent = parentNode
        self.tagId = tagId
        self.scopeInfo = scopeInfo
        self.childs = []
        self.raw_data = None
        # Whether RAW data has been updated and RSRC parsing is required to update properties
        self.raw_data_updated = False
        # Whether any properties have been updated and preparation of new RAW data is required
        self.parsed_data_updated = False

    def getScopeInfo(self):
        if self.scopeInfo not in set(item.value for item in NODE_SCOPE):
            return self.scopeInfo
        return NODE_SCOPE(self.scopeInfo)

    def parseRSRCData(self, bldata, hasAttrList, sizeSpec):
        attribs = []
        if hasAttrList != 0:
            count = LVmisc.readVariableSizeFieldU124(bldata)

            if (self.po.verbose > 2):
                print("{:s}: Heap Container start id=0x{:02X} scopeInfo={:d} sizeSpec={:d} attrCount={:d}"\
                  .format(self.vi.src_fname, self.tagId, self.scopeInfo, sizeSpec, count))
            attribs = [SimpleNamespace() for _ in range(count)]
            for attr in attribs:
                attr.atType = LVmisc.readVariableSizeFieldS124(bldata)
                attr.atVal = LVmisc.readVariableSizeFieldS24(bldata)
        else:
            if (self.po.verbose > 2):
                print("{:s}: Heap Container id=0x{:02X} scopeInfo={:d} sizeSpec={:d} noAttr"\
                  .format(self.vi.src_fname, self.tagId, self.scopeInfo, sizeSpec))

        # Read size of data, unless sizeSpec identifies the size completely
        dataSize = 0;
        if sizeSpec == 0 or sizeSpec == 7: # bool data
            dataSize = 0
        elif sizeSpec <= 4:
            dataSize = sizeSpec
        elif sizeSpec == 6:
            dataSize = LVmisc.readVariableSizeFieldU124(bldata)
        else:
            dataSize = 0
            eprint("{:s}: Warning: Unexpected value of SizeSpec={:d} on heap"\
              .format(self.vi.src_fname, sizeSpec))

        data = None
        if dataSize > 0:
            data = bldata.read(dataSize)
        elif sizeSpec == 0:
            data = False
        elif sizeSpec == 7:
            data = True

        self.properties = attribs
        self.data = data

    def getData(self):
        bldata = BytesIO(self.raw_data)
        return bldata

    def setData(self, data_buf, incomplete=False):
        self.raw_data = data_buf
        self.size = len(self.raw_data)
        if not incomplete:
            self.raw_data_updated = True

    def updateData(self, avoid_recompute=False):

        if avoid_recompute and self.raw_data_updated:
            return # If we have strong raw data, and new one will be weak, then leave the strong buffer

        data_buf = b''

        hasAttrList = 1 if len(self.properties) > 0 else 0

        if hasAttrList != 0:
            data_buf += LVmisc.prepareVariableSizeFieldU124(len(self.properties))
            for attr in self.properties:
                data_buf += LVmisc.prepareVariableSizeFieldS124(attr.atType)
                data_buf += LVmisc.prepareVariableSizeFieldS24(attr.atVal)

        if self.data is None:
            sizeSpec = 0
        elif isinstance(self.data, bool):
            if self.data == True:
                sizeSpec = 7
            else:
                sizeSpec = 0
        elif isinstance(self.data, bytes):
            if len(self.data) <= 4:
                sizeSpec = len(self.data)
            else:
                sizeSpec = 6
        else:
            eprint("{:s}: Warning: Unexpected type of data on heap"\
              .format(self.vi.src_fname))

        if sizeSpec == 6:
            data_buf += LVmisc.prepareVariableSizeFieldU124(len(self.data))

        if sizeSpec in [1,2,3,4,6]:
            data_buf += self.data

        if (self.po.verbose > 2):
            print("{:s}: Heap Container id=0x{:02X} scopeInfo={:d} sizeSpec={:d} attrCount={:d}"\
              .format(self.vi.src_fname, self.tagId, self.scopeInfo, sizeSpec, len(self.properties)))

        if (self.tagId + 31) < 1023:
            rawTagId = self.tagId + 31
        else:
            rawTagId = 1023

        data_head = bytearray(2)
        data_head[0] = ((sizeSpec & 7) << 5) | ((hasAttrList & 1) << 4) | ((self.scopeInfo & 3) << 2) | ((rawTagId >> 8) & 3)
        data_head[1] = (rawTagId & 0xFF)
        if rawTagId == 1023:
            data_head += int(self.tagId).to_bytes(4, byteorder='big', signed=True)

        self.setData(data_head+data_buf, incomplete=avoid_recompute)

    def initWithXML(self, elem):
        attribs = []
        for name, value in elem.attrib.items():
            attr = SimpleNamespace()

            if name in ["ScopeInfo"]: # TODO compute scopeInfo instead of reading XML
                scopeInfo = int(value, 0)
                if self.scopeInfo != scopeInfo:
                    eprint("{:s}: Warning: Tag '{}' 0x{:04X} automatic scopeInfo={:d} bad, replaced by {:d}"\
                      .format(self.vi.src_fname, tagIdToName(self.tagId), self.tagId, self.scopeInfo, scopeInfo))
                    self.scopeInfo = scopeInfo
                continue
            elif "SL__"+name in SL_SYSTEM_ATTRIB_TAGS.__members__:
                propId = SL_SYSTEM_ATTRIB_TAGS["SL__"+name].value
            else:
                nameParse = re.match("^Prop([0-9A-F]{4,8})$", name)
                if nameParse is not None:
                    propId = int(nameParse[1], 16)
                else:
                    raise AttributeError("Unrecognized attrib in heap XML, '{}'".format(name))
            attr.atType = propId
            attr.atVal = int(value, 0)
            attribs.append(attr)
        self.properties = attribs

        data = None
        if elem.text is not None:
            tagData = elem.text.strip()
            if tagData == "":
                pass # no data
            elif tagData in ["True", "False"]:
                data = (tagData == "True")
            else:
                data = bytes.fromhex(tagData)
        self.data = data
        pass


def getFrontPanelHeapIdent(hfmt):
    """ Gives 4-byte heap identifier from HEAP_FORMAT member
    """
    heap_ident = {
        HEAP_FORMAT.VersionT: b'FPHT',
        HEAP_FORMAT.XMLVer: b'FPHX',
        HEAP_FORMAT.BinVerA: b'FPHB',
        HEAP_FORMAT.BinVerB: b'FPHb',
        HEAP_FORMAT.BinVerC: b'FPHc',
    }.get(hfmt, b'')
    return heap_ident


def recognizePanelHeapFmtFromIdent(heap_ident):
    """ Gives FILE_FMT_TYPE member from given 4-byte file identifier
    """
    heap_id = bytes(heap_ident)
    for hfmt in HEAP_FORMAT:
        curr_heap_id = getFrontPanelHeapIdent(hfmt)
        if len(curr_heap_id) > 0 and (curr_heap_id == heap_id):
            return hfmt
    return HEAP_FORMAT.Unknown

def tagIdToName(tagId):
    if tagId in set(itm.value for itm in SL_SYSTEM_TAGS):
        tagName = SL_SYSTEM_TAGS(tagId).name
    elif tagId in set(itm.value for itm in OBJ_FIELD_TAGS):
        tagName = OBJ_FIELD_TAGS(tagId).name[4:]
    else:
        tagName = 'Tag{:04X}'.format(tagId)
    return tagName

def tagNameToId(tagName):
    if tagName in SL_SYSTEM_TAGS.__members__:
        tagId = SL_SYSTEM_TAGS[tagName].value
    elif "OF__"+tagName in OBJ_FIELD_TAGS.__members__:
        tagId = OBJ_FIELD_TAGS["OF__"+tagName].value
    else:
        tagParse = re.match("^Tag([0-9A-F]{4,8})$", tagName)
        if tagParse is not None:
            tagId = int(tagParse[1], 16)
        else:
            tagId = None
    return tagId

def createObjectNode(vi, po, tagId, scopeInfo):
    """ create new Heap Node

    Acts as a factory which selects object class based on tagId.
    """
    if isinstance(tagId, str):
        tagName = tagId
        tagId = tagNameToId(tagName)
        if tagId is None:
            raise AttributeError("Unrecognized tag in heap XML, '{}'".format(tagName))
    obj = HeapNode(vi, po, None, tagId, scopeInfo)
    return obj

def addObjectNodeToTree(section, parentIdx, objectIdx):
    """ put object node into tree struct
    """
    obj = section.objects[objectIdx]
    # Add node to parent
    if parentIdx > 0:
        parent = section.objects[parentIdx]
        parent.childs.append(objectIdx)
    else:
        parent = None
    obj.parent = parent
