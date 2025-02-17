############################################################
# define basic process
############################################################

import FWCore.ParameterSet.Config as cms
import FWCore.Utilities.FileUtils as FileUtils
import FWCore.ParameterSet.VarParsing as VarParsing
import os

############################################################
# edit options here
############################################################
L1TRK_INST ="MyL1TrackJets" ### if not in input DIGRAW then we make them in the above step
process = cms.Process(L1TRK_INST)

#L1TRKALGO = 'HYBRID'  #baseline, 4par fit
#L1TRKALGO = 'HYBRID_DISPLACED'  #extended, 5par fit
L1TRKALGO = 'HYBRID_PROMPTANDDISP'

DISPLACED = ''


runVtxNN = True
############################################################
# import standard configurations
############################################################

process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.EventContent.EventContent_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.Geometry.GeometryExtendedRun4D110Reco_cff')
process.load('Configuration.Geometry.GeometryExtendedRun4D110_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')

from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, 'auto:phase2_realistic', '')

process.load("FWCore.MessageLogger.MessageLogger_cfi")
process.MessageLogger.cerr.INFO.limit = cms.untracked.int32(0) # default: 0

############################################################
# input and output
############################################################

options = VarParsing.VarParsing ('analysis')
options.parseArguments()

inputFiles = []
for filePath in options.inputFiles:
    if filePath.endswith(".root"):
        inputFiles.append(filePath)
    else:
        inputFiles += FileUtils.loadListFromFile(filePath)

process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(-1))

readFiles = cms.untracked.vstring(inputFiles)
# readFiles = cms.untracked.vstring('/store/mc/Phase2Spring24DIGIRECOMiniAOD/TT_TuneCP5_14TeV-powheg-pythia8/GEN-SIM-DIGI-RAW-MINIAOD/PU200_Trk1GeV_140X_mcRun4_realistic_v4-v2/130000/00c7f40e-b44e-4eea-a86b-def8f7d82b0e.root')
secFiles = cms.untracked.vstring()

process.source = cms.Source ("PoolSource",
                            fileNames = readFiles,
                            secondaryFileNames = secFiles,
                            duplicateCheckMode = cms.untracked.string('noDuplicateCheck'),
                            )

process.source.inputCommands = cms.untracked.vstring("keep *","drop l1tTkPrimaryVertexs_L1TkPrimaryVertex__*")
process.Timing = cms.Service("Timing",
  summaryOnly = cms.untracked.bool(True),
  useJobReport = cms.untracked.bool(False)
)

process.TFileService = cms.Service("TFileService", fileName = cms.string(f'/mercury/data3/linacre/linacre-l1t/output_1420pre4/GTTObjects_{options.outputFile}'), closeFileFast = cms.untracked.bool(True))
# process.TFileService = cms.Service("TFileService", fileName = cms.string('GTTObjects_ttbar200PU_Spring23.root'), closeFileFast = cms.untracked.bool(True))


############################################################
# L1 tracking: remake stubs?
############################################################

process.load('L1Trigger.TrackTrigger.TrackTrigger_cff')
from L1Trigger.TrackTrigger.TTStubAlgorithmRegister_cfi import *
process.load("SimTracker.TrackTriggerAssociation.TrackTriggerAssociator_cff")

from SimTracker.TrackTriggerAssociation.TTClusterAssociation_cfi import *
TTClusterAssociatorFromPixelDigis.digiSimLinks = cms.InputTag("simSiPixelDigis","Tracker")

process.TTClusterStub = cms.Path(process.TrackTriggerClustersStubs)
process.TTClusterStubTruth = cms.Path(process.TrackTriggerAssociatorClustersStubs)


# DTC emulation
process.load('L1Trigger.TrackerDTC.ProducerED_cff')
process.dtc = cms.Path(process.TrackerDTCProducer)

process.load("L1Trigger.TrackFindingTracklet.L1HybridEmulationTracks_cff")
process.load("L1Trigger.L1TTrackMatch.l1tTrackSelectionProducer_cfi")
process.load("L1Trigger.L1TTrackMatch.l1tTrackVertexAssociationProducer_cfi")
process.load("L1Trigger.L1TTrackMatch.l1tTrackJets_cfi")
process.load("L1Trigger.L1TTrackMatch.l1tGTTInputProducer_cfi")
process.load("L1Trigger.L1TTrackMatch.l1tTrackJetsEmulation_cfi")
process.load("L1Trigger.L1TTrackMatch.l1tTrackFastJets_cfi")
process.load("L1Trigger.L1TTrackMatch.l1tTrackerEtMiss_cfi")
process.load("L1Trigger.L1TTrackMatch.l1tTrackerEmuEtMiss_cfi")
process.load("L1Trigger.L1TTrackMatch.l1tTrackerHTMiss_cfi")
process.load("L1Trigger.L1TTrackMatch.l1tTrackerEmuHTMiss_cfi")
process.load("L1Trigger.L1TTrackMatch.l1tTrackTripletEmulation_cfi")
process.load('L1Trigger.VertexFinder.l1tVertexProducer_cfi')
 


############################################################
# Primary vertex
############################################################
process.pPV = cms.Path(process.l1tVertexFinder)


