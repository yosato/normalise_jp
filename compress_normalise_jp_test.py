import unittest,imp,sys,os
from pdb import set_trace

import compress_normalise_jp
import mecabtools
imp.reload(compress_normalise_jp)
imp.reload(mecabtools)

TestPairs=[
    # reru and seru
    ('なにが彼をそうさせるのか考えられない','何 が 彼 を そう s a せ る の か 考え られ な い'),
    # case of unique rendering
    ('そのキュウリがからくなる','その 胡瓜 が 辛 く なr u'),
    # case of exemplar
    ('そういわれても','そう 言w a れ て も'),
    # case of kana rendering
    ('サッパリとしたリンゴ', 'さっぱり と s i た りんご'),
    # case of suffix-kana change
    ('サボったらどうなるかな','さぼr t たら どう なr u かな'),
    # case of elongationb
    ('どーなってもいーや','どうなってもいいや'),
    #
    ('深い切り込みを入れる','深 い 切込み を 入れ る')

]


class TestCompressNormalise(unittest.TestCase):
    def setUp(self):
        HomeDir=os.getenv('HOME')
        DataDir=os.path.join('/links/processedData')
        self.testpairs=TestPairs
        self.explines=[Pair[1] for Pair in TestPairs]
        self.testorgsents=[TestPair[0] for TestPair in TestPairs]
        self.testfp=os.path.join(DataDir,'mecabStdJp/corpora/compress_normalise_test.txt')

        with open(self.testfp,'tw') as FSw:
            FSw.write('\n'.join(self.testorgsents)+'\n')

        self.exemplarfp=os.path.join(DataDir,'dics/compressed/exemplars.txt')
        self.dicloc=os.path.join(DataDir,'dics')
        self.stdmodelloc=os.path.join(DataDir,'models/standard')

    def test_compress_normalise(self):
        ResultNewLines=[]
#        set_trace()
        compress_normalise_jp.main0(self.testfp, self.dicloc, self.stdmodelloc, ExemplarFP=self.exemplarfp, Debug=1)
        OutFP='.'.join(self.testfp.split('.')[:-1])+'.compressed.normed.mecab'
        assert(os.path.isfile(OutFP))
        MecabSentsG=mecabtools.mecabfile2mecabsents(OutFP)
        for Sent in MecabSentsG:
            ResultNewLines.append(Sent.stringify_orths())
        self.maxDiff=None
        self.assertEqual(self.explines,ResultNewLines)

if __name__=='__main__':
    unittest.main()

    
