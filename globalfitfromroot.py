import math
import ROOT
import numpy as np
import concurrent.futures
import matplotlib.pyplot as plt
import threading
import scipy
import scipy.linalg
import sys
import scipy.sparse.linalg
import scipy.sparse

np.set_printoptions(threshold=sys.maxsize)


def ptparm(parms):
  p = np.abs(1./parms[0])
  theta = np.pi/2. - parms[1]
  pt = p*np.sin(theta)
  return pt
  
def deltaphi(phi1,phi2):
  if phi1 < -np.pi:
    phi1 += 2*np.pi
  elif phi1 >= np.pi:
    phi1 += -2*np.pi

  if phi2 < -np.pi:
    phi2 += 2*np.pi
  elif phi2 >= np.pi:
    phi2 += -2*np.pi
  
  dphi = phi2-phi1
  if dphi < -np.pi:
    dphi += 2*np.pi
  elif dphi >= np.pi:
    dphi += -2*np.pi
  return dphi

#results = np.load('combinedgrads.npz')

#gradfull = results["grad"]
#hessfull = results["hess"]


##assert(0)

##print(grad[0])
##print(hess[0])


#print("filling in lower triangular part of hessian")
#for i in range(hessfull.shape[0]):
  #print(i)
  #hessfull[i,:i] = hessfull[:i,i]

#print(hessfull[0,0])
#print(hessfull[0,:10])
#print(hessfull[:10,0])

#print(hessfull[1,1])
#print(hessfull[1,:10])
#print(hessfull[:10,1])
  
  
#print(np.linalg.eigvalsh(hessfull))
#assert(0)


#filenameinfo = "/data/bendavid/cmsswdevslc6/CMSSW_8_0_30/work/trackTreeGradsParmInfo.root"
#filenameinfo = "/data/bendavid/cmsswdevslc6/CMSSW_10_2_23/work/trackTreeGradsParmInfo.root"
filenameinfo = "root://eoscms.cern.ch//store/cmst3/group/wmass/bendavid/muoncal/DoubleMuonGun_Pt3To150/MuonGunUL2016_v21_Gen/201130_004723/0000/globalcor_0_1.root"
finfo = ROOT.TFile.Open(filenameinfo)

#runtree = finfo.tree
#runtree = finfo.globalCorGen.runtree
runtree = finfo.runtree

nparmsfull = np.int64(runtree.GetEntries())

gradfull = np.zeros((nparmsfull,1), dtype=np.float64)
hessfull = np.zeros((nparmsfull, nparmsfull), dtype=np.float64)

filenamegrads = "combinedgrads.root"
#filenamegrads = "combinedgradsrec.root"
#filenamegrads = "/data/bendavid/muoncaldata/combinedgrads.root"
fgrads = ROOT.TFile.Open(filenamegrads)
gradtree = fgrads.tree

print("loading grads")
for i, entry in enumerate(gradtree):
  #break
  print(i)
  gradfull[i,0] = entry.gradelem
  hessfull[i] = entry.hessrow

#nonzero = np.count_nonzero(hessfull)
#print("nonzero", nonzero)
#assert(0)

print("filling in lower triangular part of hessian")
def filllower(i):
  hessfull[i,:i] = hessfull[:i,i]
  
with concurrent.futures.ThreadPoolExecutor(32) as e:
  results = e.map(filllower, range(hessfull.shape[0]))
  
for result in results:
  pass


#for i in range(hessfull.shape[0]):
  #print(i)
  #hessfull[i,:i] = hessfull[:i,i]


parmset = set()
parmlistfull = []
for iidx,parm in enumerate(runtree):
    parmtype = runtree.parmtype
    ieta = math.floor(runtree.eta/0.1)
    #ieta = runtree.stereo
    iphi = math.floor(runtree.phi/(math.pi/8.))
    #iphi = math.floor(runtree.phi/(math.pi/1024.))
    #iphi = 0
    #ieta = math.floor(runtree.eta/1.0)
    subdet = runtree.subdet
    layer = abs(runtree.layer)
    #if (parmtype==2 and subdet==0 and layer==1) :
    #if (parmtype!=2):
    #if (False):
    #if (parmtype==2):
    #if (parmtype!=2 or (subdet==0 and layer==1)) :
    #if (parmtype>2):
    #if (abs(gradfull[ieta,0])<1e-9):
    if parmtype not in [0,2]:
    #if parmtype > 1 or subdet > 1:
        parmtype = -1
        subdet = -1
        layer = -1
        ieta = 0
        iphi = 0
    #elif (parmtype==3):
    else:
        ieta = iidx
        iphi = 0
      
  #if parmtype>1:
    #if (subdet==3 and layer==7) or (subdet==5 and layer==9):
      #subdet = -1
      #layer = -1
      #ieta = 0
      #parmtype = -1
    key = (parmtype, subdet, layer, ieta)
    #key = (parmtype, subdet, layer, (ieta,iphi))
    parmset.add(key)
    parmlistfull.append(key)
  
