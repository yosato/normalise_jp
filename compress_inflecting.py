import imp,re,sys,os
import romkan
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
        if Debug>=2:  sys.stderr.write('Org line: '+LiNe)
        if CorpusOrDic=='corpus' and Line=='EOS':
            AsIs=True
        else:
            FtsVals=mecabtools.pick_feats_fromline(Line,('cat','infpat','infform'),CorpusOrDic=CorpusOrDic)
            FtsValsDic=dict(FtsVals)
            #most of the time, you don't compress
            AsIs=True
            if FtsValsDic['cat'] in ('動詞','形容詞','助動詞'):
                # but if they're inflecting, you usually compress
                AsIs=False
                #except it is ichidan renyo and mizen
                if FtsValsDic['infpat']=='一段' and FtsValsDic['infform'] in ('連用形','未然形'):
                    AsIs=True
        if AsIs:
            ToWrite=LiNe
            if Debug>=2:   sys.stderr.write('no change\n')
        else:
            if Debug>=2:
                print('\nPotentially compressable line '+str(Cntr+1)+'\n'+LiNe+'\n')
            OrgWd=mecabtools.mecabline2mecabwd(LiNe,CorpusOrDic=CorpusOrDic,WithCost=True)
            # THIS IS WHERE RENDERING HAPPENS
            try:
                NewWd,Suffix=generate_stem_suffix_wds(OrgWd)
            except:
                generate_stem_suffix_wds(OrgWd)
            NecEls=(NewWd.orth,NewWd.cat,NewWd.subcat,NewWd.infpat,NewWd.infform,NewWd.reading)

            if CorpusOrDic=='dic' and NecEls in NewWds:
                if Debug>=2:
                    sys.stderr.write('Not rendered, already found\n')
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
                if Debug:    sys.stderr.write('rendered: '+ToWrite+'\n')

        Out.write(ToWrite)

#SuffixDicFP='/home/yosato/links/myData/mecabStdJp/dics/compressed/suffixes.csv'
#SuffixWds=[ mecabtools.mecabline2mecabwd(Line,CorpusOrDic='dic') for Line in open(SuffixDicFP) ]

def generate_stem_suffix_wds(OrgMecabWd):
    (Stem,StemReading),Suffix=OrgMecabWd.divide_stem_suffix_radical()

    StemWd=OrgMecabWd.get_variant([('orth',Stem),('infform','語幹'),('reading',StemReading),('pronunciation',StemReading),('suffix','')])
    if not nonstem_wd_p(OrgMecabWd):
        StemWd.infform='語幹'

    SuffixAVs={'orth':Suffix,'lemma':Suffix, 'infform':OrgMecabWd.infform, 'cat':'活用語尾', 'pronunciation':romkan.to_katakana(Suffix)}
    SuffixWd=mecabtools.MecabWdParse(**SuffixAVs)

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
