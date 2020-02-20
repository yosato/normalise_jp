import gensim.models
import numpy as np
import pickle,sys,os,imp,json
from collections import defaultdict
sys.path.append('/home/yosato/myProjects/normalise_jp')
import count_homophones
from  pythonlib_ys import main as myModule
imp.reload(count_homophones)
imp.reload(myModule)


def main(CorpusFP,HomStats,CBowModel,Window=5,UpToPercent=None):
    print('finding contexts...')
    JsonFP=CorpusFP+'_contexts.json'
    PronsOrthsCnts,TokenCnt,Unit=get_homs_contexts(CorpusFP,HomStats,Window,JsonFP,UpToPercent=UpToPercent)
    print('finding mean vectors for contexts...')
    HomsMVecs=get_homs_meanvecs(JsonFP,CBowModel,PronsOrthsCnts,TokenCnt,Unit)
    return HomsMVecs


def context2vec(CxtVecs):
    return np.average(CxtVecs)

def get_context_wds(Wds,CentreInd,WindowSize):
    LeftCxtWds=Wds[:CentreInd] if CentreInd<WindowSize else Wds[CentreInd-WindowSize:CentreInd] 
    RightCxtWds=Wds[CentreInd+1:] if CentreInd+1+WindowSize>len(Wds)-1 else Wds[CentreInd+1:CentreInd+1+WindowSize]
    
    return [LeftCxtWds,RightCxtWds]


def get_meanvector_when_available(Wds,Model):
    Vecs=[];NotFound=[]
    for Wd in Wds:
        if Wd in Model.wv:
            Vecs.append(Model.wv[Wd])
        else:
            NotFound.append(Wd)
    return np.mean(Vecs,axis=0),NotFound

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

def get_homs_contexts(CorpusFP,HomStats,Window,OutJsonFP,UpToPercent=None):
#    LineCnt=myModule.get_linecount(CorpusFP)
    LineCnt=2664239
    Unit=LineCnt//100;UnitIncrement=0
        # extract homophones on the pos level and put them in orth-based dict
    OrthsHomStats=get_target_homophones(HomStats)
    TokenCnt=0
    TmpFP=OutJsonFP+'.tmp'
    PronsOrthsCnts=defaultdict(dict)
    FSw=open(TmpFP,'wt')
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
                # check if the word is one of the homophone targets and if so, return that homstat, if not, move to the next one
                RelvHomStat=get_relevant_homstat(Orth,OrthsHomStats)
                if not RelvHomStat:
                    continue
                # then get the average of the context vecs
                CxtWds=get_context_wds(Wds,Ind,Window)

                Pron=RelvHomStat.pron
                FSw.write(json.dumps([Pron,Orth,CxtWds],ensure_ascii=False)+'\n')
                if Pron not in PronsOrthsCnts:
                    PronsOrthsCnts[Pron]={Orth:1}
                else:
                    if Orth not in PronsOrthsCnts[Pron]:
                        PronsOrthsCnts[Pron][Orth]=1
                    else:
                        PronsOrthsCnts[Pron][Orth]+=1                
    FSw.close()

    return PronsOrthsCnts, TokenCnt, Unit

def get_homs_meanvecs(InJsonFP,CBowModel,PronsOrthsCnts, TokenCnt,Unit):
    HomsMVecs=defaultdict(dict)
    NotFounds=set();PercUnit=0
    with open(InJsonFP,'rt') as FSr:
        for Cntr,LiNe in enumerate(FSr):
            if Cntr!=0 and Cntr%Unit==0:
                PercUnit+=1
                print(str(Cntr+1)+' or '+str(PercUnit)+'% done')
            Pron,Orth,CxtWds=json.loads(LiNe)
            OrthsCnts=PronsOrthsCnts[Pron]
            if len(OrthsCnts)>=2 and sum(OrthsCnts.values())>=30:
                MeanVec,NotFoundsJustNow=get_meanvector_when_available(CxtWds[0]+CxtWds[1],CBowModel)
                if NotFoundsJustNow:
                # NotFoundTokenCnt+=len(NotFoundsJustNow)
                  #  if UnitIncrement>=5:
                   #     NotFoundTokenRate=NotFoundTokenCnt/TokenCnt
                    #    if NotFoundTokenRate>.2:
                     #       break
                    NotFounds.update(set(NotFoundsJustNow))
                    #if len(NotFoundsJustNow)/len(CxtWds)>.1:
                
                if Pron not in HomsMVecs:
                    HomsMVecs[Pron]={Orth:[MeanVec]}
                else:
                    if Orth not in HomsMVecs[Pron]:
                        HomsMVecs[Pron][Orth]=[MeanVec]
                    else:
                        HomsMVecs[Pron][Orth].append(MeanVec)
                    
    return HomsMVecs

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
    HomVecs=main(Args.corpus_fp,HomStats,Model,UpToPercent=Args.up_to_percent)
    VecsFP=Args.corpus_fp+'.homvecs.pickle'
    print('saving vecs in '+VecsFP)
    myModule.dump_pickle(HomVecs,VecsFP)
                    
                    
