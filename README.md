# hippo
Using state space models on neural spiking data in the hippocampus

Hi there! This is the repository for all of my work on analysis of neural spiking data in the hippocampus using state-space time series models.
In particular, I use a great python library from Scott Linderman designed for the analysis of this kind of data.

My work, in particular, focuses on goodness-of-fit of the state-space models to hippocampus spiking data via residual analysis (see the `notebooks/` folder),
as well as some EDA and exploration of the sequences predicted by these state-space models using the `TraMineR` package (see `r-notebooks/`). Lastly, I wanted
to try out training multiple copies of these models simultaneously in the cloud, to cut down on time of training, so the `scripts/` folder contains some scripts
to automate this high-throughput training process on GCP.
