import pickle
import ssm
import sys

it = sys.argv[1]

DATA_PATH = './data/'
DUMP_PATH = './data/fitted/'
lb = 95
ub = 100

[y_train, y_test] = pickle.load(open(DATA_PATH + f'train_test_{lb}-{ub}.pkl', 'rb'))
N = y_train.shape[1]
K = 5
D = 2

print("Fitting SLDS with Laplace-EM")
slds_lem = ssm.SLDS(N, K, D, emissions="poisson_orthog", emission_kwargs=dict(link="softplus"))
slds_lem.initialize(y_train)

q_lem_elbos, q_lem = slds_lem.fit(y_train, method="laplace_em",
                              variational_posterior="structured_meanfield",
                              num_iters=20, initialize=False, alpha=0)

pickle.dump([[q_lem_elbos, q_lem], y_train], open(DUMP_PATH + f'lem_{it}.pkl', 'wb'))