if runVtxNN:
    process.l1tVertexFinderEmulator = process.l1tVertexProducer.clone()
    process.l1tVertexFinderEmulator.VertexReconstruction.Algorithm = "NNEmulation"
    # Note: these cuts don't actually change the selected tracks wrt the ones in the nominal l1tTrackSelectionProducer because of the extra comma ...
    process.l1tTrackSelectionProducer.cutSet = cms.PSet(ptMin = cms.double(2.0), # pt must be greater than this value, [GeV]
                                                        absEtaMax = cms.double(2.4), # absolute value of eta must be less than this value
                                                        absZ0Max = cms.double(15.0), # z0 must be less than this value, [cm]
                                                        nStubsMin = cms.int32(4), # number of stubs must be greater than or equal to this value
                                                        nPSStubsMin = cms.int32(0), # the number of stubs in the PS Modules must be greater than or equal to this value
                                                        promptMVAMin = cms.double(-1.0), # MVA must be greater than this value
                                                        reducedBendChi2Max = cms.double(999.0), # bend chi2 must be less than this value
                                                        reducedChi2RZMax = cms.double(999.0), # chi2rz/dof must be less than this value
                                                        reducedChi2RPhiMax = cms.double(999.0), # chi2rphi/dof must be less than this value
                                                        reducedChi2MaxNstub4 = cms.double(999.9), # chi2/dof with nstub==4 must be less than this value
                                                        reducedChi2MaxNstub5 = cms.double(999.9), # chi2/dof with nstub>4 must be less than this value
                                                        reducedBendChi2MaxNstub4 = cms.double(999.9), # bend chi2 with nstub==4 must be less than this value
                                                        reducedBendChi2MaxNstub5 = cms.double(999.9), # bend chi2 with nstub>4 must be less than this value
                                                        ),
    VertexAssociator = process.l1tTrackVertexNNAssociationProducer
    AssociationName = "l1tTrackVertexNNAssociationProducer"
else:
    VertexAssociator = process.l1tTrackVertexAssociationProducer
    AssociationName = "l1tTrackVertexAssociationProducer"
# TODO: use NN association emulation also for downstream quantities like l1tTrackVertexAssociationProducerForEtMiss. Currently, TrackMET emulation uses the NN emulated vertex but the nominal track-vertex association.
process.pPVemu = cms.Path(process.l1tVertexFinderEmulator)

# HYBRID: prompt tracking
if (L1TRKALGO == 'HYBRID'):
    process.TTTracksEmu = cms.Path(process.L1THybridTracks)
    process.TTTracksEmuWithTruth = cms.Path(process.L1THybridTracksWithAssociators)
    process.pL1TrackSelection = cms.Path(process.l1tTrackSelectionProducer *
                                         process.l1tTrackSelectionProducerForJets *
                                         process.l1tTrackSelectionProducerForEtMiss)
    process.pL1TrackVertexAssociation = cms.Path(VertexAssociator *
                                                 process.l1tTrackVertexAssociationProducerForJets*
                                                 process.l1tTrackVertexAssociationProducerForEtMiss)
    process.pL1TrackJets = cms.Path(process.l1tTrackJets)
    process.pL1TrackFastJets=cms.Path(process.l1tTrackFastJets)
    process.pL1GTTInput = cms.Path(process.l1tGTTInputProducer)
    process.pL1TrackJetsEmu = cms.Path(process.l1tTrackJetsEmulation)
    process.pTkMET = cms.Path(process.l1tTrackerEtMiss)
    process.pTkMETEmu = cms.Path(process.l1tTrackerEmuEtMiss)
    process.pTkMHT = cms.Path(process.l1tTrackerHTMiss)
    process.pTkMHTEmulator = cms.Path(process.l1tTrackerEmuHTMiss)
    process.pL1TrackTripletEmulator = cms.Path(process.l1tTrackTripletEmulation)
    DISPLACED = 'Prompt'

# HYBRID: extended tracking
elif (L1TRKALGO == 'HYBRID_DISPLACED'):
    process.TTTracksEmu = cms.Path(process.L1TExtendedHybridTracks)
    process.TTTracksEmuWithTruth = cms.Path(process.L1TExtendedHybridTracksWithAssociators)
    process.pL1TrackSelection = cms.Path(process.l1tTrackSelectionProducer *
                                         process.l1tTrackSelectionProducerExtended *
                                         process.l1tTrackSelectionProducerExtendedForJets *
                                         process.l1tTrackSelectionProducerExtendedForEtMiss)
    process.pL1TrackVertexAssociation = cms.Path(process.l1tTrackVertexAssociationProducerExtended *
                                                 process.l1tTrackVertexAssociationProducerExtendedForJets *
                                                 process.l1tTrackVertexAssociationProducerExtendedForEtMiss)
    process.pL1TrackJets = cms.Path(process.l1tTrackJetsExtended)
    process.pL1TrackFastJets = cms.Path(process.l1tTrackFastJetsExtended)
    process.pL1GTTInput = cms.Path(process.l1tGTTInputProducerExtended)
    process.pL1TrackJetsEmu = cms.Path(process.l1tTrackJetsExtendedEmulation)
    process.pTkMET = cms.Path(process.l1tTrackerEtMissExtended)
    process.pTkMHT = cms.Path(process.l1tTrackerHTMissExtended)
    process.pTkMHTEmulator = cms.Path(process.l1tTrackerEmuHTMissExtended)
    DISPLACED = 'Displaced'#

