import os,sys,imp,time,romkan,copy,re,functools,itertools
from collections import OrderedDict
from collections import defaultdict
#from mecabtools import mecabtools
#imp.reload(mecabtools)

from pdb import set_trace

from pythonlib_ys import main as myModule
from pythonlib_ys import jp_morph

imp.reload(myModule)
from mecabtools import mecabtools
imp.reload(mecabtools)
from probability import probability
imp.reload(probability)

def main0(LexFPs,MecabCorpusFPs,CorpusOnly=False,FreqWdFP=None,UnnormalisableMarkP=True,ProbExemplarFP=None,OutFP=None,Fts=None,Debug=0):
    for FP in (FreqWdFP,ProbExemplarFP):
        if FP is not None and not os.path.isfile(FreqWdFP):
            sys.exit(FP+' does not exist\n')
            
    LexDir=os.path.dirname(LexFPs[0])
    RelvFts=('cat','subcat','subcat2','sem','infform','infpat','pronunciation')
    ProbExemplars=get_exemplars(ProbExemplarFP) if ProbExemplarFP else None
    Frequents=collect_freq_wds(FreqWdFP,1000) if FreqWdFP else set()
    OutFPStem=LexDir+'/'+'--'.join([os.path.basename(LexFP) for LexFP in LexFPs])
    OutFPStem=OutFPStem.replace('rawData','processedData')
    HClusters,_=myModule.ask_filenoexist_execute_pickle(OutFPStem+'.pickle',get_clustered_homs,([LexFPs,RelvFts],{'Frequents':Frequents,'ProbExemplars':ProbExemplars,'Debug':Debug}),TO=5)
    if Debug:
        print_clustered_homs(HClusters,OutFP=os.path.join(LexDir,'exemplarless_clusters.txt'),Debug=Debug)
    LexFPs=[] if CorpusOnly else LexFPs
    for MecabFile,CorpusOrDic in [(LexFP,'dic') for LexFP in LexFPs]+[(MecabCorpusFP,'corpus') for MecabCorpusFP in MecabCorpusFPs]:
        sys.stderr.write('\n\nNormalising a '+CorpusOrDic+' '+MecabFile+'\n')
        #time.sleep(2)
        FN=os.path.basename(MecabFile)
        NewFN=myModule.change_stem(FN,'.normed')
        NewDir=os.path.join(os.path.dirname(MecabFile),'normed')
        if not os.path.isdir(NewDir):
            os.makedirs(NewDir)
        if OutFP:
            OutFP=OutFP
        else:
            OutFP=os.path.join(NewDir,NewFN)
        OutFP=OutFP+'.tmp'
            
        normalise_mecabfile(MecabFile,RelvFts,HClusters,Fts=Fts,OutFP=OutFP,CorpusOrDic=CorpusOrDic,UnnormalisableMarkP=UnnormalisableMarkP,Debug=Debug)
        os.rename(OutFP,re.sub(r'\.tmp$','',OutFP))


def print_clustered_homs(ClusteredHs,OutFP=None,Debug=0):
    Out=open(OutFP,'wt') if OutFP else sys.stdout
    for ClusteredH in ClusteredHs:
        if Debug<2:
            Out.write(ClusteredH.show_summary()+'\n\n')
    if OutFP:
        Out.close()

def get_exemplars(ExemplarFP):
    WdsReprs={}
    with open(ExemplarFP) as FSr:
        for LiNe in FSr:
            if LiNe:
                KanaRepr=LiNe.strip().split()
                if len(KanaRepr)==2:
                    Wd,Repr=KanaRepr[0],KanaRepr[1]
                    WdsReprs[Wd]=Repr
    return WdsReprs

def upto_char(Str,Chars):
    Substr=''
    for Char in Str:
        if Char in Chars:
            break
        else:
            Substr+=Char
    return Substr

def normalise_mecabfile(FP,RelvFts,ClusteredHs,OutFP=None,RelvFtCnt=7,CorpusOrDic='corpus',Format='corpus',KanaOnly=True,UnnormalisableMarkP=True,Fts=None,Debug=0):
    # outfp could be none, true or string
    if not OutFP:
        Out=sys.stdout
    else:
        if OutFP is True:
            TmpOutFP=FP+'.normed.tmp'
        else:
            TmpOutFP=OutFP+'.tmp'
        Out=open(TmpOutFP,'wt')

    AlreadyNormedCommonFtsVals=[]
    #MSs,Consts=None,myModule.prepare_progressconsts(FP)
    FSr=open(FP)
