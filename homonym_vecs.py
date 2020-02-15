import gensim.models
import numpy as np
import pickle,sys,os,imp
from collections import defaultdict
sys.path.append('/home/yosato/myProjects/normalise_jp')
import count_homophones
from  pythonlib_ys import main as myModule
imp.reload(count_homophones)
imp.reload(myModule)

def context2vec(CxtVecs):
    return np.average(CxtVecs)

def list_slice_upto(List,HeadInd,TailInd=None):
    HeadInd=0 if HeadInd+1<len(List) else HeadInd
    TailInd=len(List) if TailInd is None or -TailInd+1>len(List) else TailInd
    
    return List[HeadInd:TailInd]
    

def context2vec(Wds,Ind,Window,Model):
    CxtWds=list_slice_upto(Wds,Ind-Window,Ind+Window+1)
    del CxtWds[Ind]
    return np.mean([Model.wv[Wd] for Wd in CxtWds],axis=0),CxtWds

def get_target_homophones(HomStats):
    OrthsHomStats=defaultdict(list)
    for HomStat in HomStats.values():
        HomStat.merge_orthidentical_subcats()
        if len(HomStat.subcatmerged_orths)>=2:
            for Orth in HomStat.subcatmerged_orths:
                OrthsHomStats[Orth].append(HomStat)
    return OrthsHomStats

def get_relevant_homstat(Orth,OrthsHomStats):
    if Orth not in OrthsHomStats:
        return None
    HomStats=OrthHomStats[Orth]
    if len(HomStats)>=2:
        RelvHomStat=sorted(HomStats,key=lambda HS:sum(HS.freqs),reverse=True)[0]
    else:
        RelvHomStat=HomStats[0]
    return RelvHomStat

def main(CorpusFP,HomStats,CBowModel,Window=5):
    # extract homophones on the pos level and put them in orth-based dict
    OrthsHomStats=get_target_homophones(HomStats)

    HomVecs=defaultdict(dict)
    ProbW2Vecs=defaultdict(list)
    #LineCnt=myModule.get_linecount(CorpusFP)
    LineCnt=2664239
    with open(CorpusFP) as FSr:
        for Cntr,Sent in enumerate(FSr):
            if Cntr!=0 and (Cntr+1)%100==0:
                print(str(Cntr+1)+'/'+str(LineCnt))
            Wds= Sent.split()
#            LstInd=len(Wds)-1
            
            for Ind,Orth in enumerate(Wds):

                if Orth in ProbW2Vecs:
                    continue
                # check if the word is one of the homophone targets and if so, return that homstat, if not, move to the next one
                RelvHomStat=get_relevant_homstat(Orth,OrthsHomStats)
                if not RelvHomStat:
                    continue
                # then get the average of the context vecs
                try:
                    Vec,CxtWds=context2vec(Wds,Ind,Window,CBowModel)
                except:
                    ProbW2Vecs[Orth].append(RelvHomStat)
                    continue

                HomVecs[Orth].append((Vec,CxtWds))
                    
    return HomVecs,ProbW2Vecs

if __name__=='__main__':
    import argparse as ap
    Psr=ap.ArgumentParser()
    Psr.add_argument('corpus_fp')
    Psr.add_argument('homstats_fp')
    Psr.add_argument('model_fp')
    Args=Psr.parse_args()
    HomStats=pickle.load(open(Args.homstats_fp,'br'))
    Model=gensim.models.Word2Vec.load(Args.model_fp)
    main(Args.corpus_fp,HomStats,Model)
                    
                    