# HYBRID: extended tracking
elif (L1TRKALGO == 'HYBRID_PROMPTANDDISP'):
    process.TTTracksEmu = cms.Path(process.L1TPromptExtendedHybridTracks)
    process.TTTracksEmuWithTruth = cms.Path(process.L1TPromptExtendedHybridTracksWithAssociators)
    process.pL1TrackSelection = cms.Path(process.l1tTrackSelectionProducer * process.l1tTrackSelectionProducerExtended *
                                         process.l1tTrackSelectionProducerForJets * process.l1tTrackSelectionProducerExtendedForJets *
                                         process.l1tTrackSelectionProducerForEtMiss * process.l1tTrackSelectionProducerExtendedForEtMiss)
    process.pL1TrackVertexAssociation = cms.Path(VertexAssociator * process.l1tTrackVertexAssociationProducerExtended *
                                                 process.l1tTrackVertexAssociationProducerForJets * process.l1tTrackVertexAssociationProducerExtendedForJets *
                                                 process.l1tTrackVertexAssociationProducerForEtMiss * process.l1tTrackVertexAssociationProducerExtendedForEtMiss)
    process.pL1TrackJets = cms.Path(process.l1tTrackJets*process.l1tTrackJetsExtended)
    process.pL1TrackFastJets = cms.Path(process.l1tTrackFastJets*process.l1tTrackFastJetsExtended)
    process.pL1GTTInput = cms.Path(process.l1tGTTInputProducer*process.l1tGTTInputProducerExtended)
    process.pL1TrackJetsEmu = cms.Path(process.l1tTrackJetsEmulation*process.l1tTrackJetsExtendedEmulation)
    process.pTkMET = cms.Path(process.l1tTrackerEtMiss*process.l1tTrackerEtMissExtended)
    process.pTkMETEmu = cms.Path(process.l1tTrackerEmuEtMiss)
    process.pTkMHT = cms.Path(process.l1tTrackerHTMiss*process.l1tTrackerHTMissExtended)
    process.pTkMHTEmulator = cms.Path(process.l1tTrackerEmuHTMiss*process.l1tTrackerEmuHTMissExtended)
    process.pL1TrackTripletEmulator = cms.Path(process.l1tTrackTripletEmulation)
    DISPLACED = 'Both'




############################################################
# Define the track ntuple process, MyProcess is the (unsigned) PDGID corresponding to the process which is run
# e.g. single electron/positron = 11
#      single pion+/pion- = 211
#      single muon+/muon- = 13
#      pions in jets = 6
#      taus = 15
#      all TPs = 1
############################################################

