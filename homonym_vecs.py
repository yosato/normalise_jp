import gensim.models
import numpy as np
import pickle,sys,os,imp,json
from collections import defaultdict
sys.path.append('/home/yosato/myProjects/normalise_jp')
import count_homophones
from  pythonlib_ys import main as myModule
imp.reload(count_homophones)
imp.reload(myModule)


def main(CorpusFP,HomStats,CBowModel,Window=5,UpToPercent=None,OutDir=None,DoRTextP=True):
    print('getting global counts...')
    StatsFP=CorpusFP+'_stats.pickle'
    PronsOrthsCnts,_=myModule.ask_filenoexist_execute_pickle(StatsFP,get_global_stats,([CorpusFP,HomStats],{}))
    OrthsHomCnts,SortedHoms,TokenCnt=filter_global_stats(PronsOrthsCnts)
    OutFN=os.path.basename(CorpusFP)+'_contexts_mvecs.json'
    OutJsonFP=os.path.dirname(CorpusFP)+'/'+OutFN if OutDir is None else os.path.join(OutDir,OutFN)
    print('finding mean vectors for contexts...')
    myModule.ask_filenoexist_execute(OutJsonFP,get_homs_contexts_mvecs,([CorpusFP,OrthsHomCnts,TokenCnt,CBowModel,Window,OutJsonFP],{}))
    
    if DoRTextP:
        get_homs_in_files(SortedHoms,OutJsonFP)

def get_homs_in_files(SortedHoms,JsonFP,UpTo=100):
    for Cntr,Hom in enumerate(Sortedhoms):
        if Cntr>UpTo:
            break
        else:
            OutFP=''
            open(OutFP,'wt').write(get_hom_in_string(Hom,JsonFP,OutFP))
    
            
        
        
def filter_global_stats(PronsOrthsCnts,OrthVar=2,HomCntLowerBound=400,HomCntUpperBound=10000):
    OrthsHomCnts=defaultdict(list);Homs=set();Orths=set();TokenCnt=0
    for Hom,OrthsCnts in PronsOrthsCnts.items():
        if len(OrthsCnts)==1:
            continue
        HomTotalCnt=sum(OrthsCnts.values())
        if HomTotalCnt<HomCntLowerBound or HomTotalCnt>HomCntUpperBound:
            continue
        TokenCnt+=HomTotalCnt
        Homs.add(Hom)
        for Orth in OrthsCnts.keys():
            OrthsHomCnts[Orth]=[Hom,OrthsCnts[Orth],HomTotalCnt]

    return OrthsHomCnts,sorted(Homs),TokenCnt
                    
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

def get_global_stats(CorpusFP,HomStats):
#    LineCnt=myModule.get_linecount(CorpusFP)
    LineCnt=3500000
    Unit=LineCnt//100;UnitIncrement=0
        # extract homophones on the pos level and put them in orth-based dict
    OrthsHomStats=get_target_homophones(HomStats)
    TokenCnt=0
    PronsOrthsCnts=defaultdict(dict)
    with open(CorpusFP) as FSr:
        for Cntr,Sent in enumerate(FSr):
            if Cntr!=0 and (Cntr+1)%Unit==0:
                UnitIncrement+=1
                print(str(Cntr+1)+'/'+str(LineCnt)+'('+str(UnitIncrement)+'%)')

            Wds= Sent.split()
            TokenCnt+=len(Wds)
            
            for Ind,Orth in enumerate(Wds):
                # check if the word is one of the homophone targets and if so, return that homstat, if not, move to the next one
                RelvHomStat=get_relevant_homstat(Orth,OrthsHomStats)
                if not RelvHomStat:
                    continue
                # then get the average of the context vecs

                Pron=RelvHomStat.pron

                if Pron not in PronsOrthsCnts:
                    PronsOrthsCnts[Pron]={Orth:1}
                else:
                    if Orth not in PronsOrthsCnts[Pron]:
                        PronsOrthsCnts[Pron][Orth]=1
                    else:
                        PronsOrthsCnts[Pron][Orth]+=1

    return PronsOrthsCnts

