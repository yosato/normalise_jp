import normalise_mecab
import sys,os,imp,glob,pickle

imp.reload(normalise_mecab)

def main(FPs,validateP=True):
    return normalise_mecab.get_clustered_homs_files(FPs,['cat','subcat','subcat2','infpat','pronunciation'],FileValidateP=validateP,CorpusOrDic='corpus')

if __name__=='__main__':
    import argparse
    psr=argparse.ArgumentParser()
    psr.add_argument('input_dir')
    psr.add_argument('--output-dir')
    myArgs=psr.parse_args()
    if not myArgs.output_dir:
        myArgs.output_dir=myArgs.input_dir
    FPs=glob.glob(myArgs.input_dir+'/*.mecab')
    if FPs:
        CHs=main(FPs,validateP=False)
        with open(os.path.join(myArgs.output_dir,'clustered_homs.pickle'),'bw') as PickleFSw:
            pickle.dump(CHs,PickleFSw)
        
