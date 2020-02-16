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

def get_context_wds(Wds,CentreInd,WindowSize):
    LeftCxtWds=Wds[:CentreInd] if CentreInd<WindowSize else Wds[CentreInd-WindowSize:CentreInd] 
    RightCxtWds=Wds[CentreInd+1:] if CentreInd+1+WindowSize>len(Wds)-1 else Wds[CentreInd+1:CentreInd+1+WindowSize]
    
    return LeftCxtWds,RightCxtWds

def get_vectors_when_available(Wds,Model):
    Vecs=[];NotFound=[]
    for Wd in Wds:
        if Wd in Model.wv:
            Vecs.append(Model.wv[Wd])
        else:
            NotFound.append(Wd)
    return Vecs,NotFound

def context2vec(Wds,Ind,Window,Model):
    CxtWds=get_context_wds(Wds,Ind,Window)
    AvailCxtWds,NotFound=get_vectors_when_available(CxtWds[0]+CxtWds[1],Model)
    return np.mean(AvailCxtWds,axis=0),CxtWds,NotFound

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
    HomStats=OrthsHomStats[Orth]
    if len(HomStats)>=2:
        RelvHomStat=sorted(HomStats,key=lambda HS:sum(HS.freqs),reverse=True)[0]
    else:
        RelvHomStat=HomStats[0]
    return RelvHomStat

def main(CorpusFP,HomStats,CBowModel,Window=5,UpToPercent=None):
    # extract homophones on the pos level and put them in orth-based dict
    OrthsHomStats=get_target_homophones(HomStats)

    HomVecs=defaultdict(dict)
    ProbW2Vecs=defaultdict(list)
    LineCnt=myModule.get_linecount(CorpusFP)
    #LineCnt=2664239
    Unit=LineCnt//100;UnitIncrement=0;NotFounds=set()
    TokenCnt=0;NotFoundTokenCnt=0
    with open(CorpusFP) as FSr:
        for Cntr,Sent in enumerate(FSr):
            if Cntr!=0 and (Cntr+1)%Unit==0:
                UnitIncrement+=1
                print(str(Cntr+1)+'/'+str(LineCnt)+'('+str(UnitIncrement)+'%)')
                if UpToPercent and UnitIncrement>=UpToPercent:
                    break
            Wds= Sent.split()
            TokenCnt+=len(Wds)
            
            for Ind,Orth in enumerate(Wds):
                if Orth in ProbW2Vecs:
                    continue
                # check if the word is one of the homophone targets and if so, return that homstat, if not, move to the next one
                RelvHomStat=get_relevant_homstat(Orth,OrthsHomStats)
                if not RelvHomStat:
                    continue
                # then get the average of the context vecs
                Vec,CxtWds,NotFoundsJustNow=context2vec(Wds,Ind,Window,CBowModel)
#                if NotFoundsJustNow:
 #                   NotFoundTokenCnt+=len(NotFoundsJustNow)
  #                  if UnitIncrement>=5:
   #                     NotFoundTokenRate=NotFoundTokenCnt/TokenCnt
    #                    if NotFoundTokenRate>.2:
     #                       break
      #              NotFounds.update(set(NotFoundsJustNow))
       #             if len(NotFoundsJustNow)/len(CxtWds)>.1:
        #                continue

                Pron=RelvHomStat.pron
                if Pron not in HomVecs:
                    HomVecs[Pron]={Orth:[(Vec,CxtWds)]}
                else:
                    if Orth not in HomVecs[Pron]:
                        HomVecs[Pron][Orth]=[(Vec,CxtWds)]
                    else:
                        HomVecs[Pron][Orth].append((Vec,CxtWds))
                    
    return HomVecs

if __name__=='__main__':
    import argparse as ap
    Psr=ap.ArgumentParser()
    Psr.add_argument('corpus_fp')
    Psr.add_argument('homstats_fp')
    Psr.add_argument('model_fp')
    Psr.add_argument('--up-to-percent',default=None,type=int)
    Args=Psr.parse_args()
    print('loading models')
    HomStats=pickle.load(open(Args.homstats_fp,'br'))
    Model=gensim.models.Word2Vec.load(Args.model_fp)
    print('finding vecs using '+Args.corpus_fp)
    HomVecs=main(Args.corpus_fp,HomStats,Model,UpToPercent=Args.up_to_percent)
    VecsFP=Args.corpus_fp+'.homvecs.pickle'
    print('saving vecs in '+VecsFP)
    myModule.dump_pickle(HomVecs,VecsFP)
                    
                    