def get_homs_contexts_mvecs(CorpusFP,OrthsHomCnts,TotalTokenCnt,CBowModel,Window,OutJsonFP):
    LineCnt=myModule.get_linecount(CorpusFP)
    Unit=LineCnt//100

    OutJsonFSw=open(OutJsonFP+'.tmp','wt')
    NotFounds=set();PercUnit=0;TokenCntSoFar=0
    with open(CorpusFP,'rt') as FSr:
        for Cntr,LiNe in enumerate(FSr):
            if not LiNe.strip():
                continue
            if Cntr!=0 and Cntr%Unit==0:
                PercUnit+=1
                print(str(Cntr+1)+' or '+str(PercUnit)+'% done')

            Wds=LiNe.strip().split()
            TokenCntInLine=len(Wds)
            TokenCntSoFar+=TokenCntInLine
            if TokenCntInLine<10:
                continue
            for Ind,Orth in enumerate(Wds):
                if Orth in OrthsHomCnts:
                    CxtWds=get_context_wds(Wds,Ind,Window)
                    MeanVec,NotFoundsJustNow=get_meanvector_when_available(CxtWds[0]+CxtWds[1],CBowModel)
                    OutJsonFSw.write(json.dumps([Orth,OrthsHomCnts[Orth][0],[CxtWds[0],CxtWds[1]],MeanVec.tolist()],ensure_ascii=False)+'\n')
                    if NotFoundsJustNow:
                # NotFoundTokenCnt+=len(NotFoundsJustNow)
                  #  if UnitIncrement>=5:
                   #     NotFoundTokenRate=NotFoundTokenCnt/TokenCnt
                    #    if NotFoundTokenRate>.2:
                     #       break
                        NotFounds.update(set(NotFoundsJustNow))
                    #if len(NotFoundsJustNow)/len(CxtWds)>.1:
                

    OutJsonFSw.close()
def remove_outliers(OrthsVecs):
    
    OrthsVecsMags=sorted([(Orth,Vec,np.linalg.norm(Vec)) for (Orth,Vec) in OrthsVecs.items()],key=lambda x:x[2])
    Len=len(OrthsVecsMags)
    ReduceMargin=Len//2
    RedOrthsVecsMags=OrthsVecsMags[ReduceMargin:-ReduceMargin]
    return {Orth:Vec for (Orth,Vec,_) in OrthsVecsMags}

def output_text_per_hom(HomsMVecs):
    FilteredHomsMVecs={}
    for Hom,OrthsMVecs in HomsMVecs.items():
        InstanceCnt=sum([len(VecSet) for VecSet in OrthsMVecs.values()])
        if len(OrthsMVecs)>=2 and InstanceCnt>=50:
            if InstanceCnt>1000:
                OrthsMVecs=remove_outliers(OrthsMVecs)
            for Orths,MVecs in OrthsMVecs.items():
                for Cntr,MVec in enumerate(MVecs):
                    FilteredHomsMVecs[Hom+str(Cntr)]=MVec


if __name__=='__main__':
    import argparse as ap
    Psr=ap.ArgumentParser()
    Psr.add_argument('corpus_fp')
    Psr.add_argument('homstats_fp')
    Psr.add_argument('model_fp')
    Psr.add_argument('--up-to-percent',default=None,type=int)
    Psr.add_argument('--out-dir',default=None)
    Psr.add_argument('--text-output',default=False)
    Args=Psr.parse_args()
    if not os.path.isfile(Args.corpus_fp):
        sys.exit('corpus file '+Args.corpus_fp+' does not exist\n')
    print('loading models')
    HomStats=pickle.load(open(Args.homstats_fp,'br'))
    Model=gensim.models.Word2Vec.load(Args.model_fp)
    main(Args.corpus_fp,HomStats,Model,UpToPercent=Args.up_to_percent,OutDir=Args.out_dir)
    #VecsFP=Args.corpus_fp+'.homvecs.pickle'
    #print('saving vecs in '+VecsFP)
    #myModule.dump_pickle(HomsMVecs,VecsFP)
    
    #if Args.text_output:
    #    output_text_per_hom()

