import numpy as np
import romkan
import re,pickle,sys,os,imp,json,glob,datetime
from collections import defaultdict
#sys.path.append('/home/yosato/myProjects/normalise_jp')
import count_homophones,get_embeddings,do_r_text
from  pythonlib_ys import main as myModule
from pythonlib_ys import sort_large_file
imp.reload(count_homophones)
imp.reload(get_embeddings)
imp.reload(myModule)

def main(SMecabCorpusDir,HomFP,ModelPath,ModelType,Window=5,UpToPercent=None,OutDir=None):
#    HomStats,Model=load_models(HomFP,ModelFP)
    print('loading homstats...')
    HomStats=pickle.load(open(Args.homstats_fp,'br'))
    print('... loaded')
    OutFNStem=os.path.basename(SMecabCorpusDir)+'_contexts_mvecs_'
    OutJsonFN=OutFNStem+ModelType+'.json'
    PickedTokenStatsFN=OutFNStem+'pickedtokenstats.pickle'
    OutDir=OutDir if OutDir is not None else SMecabCorpusDir
    FPPair=[os.path.join(OutDir,FN) for FN in (OutJsonFN,PickedTokenStatsFN)]
    OutJsonFP=FPPair[0]

    get_homs_vecs(SMecabCorpusDir,HomStats,ModelPath,ModelType,OutJsonFP=OutJsonFP)
#    myModule.ask_filenoexist_execute(OutJsonFP,get_homs_vecs,([SMecabCorpusDir,HomStats,ModelPath,ModelType],{'OutJsonFP':OutJsonFP}))

def find_subst_matches(TgtStr,PotStrs):
    StartInd=None
    for Ind,PotStr in enumerate(PotStrs):
        if TgtStr==PotStr:
            return Ind,(PotStr,)
        elif TgtStr.startswith(PotStr):
            StartInd=Ind
            FndPotStr=PotStr
            break
    if StartInd:    
        FndPotStrs=[FndPotStr]
        for i in range(StartInd+1,len(PotStrs)):
            PotStr=PotStrs[i]
            FndStr=''.join(FndPotStrs);PotCombStrs=FndStr+PotStr,FndStr+PotStr.replace('##','')
            if TgtStr in PotCombStrs:
                FndPotStrs.append(PotStr)
                return StartInd,tuple(FndPotStrs)
            else:
                FndPotStrs.append(PotStr)
    return None 
        
            
    