parmlist = list(parmset)
parmlist.sort()

parmmap = {}
for iparm,key in enumerate(parmlist):
  parmmap[key] = iparm
  
idxmap = []
for iidx, key in enumerate(parmlistfull):
  idxmap.append(parmmap[key])

#print(len(parmlist))
idxmap = np.array(idxmap)
#print(idxmap)

nglobal = len(parmlist)
print(nglobal)


nalign = 0
nbfield = 0 
for parm in parmlist:
  print(parm)
  parmtype, subdet, layer, ieta = parm
  if parmtype<2:
    nalign+=1
  if parmtype==2:
    nbfield+=1

grad = np.zeros((nglobal,1), dtype=np.float64)
hess = np.zeros((nglobal,nglobal), dtype=np.float64)


#for iparm,parm in enumerate(parmlist):
  #parmtype, subdet, layer, ieta = parm
  #print(parmtype)
  #if parmtype==-1:
    #print(f"null parameter for index {iparm}")

#assert(0)

print("reducing grad")
np.add.at(grad.ravel(), idxmap, gradfull.ravel())



#assert(0)

lock = threading.Lock()
hesstmps = {}
#def inithesstmp():
  #with lock:
    #hesstmps[threading.get_ident()] = np.zeros((nglobal,nglobal),dtype=np.float64)

print("reducing hess")
stepsize = 200
def fillhess(i):
  #hesstmp = hesstmps[threading.get_ident()]
  with lock:
    hesstmp = hesstmps.get(threading.get_ident())
    if hesstmp is None:
      hesstmp = np.zeros((nglobal,nglobal),dtype=np.float64)
      hesstmps[threading.get_ident()] = hesstmp
  end = np.minimum(i+stepsize, hessfull.shape[0])
  idxs = nglobal*idxmap[i:end, np.newaxis] + idxmap[np.newaxis,:]
  np.add.at(hesstmp.ravel(), idxs.ravel(), hessfull[i:end].ravel())

#with concurrent.futures.ThreadPoolExecutor(max_workers=32, initializer=inithesstmp) as e:
with concurrent.futures.ThreadPoolExecutor(max_workers=32) as e:    
  results = e.map(fillhess, range(0, hessfull.shape[0], stepsize))

hessfull = None

for hesstmp in hesstmps.values():
  hess += hesstmp

hesstmp = None

#for res in results:
  #pass;

##idxs = nglobal*idxmap[:, np.newaxis] + idxmap[np.newaxis,:]
#np.add.at(hess.ravel(), idxs.ravel(), hessfull.ravel())

#idxmaprev = nglobal*[[]]
#for iidx, idx in enumerate(idxmap):
  #idxmaprev[idx].append(iidx)

#for i in range(nglobal):
  #print(i)
  #idxsfull = np.array(idxmaprev[i])
  #nlocal = idxsfull.shape[0]
  
  #hessfullidxs = nparmsfull*idxsfull[:,np.newaxis] + idxsfull[np.newaxis,:]
  
  #idxs = idxmap[idxsfull]
  #hessidxs = nglobal*idxs[:,np.newarray] + idxs[np.newarray,:]
  
  #np.add.at(hess.ravel(), hessidxs, hessfull.ravel()[hessfullidxs])

  
#print("hessfull shape[0]", hessfull.shape[0])

#for i in range(0, hessfull.shape[0], stepsize):
##for i in range(hessfull.shape[0]):  
  #print(i)
  #end = np.minimum(i+stepsize, hessfull.shape[0])
  ##idxs = nglobal*idxmap[i:i+1, np.newaxis] + idxmap[np.newaxis,:]
  ##np.add.at(hess.ravel(), idxs.ravel(), hessfull[i:i+1].ravel())
  #idxs = nglobal*idxmap[i:end, np.newaxis] + idxmap[np.newaxis,:]
  #np.add.at(hess.ravel(), idxs.ravel(), hessfull[i:end].ravel())