process.L1TrackNtuple = cms.EDAnalyzer('L1TrackObjectNtupleMaker',
        MyProcess = cms.int32(1),
        DebugMode = cms.bool(False),      # printout lots of debug statements
        SaveAllTracks = cms.bool(True),  # save *all* L1 tracks, not just truth matched to primary particle
        SaveStubs = cms.bool(False),      # save some info for *all* stubs
        Displaced = cms.string(DISPLACED),# "Prompt", "Displaced", "Both"
        L1Tk_minNStub = cms.int32(4),     # L1 tracks with >= 4 stubs
        TP_minNStub = cms.int32(4),       # require TP to have >= X number of stubs associated with it
        TP_minNStubLayer = cms.int32(4),  # require TP to have stubs in >= X layers/disks
        TP_minPt = cms.double(2.0),       # only save TPs with pt > X GeV
        TP_maxEta = cms.double(2.5),      # only save TPs with |eta| < X
        TP_maxZ0 = cms.double(15.0),      # only save TPs with |z0| < X cm
        L1TrackInputTag = cms.InputTag("l1tTTTracksFromTrackletEmulation", "Level1TTTracks"),                                                      # TTTracks, prompt
        L1TrackExtendedInputTag = cms.InputTag("l1tTTTracksFromExtendedTrackletEmulation", "Level1TTTracks"),                                      # TTTracks, extended
        MCTruthTrackInputTag = cms.InputTag("TTTrackAssociatorFromPixelDigis", "Level1TTTracks"),                                               # MCTruth track, prompt
        MCTruthTrackExtendedInputTag = cms.InputTag("TTTrackAssociatorFromPixelDigisExtended", "Level1TTTracks"),                               # MCTruth track, extended
        L1TrackGTTInputTag = cms.InputTag("l1tGTTInputProducer","Level1TTTracksConverted"),                                                      # TTTracks, prompt, GTT converted
        L1TrackExtendedGTTInputTag = cms.InputTag("l1tGTTInputProducerExtended","Level1TTTracksExtendedConverted"),                              # TTTracks, extended, GTT converted
        L1TrackSelectedInputTag = cms.InputTag("l1tTrackSelectionProducer", "Level1TTTracksSelected"),                                           # TTTracks, prompt, selected
        L1TrackSelectedEmulationInputTag = cms.InputTag("l1tTrackSelectionProducer", "Level1TTTracksSelectedEmulation"),                         # TTTracks, prompt, emulation, selected
        L1TrackSelectedAssociatedInputTag = cms.InputTag(AssociationName, "Level1TTTracksSelectedAssociated"),                                           # TTTracks, prompt, selected, associated
        L1TrackSelectedAssociatedEmulationInputTag = cms.InputTag(AssociationName, "Level1TTTracksSelectedAssociatedEmulation"),                         # TTTracks, prompt, emulation, selected, associated

        L1TrackSelectedForJetsInputTag = cms.InputTag("l1tTrackSelectionProducerForJets", "Level1TTTracksSelected"),                                           # TTTracks, prompt, selected
        L1TrackSelectedEmulationForJetsInputTag = cms.InputTag("l1tTrackSelectionProducerForJets", "Level1TTTracksSelectedEmulation"),                         # TTTracks, prompt, emulation, selected
        L1TrackSelectedAssociatedForJetsInputTag = cms.InputTag("l1tTrackVertexAssociationProducerForJets", "Level1TTTracksSelectedAssociated"),                                           # TTTracks, prompt, selected, associated
        L1TrackSelectedAssociatedEmulationForJetsInputTag = cms.InputTag("l1tTrackVertexAssociationProducerForJets", "Level1TTTracksSelectedAssociatedEmulation"),                         # TTTracks, prompt, emulation, selected, associated
                                       
        L1TrackSelectedForEtMissInputTag = cms.InputTag("l1tTrackSelectionProducerForEtMiss", "Level1TTTracksSelected"),                                           # TTTracks, prompt, selected
        L1TrackSelectedEmulationForEtMissInputTag = cms.InputTag("l1tTrackSelectionProducerForEtMiss", "Level1TTTracksSelectedEmulation"),                         # TTTracks, prompt, emulation, selected
        L1TrackSelectedAssociatedForEtMissInputTag = cms.InputTag("l1tTrackVertexAssociationProducerForEtMiss", "Level1TTTracksSelectedAssociated"),                                           # TTTracks, prompt, selected, associated
        L1TrackSelectedAssociatedEmulationForEtMissInputTag = cms.InputTag("l1tTrackVertexAssociationProducerForEtMiss", "Level1TTTracksSelectedAssociatedEmulation"),                         # TTTracks, prompt, emulation, selected, associated

        L1TrackExtendedSelectedInputTag = cms.InputTag("l1tTrackSelectionProducerExtended", "Level1TTTracksExtendedSelected"),                                           # TTTracks, extended, selected
        L1TrackExtendedSelectedEmulationInputTag = cms.InputTag("l1tTrackSelectionProducerExtended", "Level1TTTracksExtendedSelectedEmulation"),                         # TTTracks, extended, emulation, selected
        L1TrackExtendedSelectedAssociatedInputTag = cms.InputTag("l1tTrackVertexAssociationProducerExtended", "Level1TTTracksExtendedSelectedAssociated"),                                           # TTTracks, extended, selected, associated
        L1TrackExtendedSelectedAssociatedEmulationInputTag = cms.InputTag("l1tTrackVertexAssociationProducerExtended", "Level1TTTracksExtendedSelectedAssociatedEmulation"),                         # TTTracks, extended, emulation, selected, associated
                                       
        L1TrackExtendedSelectedForJetsInputTag = cms.InputTag("l1tTrackSelectionProducerExtendedForJets", "Level1TTTracksExtendedSelected"),                                           # TTTracks, extended, selected
        L1TrackExtendedSelectedEmulationForJetsInputTag = cms.InputTag("l1tTrackSelectionProducerExtendedForJets", "Level1TTTracksExtendedSelectedEmulation"),                         # TTTracks, extended, emulation, selected
        L1TrackExtendedSelectedAssociatedForJetsInputTag = cms.InputTag("l1tTrackVertexAssociationProducerExtendedForJets", "Level1TTTracksExtendedSelectedAssociated"),                                           # TTTracks, extended, selected, associated
        L1TrackExtendedSelectedAssociatedEmulationForJetsInputTag = cms.InputTag("l1tTrackVertexAssociationProducerExtendedForJets", "Level1TTTracksExtendedSelectedAssociatedEmulation"),                         # TTTracks, extended, emulation, selected, associated
                                       
        L1TrackExtendedSelectedForEtMissInputTag = cms.InputTag("l1tTrackSelectionProducerExtendedForEtMiss", "Level1TTTracksExtendedSelected"),                                           # TTTracks, extended, selected
        L1TrackExtendedSelectedEmulationForEtMissInputTag = cms.InputTag("l1tTrackSelectionProducerExtendedForEtMiss", "Level1TTTracksExtendedSelectedEmulation"),                         # TTTracks, extended, emulation, selected
        L1TrackExtendedSelectedAssociatedForEtMissInputTag = cms.InputTag("l1tTrackVertexAssociationProducerExtendedForEtMiss", "Level1TTTracksExtendedSelectedAssociated"),                                           # TTTracks, extended, selected, associated
        L1TrackExtendedSelectedAssociatedEmulationForEtMissInputTag = cms.InputTag("l1tTrackVertexAssociationProducerExtendedForEtMiss", "Level1TTTracksExtendedSelectedAssociatedEmulation"),                         # TTTracks, extended, emulation, selected, associated
                                                                              
        L1StubInputTag = cms.InputTag("TTStubsFromPhase2TrackerDigis","StubAccepted"),
        MCTruthClusterInputTag = cms.InputTag("TTClusterAssociatorFromPixelDigis", "ClusterAccepted"),
        MCTruthStubInputTag = cms.InputTag("TTStubAssociatorFromPixelDigis", "StubAccepted"),
        TrackingParticleInputTag = cms.InputTag("mix", "MergedTrackTruth"),
        TrackingVertexInputTag = cms.InputTag("mix", "MergedTrackTruth"),
        GenJetInputTag = cms.InputTag("ak4GenJets", ""),
        ##track jets and track MET
        SaveTrackJets = cms.bool(True), #includes emulated jets
        SaveTrackSums = cms.bool(True), #includes simulated/emulated track MET, MHT, and HT
        TrackFastJetsInputTag = cms.InputTag("l1tTrackFastJets","L1TrackFastJets"),
        TrackFastJetsExtendedInputTag = cms.InputTag("l1tTrackFastJetsExtended","L1TrackFastJetsExtended"),
        TrackJetsInputTag=cms.InputTag("l1tTrackJets", "L1TrackJets"),
        TrackTripletsInputTag = cms.InputTag("l1tTrackTripletEmulation", "L1TrackTriplet"),
        TrackJetsExtendedInputTag=cms.InputTag("l1tTrackJetsExtended", "L1TrackJetsExtended"),
        TrackJetsEmuInputTag = cms.InputTag("l1tTrackJetsEmulation","L1TrackJets"),
        TrackJetsExtendedEmuInputTag = cms.InputTag("l1tTrackJetsExtendedEmulation","L1TrackJetsExtended"),
        TrackMETInputTag = cms.InputTag("l1tTrackerEtMiss","L1TrackerEtMiss"),
        TrackMETExtendedInputTag = cms.InputTag("l1tTrackerEtMissExtended","L1TrackerExtendedEtMiss"),
        TrackMETEmuInputTag = cms.InputTag("l1tTrackerEmuEtMiss","L1TrackerEmuEtMiss"),
        TrackMHTInputTag = cms.InputTag("l1tTrackerHTMiss","L1TrackerHTMiss"), #includes HT
        TrackMHTExtendedInputTag = cms.InputTag("l1tTrackerHTMissExtended","L1TrackerHTMissExtended"),
        TrackMHTEmuInputTag = cms.InputTag("l1tTrackerEmuHTMiss",process.l1tTrackerEmuHTMiss.L1MHTCollectionName.value()),
        TrackMHTEmuExtendedInputTag = cms.InputTag("l1tTrackerEmuHTMissExtended",process.l1tTrackerEmuHTMissExtended.L1MHTCollectionName.value()),
        SimVertexInputTag = cms.InputTag("g4SimHits",""),
        GenParticleInputTag = cms.InputTag("genParticles",""),
        RecoVertexInputTag=cms.InputTag("l1tVertexFinder", "L1Vertices"),
        RecoVertexEmuInputTag=cms.InputTag("l1tVertexFinderEmulator", "L1VerticesEmulation"),
)

