import homonym_vecs
import os,sys
import numpy as np

from scipy.cluster import hierarchy as cluster

def main(HomsMVecs):
    for Hom,OrthsMVecs in HomsMVecs.items():
        Clusters=cluster_vecs(OrthsMVecs.values())
        ClusterSets.append(Clusters)
    return ClusterSets

def cluster_homonyms(Vecs):
    cluster.linkage('ward')


if __name__=='__main__':
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('homsmvecs_path')
    Args=Psr.parse_args()
    
    main(Args.homsvecs_path)
        
        