#print(grad[0])
#print(hess[0])
#print(hess[0,0])
#print(hess[0,:10])
#print(hess[:10,0])

#print(hess[1,1])
#print(hess[1,:10])
#print(hess[:10,1])

#print(hess[-1,-1])





    
#for i in range(nalign, nalign+nbfield):
  #hess[i,i] += 1./0.038**2
    
#for i in range(nalign+nbfield, nglobal):
  #hess[i,i] += 1./1e-2**2


#print("align")
#print(grad[:nalign])
#print("bfield")
#print(grad[nalign:nalign+nbfield])
#print("eloss")
#print(grad[nalign+nbfield:])

#e,v = np.linalg.eigh(hess)
#print(e)



for iparm,parm in enumerate(parmlist):
  parmtype, subdet, layer, ieta = parm
  if parmtype==-1:
    print(f"null parameter for index {iparm}")
    grad[iparm] = 0.
    hess[iparm, :] = 0.
    hess[:, iparm] = 0.
    hess[iparm,iparm] = 2.
  if parmtype < 2:
    hess[iparm, iparm] += 2.*1./1e-1**2
  if parmtype == 2:
    #hess[iparm, iparm] += 2.*1./0.038**2
    hess[iparm, iparm] += 2.*1./0.2**2
  if parmtype == 3:
    hess[iparm, iparm] += 2.*1./1e-4**2
    

#nalign = 0
#for parm in parmlist:
  #parmtype, subdet, layer, ieta = parm
  #if parmtype<3:
    #nalign+=1
    
#grad[nalign:] = 0.
#hess[nalign:] = 0.
#hess[:,nalign:] = 0.
#hess[nalign:,nalign:] = np.eye(nglobal-nalign)

hessbak = hess
gradbak = grad

#assert(0)

#print(np.linalg.eigvalsh(hess))


#v0 = v[:,0]

#print(e)
#assert(0)

#e,v = np.linalg.eigh(hess)
#e = np.linalg.eigvalsh(hess)
#print("hess eiganvalues")
#print(e)

#badidxs = []
#for i in range(nglobal):
  #if e[i]<0.:
    #idx = np.argmax(np.abs(v[:,i]))
    #grad[idx] = 0.
    #hess[idx] *= 0.
    #hess[:,idx] *= 0.
    #hess[idx,idx] = 2.
    #badidxs.append(idx)

bconstraint = 0.01*3.8
Jb = np.zeros((nglobal,1), dtype=np.float64)

for iparm,parm in enumerate(parmlist):
  parmtype, subdet, layer, ieta = parm
  if parmtype==2:
    Jb[iparm] = 1.

#hess += 2.*Jb*Jb.transpose()/bconstraint**2

#e,v = np.linalg.eigh(hess)
#print(e)


    
#print("making sparse")
#hesssparse = scipy.sparse.csc_matrix(hess)
print("solving")
#xout = scipy.sparse.linalg.spsolve(hesssparse, -grad)

#xout[1:] = 0.05*3.8

#xout = scipy.sparse.linalg.spsolve(hess, -grad)
#xout = scipy.sparse.linalg.gmres(hess, -grad)
#xout = scipy.linalg.cho_solve(scipy.linalg.cho_factor(hess), -grad)
xout = np.linalg.solve(hess,-grad)

#xout, residuals, rank, s = np.linalg.lstsq(hess, -grad, rcond=1e-8)
#xout, residuals, rank, s = np.linalg.lstsq(hess, -grad, rcond=5e-11)
#xout, residuals, rank, s = np.linalg.lstsq(hess, -grad, rcond=5e-6)
#xout, residuals, rank, s = np.linalg.lstsq(hess, -grad, rcond=None)

#rcond = 2./bconstraint**2/s[0]
#print("rcond", rcond)
#rcond = 1./e[-1]
#xout, residuals, rank, s = np.linalg.lstsq(hess, -grad, rcond=rcond)
#xout, residuals, rank, s = np.linalg.lstsq(hess, -grad)
#xout, residuals, rank, s = np.linalg.lstsq(hess, -grad, rcond=1e-14)
#print("rank", rank)
#print("singular values:")
#print(s)

print("done solve")

