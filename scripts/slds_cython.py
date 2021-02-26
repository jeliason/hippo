from scipy.linalg import block_diag
from scipy.io import loadmat
import autograd.numpy as np
import ssm
import scipy.io as spio


def loadmat(filename):
    '''
    this function should be called instead of direct spio.loadmat
    as it cures the problem of not properly recovering python dictionaries
    from mat files. It calls the function check keys to cure all entries
    which are still mat-objects
    '''
    def _check_keys(d):
        '''
        checks if entries in dictionary are mat-objects. If yes
        todict is called to change them to nested dictionaries
        '''
        for key in d:
            if isinstance(d[key], spio.matlab.mio5_params.mat_struct):
                d[key] = _todict(d[key])
        return d

    def _todict(matobj):
        '''
        A recursive function which constructs from matobjects nested dictionaries
        '''
        d = {}
        for strg in matobj._fieldnames:
            elem = matobj.__dict__[strg]
            if isinstance(elem, spio.matlab.mio5_params.mat_struct):
                d[strg] = _todict(elem)
            elif isinstance(elem, np.ndarray):
                d[strg] = _tolist(elem)
            else:
                d[strg] = elem
        return d

    def _tolist(ndarray):
        '''
        A recursive function which constructs lists from cellarrays
        (which are loaded as numpy ndarrays), recursing into the elements
        if they contain matobjects.
        '''
        elem_list = []
        for sub_elem in ndarray:
            if isinstance(sub_elem, spio.matlab.mio5_params.mat_struct):
                elem_list.append(_todict(sub_elem))
            elif isinstance(sub_elem, np.ndarray):
                elem_list.append(_tolist(sub_elem))
            else:
                elem_list.append(sub_elem)
        return elem_list
    data = spio.loadmat(filename, struct_as_record=False, squeeze_me=True)
    return _check_keys(data)


num_states = 30
obs_dim = 137

DATA_PATH = '../'
binnedPRE = loadmat(DATA_PATH + 'binnedPBEs_PRE.mat')['binnedPBEs_PRE']
binnedRUN = loadmat(DATA_PATH + 'binnedPBEs_RUN.mat')['binnedPBEs_RUN']
binnedPOST = loadmat(DATA_PATH + 'binnedPBEs_POST.mat')['binnedPBEs_POST']

BDseqscore = loadmat(DATA_PATH + 'BayesianReplayDetection.mat')['BDseqscore']

prctilePOST = np.array(BDseqscore['POST']['data']['wPBEtimeswap']['weightedCorr']['prctilescore'])
prctilePRE = np.array(BDseqscore['PRE']['data']['wPBEtimeswap']['weightedCorr']['prctilescore'])
prctileRUN = np.array(BDseqscore['RUN']['data']['wPBEtimeswap']['weightedCorr']['prctilescore'])
del BDseqscore

thresholds = [99,98,97,95,90,85,80,70,60,50]

# test set creation
threshold = 50
testDataFrac = 0.25
restrictedDataPOST = binnedPOST[np.where(prctilePOST < threshold),:]
restrictedDataPRE = binnedPRE[np.where(prctilePRE < threshold),:]
restrictedDataRUN = binnedRUN[np.where(prctileRUN < threshold),:]

restrictedEvents = np.concatenate((restrictedDataPRE,
                    restrictedDataRUN,
                    restrictedDataPOST), axis = 1).squeeze()

ref50Indices = restrictedEvents[:,2]
numTest = int(restrictedEvents.shape[0]*testDataFrac)
testPBEIndices = np.random.choice(ref50Indices, numTest)


testIndices = testPBEIndices[np.where(np.isin(testPBEIndices, restrictedEvents[:,2]))].astype('uint8')
testData = restrictedEvents[testIndices,:]

threshold = 50

restrictedDataPOST = binnedPOST[np.where(prctilePOST < threshold),:]
restrictedDataPRE = binnedPRE[np.where(prctilePRE < threshold),:]
restrictedDataRUN = binnedRUN[np.where(prctileRUN < threshold),:]

restrictedEvents = np.concatenate((restrictedDataPRE,
                restrictedDataRUN,
                restrictedDataPOST), axis = 1).squeeze()

testIndices = np.where(~np.isin(restrictedEvents[:,2], testPBEIndices))[0]
restrictedEvents = restrictedEvents[testIndices,:]
trainPBEIndices = restrictedEvents[:,2]

numPBEs = restrictedEvents.shape[0]               
numTrain = int((1-testDataFrac)*numPBEs)
trainData = restrictedEvents[:numTrain]

d = np.concatenate([x[1].T.astype(np.int8) for x in trainData]).astype(int)


y = d
N = obs_dim
K = 5
D = 2

print("Fitting SLDS with Laplace-EM")
slds_lem = ssm.SLDS(N, K, D, emissions="poisson_orthog", emission_kwargs=dict(link="softplus"))
slds_lem.initialize(y)

q_lem_elbos, q_lem = slds_lem.fit(y, method="laplace_em",
                              variational_posterior="structured_meanfield",
                              num_iters=20, initialize=False, alpha=0)
q_lem_x = q_lem.mean_continuous_states[0]

# Find the permutation that matches the true and inferred states
q_lem_z = slds_lem.most_likely_states(q_lem_x, y)

# Smooth the data under the variational posterior
q_lem_y = slds_lem.smooth(q_lem_x, y)