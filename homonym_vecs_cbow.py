import gensim.models
import numpy as np
import romkan
import pickle,sys,os,imp,json,glob
from collections import defaultdict
#sys.path.append('/home/yosato/myProjects/normalise_jp')
import count_homophones
from  pythonlib_ys import main as myModule
from pythonlib_ys import sort_large_file
imp.reload(count_homophones)
imp.reload(myModule)


def main(SMecabCorpusDir,HomStats,Model,ModelType='cbow',Window=5,UpToPercent=None,OutDir=None,DoRTextP=True):
    
    OutFNStem=os.path.basename(SMecabCorpusDir)+'_contexts_mvecs'
    OutFN=OutFNStem+'_'+ModelType+'.json'
    PickedTokenStatsFN=OutFNStem+'_pickedtokenstats.pickle'
    OutJsonFP,PickedTokenStatsFP=[(SMecabCorpusDir if OutDir is None else OutDir)+'/'+FN for FN in (OutFN,PickedTokenStatsFN)]
#    print('finding mean vectors for contexts...')
    myModule.ask_filenoexist_execute([OutJsonFP,PickedTokenStatsFP],get_homs_contexts_mvecs,([SMecabCorpusDir,HomStats,Model,Window],{'OutJsonFP':OutJsonFP}))
    
    if DoRTextP:
        TxtDir=os.path.join(os.path.dirname(OutJsonFP),OutFNStem+'_txtfiles')
        if not os.path.isdir(TxtDir):
            os.mkdir(TxtDir)
        SortedP=json_sorted_p(OutJsonFP)
        HomsOrthsCnts=myModule.load_pickle(PickedTokenStatsFP)
        HomsCnts=sorted([(Hom,sum(OrthsCnts.values())) for (Hom,OrthsCnts) in HomsOrthsCnts.items()])
        CntSoFar=0
        for Cntr,(Hom,Cnt) in enumerate(HomsCnts):
            if Cntr>1000:
                break
            OrthsVecs=get_hom_in_file(Hom,OutJsonFP,FstPosition=CntSoFar,AssumeSortedP=SortedP)
            RomHom=romkan.to_roma(Hom)
            OutHomFP=os.path.join(TxtDir,'homvecs_'+RomHom)
            with open(OutHomFP,'wt') as FSw:
                FSw.write(stringify_hom_vecs(OrthsVecs))
            CntSoFar+=Cnt

def jump_to_linum(FSr,LiNum):
    for Cntr,LiNe in enumerate(FSr):
        if Cntr==LiNum:
            return FSr
                        
def json_sorted_p(JsonFP,UpTo=50000):
    with open(JsonFP) as FSr:
        PrvHeader=json.loads(FSr.readline())[0]
        for Cntr,LiNe in enumerate(FSr):
            CurHeader=json.loads(LiNe)[0]
            if CurHeader==PrvHeader:
                PrvHeader=CurHeader
            else:
                if CurHeader>PrvHeader:
                    if Cntr>UpTo:
                        break
                    PrvHeader=CurHeader
                    continue
                else:
                    return False
        return True

def get_hom_in_file(TgtHom,JsonFP,UpTo=100000,FstPosition=0,AssumeSortedP=False):
    print('trying to find homs for '+TgtHom)
    Fnd=False;FndCnt=0
    OrthsVecs=defaultdict(list)
    with open(JsonFP) as FSr:
        if AssumeSortedP:
            jump_to_linum(FSr,FstPosition)
        for Cntr,LiNe in enumerate(FSr):
            if FndCnt>UpTo:
                break
            CurHom=LiNe.split(',')[0].lstrip('[').strip('"')
            if AssumeSortedP and Fnd and CurHom!=TgtHom:
                break
            if CurHom==TgtHom:
                HomVecs=json.loads(LiNe)
                FndCnt+=1
                if FndCnt%100==0:
                    print('found '+str(FndCnt)+' homs')
                if AssumeSortedP and not Fnd:
                    Fnd=True
                OrthsVecs[HomVecs[1]].append(HomVecs[3])
    return OrthsVecs            
                    
def generate_homvecs_json(FSr):
    Vecs=[]
    HomVec=json.loads(FSr.readline())
    PrvHom=HomVec[0]
    for LiNe in FSr:
        HomVec=json.loads(LiNe)
        if HomVec[0]==PrvHom:
            Vec=HomVec[2]
            Vecs.append(Vec)
        else:
            yield Vecs
            
                
def stringify_hom_vecs(OrthsVecs,UpToPerOrth=1000):
    Str=''
    for OrthCntr,(Orth,Vecs) in enumerate(OrthsVecs.items()):
        for VecCntr,Vec in enumerate(Vecs):
            if VecCntr>=UpToPerOrth:
                break
            Line=Orth+str(OrthCntr)+'_'+str(VecCntr)+'\t'+'\t'.join([str(Num) for Num in Vec])
            Str+=Line+'\n'
            
    return Str
        
                    
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

def homstats2orthshomstats(HomStats):
    OrthsHomStats=defaultdict(list)
    for HomStat in HomStats.values():
        HomStat.merge_orthidentical_subcats()
        for Orth in HomStat.subcatmerged_orths:
            OrthsHomStats[Orth].append(HomStat)
    return OrthsHomStats

def get_linecount0(FPs):
    Total=0
    for FP in FPs:
        Total+=sum(1 for i in open(FP, 'rb'))
    return Total