def get_homs_vecs(CorpusDir,HomStats,ModelPath,ModelType,OutJsonFP,SortP=True):
    def get_write_embeddings(WdTriples,RelvInds,OutJsonFSw):
        def find_new_relvinds(RelvIndOrthPairs,NewTokens):
            IndPairs=[];Seen=set();MissedRelvOrths=set()
            for OldInd,RelvOrth in RelvIndOrthPairs:
                if RelvOrth in Seen:
                    continue
                if RelvOrth in NewTokens:
                    IndPairs.append((OldInd,NewTokens.index(RelvOrth),1))
                    Seen.add(RelvOrth)
                else:
                    Match=find_subst_matches(RelvOrth,NewTokens)
                    if Match:
                        IndPairs.append((OldInd,Match[0],len(Match[1])))
            return IndPairs

        Orths=[Wd[0] for Wd in WdTriples]
        RelvIndOrthPairs=[(OldInd,WdT[0]) for (OldInd,WdT) in enumerate(WdTriples) if OldInd in RelvInds]
        Vecs,NewTokens=get_embeddings_type(Orths)

        IndPairs=find_new_relvinds(RelvIndOrthPairs,NewTokens)
        for OldInd,NewInd,MatchLen in IndPairs:
            Pron=WdTriples[OldInd][2];Cat=WdTriples[OldInd][1]
            Vec=Vecs[NewInd] if MatchLen==1 else np.mean([Vec.detach().numpy() for Vec in Vecs[NewInd:NewInd+MatchLen]],axis=0)
            Output=[Pron+':'+Cat,NewInd,MatchLen,NewTokens,Vec.tolist()]
            OutJsonFSw.write(json.dumps(Output,ensure_ascii=False)+'\n')
        
    def check_return_wdtriples(LiNe,PercUnit,Unprocessables,PrvFinishedDT):
                if CumCntrInside!=0 and CumCntrInside%Unitile==0:
                    PercUnit+=1
                    print(str(PercUnit/(Unit/100))+'%'+' or '+str(CumCntrInside+1)+' sentences done')
                    FinishedDT=datetime.datetime.now()
                    TDelta=FinishedDT-PrvFinishedDT
                    print(TDelta)

                else:
                    FinishedDT=PrvFinishedDT

                # triple reprs of the sent    
                WdTriples=[tuple(WdTStr.split(':')) for WdTStr in LiNe.strip().split()]
                # exclude too short sentences
                if len(WdTriples)<=4:
                    return None
                # exclude non well-formed data
                BadWdTriples={WdT for WdT in WdTriples if len(WdT)!=3}
                if BadWdTriples:
                    Unprocessables.update(BadWdTriples)
                    if BadWdTriples:
                        return None
                    else:
                        WdTriples=[WdT for WdT in WdTriples if WdT not in BadWdTriples]

                return WdTriples,BadWdTriples,PercUnit,Unprocessables,FinishedDT

    def get_homonym_inds(WdTriples,SelectedTokenStats,OrthsHomStats,Unprocessables,Omits):            
                RelvInds=[]
                for Ind,WdT in enumerate(WdTriples):
                    if WdT in Unprocessables or WdT in Omits:
                        continue
                    Orth,Cat,Pron=WdT
                    # these pos's are ignored
                    if Cat in ('記号','助詞','助動詞','代名詞') or Pron=='*':
                        continue
                    if Pron in SelectedTokenStats and Orth in SelectedTokenStats[Pron] and SelectedTokenStats[Pron][Orth]>1000:
                        continue
                    # make sure it exists in the stats, should not be necessary, but it is...
                    if Orth in OrthsHomStats:
                        HomStats=OrthsHomStats[Orth]
                        # select the stats of the right pos
                        HitHomStats=[HomStat for HomStat in HomStats if HomStat.cat==Cat and HomStat.pron==Pron]
                        if len(HitHomStats)!=1:
                            Unprocessables.add(WdT)
                            continue
                        HomStat=HitHomStats[0]
                        ApproxAmbInds=approximate_ambiguity(HomStat.freqs)
                        if not (HomStat and len(ApproxAmbInds)>=2 and sum(HomStat.freqs)>500 and orth_variety_cond(HomStat,ApproxAmbInds)):
                            Omits.add(WdT)
                        else:
                            if Pron not in SelectedTokenStats:
                                SelectedTokenStats[Pron]={Orth:1}
                            elif Orth not in SelectedTokenStats[Pron]:
                                SelectedTokenStats[Pron][Orth]=1
                            else:
                                SelectedTokenStats[Pron][Orth]+=1
                            RelvInds.append(Ind)
                return RelvInds,SelectedTokenStats,Omits

            
    FPs=glob.glob(CorpusDir+'/*.mecabsimple')
    Unprocessables=set();Omits=set()
    TmpFP=OutJsonFP+'.tmp'
    OutJsonFSw=open(TmpFP,'wt')
    print('counting lines...')
    LineCnt=3951450#get_linecount0(FPs)
    print('Total line count: '+str(LineCnt))
    Unit=100
    Unitile=LineCnt//Unit
    # this is to be used to select the ones we care about, homonyms
    OrthsHomStats=homstats2orthshomstats(HomStats)
    FailedSents=[]
    if ModelType=='bert':
        from transformers import BertModel,BertTokenizer
        from torch import tensor
        BTsr=BertTokenizer.from_pretrained(ModelPath)
        BModel=BertModel.from_pretrained(ModelPath)
        get_embeddings_type=lambda Orths: get_embeddings.get_bert_embeddings(' '.join(Orths),BModel,BTsr)
    
    PercUnit=0;PrvFinishedDT=datetime.datetime.now()
    SelectedTokenStats={};CumCntr=0;Cntr=0
    for CorpusFP in FPs:
        with open(CorpusFP,'rt') as FSr:
            CumCntr+=Cntr
            for Cntr,LiNe in enumerate(FSr):
                OldLine=LiNe.strip()
                if not OldLine:
                    continue
                if len(OldLine)<400:
                    Lines=[OldLine]
                else:
                    Lines=re.split(' 、:記号:、 ',OldLine)
                for Line in Lines:
                    if len(Line)>350:
                        continue
                    LiNe=Line+'\n'
                    CumCntrInside=CumCntr+Cntr
                    Ret=check_return_wdtriples(LiNe,PercUnit,Unprocessables,PrvFinishedDT)
                    if Ret is None:
                        continue
                    else:
                        WdTriples,BadWdTriples,PercUnit,Unprocessables,FinishedDT=Ret

                # real processing starts here, first pick the relevant words
#                try:
                    RelvInds,SelectedTokenStats,Omits=get_homonym_inds(WdTriples,SelectedTokenStats,OrthsHomStats,Unprocessables,Omits)

                    if RelvInds:
                        try:
                            get_write_embeddings(WdTriples,RelvInds,OutJsonFSw)
                        except:
                            print(LiNe)
                            get_write_embeddings(WdTriples,RelvInds,OutJsonFSw)
                            
                      #  FailedSents.append(LiNe.strip())

    OutJsonFSw.close()
    myModule.dump_pickle(SelectedTokenStats,OutJsonFP+'.pickle')

    print('bulk of the processing done, now sorting')

    if SortP:
        sort_large_file.batch_sort(TmpFP,OutJsonFP)
        if os.path.getsize(TmpFP)==os.path.getsize(OutJsonFP):
            os.remove(TmpFP)
    else:
        os.rename(TmpFP,OutJsonFP)


        


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

def approximate_ambiguity(Nums,ThreshRatio=.05):
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


if __name__=='__main__':
    import argparse as ap
    Psr=ap.ArgumentParser()
    Home=os.getenv('HOME')
    Psr.add_argument('--corpus-dir',default=Home+'/processedData/bcwj/bcwj_simplemecab')
    Psr.add_argument('--homstats-fp',default=Home+'/processedData/bcwj/mecab/LBa_1--LBa_10--LBa_2--LBa_3--LBa_4--LBa_5--others.mecab_homs_plain.pickle')
    Psr.add_argument('--model-path',default=Home+'/processedData/bert/BERT-base_mecab-ipadic-bpe-32k')
    Psr.add_argument('--model-type',default='bert')
    Psr.add_argument('--up-to-percent',default=None,type=int)
    Psr.add_argument('--out-dir',default=None)
    Psr.add_argument('--text-output',default=True)
    Args=Psr.parse_args()
    AbortP=False
    if not os.path.isdir(Args.corpus_dir):
        print('corpus dir '+Args.corpus_dir+' does not exist\n')
        AbortP=True
    
    main(Args.corpus_dir,Args.homstats_fp,Args.model_path,Args.model_type,UpToPercent=Args.up_to_percent,OutDir=Args.out_dir)