#for iparm,parm in enumerate(parmlist):
  #parmtype, subdet, layer, ieta = parm
  ##if parmtype < 2:
    ##hess[iparm, iparm] += 2.*1./1e-2**2
  #if parmtype == 2:
    #hess[iparm, iparm] += 2.*1./bconstraint**2
  ##if parmtype == 3:
    ##hess[iparm, iparm] += 2.*1./1e-4**2

cov = np.linalg.inv(hess)
errs = np.sqrt(2.*np.diag(cov))

#cov = hess
#errs = np.sqrt(2./np.diag(cov))

#errs = np.sqrt(2./np.diag(hess))

#write output file
fout = ROOT.TFile.Open("correctionResults.root", "RECREATE")
#fout = ROOT.TFile.Open("correctionResults2016.root", "RECREATE")

idxmaptree = ROOT.TTree("idxmaptree","")
idx = np.empty((1), dtype=np.uint32)
idxmaptree.Branch("idx", idx, "idx/i")
for i in range(nparmsfull):
    idx[0] = idxmap[i]
    idxmaptree.Fill()
    
idxmaptree.Write()

parmtree = ROOT.TTree("parmtree","")
x = np.empty((1), dtype=np.float32)
err = np.empty((1), dtype=np.float32)

parmtree.Branch("x", x, "x/F")
parmtree.Branch("err", err, "err/F")

for i in range(nglobal):
    x[0] = xout[i]
    err[0] = errs[i]
    parmtree.Fill()
    
parmtree.Write()
fout.Close()

print(xout)
#assert(0)
#docors = True
docors = False

if docors:
  


  #filename = "/data/bendavid/cmsswdevslc6/CMSSW_10_2_23/work/trackTreeGrads.root"
  #filename = "/data/bendavid/muoncaldatalarge/Muplusandminus_Pt3to150-gun/MuonGunGlobalCor_v4/200820_002243/0000/trackTreeGrads_2.root"
  filename = "/data/bendavid/muoncaldatalarge/MuonGunGlobalCorRec_GBLNo2dStrip/200909_151136/0000/globalcor_1.root"
  #filename = "/data/bendavid/cmsswdevslc6/CMSSW_8_0_30/work/trackTreeGrads.root"
  #filename = "/data/bendavid/cmsswdevslc6/CMSSW_8_0_30/work/trackTreeGradsdebug2.root"
  
  f = ROOT.TFile.Open(filename)
  #tree = f.tree
  tree = f.globalCor.tree
  
  r = []
  ralt = []
  rcor = []
  rcoralt = []
  itrack = 0
  for track in tree:
    #print(track.trackPt)
    if track.trackPt < 5.5:
      continue
    
    itrack += 1
    
    if (itrack>50000):
        break
    
    #if not (track.trackPt>100):
      #continue
    
    ljacref = np.array(track.jacrefv)
    #ljacref = np.reshape(ljacref,(-1,5)).transpose()
    ljacref = np.reshape(ljacref,(5,-1))
    idxs = np.array(track.globalidxv)
    idxs = idxmap[idxs]
    
    parms = xout[idxs]
    dtk = ljacref@parms
    dtk = np.reshape(dtk,(5,))
    #print(dtk)
    
    #print(ljacref)
    #print(parms)
    #print(dtk)
    
    tkcor = np.array(track.trackParms) + dtk
    tkcoralt = np.array(track.refParms) + dtk
    
    #tkcor = np.frombuffer(track.trackParms, dtype=np.float32) + dtk
    #tkcoralt = np.frombuffer(track.refParms, dtype=np.float32) + dtk
    
    
    pt = ptparm(track.trackParms)
    ptalt = ptparm(track.refParms)
    
    #r.append(track.trackPt/track.genPt)
    
    ptcor = ptparm(tkcor)
    ptcoralt = ptparm(tkcoralt)
    
    
  
     
    
    if track.genPt>0.:
      r.append(pt/track.genPt)
      ralt.append(ptalt/track.genPt)
      rcor.append(ptcor/track.genPt)
      rcoralt.append(ptcoralt/track.genPt)
    

  r = np.array(r)
  ralt = np.array(ralt)
  rcor = np.array(rcor)
  rcoralt = np.array(rcoralt)

  #hr = np.histogram(r, bins=100, range=(0.9,1.1))

  plt.plot()
  histrange = (0.9,1.1)
  #histrange = (0.7,1.3)
  plt.hist(r, bins=100, range=histrange)
  ##plt.hist(ralt, bins=100, range=histrange)
  ##plt.hist(rcor, bins=100, range=histrange)
  plt.hist(rcoralt, bins=100, range=histrange)
  


  #plt.show()