#    ClusteredHDic={tuple(ClusterH.cluster_on):ClusterH for ClusterH in ClusteredHs}
    RelvFtsVals=[Cluster.cluster_on for Cluster in ClusteredHs]
    ExclCats=('助詞','動詞活用語尾')
    #PronOnly={ Key[-1] for Key in ClusteredHDic.keys() }
    for Cntr,LiNe in enumerate(FSr):
        if Debug:
            if LiNe!='EOS\n':
                sys.stderr.write('Line '+str(Cntr+1)+': '+LiNe)
     #   if Cntr+1%1000==0:
      #      MSs=myModule.progress_counter(MSs,Cntr,Consts)
        if not LiNe.strip():
            continue
        if CorpusOrDic=='corpus' and LiNe=='EOS\n':
            AsItIs=True
        elif KanaOnly and not myModule.all_of_chartypes_p(upto_char(LiNe,[',','\t']),['hiragana','katakana','roman']):
            AsItIs=True
        else:
            CommonFtsVals={}
            Tuple=tuple(mecabtools.pick_feats_fromline(LiNe,RelvFts,Fts=Fts,CorpusOrDic=CorpusOrDic))
            CommonFtsVals.update(Tuple)
            # excluding symbols and unknowns
            if CorpusOrDic=='corpus' and (CommonFtsVals['cat'] in ExclCats or len(CommonFtsVals)<RelvFtCnt):
                AsItIs=True
            else:
                if CommonFtsVals in RelvFtsVals:
                    AsItIs=False
                else:
                    AsItIs=True
        if AsItIs:
            ToWrite=LiNe
        else:
            # !!! THE CASE FOR NORMALISATION
            if Debug>=1:
                print('\nLikely normalisable cand')

            # for dic, don't repeat
            if CorpusOrDic=='dic' and CommonFtsVals in AlreadyNormedCommonFtsVals:
                ToWrite=''
            else:
                OrgOrth=LiNe.split('\t')[0]
                # pick the right cluster
                ClusteredH=next(Cluster for Cluster in ClusteredHs if Cluster.cluster_on==CommonFtsVals)
                if len(ClusteredH.represent_wds)==1:
                    NormTypeStr='uniqueness' if not ClusteredH.exemplar else 'exemplar'
                    NormalisedWd=ClusteredH.represent_wds[0]
                    ToWrite=NormalisedWd.get_mecabline(CorpusOrDic=Format)+'\tNORMALISED by '+NormTypeStr+'from '+OrgOrth+'\n'
                    if CorpusOrDic=='dic':
                        AlreadyNormedCommonFtsVals.append(CommonFtsVals)
                else:
                    if CorpusOrDic=='corpus' and UnnormalisableMarkP:
                        ToWrite='('+';'.join([KanjiWd.orth for KanjiWd in ClusteredH.kanji_tops])+')\t'+LiNe.strip().split('\t')[1]+'\tAMBIGUOUS '+OrgOrth+'\n'
                    else:
                        ToWrite=LiNe
            if Debug:    sys.stderr.write('after normalisation: '+ToWrite)
        Out.write(ToWrite)
        
    FSr.close()
    if OutFP:
        Out.close()
        os.rename(TmpOutFP,OutFP)

def get_clustered_homs(LexFPs,*Args,**KWArgs):
    ClusteredH=[]
    for LexFP in LexFPs:
        if KWArgs['Debug']:
            sys.stderr.write('\n\nfinding homonym clusters with the lexicon '+LexFP+'\n\n')
        ClusteredH.extend(get_clustered_homs_file(LexFP,*Args,**KWArgs))
    return ClusteredH
        
