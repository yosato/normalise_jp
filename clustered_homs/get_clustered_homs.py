import normalise_mecab
import sys,os,imp,glob,pickle

imp.reload(normalise_mecab)

def main(FPs):
    return normalise_mecab.get_clustered_homs_files(FPs,['cat','subcat','subcat2','infpat','pronunciation'],CorpusOrDic='corpus')

if __name__=='__main__':
    Dir=sys.argv[1]
    FPs=glob.glob(Dir+'/*.txt')
    if FPs:
        CHs,Errors=main(FPs)
        with open(os.path.join(Dir,'clustered_homs.pickle'),'bw') as PickleFSw:
            pickle.dump(CHs,PickleFSw)
                    