#print("align:")
#print(v0[:nalign])
#print("bfield:")
#print(v0[nalign:nalign+nbfield])
#print("eloss")
#print(v0[nalign+nbfield:])

#print(np.argmax(np.abs(v0)))

#assert(0)

#print("before:")
#print(np.linalg.eigvalsh(hess))
#diagadd = np.zeros((nglobal,),np.float64)
##diagadd[:nalign] = 1./1e-2**2
#diagadd[nalign:nalign+nbfield] = 1/0.038**2
##diagadd[nalign:nalign+nbfield] = 1/0.00038**2
##diagadd[nalign+nbfield:] = 1./1e-4**2

#diagidxs = np.diag_indices_from(hess)
#np.add.at(hess, diagidxs, diagadd)
#print("after:")
#print(np.linalg.eigvalsh(hess))
#assert(0)
  
#np.fill_diagonal(hess,np.diag(hess)+diagadd)
  

#e,v = np.linalg.eigh(hess)
#print(e)


print(xout)
print(errs)

resmap = {}
#for parm in runtree:
  #iidx = parm.iidx
  #if iidx in badidxs:
    #continue
  #parmtype = parm.parmtype
  #subdet = parm.subdet
  #layer = parm.layer
  #ieta = math.floor(parm.eta/0.2)
  
  #resmap[(parmtype, subdet, abs(layer), ieta)] = (xout[iidx], errs[iidx])
  
for iparm,parm in enumerate(parmlist):
  resmap[parm] = (xout[iparm], errs[iparm])
  
  


#subdet = 1
#parmtype = 2
#layer = 1
for parmtype in range(4):
  for subdet in range(7):
    for layer in range(50):
      etas = []
      vals = []
      valerrs = []
      for ieta in range(-30,30):
        key = (parmtype, subdet, layer, ieta)
        if key in resmap:
          eta = 0.1*ieta
          etas.append(eta)
          val,err = resmap[key]
          vals.append(val)
          valerrs.append(err)
          print(key, resmap[key])
      #if vals:
      if False:
        plot = plt.figure()
        label = f"parmtype {parmtype}, subdet {subdet}, layer {layer}"
        plt.title(label)
        #plt.xlabel("$Module Center \eta$")
        plt.xlabel("isStereo")
        plt.errorbar(etas, vals, yerr=valerrs,xerr=0.05, fmt='none')



for parmtype in range(4):
  ientry = 0        
  xs = []
  vals = []
  valerrs = []
  for subdet in range(7):
      for layer in range(50):
          for ieta in range(-30,30):
                  key = (parmtype, subdet, layer, ieta)
                  if key in resmap:
                      x = ientry + 0.5
                      val,err = resmap[key]
                      if parmtype<2 and err==0.1:
                          continue
                      if parmtype==2 and err==0.2:
                          continue
                      if parmtype==3 and err==1e-4:
                          continue
                      #val /= 1e-4
                      #err /= 1e-4
                      xs.append(x)
                      vals.append(val)
                      valerrs.append(err)
                      print(key, resmap[key])
                      ientry += 1
    #if vals:
    #label = f"parmtype {parmtype}, subdet {subdet}, layer {layer}"
    #plt.title(label)
    #plt.xlabel("$Module Center \eta$")

  plot = plt.figure()        
  plt.xlabel("layer/parameter idx")
  #plt.ylabel("charge dependent correction ($\mu$m)")
  plt.title(f"parmtype {parmtype}")
  plt.errorbar(xs, vals, yerr=valerrs,xerr=0.5, fmt='none')
        
        
plt.show()
#assert(0)




#np.set_printoptions(threshold=sys.maxsize)



#print(v[:7])

#print(xout)
#ldlt = scipy.linalg.ldl(a, overwrite_a=True, check_finite=False)
#cho = scipy.linalg.cho_factor(hess, overwrite_a=True, check_finite=False)
#xout = scipy.linalg.cho_solve(cho, -grad, overwrite_b=True, check_finite=False)
#xout = scipy.linalg.lstsq(hess,-grad)

#print(grad)
#print(hess)