process.ntuple = cms.Path(process.L1TrackNtuple)

# variations

parameters = [ "Algorithm", "PFA_EtaDependentResolution", "PFA_ResolutionSF", "PFA_UseMultiplicityMaxima", "PFA_WeightFunction", "PFA_WeightedZ0", "WeightedMean" ]

# PFA = "PFASingleVertex"
PFA = "PFA"

'''
    ["", PFA, True, SF, False, 3, 0, P],
    ["", PFA, True, SF, False, 2, 0, P],
    ["", PFA, True, SF, False, 1, 0, P],
    ["", PFA, True, SF, False, 0, 0, P],
    ["", PFA, True, SF, False, 3, 1, P],
    #["", PFA, True, SF, False, 2, 1, P],
    ["", PFA, True, SF, False, 1, 1, P],
    ["", PFA, True, SF, False, 0, 1, P],
    ["", PFA, True, SF, False, 3, 2, P],
    ["", PFA, True, SF, False, 2, 2, P],
    #["", PFA, True, SF, False, 1, 2, P],
    #["", PFA, True, SF, False, 0, 2, P],
    ["", PFA, True, SF, False, 3, 3, P],
    #["", PFA, True, SF, False, 2, 3, P],
    #["", PFA, True, SF, False, 1, 3, P],
    #["", PFA, True, SF, False, 0, 3, P],
    ["", PFA, True, SF, False, 3, 4, P],
    ["", PFA, True, SF, False, 3, 5, P],
    ["", PFA, True, SF, False, 2, 6, P],
'''

variations_template = lambda SF, P : [

    ["", PFA, False, SF, False, 3, 0, P],
    ["", PFA, False, SF, False, 2, 0, P],
    ["", PFA, False, SF, False, 1, 0, P],
    #["", PFA, False, SF, False, 0, 0, P],
    ["", PFA, False, SF, False, 3, 1, P],
    #["", PFA, False, SF, False, 2, 1, P],
    ["", PFA, False, SF, False, 1, 1, P],
    #["", PFA, False, SF, False, 0, 1, P],
    ["", PFA, False, SF, False, 3, 2, P],
    ["", PFA, False, SF, False, 2, 2, P],
    #["", PFA, False, SF, False, 1, 2, P],
    #["", PFA, False, SF, False, 0, 2, P],
    ["", PFA, False, SF, False, 3, 3, P],
    #["", PFA, False, SF, False, 2, 3, P],
    #["", PFA, False, SF, False, 1, 3, P],
    #["", PFA, False, SF, False, 0, 3, P],
    #["", PFA, False, SF, False, 3, 4, P],
    #["", PFA, False, SF, False, 3, 5, P],
    #["", PFA, False, SF, False, 2, 6, P],

    ]

# SFFHLA = 0.86673747
# SFFH = 1.46588787

