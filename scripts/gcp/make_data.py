from scipy.linalg import block_diag
from scipy.io import loadmat
import autograd.numpy as np
import ssm
import scipy.io as spio
import pickle


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

obs_dim = 137

DATA_PATH = '../../data/'
GCP_DATA_PATH = './data/'
binnedPRE = loadmat(DATA_PATH + 'binnedPBEs_PRE.mat')['binnedPBEs_PRE']
binnedRUN = loadmat(DATA_PATH + 'binnedPBEs_RUN.mat')['binnedPBEs_RUN']
binnedPOST = loadmat(DATA_PATH + 'binnedPBEs_POST.mat')['binnedPBEs_POST']

BDseqscore = loadmat(DATA_PATH + 'BayesianReplayDetection.mat')['BDseqscore']

prctilePOST = np.array(BDseqscore['POST']['data']['wPBEtimeswap']['weightedCorr']['prctilescore'])
prctilePRE = np.array(BDseqscore['PRE']['data']['wPBEtimeswap']['weightedCorr']['prctilescore'])
prctileRUN = np.array(BDseqscore['RUN']['data']['wPBEtimeswap']['weightedCorr']['prctilescore'])

lb = 95
ub = 100

restrictedDataPOST = binnedPOST[np.where(prctilePOST > lb),:]
restrictedDataPRE = binnedPRE[np.where(prctilePRE > lb),:]
restrictedDataRUN = binnedRUN[np.where(prctileRUN > lb),:]

restrictedEvents = np.concatenate((restrictedDataPRE,
                restrictedDataRUN,
                restrictedDataPOST), axis = 1).squeeze()

n_events = restrictedEvents.shape[0]
train_frac = 0.75
n_train = int(0.75*n_events)

indices = np.random.permutation(n_events)
training_idx, test_idx = indices[:n_train], indices[n_train:]
training, test = restrictedEvents[training_idx,:], restrictedEvents[test_idx,:]

y_train = np.concatenate([x[1].T.astype(np.int8) for x in training]).astype(int)
y_test = np.concatenate([x[1].T.astype(np.int8) for x in test]).astype(int)

pickle.dump([y_train, y_test], open(GCP_DATA_PATH + f'train_test_{lb}-{ub}.pkl', 'wb'))