def get_clustered_homs_file(LexFP,RelvFts,Frequents=set(),ProbExemplars={},OutFP=None,Debug=0):
    RelvInds=mecabtools.fts2inds(RelvFts,CorpusOrDic='dic')
    if Debug:
        print('doing the raw clustering')
    FtLines={ Ft:Lines for (Ft,Lines) in mecabtools.cluster_samefeat_lines(LexFP,RelvInds).items() if len(Lines)>=2 and Ft[-1]!='*' }

    ClusteredHs=[]
    MSs,Consts=None,myModule.prepare_progressconsts(FtLines)
    for Cntr,(FtSet,Lines) in enumerate(FtLines.items()):
        if Debug and Cntr+1%100==0:
            MSs=myModule.prepare_progressconsts(MSs,Cntr,Consts)
        MWds=[]
        for Line in Lines:
            MWd= mecabtools.mecabline2mecabwd(Line,CorpusOrDic='dic')
            #MWd.summary()
            MWds.append(MWd)
        if MWd.cat!='名詞' and not any(MWd.lemma in Frequents for MWd in MWds):
            continue
        #FtSetLabeled=list(zip(RelvFts,FtSet))
        if (Debug==1 and Cntr%50==0) or Debug>=2 :
            sys.stderr.write(' '.join([MWd.orth for MWd in MWds])+'\n')
        try:
            myCHs=ClusteredHomonyms(MWds,RelvFts,ExemplarDict=ProbExemplars)
        except:
            ClusteredHomonyms(MWds,RelvFts,ExemplarDict=ProbExemplars)
        ClusteredHs.append(myCHs)
    return ClusteredHs

    
def collect_freq_wds(FreqWdFP,RankUpTo,HiraganaOnly=False):
    Wds=set()
    with open(FreqWdFP) as FSr:
        for Cntr,LiNe in enumerate(FSr):
            if Cntr==RankUpTo-1:
                break
            Wd=LiNe.strip().strip().split()[-1]
            if HiraganaOnly:
                if myModule.all_of_chartypes_p(Wd,['hiragana']):
                    Wds.add(Wd)
            else: 
                Wds.add(Wd)
    return Wds
    
    
class ClusteredHomonyms:
    def __init__(self,MecabWds,FtsToClusterOn,ExemplarDict={}):
        if self.homonymity_check(MecabWds):
            ClusterOn={}
            for Wd in MecabWds:
                FtsVals=tuple([(Ft,Wd.__dict__[Ft]) for Ft in FtsToClusterOn])
                ClusterOn.update(FtsVals)
            # cluster_on is a dict    
            self.cluster_on=ClusterOn
            self.hiragana_rendering=jp_morph.kana2kana(self.cluster_on['pronunciation'])
            self.cluster_str=','.join([Val for (_,Val) in self.cluster_on.items() ])
            self.all_words=MecabWds
            (KanaC,KanjiCs)=self.cluster_homonyms(self.all_words)
            self.kana_cluster=KanaC
            self.kana_lemma='unknown' if not self.kana_cluster else self.kana_cluster[0].lemma
            self.kanji_clusters=KanjiCs
            self.kanji_tops=[KanjiC[0] for KanjiC in self.kanji_clusters]
            # exemplar is dynamically set with set_exemplar
            #self.exemplar=self.set_exemplar(Exemplars) if Exemplars else None
            #self.interkanji_dist=InterkanjiDist
            self.exemplar=False
            ReprType,ReprWds=self.pick_representative(ExemplarDict)
            self.represent_wds=ReprWds
            self.represent_type=ReprType

        else:
            self.homonymity_check(MecabWds)
            sys.exit('\nhomonimity violated\n')

    def special_kana_exemplar_p(self):
        # いる　なる　やる　ある only for now
        Specials={'いる':{'infpat':'一段'},'なる':{'cat':'動詞'},'やる':{'cat':'動詞'},'ある':{'cat':'動詞'}}
        Bool=False
        if self.kana_lemma in Specials.keys():
            FtValPairs=Specials[self.kana_lemma]
            if all(self.represent_wds[0].__dict__[Ft]==Val for (Ft,Val) in FtValPairs.items()):
                Bool=True
                
        return Bool
            

    def pick_representative(self,ExemplarDict={}):
        if not (self.kana_cluster or self.kanji_clusters):
            sys.exit('something is wrong, no cluster content')
        else:
            # first, if there's an exemplar, return it
            ExemplarP=False
            if ExemplarDict and self.kana_lemma in ExemplarDict.keys():
                ExemplarStr=ExemplarDict[self.kana_lemma]
                Exemplars=[Wd for Wd in self.all_words if Wd.lemma==ExemplarStr]
                if Exemplars:
                    ExemplarP=True

            if ExemplarP:
                Exemplar=Exemplars[0]
                Type='kana' if Exemplar else 'kanji'
                self.exemplar=True
                return Type, [Exemplar]
            # either kana or kanji clusters is empty, pick the top of the non-empty ones
            else:
                if not self.kana_cluster or not self.kanji_clusters:
                    return ('kana',[self.kana_cluster[0]]) if self.kana_cluster else ('kanji', [Cluster[0] for Cluster in self.kanji_clusters])

                elif len(self.kanji_clusters)>=2:
                    return 'kanji', [Cluster[0] for Cluster in self.kanji_clusters]
            
                else:
                    #set_trace()
                    KanaWd=self.kana_cluster[0]
                    KanjiTopWd=self.kanji_clusters[0][0]
                    (MoreCostly,LessCostly),IndexHigher,Rate=larger_smaller(KanaWd,KanjiTopWd,Lambda=lambda x:x.costs[-1])
                    if IndexHigher==1 and Rate<0.7:
                        Type='kana'; Wd=KanaWd
                    else:
                        Type='kanji'; Wd=KanjiTopWd
                    return Type, [Wd]