FHLAbinwidth = 0.15
FHbinwidth = 0.15991504
# PFAbinwidth = 0.03997876
PFAbinwidth = 0.15991504
PFAGaussianWidth = 0.15

SFFHLA = (2*FHLAbinwidth - PFAbinwidth) / (2*PFAGaussianWidth)
SFFH = (3*FHbinwidth - PFAbinwidth) / (2*PFAGaussianWidth)

algo_template = lambda algo: [
    ["", algo, False, 0, False, 0, 0, 1],
    ["", algo, False, 0, False, 0, 0, 2],
    ["", algo, False, 0, False, 0, 1, 1],
    ["", algo, False, 0, False, 0, 1, 2],
    ]

variations = algo_template("fastHisto") + algo_template("fastHistoLooseAssociation")
variations += variations_template(SFFH, 1) + variations_template(SFFH, 2)
#variations += variations_template(1.0, 2) + variations_template(1.189, 2) + variations_template(1.414, 2) + variations_template(1.682, 2) + variations_template(2.0, 2) + variations_template(2.4, 2) + variations_template(2.9, 2)
#variations += variations_template(0.5, 1) + variations_template(0.63, 1) + variations_template(0.794, 1) + variations_template(1.0, 1) + variations_template(1.26, 1) + variations_template(1.587, 1) + variations_template(2.0, 1)

VertexAssociators = {}
AssociationNames = {}

