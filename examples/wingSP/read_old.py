import numpy as np
import pickle
import scipy.linalg

directory = "/home/ac5015/programs/FEM4INAS/Models/wingSP/Test/results_27-9-2023_10-31/"
nmodes = 53

q = np.load("%s/q_%s.npy"%(directory, nmodes))
omega = np.load("%s/Results_modes/Omega_%s.npy"%(directory, nmodes))

alpha1 = np.load("%s/Results_modes/alpha1_%s.npy"%(directory, nmodes))
alpha2 = np.load("%s/Results_modes/alpha2_%s.npy"%(directory, nmodes))
gamma1 = np.load("%s/Results_modes/gamma1_%s.npy"%(directory, nmodes))
gamma2 = np.load("%s/Results_modes/gamma2_%s.npy"%(directory, nmodes))


with open ("%s/Results_modes/Phil_%s"%(directory, nmodes), 'rb') as fp:
    [phi0l,phi1l,phi1ml,phi2l,mphi1l,cphi2xl]  = pickle.load(fp)

with open ("%s/Results_modes/Phi_%s"%(directory, nmodes), 'rb') as fp:
    [phi0,phi1,phi1m,phi2,mphi1,cphi2x]  = pickle.load(fp)

with open ("%s/Results_modes/Geometry"%(directory), 'rb') as fp:
    BeamSeg, NumNode, NumNodes, DupNodes, inverseconn  = pickle.load(fp)

with open ("%s/Sols_%s"%(directory, nmodes), 'rb') as fp:
    ra0,ra,Rab,strain,kappa  = pickle.load(fp)

Ka = np.load("../../Models/wingSP/FEM/Ka.npy")
Ma = np.load("../../Models/wingSP/FEM/Ma.npy")
w, v = scipy.linalg.eigh(Ka, Ma)

save_eigs = False
if save_eigs:
    np.save("../wingSP/FEM/Ka.npy", Ka)
    np.save("../wingSP/FEM/Ma.npy", Ma)    
    np.save("../wingSP/FEM/eigenvals.npy", w)
    np.save("../wingSP/FEM/eigenvecs.npy", v)