#                else:
 #                   if not self.kanji_clusters:
  #                      return 'kana',[jp_morph.pick_highest_charrate(self.kana_cluster,['hiragana'])[0]]
   #                 else:
    #                    return 'kanji',[jp_morph.pick_highest_charrate(Cluster,['han'])[0] for Cluster in self.kanji_clusters]

    def homonymity_check(self,MecabWds):
        Bool=True; PrvPron=None
        for MecabWd in MecabWds:
            if PrvPron:
                if MecabWd.pronunciation!=PrvPron:
                    Bool=False
                    break
            PrvPron=MecabWd.pronunciation
        return Bool
    
    def cluster_homonyms(self,MecabWds,SortP=False):
        KanaCluster=[ Hom  for Hom in MecabWds if myModule.all_of_chartypes_p(Hom.orth,['hiragana','katakana','roman'],Exceptions=['〜']) ]
        if SortP:
            KanaCluster=sorted(KanaCluster,key=lambda x:x.count,reverse=True)

        KanjiClusters=[]
        for Cntr,Hom in enumerate(set(MecabWds)-set(KanaCluster)):
            if Cntr==0:
                KanjiClusters.append([Hom])
            else:
                for Cluster in KanjiClusters:
                    if homonympair_identical_p(Cluster[-1],Hom):
                        Cluster.append(Hom)
                        break
                else:
                    KanjiClusters.append([Hom])

        if SortP:
            # sorting, inside a kanji cluster
            KanjiClusters=[ sorted(Cluster,key=lambda x:x.count,reverse=True) for Cluster in KanjiClusters ]
            # sorting, between clusters
            if len(KanjiClusters)>=2:
                KanjiClusters=sorted( KanjiClusters, key=lambda x:x[0].count, reverse=True )