# TODO: currently assuming L1TRKALGO = 'HYBRID_PROMPTANDDISP'
for variation in variations:
    # automatically generate the label and store at the first index
    variation[0] = f"{variation[1]}Z{variation[6]}P{variation[7]}" if "PFA" not in variation[1] else f"{variation[1]}{'Eta' if variation[2] else 'NoE'}SF{100*variation[3]:03.0f}{'MM' if variation[4] else 'PM'}WF{variation[5]}Z{variation[6]}P{variation[7]}"
    print(variation[0])
    setattr(process, f'l1tVertexFinder{variation[0]}', process.l1tVertexFinder.clone())
    for p, param in enumerate(parameters):
        # print(f'l1tVertexFinder{variation[0]}.VertexReconstruction.{param}', variation[1 + p])
        setattr( getattr(process, f'l1tVertexFinder{variation[0]}' ).VertexReconstruction , f'{param}', variation[1 + p])
    setattr(process, f'pPV{variation[0]}', cms.Path(getattr(process, f'l1tVertexFinder{variation[0]}')))

    setattr(process, f'L1TrackNtuple{variation[0]}', process.L1TrackNtuple.clone())
    # setattr(process, f'L1TrackNtuple{variation[0]}.RecoVertexInputTag', cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices"))
    # setattr( getattr(process, f'L1TrackNtuple{variation[0]}' ), "RecoVertexInputTag", cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices"))
    getattr(process, f'L1TrackNtuple{variation[0]}' ).RecoVertexInputTag = cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices")


    if runVtxNN:
        setattr(process, f'l1tTrackVertexNNAssociationProducer{variation[0]}', process.l1tTrackVertexNNAssociationProducer.clone())
        getattr(process, f'l1tTrackVertexNNAssociationProducer{variation[0]}' ).l1VerticesInputTag = cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices")
        VertexAssociators[variation[0]] = getattr(process, f'l1tTrackVertexNNAssociationProducer{variation[0]}')
        AssociationNames[variation[0]] = f'l1tTrackVertexNNAssociationProducer{variation[0]}'
    else:
        setattr(process, f'l1tTrackVertexAssociationProducer{variation[0]}', process.l1tTrackVertexAssociationProducer.clone())
        getattr(process, f'l1tTrackVertexAssociationProducer{variation[0]}' ).l1VerticesInputTag = cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices")
        VertexAssociators[variation[0]] = getattr(process, f'l1tTrackVertexAssociationProducer{variation[0]}')
        AssociationNames[variation[0]] = f'l1tTrackVertexAssociationProducer{variation[0]}'

    setattr(process, f'l1tTrackVertexAssociationProducerExtended{variation[0]}', process.l1tTrackVertexAssociationProducerExtended.clone())
    setattr(process, f'l1tTrackVertexAssociationProducerForJets{variation[0]}', process.l1tTrackVertexAssociationProducerForJets.clone())
    setattr(process, f'l1tTrackVertexAssociationProducerExtendedForJets{variation[0]}', process.l1tTrackVertexAssociationProducerExtendedForJets.clone())
    setattr(process, f'l1tTrackVertexAssociationProducerForEtMiss{variation[0]}', process.l1tTrackVertexAssociationProducerForEtMiss.clone())
    setattr(process, f'l1tTrackVertexAssociationProducerExtendedForEtMiss{variation[0]}', process.l1tTrackVertexAssociationProducerExtendedForEtMiss.clone())

    getattr(process, f'l1tTrackVertexAssociationProducerExtended{variation[0]}' ).l1VerticesInputTag = cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices")
    getattr(process, f'l1tTrackVertexAssociationProducerForJets{variation[0]}' ).l1VerticesInputTag = cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices")
    getattr(process, f'l1tTrackVertexAssociationProducerExtendedForJets{variation[0]}' ).l1VerticesInputTag = cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices")
    getattr(process, f'l1tTrackVertexAssociationProducerForEtMiss{variation[0]}' ).l1VerticesInputTag = cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices")
    getattr(process, f'l1tTrackVertexAssociationProducerExtendedForEtMiss{variation[0]}' ).l1VerticesInputTag = cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices")

    pathtemp = cms.Path(VertexAssociators[variation[0]] * getattr(process, f'l1tTrackVertexAssociationProducerExtended{variation[0]}') *
                                                    getattr(process, f'l1tTrackVertexAssociationProducerForJets{variation[0]}') * getattr(process, f'l1tTrackVertexAssociationProducerExtendedForJets{variation[0]}') *
                                                    getattr(process, f'l1tTrackVertexAssociationProducerForEtMiss{variation[0]}') * getattr(process, f'l1tTrackVertexAssociationProducerExtendedForEtMiss{variation[0]}'))
    setattr(process, f'pL1TrackVertexAssociation{variation[0]}', pathtemp )

    getattr(process, f'L1TrackNtuple{variation[0]}' ).L1TrackSelectedAssociatedInputTag = cms.InputTag(AssociationNames[variation[0]], "Level1TTTracksSelectedAssociated") # TTTracks, prompt, selected, associated
    getattr(process, f'L1TrackNtuple{variation[0]}' ).L1TrackSelectedAssociatedForJetsInputTag = cms.InputTag(f'l1tTrackVertexAssociationProducerForJets{variation[0]}', "Level1TTTracksSelectedAssociated") # TTTracks, prompt, selected, associated
    getattr(process, f'L1TrackNtuple{variation[0]}' ).L1TrackSelectedAssociatedForEtMissInputTag = cms.InputTag(f'l1tTrackVertexAssociationProducerForEtMiss{variation[0]}', "Level1TTTracksSelectedAssociated") # TTTracks, prompt, selected, associated
    getattr(process, f'L1TrackNtuple{variation[0]}' ).L1TrackExtendedSelectedAssociatedInputTag = cms.InputTag(f'l1tTrackVertexAssociationProducerExtended{variation[0]}', "Level1TTTracksExtendedSelectedAssociated") # TTTracks, extended, selected, associated
    getattr(process, f'L1TrackNtuple{variation[0]}' ).L1TrackExtendedSelectedAssociatedForJetsInputTag = cms.InputTag(f'l1tTrackVertexAssociationProducerExtendedForJets{variation[0]}', "Level1TTTracksExtendedSelectedAssociated") # TTTracks, extended, selected, associated
    getattr(process, f'L1TrackNtuple{variation[0]}' ).L1TrackExtendedSelectedAssociatedForEtMissInputTag = cms.InputTag(f'l1tTrackVertexAssociationProducerExtendedForEtMiss{variation[0]}', "Level1TTTracksExtendedSelectedAssociated") # TTTracks, extended, selected, associated


    setattr(process, f'l1tTrackJets{variation[0]}', process.l1tTrackJets.clone())
    setattr(process, f'l1tTrackJetsExtended{variation[0]}', process.l1tTrackJetsExtended.clone())
    getattr(process, f'l1tTrackJets{variation[0]}' ).L1TrackInputTag = cms.InputTag(f'l1tTrackVertexAssociationProducerForJets{variation[0]}', "Level1TTTracksSelectedAssociated")
    getattr(process, f'l1tTrackJetsExtended{variation[0]}' ).L1TrackInputTag = cms.InputTag(f'l1tTrackVertexAssociationProducerExtendedForJets{variation[0]}', "Level1TTTracksExtendedSelectedAssociated")
    setattr(process, f'pL1TrackJets{variation[0]}', cms.Path( getattr(process, f'l1tTrackJets{variation[0]}') * getattr(process, f'l1tTrackJetsExtended{variation[0]}') ) )

    getattr(process, f'L1TrackNtuple{variation[0]}' ).TrackJetsInputTag = cms.InputTag(f'l1tTrackJets{variation[0]}', "L1TrackJets")
    getattr(process, f'L1TrackNtuple{variation[0]}' ).TrackJetsExtendedInputTag = cms.InputTag(f'l1tTrackJetsExtended{variation[0]}', "L1TrackJetsExtended")


    setattr(process, f'l1tTrackFastJets{variation[0]}', process.l1tTrackFastJets.clone())
    setattr(process, f'l1tTrackFastJetsExtended{variation[0]}', process.l1tTrackFastJetsExtended.clone())
    getattr(process, f'l1tTrackFastJets{variation[0]}' ).L1TrackInputTag = cms.InputTag(f'l1tTrackVertexAssociationProducerForJets{variation[0]}', "Level1TTTracksSelectedAssociated")
    getattr(process, f'l1tTrackFastJetsExtended{variation[0]}' ).L1TrackInputTag = cms.InputTag(f'l1tTrackVertexAssociationProducerExtendedForJets{variation[0]}', "Level1TTTracksExtendedSelectedAssociated")
    setattr(process, f'pL1TrackFastJets{variation[0]}', cms.Path( getattr(process, f'l1tTrackFastJets{variation[0]}') * getattr(process, f'l1tTrackFastJetsExtended{variation[0]}') ) )

    getattr(process, f'L1TrackNtuple{variation[0]}' ).TrackFastJetsInputTag = cms.InputTag(f'l1tTrackFastJets{variation[0]}', "L1TrackFastJets")
    getattr(process, f'L1TrackNtuple{variation[0]}' ).TrackFastJetsExtendedInputTag = cms.InputTag(f'l1tTrackFastJetsExtended{variation[0]}', "L1TrackFastJetsExtended")


    setattr(process, f'l1tTrackerEtMiss{variation[0]}', process.l1tTrackerEtMiss.clone())
    setattr(process, f'l1tTrackerEtMissExtended{variation[0]}', process.l1tTrackerEtMissExtended.clone())
    getattr(process, f'l1tTrackerEtMiss{variation[0]}' ).L1TrackAssociatedInputTag = cms.InputTag(f'l1tTrackVertexAssociationProducerForEtMiss{variation[0]}', "Level1TTTracksSelectedAssociated")
    getattr(process, f'l1tTrackerEtMissExtended{variation[0]}' ).L1TrackAssociatedInputTag = cms.InputTag(f'l1tTrackVertexAssociationProducerExtendedForEtMiss{variation[0]}', "Level1TTTracksExtendedSelectedAssociated")
    setattr(process, f'pTkMET{variation[0]}', cms.Path( getattr(process, f'l1tTrackerEtMiss{variation[0]}') * getattr(process, f'l1tTrackerEtMissExtended{variation[0]}') ) )

    getattr(process, f'L1TrackNtuple{variation[0]}' ).TrackMETInputTag = cms.InputTag(f'l1tTrackerEtMiss{variation[0]}', "L1TrackerEtMiss")
    getattr(process, f'L1TrackNtuple{variation[0]}' ).TrackMETExtendedInputTag = cms.InputTag(f'l1tTrackerEtMissExtended{variation[0]}', "L1TrackerExtendedEtMiss")


    setattr(process, f'l1tTrackerHTMiss{variation[0]}', process.l1tTrackerHTMiss.clone())
    setattr(process, f'l1tTrackerHTMissExtended{variation[0]}', process.l1tTrackerHTMissExtended.clone())
    getattr(process, f'l1tTrackerHTMiss{variation[0]}' ).L1TkJetInputTag = cms.InputTag(f'l1tTrackJets{variation[0]}', "L1TrackJets")
    getattr(process, f'l1tTrackerHTMissExtended{variation[0]}' ).L1TkJetInputTag = cms.InputTag(f'l1tTrackJetsExtended{variation[0]}', "L1TrackJetsExtended")
    getattr(process, f'l1tTrackerHTMiss{variation[0]}' ).L1VertexInputTag = cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices")
    getattr(process, f'l1tTrackerHTMissExtended{variation[0]}' ).L1VertexInputTag = cms.InputTag(f'l1tVertexFinder{variation[0]}', "L1Vertices")
    setattr(process, f'pTkMHT{variation[0]}', cms.Path( getattr(process, f'l1tTrackerHTMiss{variation[0]}') * getattr(process, f'l1tTrackerHTMissExtended{variation[0]}') ) )

    getattr(process, f'L1TrackNtuple{variation[0]}' ).TrackMHTInputTag = cms.InputTag(f'l1tTrackerHTMiss{variation[0]}', "L1TrackerHTMiss")
    getattr(process, f'L1TrackNtuple{variation[0]}' ).TrackMHTExtendedInputTag = cms.InputTag(f'l1tTrackerHTMissExtended{variation[0]}', "L1TrackerHTMissExtended")


    setattr(process, f'ntuple{variation[0]}', cms.Path(getattr(process, f'L1TrackNtuple{variation[0]}')))


