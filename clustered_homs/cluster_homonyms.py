from matplotlib import pyplot as plt
import homonym_vecs
import os,sys,json,pickle
import numpy as np
from pythonlib_ys import main as myModule

from scipy.cluster import hierarchy as hc
from scipy.cluster.hierarchy import cophenet
from scipy.spatial.distance import pdist

def main(HomsMVecsPath,UpTo=float('inf')):
    HomsMVecs=pickle.load(open(HomsMVecsPath,'br'))
    OutPath=os.path.splitext(HomsMVecsPath)[0]+'_clusters.pickle'
    ClusterSets,_=myModule.ask_filenoexist_execute_pickle(OutPath,cluster_homs,([HomsMVecs],{'UpTo':UpTo}))
    evaluate_clusters(ClusterSets,HomsMVecs,OutDir=os.path.dirname(OutPath))
    

def cluster_homs(HomsMVecs,UpTo=float('inf')):
    ClusterSets={}
    for HomCntr,(Hom,OrthsMVecs) in enumerate(HomsMVecs.items()):
        if HomCntr>UpTo:
            break
        OrthsCnts={Orth:len(MVecs) for (Orth,MVecs) in OrthsMVecs.items()}
        print(OrthsCnts)
        Len=sum(OrthsCnts.values())
        if Len<10 or Len>1000:
            print('too little or too much not doing them')
            continue
        Vecs=myModule.flatten_list(OrthsMVecs.values())
        Clusters=cluster_vecs(Vecs)
        ClusterSets[Hom]=Clusters
    return ClusterSets
    
        

def evaluate_clusters(ClusterSets,HomsMVecs,OutDir):
    for Hom,Clusters in ClusterSets.items():
        OrthsMVecs=HomsMVecs[Hom]
        OrthsCnts={Orth:len(MVecs) for (Orth,MVecs) in OrthsMVecs.items()}
        Indices=[];PrvCnt=None
        for Ind,(Orth,Cnt) in enumerate(OrthsCnts.items()):
            StartInd=Ind if Ind==0 else PrvCnt-1
                
            Indices.append(list(range(StartInd,StartInd+Cnt)))
            PrvCnt=Cnt
        plt.figure(figsize=(25, 10))
        plt.title(repr(OrthsCnts))
        hc.dendrogram(
           Clusters,
           leaf_rotation=90.,  # rotates the x axis labels
           leaf_font_size=8.,  # font size for the x axis labels
        )
        plt.savefig(os.path.join(OutDir,repr(OrthsCnts)+'.png'))
        plt.close()


def cluster_vecs(Vecs):
    Clusters=hc.linkage(Vecs,'ward')
    hello=cophenet(Clusters,pdist(Vecs))
    return Clusters


if __name__=='__main__':
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('homsmvecs_path')
    Psr.add_argument('--up-to',type=float,default=float('inf'))
    Args=Psr.parse_args()

    main(Args.homsmvecs_path,UpTo=Args.up_to)
        
        
