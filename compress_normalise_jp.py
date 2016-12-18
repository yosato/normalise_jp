import imp,sys,os,subprocess,glob
import compress_inflecting, normalise_mecab
from pythonlib_ys import main as myModule
imp.reload(compress_inflecting)
imp.reload(normalise_mecab)


def main0(StdJpTxtFP,DicLoc,StdModelLoc,ExemplarFP=None,FreqWdFP=None):
    # first do the compression on dic and corpus
    #CmpDicFPs=build_compressed_dic(StdModelLoc)
    CmpDicFPs=glob.glob(os.path.join(DicLoc,'compressed','*.csv'))
    CmpMecabFP=myModule.change_stem(myModule.change_stem(StdJpTxtFP,'.std',AddOrRemove='remove'),'.compressed')
    myModule.ask_filenoexist_execute(CmpMecabFP,build_compressed_corpus,([StdJpTxtFP,StdModelLoc,CmpMecabFP],{}))
    
    # do normalisation of the corpus
    FinalMecabFP=myModule.change_stem(CmpMecabFP,'.normed')
    ExemplarFP=os.path.join(DicLoc,'compressed','exemplars.txt') if not ExemplarFP else ExemplarFP
    FreqWdFP=os.path.join(os.path.dirname(StdJpTxtFP),'freqwds.txt') if not FreqWdFP else FreqWdFP
    normalise_mecab.main0(CmpDicFPs,[CmpMecabFP],ProbExemplarFP=ExemplarFP,FreqWdFP=FreqWdFP,OutFP=FinalMecabFP,CorpusOnly=True,UnnormalisableMarkP=True)
    # do another mecab parsing with a compressed model
#    do_mecab_parse(GluedMecabFP,CNModelLoc,OutFP=FinalMecabFP)

def do_mecab_parse(InFP,ModelDir,OutFP,WakatiOnly=False):
    Wakati='' if not WakatiOnly else '-o wakati'
    Cmd=' '.join(['mecab -d',Wakati,ModelDir,InFP,'>', OutFP])
    Proc=subprocess.Popen(Cmd,shell=True)
    Proc.communicate()

def build_compressed_dic(StdModelLoc):
    
    StdDicFP=os.path.join(StdModelLoc,'inflecting.csv')
    CmpDicDir=os.path.join(os.path.dirname(StdDicFP),'compressed')
    if not os.path.isdir(CmpDicDir):
        os.makedirs(CmpDicDir)
    CmpDicFN=os.path.basename(StdDicFP)
    CmpDicFN=myModule.change_stem(os.path.basename(StdDicFP),'.compressed')
    CmpDicFP=os.path.join(CmpDicDir,CmpDicFN)
    
    compress_inflecting.main0(StdDicFP,CorpusOrDic='dic',OutFP=CmpDicFP)
    return CmpDicFP

def build_compressed_corpus(StdJpTxtFP,StdModelLoc,CmpMecabFP):
    # do mecab parsing with the standard text
    StdMecabFP=StdJpTxtFP+'.std.mecab'
    do_mecab_parse(StdJpTxtFP,StdModelLoc,OutFP=StdMecabFP)
    # do compression of the above
    compress_inflecting.main0(StdMecabFP,CorpusOrDic='corpus',OutFP=CmpMecabFP)
    return CmpMecabFP
    
def main():
    import argparse
    ArgPsr=argparse.ArgumentParser(description='''
     to be written
    ''')
    ArgPsr.add_argument('raw_fp')
    ArgPsr.add_argument('dic_loc')
    ArgPsr.add_argument('--std-modeldir','-d')
    ArgPsr.add_argument('--exemplar-fp','-e')
    ArgPsr.add_argument('--freqwd-fp','-f')
    Args=ArgPsr.parse_args()

    if not os.path.isfile(Args.raw_fp):
        sys.exit('\n\n  source file not found \n')

    if not os.path.isdir(Args.std_modeldir):
        sys.exit('\n\n  model dir not found \n')

    if (Args.exemplar_fp is not None and not os.path.isfile(Args.exemplar_fp)) or (Args.freqwd_fp is not None and not os.path.isfile(Args.freqwd_fp)):
        sys.exit('\n\n one of the assisting files for normalisations (exemplar, freqwd) not found\n')
        
    
    main0(Args.raw_fp,Args.dic_loc,Args.std_modeldir,ExemplarFP=Args.exemplar_fp,FreqWdFP=Args.freqwd_fp)

if __name__=='__main__':
    main()