process.out = cms.OutputModule( "PoolOutputModule",
 #                               outputCommands = process.RAWSIMEventContent.outputCommands,
                                outputCommands = cms.untracked.vstring("keep *","drop *_*_*_HLT"),
                                fileName = cms.untracked.string("test.root" )
		               )
#process.out.outputCommands.append('keep  *_*_*_*')
#process.out.outputCommands.append('drop  l1tEMTFHits_*_*_*')
process.pOut = cms.EndPath(process.out)


# use this if you want to re-run the stub making
# process.schedule = cms.Schedule(process.TTClusterStub,process.TTClusterStubTruth,process.TTTracksEmuWithTruth,process.ntuple)

# use this if cluster/stub associators not available
# process.schedule = cms.Schedule(process.TTClusterStubTruth,process.TTTracksEmuWithTruth,process.ntuple)

process.schedule = cms.Schedule(process.TTClusterStub, process.TTClusterStubTruth, process.dtc, process.TTTracksEmuWithTruth, process.pL1GTTInput, process.pL1TrackSelection, process.pPV, process.pPVemu,process.pL1TrackVertexAssociation, process.pL1TrackJets, process.pL1TrackJetsEmu,process.pL1TrackFastJets, process.pTkMET, process.pTkMETEmu, process.pTkMHT, process.pTkMHTEmulator,process.pL1TrackTripletEmulator, process.ntuple)

for variation in variations:
    process.schedule.append( getattr(process, f'pPV{variation[0]}' ) )
    process.schedule.append( getattr(process, f'pL1TrackVertexAssociation{variation[0]}' ) )
    process.schedule.append( getattr(process, f'pL1TrackJets{variation[0]}' ) )
    process.schedule.append( getattr(process, f'pL1TrackFastJets{variation[0]}' ) )
    process.schedule.append( getattr(process, f'pTkMET{variation[0]}' ) )
    process.schedule.append( getattr(process, f'pTkMHT{variation[0]}' ) )
    process.schedule.append( getattr(process, f'ntuple{variation[0]}' ) )
