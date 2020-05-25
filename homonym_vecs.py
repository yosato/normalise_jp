import numpy as np
import romkan
import re,pickle,sys,os,imp,json,glob
from collections import defaultdict
#sys.path.append('/home/yosato/myProjects/normalise_jp')
import count_homophones,get_embeddings
from  pythonlib_ys import main as myModule
from pythonlib_ys import sort_large_file
imp.reload(count_homophones)
imp.reload(get_embeddings)
imp.reload(myModule)

def main(SMecabCorpusDir,HomFP,ModelPath,ModelType,Window=5,UpToPercent=None,OutDir=None,DoRTextP=True):
#    HomStats,Model=load_models(HomFP,ModelFP)

    HomStats=pickle.load(open(Args.homstats_fp,'br'))
    
    OutFNStem=os.path.basename(SMecabCorpusDir)+'_contexts_mvecs_'
    OutJsonFN=OutFNStem+ModelType+'.json'
    PickedTokenStatsFN=OutFNStem+'pickedtokenstats.pickle'
    OutDir=OutDir if OutDir is not None else SMecabCorpusDir
    FPPair=[os.path.join(OutDir,FN) for FN in (OutJsonFN,PickedTokenStatsFN)]
    OutJsonFP=FPPair[0]
#    print('finding mean vectors for contexts...')
    myModule.ask_filenoexist_execute(FPPair,get_homs_vecs,([SMecabCorpusDir,HomStats,ModelPath,ModelType],{'OutJsonFP':OutJsonFP}))

    if DoRTextP:
        print('We write out the results in text too...')
        output_text_per_hom(OutJsonFP)
    

def get_homs_vecs(CorpusDir,HomStats,ModelPath,ModelType,OutJsonFP,SortP=True):
    def check_return_wdtriples(LiNe,PercUnit,Unprocessables):
                if CumCntrInside!=0 and CumCntrInside%Unitile==0:
                    PercUnit+=1
                    print(str(PercUnit/(Unit/100))+'%'+' or '+str(CumCntrInside+1)+' sentences done')

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

                return WdTriples,BadWdTriples,PercUnit,Unprocessables

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
    LineCnt=3950000#get_linecount0(FPs)
    print('Total line count: '+str(LineCnt))
    Unit=1000
    Unitile=LineCnt//Unit
    # this is to be used to select the ones we care about, homonyms
    OrthsHomStats=homstats2orthshomstats(HomStats)

    if ModelType=='bert':
        from transformers import BertModel,BertTokenizer
        from torch import tensor
        BTsr=BertTokenizer.from_pretrained(ModelPath)
        BModel=BertModel.from_pretrained(ModelPath)
        get_embeddings_type=lambda Orths: get_embeddings.get_bert_embeddings(' '.join(Orths),BModel,BTsr)
    
    PercUnit=0
    SelectedTokenStats={};CumCntr=0;Cntr=0
    for CorpusFP in FPs:
        with open(CorpusFP,'rt') as FSr:
            CumCntr+=Cntr
            for Cntr,LiNe in enumerate(FSr):
                if not LiNe.strip():
                    continue
                CumCntrInside=CumCntr+Cntr
                Ret=check_return_wdtriples(LiNe,PercUnit,Unprocessables)
                if Ret is None:
                    continue
                else:
                    WdTriples,BadWdTriples,PercUnit,Unprocessables=Ret

                # real processing starts here, first pick the relevant words
#                try:
                RelvInds,SelectedTokenStats,Omits=get_homonym_inds(WdTriples,SelectedTokenStats,OrthsHomStats,Unprocessables,Omits)

                if RelvInds:
                    Orths=[WdT[0] for WdT in WdTriples]
                    Vecs=get_embeddings_type(Orths)

                    for Ind in RelvInds:
                        Pron=WdTriples[Ind][2]
                        OutJsonFSw.write(json.dumps([Pron,Ind,Orths,Vecs[Ind].tolist()],ensure_ascii=False)+'\n')

    OutJsonFSw.close()
    myModule.dump_pickle(SelectedTokenStats,OutJsonFP+'.pickle')

    print('bulk of the processing done, now sorting')

    if SortP:
        sort_large_file.batch_sort(TmpFP,OutJsonFP)
        if os.path.getsize(TmpFP)==os.path.getsize(OutJsonFP):
            os.remove(TmpFP)
    else:
        os.rename(TmpFP,OutJsonFP)


        

def output_text_per_hom(OutJsonFP,Max=3000):
        TxtDir=os.path.join(os.path.dirname(OutJsonFP),os.path.basename(OutJsonFP)+'_txt')
        if not os.path.isdir(TxtDir):
            os.mkdir(TxtDir)
        CntSoFar=0;Cntr=0
        with open(OutJsonFP) as FSr:
            #print('retrieving homvecs for '+Hom+'...')
            while FSr or Cntr<Max:
                FSr,OrthsVecs,Hom,Cnt=get_hom_in_file(FSr,OutJsonFP,FstPosition=CntSoFar)
                OrthVarCnt=len(OrthsVecs)
                if OrthVarCnt>=2 and Cnt>100:
                    print('For '+Hom+', we found '+str(OrthVarCnt)+' orths, '+str(Cnt)+' items, now writing out...')
                    RomHom=romkan.to_roma(Hom)
                    OutHomFP=os.path.join(TxtDir,'homvecs_'+RomHom)
                    with open(OutHomFP,'wt') as FSw:
                        FSw.write(stringify_hom_vecs(OrthsVecs))
                        print('... done, fp: '+OutHomFP)
                    CntSoFar+=Cnt;Cntr+=1

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

def get_hom_in_file(FSr,JsonFP,UpTo=100000,FstPosition=0,AssumeSortedP=False):
    #print('trying to find homs for '+TgtHom)
   # Fnd=False;FndCnt=0
    OrthsVecs=defaultdict(list)
 #    TgtHomRegex='["'+TgtHom
    FSr,Chunk,LineCnt,_=myModule.pop_chunk_from_stream(FSr,Pattern=',',Type='cont')
    for Line in Chunk.strip().split('\n'):
        HomVecs=json.loads(Line)
        #assert(HomVecs[0]==TgtHom)
        Orth=HomVecs[2][HomVecs[1]]
        OrthsVecs[Orth].append(HomVecs[3])
 #   print(str(Cntr+1)+' found')
    return FSr,OrthsVecs,HomVecs[0],LineCnt

                    
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
    Psr.add_argument('--corpus-dir',default='/home/yosato/processedData/bcwj/bcwj_simplemecab')
    Psr.add_argument('--homstats-fp',default='/home/yosato/processedData/bcwj/mecab/LBa_1--LBa_10--LBa_2--LBa_3--LBa_4--LBa_5--others.mecab_homs_plain.pickle')
    Psr.add_argument('--model-path',default='/home/yosato/processedData/bert/BERT-base_mecab-ipadic-bpe-32k')
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
