import imp,re,sys,os

mecabtools=imp.load_source('mecabtools',os.path.join(os.getenv('HOME'),'myProjects/myPythonLibs/mecabtools/mecabtools.py'))
import mecabtools
from pythonlib_ys import main as myModule
from pythonlib_ys import jp_morph
imp.reload(mecabtools)
imp.reload(jp_morph)

#Debug=2

def main0(MecabFP,CorpusOrDic='dic',OutFP=None,Debug=0):
    NewWds=set()
    if OutFP is True:
        Stem,Ext=myModule.get_stem_ext(MecabFP)
        Out=open(Stem+'.compressed.'+Ext,'wt')
    elif OutFP is None or OutFP is False:
        Out=sys.stdout
    else:
        Out=open(OutFP,'wt')

    Consts=myModule.prepare_progressconsts(MecabFP)
    MLs=None
    FSr=open(MecabFP)
    for Cntr,LiNe in enumerate(FSr):
        if (Cntr+1)%1000==0:
            MLs=myModule.progress_counter(MLs,Consts,Cntr)
        Line=LiNe.strip()
        if CorpusOrDic=='corpus' and Line=='EOS':
            AsIs=True
        else:
            FtsVals=mecabtools.pick_feats_fromline(Line,('cat','infpat','infform'),CorpusOrDic=CorpusOrDic)
            FtsValsDic=dict(FtsVals)
            if FtsValsDic['cat'] not in ('動詞','形容詞','助動詞'):
                AsIs=True
            elif FtsValsDic['infpat'].startswith('五段') and FtsValsDic['infform'] not in ('連用タ接続','連用テ接続'):
                AsIs=False
            elif FtsValsDic['infpat']=='一段':
                if FtsValsDic['infform'] not in ('連用形','未然形'):
                    AsIs=False
                else:
                    AsIs=True
            else:
                AsIs=True
        if AsIs:
            ToWrite=LiNe

        else:
            if Debug>=2:
                print('\nPotentially compressable line '+str(Cntr+1)+'\n'+LiNe+'\n')
            OrgWd=mecabtools.mecabline2mecabwd(LiNe,CorpusOrDic=CorpusOrDic,WithCost=True)
            # THIS IS WHERE RENDERING HAPPENS
            NewWd,Suffix=generate_stem_suffix_wds(OrgWd)
            NecEls=(NewWd.orth,NewWd.cat,NewWd.subcat,NewWd.infpat,NewWd.infform,NewWd.reading)

            if CorpusOrDic=='dic' and NecEls in NewWds:
                if Debug:
                    sys.stderr.write('\nNot rendered, already found\n')
                ToWrite=''
            else:
                Line=NewWd.get_mecabline(CorpusOrDic=CorpusOrDic)
                if Debug>=1:
                    print('Rendered, '+OrgWd.orth+' ->'+NewWd.orth+'\n')
                if CorpusOrDic=='dic':
                    NewWds.add(NecEls)
                    ToWrite=Line+'\n'
                else:
                    if Suffix:
                        ToWrite=Line+'\n'+Suffix.get_mecabline(CorpusOrDic='corpus')+'\n'
                    else:
                        ToWrite=Line+'\n'

        Out.write(ToWrite)

SuffixDicFP='/home/yosato/links/myData/mecabStdJp/dics/compressed/suffixes.csv'
SuffixWds=[ mecabtools.mecabline2mecabwd(Line,CorpusOrDic='dic') for Line in open(SuffixDicFP) ]

def generate_stem_suffix_wds(OrgMecabWd):
    (Stem,StemReading),Suffix=OrgMecabWd.divide_stem_suffix_radical()
    #    LenSuffix=len(Suffix)
    
#    if (LenSuffix==1 or LenSuffix==2) and not myModule.is_kana(Suffix[0]):
 #       NewReading=MecabWd.reading[:-LenSuffix]+Stem[:-LenSuffix]
  #  else:
   #     NewReading=re.sub(r'%s$'%myModule.render_katakana(Suffix),'',MecabWd.reading)
    StemWd=OrgMecabWd.get_variant([('orth',Stem),('reading',StemReading),('pronunciation',StemReading),('suffix','')])
    if not nonstem_wd_p(OrgMecabWd):
        StemWd.infform='語幹'
    SuffixWd=next(Wd for Wd in SuffixWds if Wd.orth==Suffix) if Suffix else ''

    return StemWd,SuffixWd

def nonstem_wd_p(Wd):
    DefBool=False
    if any(Wd.infform==Form for Form in ('未然特殊','連用タ接続')) or Wd.infpat=='一段' and any(Wd.infform==Form for Form in ('連用','未然')):
        return not DefBool
    return DefBool

def already_seen(NewWd,Wds):
    DefBool=False
    for Wd in Wds:
        if Wd.feature_identical(NewWd,Excepts=('costs')):
            return not DefBool
    return DefBool

def main():
    import argparse
    APsr=argparse.ArgumentParser(description='''
      compress mecab dic/corpus inflecting items on mecab dic/corpus
      does *not* do the mecab parsing itself (use the wrapper, compress_normalise_jp.py if you start from the raw corpus)
    ''')
    APsr.add_argument('mecab_fp')
    APsr.add_argument('--out-fp',default=None)
    APsr.add_argument('--debug',type=int,default=1)
    Args=APsr.parse_args()

    if Args.mecab_fp.endswith('.csv'):
        CorpusOrDic='dic'
    elif Args.mecab_fp.endswith('.mecab'):
        CorpusOrDic='corpus'
    else:
        sys.exit('\n\nmecabfile should end with either csv (dic) or mecab (corpus)\n\n')
    if Args.out_fp=='True':
        OutFP=True
    else:
        OutFP=Args.out_fp
        
    main0(Args.mecab_fp,CorpusOrDic=CorpusOrDic,OutFP=OutFP,Debug=Args.debug)
    
if __name__=='__main__':
    main()
