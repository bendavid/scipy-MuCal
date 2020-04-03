import ROOT
import pickle
import numpy as np
from header import *
from root_numpy import array2hist, fill_hist
import argparse
import itertools

#ROOT.gSystem.Load('bin/libKalman.so')

parser = argparse.ArgumentParser("")
parser.add_argument('-isJ', '--isJ', default=False, action='store_true', help="Use to run on JPsi, omit to run on Z")
parser.add_argument('-isData', '--isData', default=False, action='store_true', help="Use if data, omit if MC")
parser.add_argument('-runClosure', '--runClosure', default=False, action='store_true', help="Use to apply full calibration. If omit, rescale data for B map and leave MC as it is")

args = parser.parse_args()
isJ = args.isJ
isData = args.isData
runClosure = args.runClosure


ROOT.ROOT.EnableImplicitMT()
RDF = ROOT.ROOT.RDataFrame

restrictToBarrel = True

if isJ:
    cut = 'pt1>3. && pt2>3.'# && mass>2.9 && mass<3.3'
    
else:
    cut = 'pt1>20.0 && pt2>20.0 && mass>80. && mass<100.'

if restrictToBarrel:
    cut+= '&& fabs(eta1)<0.8 && fabs(eta2)<0.8'

else:
    cut+= '&& fabs(eta1)<2.4 && fabs(eta2)<2.4' 

if not isData:

    cut+= '&& mcpt1>0. && mcpt2>0.'

if isJ:
    inputFileMC ='/scratchssd/emanca/wproperties-analysis/muonCalibration/muonTree.root'
    inputFileD ='/scratchssd/emanca/wproperties-analysis/muonCalibration/muonTreeData.root'
else:
    inputFileMC ='/scratchssd/emanca/wproperties-analysis/muonCalibration/muonTreeMCZ.root'
    inputFileD ='/scratchssd/emanca/wproperties-analysis/muonCalibration/muonTreeDataZ.root'

if isData: inputFile = inputFileD
else: inputFile = inputFileMC

d = RDF('tree',inputFile)

NSlots = d.GetNSlots()
ROOT.gInterpreter.ProcessLine('''
                std::vector<TRandom3> myRndGens({NSlots});
                int seed = 1; // not 0 because seed 0 has a special meaning
                for (auto &&gen : myRndGens) gen.SetSeed(seed++);
                '''.format(NSlots = NSlots))

print cut
d = d.Filter(cut)\
	 .Define('v1', 'ROOT::Math::PtEtaPhiMVector(pt1,eta1,phi1,0.105)')\
     .Define('v2', 'ROOT::Math::PtEtaPhiMVector(pt2,eta2,phi2,0.105)')\
	 .Define('rapidity', 'float((v1+v2).Rapidity())').Filter('fabs(rapidity)<0.8')\
     .Define('v1sm', 'ROOT::Math::PtEtaPhiMVector(mcpt1+myRndGens[rdfslot_].Gaus(0., cErr1*pt1),eta1,phi1,0.105)')\
     .Define('v2sm', 'ROOT::Math::PtEtaPhiMVector(mcpt2+myRndGens[rdfslot_].Gaus(0., cErr2*pt2),eta2,phi2,0.105)')\
     .Define('smearedgenMass', '(v1sm+v2sm).M()')

if isData:
    f = ROOT.TFile.Open("/scratchssd/emanca/wproperties-analysis/muonCalibration/calibData/bFieldMap.root")
    bFieldMap = f.Get('bfieldMap')

    if runClosure: print "taking corrections from", "/scratchssd/emanca/wproperties-analysis/muonCalibration/calibData/scale_{}_80X_13TeV.root".format("DATA" if isData else "MC")
    f2 = ROOT.TFile.Open("/scratchssd/emanca/wproperties-analysis/muonCalibration/calibData/scale_{}_80X_13TeV.root".format("DATA" if isData else "MC"))
    A = f2.Get('magnetic')
    e = f2.Get('e')
    M = f2.Get('B')

    module = ROOT.applyCalibration(bFieldMap, A, e, M, isData, runClosure)

    d = module.run(CastToRNode(d))

etas = np.arange(-0.8, 1.2, 0.4)
#pts = np.array((3.,7.,15.,20.))
mass = np.arange(3.05,3.151,0.001)
#etas = np.array((-0.8,0.8))
pts = np.array((3.,20.))

#phis = np.arange(-np.pi, np.pi+2.*np.pi/6.,2.*np.pi/6.)
phis = np.array((-np.pi,np.pi))

data = d.AsNumpy(columns=["smearedgenMass","eta1", "pt1", "eta2", "pt2"])

dataset = np.array([data["eta1"],data["eta2"],data["smearedgenMass"],data["pt1"],data["pt2"]])

histo, edges = np.histogramdd(dataset.T, bins = [etas,etas,mass,pts,pts])


if not isJ:
    filehandler = open('calInputZ{}.pkl'.format("DATA" if isData else "MC"), 'w')
else:
    filehandler = open('calInputJ{}.pkl'.format("DATA" if isData else "MC"), 'w')
pickle.dump(histo, filehandler)

#mass = np.arange(3.05,3.1501,0.0001)
#mass = np.arange(2.8,3.4,0.0006)
#print len(mass), mass

if not isData:

    dataGen = d.AsNumpy(columns=["genMass","eta1", "pt1", "phi1", "eta2", "pt2", "phi2"])

    datasetGen = np.array([dataGen["eta1"],dataGen["eta2"],dataGen["genMass"],dataGen["pt1"],dataGen["pt2"]])
    histoGen, edges = np.histogramdd(datasetGen.T, bins = [etas,etas,mass,pts,pts])

    if not isJ:
        filehandler = open('calInputZMCgen.pkl', 'w')
    else:
        filehandler = open('calInputJMCgen.pkl', 'w')
    pickle.dump(histoGen, filehandler)




