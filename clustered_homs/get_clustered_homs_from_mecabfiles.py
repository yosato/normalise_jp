import normalise_mecab
import sys,os,imp,glob,pickle

imp.reload(normalise_mecab)

def main(FPs):
    return normalise_mecab.get_clustered_homs_files(FPs,['cat','subcat','subcat2','infpat','pronunciation'],CorpusOrDic='corpus')

if __name__=='__main__':
    InDir=sys.argv[1]
    OutDir=sys.argv[2]
    FPs=[]
    for FType in ['TKC','KYT','KSJ']:
        FPs.extend(glob.glob(InDir+'/'+FType+'*.txt'))
    if FPs:
        CHs=main(FPs)
        with open(os.path.join(OutDir,'clustered_homs.pickle'),'bw') as PickleFSw:
            pickle.dump(CHs,PickleFSw)
        