#        InterClusterDist=probability.DiscDist({ KanjiCluster[0]:KanjiCluster[0].count for KanjiCluster in KanjiClusters },Smooth=True)
        
        return KanaCluster,KanjiClusters
    #,InterClusterDist

    def order_clusters(self,Criterion='cost'):
        if not self.kanji_clusters:
            OrderedReprs=[self.order_by_countscore(self.kana_cluster)]
        else:
            OrderedReprs=[]
            for KanjiC in self.kanji_clusters:
                OrderedReprs.append(self.order_by_countscore(self.kana_cluster.union(KanjiC)))
        self.ordered_clusters=sorted(OrderedReprs,key=lambda x: x[0].count, reverse=True)
    
    def order_by_countscore(self,OrgWds,RareKanjiScale=4):
        ApplyRKS=False
        Wds=copy.copy(OrgWds)
        RareKanjis= [Wd for Wd in Wds if Wd.count<5 and any(myModule.identify_chartype(Char)=='han' for Char in Wd.orth)]
        if RareKanjis:
            ApplyRKS=True
        WdsScores=[]
        for Wd in Wds:
            if ApplyRKS:
                if Wd in RareKanjis:
                    WdsScores.append((Wd,(Wd.count+1)*RareKanjiScale))
                elif myModule.all_of_chartypes_p(Wd.orth,['hiragana','katakana']):
                    WdsScores.append((Wd,Wd.count//RareKanjiScale))
                else:
                    WdsScores.append((Wd,Wd.count))
            else:
                WdsScores.append((Wd,Wd.count))
        return [ Wd for (Wd,Score) in sorted(WdsScores,key=lambda x:x[1],reverse=True) ]

    def show_summary(self):
        get_wdcntstrs=lambda Cl: [ Wd.orth+' '+str(Wd.count) for Wd in Cl]
        Lines=[]
        Lines.append(self.hiragana_rendering)
        Lines.append(repr(self.cluster_on))
        #Lines.append(repr([Wd.lemma for Wd in self.represent_wds]))
        Lines.append('kana cluster: '+' '.join(get_wdcntstrs(self.kana_cluster)))
        KanjiClustersStr=''
        if self.kanji_clusters:
            for Cl in self.kanji_clusters:
                KanjiClustersStr+=' '.join(get_wdcntstrs(Cl))+' / '
        Lines.append('kanji clusters: '+KanjiClustersStr)
        if self.exemplar:
            Lines.append('Exemplar exists')
        Lines.append(repr([Wd.orth for Wd in self.represent_wds]))

        #LineElsIKD=[]
#        if len(self.kanji_clusters)>=2:
 #           for (Evt,Prob) in self.interkanji_dist.evtprob.items():
  #              LineElsIKD.append(Evt.orth+str(Prob))
        #Lines.append('kanji-conversion ratio '+' '.join(LineElsIKD))
        return '\n'.join(Lines)

def larger_smaller(El1,El2,Lambda):
    Figures=Lambda(El1),Lambda(El2)
    if Figures[0]==Figures[1]:
        return (None,None),None,0
    elif Figures[0]<Figures[1]:
        Smaller=El1;Larger=El2;HigherIndex=1;LowerIndex=0
    else:
        Smaller=El2;Larger=El1;HigherIndex=0;LowerIndex=1
    Rate=Figures[LowerIndex]/Figures[HigherIndex]
    return (Smaller,Larger),HigherIndex,Rate
    
def output_model_text(Homs,Out):
    FSw=open(Out,'wt')
    for Hom in Homs:
        try:
            ClusterStr=Hom.show_summary()
        except:
            Hom.show_summary()
        FSw.write(ClusterStr+'\n\n')
        
    FSw.close()

            
def create_clustered_homonyms(CorpusFPs,LexFP,FtNums):
    print('\nfirst we do the raw counts')
    ClusteredWds=count_variants(CorpusFPs)
    print('\nnow we collect non-ocurring items from the lexicon')
    ClusteredWds=augment_withnulloccs(ClusteredWds,FtNums,LexFP)
    print('\nnow we cluster homonyms')
    ClusteredHoms=normalise_clustered_wds(ClusteredWds)
    return ClusteredHoms

def normalise_mecab(Files, WdsRepls, LorC='corpus',Debug=0):
    for File in Files:
        print('normalising '+File)
        normalise_mecab_file(File,WdsRepls,LorC,Debug=Debug)

def normalise_mecab_file(InputFP,WdsRepls,LexOrCorpus,OutputDiff=True,Debug=0):

    def return_match_ifany(Line,LinesRepls,LexOrCorpus,Regex):
        if LexOrCorpus=='lex':
            LineForm=re.sub(Regex,'\t',Line)
        elif LexOrCorpus=='simplelex':
            LineForm=Line.split('\t')[0]
        else:
            LineForm=Line
        if LineForm in LinesRepls.keys():
            ToReturn=LinesRepls[LineForm]
        else:
            ToReturn=None
        return ToReturn

    LinesRepls={ Wd.get_mecabline():Repl for (Wd,Repl) in WdsRepls.items() }

    FSr=open(InputFP)
    FSw=open(InputFP+'.normed','wt')

    Regex=re.compile(r',([0-9]+,){3}')
    if Debug:
        TgtLines=set([Line for Line in LinesRepls.keys()])
        SrcLinesUpTo100k=set();AllP=False
        for i in range(100000):
            Next=FSr.readline()
            if not Next:
                AllP=True
                break
            else:
                SrcLinesUpTo100k.add(Next.strip())
        if LexOrCorpus=='lex':
            SrcLinesUpTo100k={re.sub(Regex,'\t',Line) for Line in SrcLinesUpTo100k}
        Intersect=TgtLines.intersection(SrcLinesUpTo100k)
            
        FSr.seek(0)

        if not Intersect:
            if AllP:
                print('there is no match, no point processing')
            else:
                print('there is no match for the first 100k, probable that there is none')
    if OutputDiff:
        FSwDiff=open(InputFP+'.diff','wt')
    show_linediff=lambda LiNe1,LiNe2: LiNe1.strip()+'\n'+LiNe2.strip()
    for Cntr,LiNe in enumerate(FSr):
        Alt=return_match_ifany(LiNe.strip(),LinesRepls,LexOrCorpus,Regex)
        if Alt:
            AmbP=False
            if LexOrCorpus=='corpus':
                if isinstance(Alt,mecabtools.MecabWdParse):
                    Picked=Alt
                else:
                    Picked=probability.rand_biased(Alt)
                    AmbP=True
                NewLiNe=Picked.get_mecabline()+'\n'

                if OutputDiff:
                    if AmbP:
                        FSwDiff.write('ambiguous case, competitors are: ')
                        FSwDiff.write(repr([(Wd.orth,Prob) for (Wd,Prob) in Alt.evtprob.items()])+'\n')
                    FSwDiff.write(show_linediff(LiNe,NewLiNe)+'\n\n')

                FSw.write(NewLiNe)
            else:
                print('found')
                pass
        else:
            FSw.write(LiNe)
    if OutputDiff:
        FSwDiff.close()
    FSr.close();FSw.close()


def extract_wds2normalise(HomCs,Debug=0):
    Wds2Normalise={}
    for HomC in HomCs:
        # if the representative is all-kana, we render everything that representative
        if HomC.represent_type=='kana':
            # that means the targets are everything except the representative itself
            Wds2Change2Kana=HomC.kana_cluster[1:]+myModule.flatten_list(HomC.kanji_clusters)
            for Wd2Change2Kana in Wds2Change2Kana:
                Wds2Normalise[Wd2Change2Kana]=HomC.represent_wd
        # on the other hand if it includes kanji, we keep the top ranked element in each cluster
        elif HomC.represent_type=='kanji':
            for KanaWd in HomC.kana_cluster:
                IKD=HomC.interkanji_dist
                KanjiWd=(list(IKD.evtprob.keys())[0] if IKD.evtcount==1 else IKD)
                Wds2Normalise[KanaWd]=KanjiWd
            for KanjiC in HomC.kanji_clusters:
                for NonTopKanjiWd in KanjiC[1:]:
                    Wds2Normalise[NonTopKanjiWd]=KanjiC[0]
    return Wds2Normalise


def pick_corefts(Fts):
    return tuple([(NumsFts[Num],Fts[Num]) for Num in CoreFtNums])
    

def count_variants(MecabCorpusFPs):
    CumCoreFtsCnts={}
    for FP in MecabCorpusFPs:
        CoreFtsCntsPerCorpus=mecabtools.count_words(FP)
        CumCoreFtsCnts=myModule.merge_countdics(CumCoreFtsCnts,CoreFtsCntsPerCorpus)
    
    ClusteredWdsCnts=wdscnts2clusteredcnts(CumCoreFtsCnts)
    return ClusteredWdsCnts

def wdscnts2clusteredcnts(WdsCnts):
    Clustered={}

    for (Wd,Fts),Cnt in WdsCnts.items():
        
        FtsDic={'orth':Wd}
        for Num in range(9):
            FtsDic[NumsFts[Num]]=Fts[Num]
        # here you make an wd obj
        MWd=mecabtools.MecabWdParse(**FtsDic)
        MWd.set_count(Cnt)
        RelvFts=pick_corefts(Fts)
        #tuple([ (NumsFts[Num],Fts[Num]) for Num in ClusterOn ])
        
        if RelvFts not in Clustered.keys():
            Clustered[RelvFts]={MWd}
        else:
            Clustered[RelvFts].add(MWd)
    ClusteredMoreThan1={ Header:Wds for Header,Wds in Clustered.items() if len(Wds)>=2 }
    return ClusteredMoreThan1


def wdcnt2wdfts(CoreFts,WdsCnts):
    WdFts=[]
    for (Wd,OtherFts) in WdsCnts:
        WdFts.append((Wd,CoreFts[:-1]+OtherFts+CoreFts[-1:]))
    return WdFts

def augment_withnulloccs(ClusteredWds,FtNums,LexFP):
    for Cntr,LexLiNe in enumerate(open(LexFP)):
        if not mecabtools.not_proper_jp_p(LexLiNe):
            WdFtPairInLex=mecabtools.line2wdfts(LexLiNe,'dic')
            Orth,FtsLex=WdFtPairInLex
            if len(FtsLex)!=9:
                sys.stderr.write('something wrong with Line: '+str(Cntr+1)+' '+LexLiNe)
                continue
            Fts={}
            Fts['orth']=Orth
            Fts.update([ (NumsFts[Cntr],Val) for (Cntr,Val) in enumerate(FtsLex) ])
            WdInLex=mecabtools.MecabWdParse(**Fts)
            WdInLex.lexpos=Cntr+1
            CoreFtsLexLine=tuple([(NumsFts[Column-1],FtsLex[Column-1]) for Column in FtNums])
            # check if the dic entry is in the cluster set
            if CoreFtsLexLine in ClusteredWds.keys():
                # if it is, check the whole entry exists in it by checking noncore features match
                Cluster=ClusteredWds[CoreFtsLexLine]
                Fnd=False
                for WdInCorpus in Cluster:
                    if all(WdInCorpus.__dict__[NonCoreFt] == WdInLex.__dict__[NonCoreFt] for NonCoreFt in NonCoreFts):
                        Fnd=True
                        WdInCorpus.lexpos=Cntr+1
                        break
                if not Fnd:
                    WdInLex.count=0
                    ClusteredWds[CoreFtsLexLine].add(WdInLex)
                    
    return ClusteredWds

def sift_list_relv_irrelv(List,Conditions=[],CntrConditions=[]):
    Relvs = []; Irrelvs = []
    for Cntr,El in enumerate(List):
        if all(Condition(El) for Condition in Conditions) and all(CntrCondition(Cntr) for CntrCondition in CntrConditions):
            Relvs.append(El)
        else:
            Irrelvs.append(El)
    return tuple(Relvs),tuple(Irrelvs)
            

def normalise_clustered_wds(ClusteredWds,Exclude=(),Debug=0):
    FtsReprs=[]
    for CoreFts,Cluster in ClusteredWds.items():
        Cluster=list(Cluster)
        if len(Cluster)==1:

            sys.stderr.write('no ambiguity\n')
#            sys.stdout.write(Lines[0]+'\n')
        else:
            if Debug:
                sys.stderr.write('\ncandidates')
                sys.stderr.write('\n'+repr([Wd.orth for Wd in Cluster])+'\n')

            MyHoms=ClusteredHomonyms(Cluster,CoreFts)
            if Debug:
                print(MyHoms.show_summary())
            FtsReprs.append(MyHoms)
    
    return FtsReprs


def reduce_infwds(LexemeClusters,Debug=0):
    #WdFts should be a pair, word and features
    NewLexCs=OrderedDict()
    for LexemeFts,Lines in LexemeClusters.items():
        if LexemeFts[0] in ('動詞','形容詞'):
            ReprLineEls=reduce_infwd(LexemeFts,Lines)
            NewLexCs[LexemeFts]=[','.join(ReprLineEls)]
        else:
            NewLexCs[LexemeFts]=Lines
    return NewLexCs

def reduce_infwd(LexemeFts,Lines):
    def change_last_char(Str):
        if Str[-1]=='う':
            return Str[:-1]+'w'
        elif Str[-1]=='え':
            return Str[:-1]
        else:
            return Str[:-1]+romkan.to_hepburn(Str[-1])[0]

    (PoS,SubCat,_,_,InfType,InfCat)=LexemeFts

    ReprLineEls=next(Line for Line in Lines if Line.split(',')[9]=='基本形').split(',')
    DanGyo=InfType.split('・')
    if DanGyo[0]=='五段':
        ReprLineEls=[ change_last_char(ReprLineEl) if Cntr==0 or Cntr>=10 else ReprLineEl for (Cntr,ReprLineEl) in enumerate(ReprLineEls)  ]
            
    elif DanGyo[0]=='一段' or PoS=='形容詞':
        ReprLineEls=[ ReprLineEl[:-1] if Cntr==0 or Cntr>=10 else ReprLineEl for (Cntr,ReprLineEl) in enumerate(ReprLineEls)  ]

    return ReprLineEls


def choose_from_homonyms(Homs):        
    return Homs.pop(),Homs

#### CORE STUFF #####
def homonympair_identical_p(Homonym1,Homonym2):
    # trivial case
    if Homonym1.orth==Homonym2.orth:
        Bool=True
    else:
        # default is true
        Bool=True
        # but don't accept kanji-only pairs as synonyms
        if all(myModule.all_of_chartypes_p(Homonym.orth,['han']) for Homonym in (Homonym1,Homonym2)):
            Bool=False
        # otherwise, we take all the kanjis from each and if one does not contain another, we say they're not synonyms
        Kanjis1={ Char for Char in Homonym1.orth if myModule.identify_type_char(Char)=='han'}
        Kanjis2={ Char for Char in Homonym2.orth if myModule.identify_type_char(Char)=='han'}
        if not (Kanjis1.issubset(Kanjis2) or Kanjis2.issubset(Kanjis1)):
            Bool=False
        #otherwise it's a synonym
        else:
            Bool=True
            
    return Bool



def cluster_possibly_ambiguous_p(Cluster):
    KanaTypes=['hiragana','katakana','roman']
    KanjiContained=[Wd for Wd in Cluster if not myModule.all_of_chartypes_p(Wd.orth,KanaTypes)]
    if Debug:
        print([Wd.orth for Wd in Cluster])
    #if theres no kanji, they're just the same
    if not KanjiContained:
        Bool= False
    else:
        Bool=any(not homonympair_identical_p(Wd1,Wd2) for (Wd1,Wd2) in itertools.combinations(Cluster,2))

    if Debug:
        DebugStr=('ambiguous' if Bool else 'unambiguous')
        print(DebugStr+'\n')
        
    return Bool


        
def main():
    import argparse,glob

    APsr=argparse.ArgumentParser()
    APsr.add_argument('-l','--lexicon-dir',required=True)
    APsr.add_argument('mecab_corpus_dir')
    APsr.add_argument('--debug',type=int,default=0)
    APsr.add_argument('--previous-clusteredhoms',default=None)
    APsr.add_argument('--additional-lexs',nargs='+',default=[])
    #APsr.add_argument('--corpus-only',action='store_true')
    APsr.add_argument('--unnormalisable-unmark',action='store_true')
    APsr.add_argument('--output-text',action='store_true')
    APsr.add_argument('-f','--freq-word-fp')
    APsr.add_argument('-e','--exemplar-fp')
    
    Args=APsr.parse_args()

    FPSets=[]
    for Dir,Ext in ((Args.lexicon_dir,'csv'),(Args.mecab_corpus_dir,'mecab')):
        if not os.path.isdir(Dir):
            sys.exit('\n\nspecified dir does not exist: '+Dir+'\n')
        else:
            FPs=glob.glob(os.path.join(Dir,'*.'+Ext))
            if not FPs:
                sys.exit('\n\nno right file in specified dir: '+Dir+'\n')
            else:
                FPSets.append(FPs)
        
    # generally, the exemplar file should be in the lex dir, the frequency file in the corpusdir
    AssistFPs=[ (Type,AssistFP) for (Type,AssistFP) in (('freq_word_fp',Args.freq_word_fp),('exemplar_fp',Args.exemplar_fp)) if AssistFP ]
    for Type,AssistFP in AssistFPs:
        if '/' not in AssistFP:
            Dir=Args.mecab_corpus_dir if Type=='freq_word_fp' else Args.lexicon_dir
            FP=os.path.join(Dir,AssistFP)
            if os.path.isfile(FP):
                Args.__dict__[Type]=FP
            else:
                sys.exit('AssistFP '+FP+' does not exist')
        
    main0(FPSets[0],FPSets[1],FreqWdFP=Args.freq_word_fp,ProbExemplarFP=Args.exemplar_fp,UnnormalisableMarkP=not Args.unnormalisable_unmark)




if __name__=='__main__':
    main()
