load('binnedPBEs_POST.mat');
load('binnedPBEs_PRE.mat');
load('binnedPBEs_RUN.mat');
load('BayesianReplayDetection.mat');

thresholds = [99,98,97,95,90,85,80,70,60,50];
prctilePOST = BDseqscore.POST.data.wPBEtimeswap.weightedCorr.prctilescore;
prctileRUN = BDseqscore.RUN.data.wPBEtimeswap.weightedCorr.prctilescore;
prctilePRE = BDseqscore.PRE.data.wPBEtimeswap.weightedCorr.prctilescore;

threshold = 99;

ref_threshold = 50;

restrictedDataPOST = binnedPBEs_POST(find(prctilePOST < threshold & prctilePOST > ref_threshold ),:);
restrictedDataPRE = binnedPBEs_PRE(find(prctilePRE < threshold & prctilePRE > ref_threshold),:);
restrictedDataRUN = binnedPBEs_RUN(find(prctileRUN < threshold & prctileRUN > ref_threshold),:);

restrictedEvents.threshold = threshold;
restrictedEvents.PRE = restrictedDataPRE;
restrictedEvents.POST = restrictedDataPOST;
restrictedEvents.RUN = restrictedDataRUN;

save(sprintf('HMMtrainingReplayQuality/restricted_events_%d_to_%d.mat',ref_threshold,threshold), 'restrictedEvents');
