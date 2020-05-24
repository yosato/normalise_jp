from transformers import BertModel,BertTokenizer
from torch import tensor

def main(Seqs,ModelType,ModelPath):
    if ModelType=='bert':
        Embs=get_bert_embeddings(Seq,ModelPath)
    return Embs

def get_bert_embeddings(Seq,ModelPath):
    BTsr=BertTokenizer.from_pretrained(ModelPath)
    Model=BertModel.from_pretrained(ModelPath)
    Toks=BTsr.wordpiece_tokenizer.tokenize(Seq)
    Embs=Model(BTsr.convert_tokens_to_ids(Toks))[0][0]
    return Embs


if __name__=='__main__':
    import argparse
    Psr=argparse.ArgumentParser()
    Psr.add_argument('seq')
    Psr.add_argument('model_type')
    Psr.add_argument('model_path')
    Args=Psr.parse_args()
    main(Args.seq,Args.model_type,Args.model_path)
