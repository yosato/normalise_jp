import os,sys, json,imp
import romkan
from collections import defaultdict
from pythonlib_ys import main as myModule
imp.reload(myModule)

def get_hom_in_file(FSr,JsonFP,UpTo=100000,FstPosition=0,AssumeSortedP=False):
    #print('trying to find homs for '+TgtHom)
   # Fnd=False;FndCnt=0
    OrthsVecs=defaultdict(list)
 #    TgtHomRegex='["'+TgtHom
    FSr,Chunk,LineCnt,_=myModule.pop_chunk_from_stream(FSr,Pattern=',',Type='cont')
    if not Chunk or not FSr:
        return None
    MultiToks=[]
    for Line in Chunk.strip().split('\n'):
        HomVecs=json.loads(Line)
        PronCat,Ind,Len,Toks,Vec=HomVecs
        Orth=''.join(Toks[Ind:Ind+Len])
        if Len>=2:
            MultiToks.append(Orth)
        OrthsVecs[Orth].append(Vec)
 #   print(str(Cntr+1)+' found')
    return FSr,OrthsVecs,PronCat,LineCnt,MultiToks

def output_text_per_hom(OutJsonFP,Max=3000):
    def is_of_interest(Orths):
        #Bool=True
        KanjiOnly=False
        # at least 2 variations in orth
        if len(Orths)<2:
            return False,None
        # at least two is kanji orths
        else:
            KanjiOrths=[Orth for Orth in Orths if myModule.at_least_one_of_chartypes_p(Orth,['han'])]
            if len(KanjiOrths)<2:
                return False,None
            elif len(KanjiOrths)==len(Orths):
                KanjiOnly=True
        return True, KanjiOnly
    LCnt=7900#myModule.get_linecount(OutJsonFP)
    TxtDir=os.path.join(os.path.dirname(OutJsonFP),os.path.basename(OutJsonFP)+'_txt')
    if not os.path.isdir(TxtDir):
        os.mkdir(TxtDir)
    CntSoFar=0;Cntr=0
    CntThresh=LCnt/1000
    with open(OutJsonFP) as FSr:
        #print('retrieving homvecs for '+Hom+'...')
        while FSr or Cntr<Max:
            Ret=get_hom_in_file(FSr,OutJsonFP,FstPosition=CntSoFar)
            if Ret:
                FSr,OrthsVecs,Hom,Cnt,MultiToks=Ret
            else:
                break
            #except:
            #    get_hom_in_file(FSr,OutJsonFP,FstPosition=CntSoFar)
            Orths=list(OrthsVecs.keys())
            print('For '+Hom+', we found the following orths, '+str(Cnt)+' items')
            print(Orths);print(CntThresh)
            IsOfInt,KanjiOnly=is_of_interest(Orths)
            if not(Cnt>CntThresh and len(Hom.split(':')[0])>=2 and IsOfInt):
                print('not selected for printing\n')
            else:
                print('writing out...')
                RomHom=romkan.to_roma(Hom)
                OutHomFP=os.path.join(TxtDir,'homvecs_'+RomHom)
                with open(OutHomFP,'wt') as FSw:
                    FSw.write(stringify_hom_vecs(OrthsVecs))
                    print('... done, fp: '+OutHomFP)
                if KanjiOnly:
                    RefClusterFP=OutHomFP+'.refclusters'
                    with open(RefClusterFP,'wt') as FSw:
                        FSw.write('\t'.join(get_cluster_ref(OrthsVecs)))
                CntSoFar+=Cnt;Cntr+=1
def get_cluster_ref(OrthsVecs):
    Refs=[]
    for Ind,Orth in enumerate(OrthsVecs.keys()):
        Refs.extend(list(str(Ind+1)*len(OrthsVecs[Orth])))
    return Refs
        
def stringify_hom_vecs(OrthsVecs,UpToPerOrth=1000):
    Str=''
    for OrthCntr,(Orth,Vecs) in enumerate(OrthsVecs.items()):
        for VecCntr,Vec in enumerate(Vecs):
            if VecCntr>=UpToPerOrth:
                break
            Line=Orth+str(OrthCntr)+'_'+str(VecCntr)+'\t'+'\t'.join([str(Num) for Num in Vec])
            Str+=Line+'\n'
            
    return Str

def main(FP):
    output_text_per_hom(FP)

if __name__=='__main__':
    FP=sys.argv[1]
    main(FP)
