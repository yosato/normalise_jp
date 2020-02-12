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
    return np.mean([Model.wv[Wd] for Wd in CxtWds],axis=0)


def main(CorpusFP,HomStats,CBowModel,Window=5):
    OrthsHomStats=defaultdict(list)
    for HomStat in HomStats.values():
        HomStat.merge_orthidentical_subcats()
        for Orth in HomStat.subcatmerged_orths:
            OrthsHomStats[Orth].append(HomStat)

    CatUnambOrthsHomStats={}; CatAmbOrthsHomStats={}
    for Orth,HomStats in OrthsHomStats.items():
        if len(HomStats)>=2:
            CatAmbOrthsHomStats[Orth]=HomStats
        else:
            CatUnambOrthsHomStats[Orth]=HomStats[0]
    HomVecs=defaultdict(dict);W2VecProbs=defaultdict(list)
    LineCnt=myModule.get_linecount(CorpusFP)
    with open(CorpusFP) as FSr:
        for Cntr,Sent in enumerate(FSr):
            if Cntr!=0 and (Cntr+1)%100==0:
                print(str(Cntr+1)+'/'+str(LineCnt))
            Wds= Sent.split()
#            LstInd=len(Wds)-1
            
            for Ind,Orth in enumerate(Wds):
                if Orth in CatAmbigOrths or Orth in W2VecProbs:
                    continue
                else:
                    if Orth in OrthsHomStats:
                        RelvHomStat=CatUnambOrthsHomStats[Orth]
                        try:
                            Vec=context2vec(Wds,Ind,Window,CBowModel)
                        except:
                            W2VecProbs[Orth].append(RelvHomStat)
                            continue

                        if Orth not in HomVecs[RelvHomStat.pron]:
                            HomVecs[RelvHomStat.pron][Orth]=[Vec]
                        else:
                            HomVecs[RelvHomStat.pron][Orth].append(Vec)
                    
    return HomVecs,Probs

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
                    
                    