def get_homs_contexts_mvecs(CorpusDir,HomStats,CBowModel,Window,OutJsonFP,SortP=True):
    FPs=glob.glob(CorpusDir+'/*.mecabsimple')
    Unprocessables=set();Omits=set()
    TmpFP=OutJsonFP+'.tmp'
    OutJsonFSw=open(TmpFP,'wt')
    LineCnt=get_linecount0(FPs)
    print('Total line count: '+str(LineCnt))
    Unit=LineCnt//100
    OrthsHomStats=homstats2orthshomstats(HomStats)
    NotFounds=set();PercUnit=0;TokenCntSoFar=0
    SelectedTokenStats={}
    for CorpusFP in FPs:
        with open(CorpusFP,'rt') as FSr:
            for Cntr,LiNe in enumerate(FSr):
    #            if Cntr<1303900:
    #                continue
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
                for Ind,Wd in enumerate(Wds):
                    if Wd in Unprocessables or Wd in Omits:
                        continue
                    OrthCatPron=Wd.split(':')
                    if len(OrthCatPron)!=3:
                        print('funny wd, '+os.path.basename(CorpusFP)+':'+str(Cntr+1)+': '+Wd)
                        Unprocessables.add(Wd)
                        continue
                    Orth,Cat,Pron=OrthCatPron
                    if Cat=='記号' or Pron=='*':
                        continue
                    if Orth in OrthsHomStats:
                        HomStats=OrthsHomStats[Orth]
                        HitHomStats=[HomStat for HomStat in HomStats if HomStat.cat==Cat and HomStat.pron==Pron]
                        if len(HitHomStats)!=1:
                            Unprocessables.add(Wd)
                            continue
                        HomStat=HitHomStats[0]
                        ApproxAmbInds=approximate_ambiguity(HomStat.freqs)
                        if not (HomStat and len(ApproxAmbInds)>=2 and sum(HomStat.freqs)>500 and orth_variety_cond(HomStat,ApproxAmbInds)):
                            Omits.add(Wd)
                        else:
                            if Pron not in SelectedTokenStats:
                                SelectedTokenStats[Pron]={Orth:1}
                            elif Orth not in SelectedTokenStats[Pron]:
                                SelectedTokenStats[Pron][Orth]=1
                            else:
                                SelectedTokenStats[Pron][Orth]+=1
                            Orths=[Wd.split(':')[0] for Wd in Wds]
                            CxtWds=get_context_wds(Orths,Ind,Window)
                            MeanVec,NotFoundsJustNow=get_meanvector_when_available(CxtWds[0]+CxtWds[1],CBowModel)
                            if NotFoundsJustNow:
                                NotFounds.update(set(NotFoundsJustNow))

                            if len(NotFoundsJustNow)>TokenCntInLine/4:
                                break
                            OutJsonFSw.write(json.dumps([Pron,Orth,[CxtWds[0],CxtWds[1]],MeanVec.tolist()],ensure_ascii=False)+'\n')

    OutJsonFSw.close()
    myModule.dump_pickle(SelectedTokenStats,OutJsonFP+'.pickle')

    print('bulk of the processing done, now sorting')

    if SortP:
        sort_large_file.batch_sort(TmpFP,OutJsonFP)
        if os.path.getsize(TmpFP)==os.path.getsize(OutJsonFP):
            os.remove(TmpFP)
    else:
        os.rename(TmpFP,OutJsonFP)

    

def orth_variety_cond(HomStat,ApproxAmbInds):
    RelvHomCnt=len(ApproxAmbInds)
    if RelvHomCnt>=4:
        return True
    else:
        OrthTypesNotWanted2=[
            {frozenset({'hiragana'}),frozenset({'han'})},
                        {frozenset({'katakana'})},
            {frozenset({'hiragana'}),frozenset({'han','hiragana'})}
            ]
        OrthTypesNotWanted3=[
            {frozenset({'hiragana'}),frozenset({'han'}),frozenset({'katakana'})},
            {frozenset({'hiragana'}),frozenset({'han','hiragana'}),frozenset({'katakana'})}
        ]
        RelvOrthTypes={frozenset(OrthType) for (Ind,OrthType) in enumerate(HomStat.orthtypes) if Ind in ApproxAmbInds}
        if (RelvHomCnt==2 and RelvOrthTypes in OrthTypesNotWanted2) or (RelvHomCnt==3 and RelvOrthTypes in OrthTypesNotWanted3):
            return False
        else:
            return True
        
            
   # print('sorting the output file...')
   # sort_large_file.batch_sort(TmpFP,OutJsonFP)
   # os.remove(TmpFP)

def approximate_ambiguity(Nums,ThreshRatio=.01):
    if len(Nums)==1:
        return [0]
    TotalNum=sum(Nums)
    Thresh=TotalNum*ThreshRatio
    return [Ind for (Ind,Num) in enumerate(Nums) if Num > Thresh]
    
   
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
    Psr.add_argument('corpus_dir')
    Psr.add_argument('homstats_fp')
    Psr.add_argument('model_fp')
    Psr.add_argument('--up-to-percent',default=None,type=int)
    Psr.add_argument('--out-dir',default=None)
    Psr.add_argument('--text-output',default=False)
    Args=Psr.parse_args()
    if not os.path.isdir(Args.corpus_dir):
        sys.exit('corpus dir '+Args.corpus_dir+' does not exist\n')
    print('loading models')
    HomStats=pickle.load(open(Args.homstats_fp,'br'))
    Model=gensim.models.Word2Vec.load(Args.model_fp)
    main(Args.corpus_dir,HomStats,Model,UpToPercent=Args.up_to_percent,OutDir=Args.out_dir)
    #VecsFP=Args.corpus_fp+'.homvecs.pickle'
    #print('saving vecs in '+VecsFP)
    #myModule.dump_pickle(HomsMVecs,VecsFP)
    
    #if Args.text_output:
    #    output_text_per_hom()
